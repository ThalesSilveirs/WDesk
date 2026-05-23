import { defineStore } from 'pinia'
import axios from 'axios'
import { io } from 'socket.io-client'

export const useChatStore = defineStore('chat', {
  state: () => ({
    user: null,
    tickets: [],
    myTickets: [],
    activeTicket: null,
    messages: [],
    socket: null,
    loading: false,
    currentFilter: 'unassigned', // 'mine', 'unassigned', 'closed', 'all'
    attendants: [],
    userRole: localStorage.getItem('role') || 'attendant',
    theme: localStorage.getItem('theme') || 'dark',
    showBroadcastModal: false
  }),

  actions: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', this.theme)
      document.documentElement.setAttribute('data-theme', this.theme)
    },
    async fetchCurrentUser() {
      try {
        const token = localStorage.getItem('token')
        if (!token) return
        const response = await axios.get('/api/v1/users/me/', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.user = response.data
      } catch (e) {
        console.error("Erro ao buscar perfil do usuário", e)
      }
    },
    async fetchAttendants() {
      const token = localStorage.getItem('token')
      const response = await axios.get(`/api/v1/users/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      this.attendants = response.data
    },

    async transferTicket(ticketId, userId) {
      const token = localStorage.getItem('token')
      await axios.post(`/api/v1/tickets/${ticketId}/transfer/`,
        { user_id: userId },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      this.activeTicket = null
      this.messages = []
      await this.fetchTickets()
      await this.fetchMyTickets()
    },

    async closeTicket(ticketId, resolution) {
      const token = localStorage.getItem('token')
      await axios.post(`/api/v1/tickets/${ticketId}/close/`,
        { resolution },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      this.activeTicket = null
      this.messages = []
      await this.fetchTickets()
      await this.fetchMyTickets()
    },

    async updateTicket(ticketId, payload) {
      const token = localStorage.getItem('token')
      const response = await axios.patch(`/api/v1/tickets/${ticketId}/`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = { ...this.activeTicket, ...response.data }
      }
      return response.data
    },

    async login(username, password) {
      const response = await axios.post(`/api/token/`, { username, password })
      localStorage.setItem('token', response.data.access)
      localStorage.setItem('role', response.data.role)
      this.userRole = response.data.role
      this.initSocket()
      return response.data
    },

    playNotificationSound() {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioCtx.createOscillator()
      const gainNode = audioCtx.createGain()

      oscillator.type = 'sine'
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime) // A5
      oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5) // A4

      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5)

      oscillator.connect(gainNode)
      gainNode.connect(audioCtx.destination)

      oscillator.start()
      oscillator.stop(audioCtx.currentTime + 0.5)
    },

    async requestNotificationPermission() {
      if ('Notification' in window && Notification.permission === 'default') {
        await Notification.requestPermission()
      }
    },

    showNotification(title, body, icon = null) {
      if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
          body,
          icon: icon || '/favicon.ico',
          tag: 'wdesk-notification',
          renotify: true
        })
        notification.onclick = () => {
          window.focus()
          notification.close()
        }
      }
    },

    initSocket() {
      const token = localStorage.getItem('token')
      if (!token) return

      this.requestNotificationPermission()

      const socketUrl = window.location.port === '5173'
        ? `${window.location.protocol}//${window.location.hostname}:3000`
        : window.location.origin
      this.socket = io(socketUrl, {
        auth: { token },
        transports: ['websocket']
      })

      this.socket.on('new_message', (message) => {
        // Se a mensagem não for minha, disparar alerta
        if (!message.from_me) {
          this.playNotificationSound()

          // Só mostra notificação se não estiver com o ticket aberto ou se a janela estiver em segundo plano
          const isCurrentTicket = this.activeTicket && message.ticket === this.activeTicket.id
          if (!isCurrentTicket || document.hidden) {
            const senderName = message.contact_name || 'Novo Cliente'

            let bodyText = message.body
            if (!bodyText && message.media_type) {
              const types = { 'image': '📷 Foto', 'audio': '🎵 Áudio', 'video': '🎥 Vídeo', 'document': '📄 Documento' }
              bodyText = types[message.media_type] || 'Nova mídia recebida'
            }

            const icon = '/favicon.png'
            this.showNotification(`💬 ${senderName}`, bodyText || 'Nova mensagem recebida', icon)
          }
        }

        if (this.activeTicket && message.ticket === this.activeTicket.id) {
          const exists = this.messages.some(m => m.id === message.id || m.message_id === message.message_id)
          if (!exists) {
            this.messages.push(message)
          }
        }
        // Recarregar ambas as listas
        this.fetchTickets()
        this.fetchMyTickets()
      })

      this.socket.on('ticket_updated', (ticket) => {
        if (this.activeTicket && ticket.id === this.activeTicket.id) {
          this.activeTicket = ticket
        }
        this.fetchTickets()
        this.fetchMyTickets()
      })

      this.socket.on('connection_update', (payload) => {
        window.dispatchEvent(new CustomEvent('connection-updated', { detail: payload }))
      })
    },

    async fetchTickets(filter = null) {
      if (filter) this.currentFilter = filter

      this.loading = true
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(`/api/v1/tickets/`, {
          params: { status_filter: this.currentFilter },
          headers: { Authorization: `Bearer ${token}` }
        })
        this.tickets = response.data
      } finally {
        this.loading = false
      }
    },

    async fetchMyTickets() {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(`/api/v1/tickets/`, {
          params: { status_filter: 'mine' },
          headers: { Authorization: `Bearer ${token}` }
        })
        this.myTickets = response.data
      } catch (e) {
        console.error("Erro ao buscar meus tickets", e)
      }
    },

    async acceptTicket(ticketId) {
      const token = localStorage.getItem('token')
      await axios.post(`/api/v1/tickets/${ticketId}/accept/`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await this.fetchTickets()
      await this.fetchMyTickets()
      const newTicket = this.myTickets.find(t => t.id === ticketId)
      if (newTicket) this.selectTicket(newTicket)
    },

    async selectTicket(ticket) {
      this.activeTicket = ticket
      const token = localStorage.getItem('token')

      // Reseta contador no backend
      if (ticket.unread_count > 0) {
        axios.post(`/api/v1/tickets/${ticket.id}/reset_unread/`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        ticket.unread_count = 0
      }

      const response = await axios.get(`/api/v1/tickets/${ticket.id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      this.activeTicket = response.data
      this.messages = response.data.last_messages
    },

    async sendMedia(file) {
      if (!this.activeTicket) return
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`/api/v1/tickets/${this.activeTicket.id}/send_media/`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      const exists = this.messages.some(m => m.id === response.data.id || m.message_id === response.data.message_id)
      if (!exists) {
        this.messages.push(response.data)
      }
    },

    async sendMessage(body) {
      if (!this.activeTicket) return
      const token = localStorage.getItem('token')
      const response = await axios.post(`/api/v1/tickets/${this.activeTicket.id}/send_message/`,
        { body },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Verifica duplicata antes de dar push (caso o socket tenha sido mais rápido)
      const exists = this.messages.some(m => m.id === response.data.id || m.message_id === response.data.message_id)
      if (!exists) {
        this.messages.push(response.data)
      }
    },

    // Ações de CRM
    async createCustomer(payload) {
      const token = localStorage.getItem('token')
      const response = await axios.post(`/api/v1/customers/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async updateContact(contactId, payload) {
      const token = localStorage.getItem('token')
      const response = await axios.patch(`/api/v1/contacts/${contactId}/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    // Configurações da Empresa
    async fetchCompanySettings() {
      const token = localStorage.getItem('token')
      const response = await axios.get(`/api/v1/companies/mine/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async updateCompanySettings(payload) {
      const token = localStorage.getItem('token')
      const response = await axios.patch(`/api/v1/companies/mine/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async resetConversations() {
      const token = localStorage.getItem('token')
      await axios.post(`/api/v1/companies/reset_conversations/`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      this.tickets = []
      this.myTickets = []
      this.activeTicket = null
      this.messages = []
    }
  }
})
