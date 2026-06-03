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
    showBroadcastModal: false,
    notifications: [],
    searchQuery: ''
  }),

  actions: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', this.theme)
      document.documentElement.setAttribute('data-theme', this.theme)
    },
    async fetchCurrentUser() {
      try {
        if (!localStorage.getItem('token')) return
        const response = await axios.get('/api/v1/users/me/')
        this.user = response.data
      } catch (e) {
        console.error("Erro ao buscar perfil do usuário", e)
      }
    },
    addNotification(notification) {
      this.notifications.unshift({
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        title: notification.title,
        body: notification.body,
        timestamp: new Date(),
        read: false,
        ticket_id: notification.ticket_id
      })
    },
    clearNotifications() {
      this.notifications = []
    },
    markAllNotificationsAsRead() {
      this.notifications.forEach(n => n.read = true)
    },
    async fetchAttendants() {
      const response = await axios.get(`/api/v1/users/`)
      this.attendants = response.data
    },

    async transferTicket(ticketId, userId) {
      await axios.post(`/api/v1/tickets/${ticketId}/transfer/`,
        { user_id: userId }
      )
      this.activeTicket = null
      this.messages = []
      await this.fetchTickets()
      await this.fetchMyTickets()
    },

    async closeTicket(ticketId, resolution) {
      await axios.post(`/api/v1/tickets/${ticketId}/close/`,
        { resolution }
      )
      this.activeTicket = null
      this.messages = []
      await this.fetchTickets()
      await this.fetchMyTickets()
    },

    async deleteTicket(ticketId) {
      await axios.delete(`/api/v1/tickets/${ticketId}/`)
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = null
        this.messages = []
      }
      await this.fetchTickets()
      await this.fetchMyTickets()
    },

    async updateTicket(ticketId, payload) {
      const response = await axios.patch(`/api/v1/tickets/${ticketId}/`,
        payload
      )
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = { ...this.activeTicket, ...response.data }
      }
      
      const updateInList = (list) => {
        const index = list.findIndex(t => t.id === ticketId)
        if (index !== -1) {
          list[index] = { ...list[index], ...response.data }
        }
      }
      updateInList(this.tickets)
      updateInList(this.myTickets)

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
            this.addNotification({
              title: `De: ${senderName}`,
              body: bodyText || 'Nova mensagem recebida',
              ticket_id: message.ticket
            })
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

      this.socket.on('message_updated', (message) => {
        if (this.activeTicket && message.ticket === this.activeTicket.id) {
          const index = this.messages.findIndex(m => m.id === message.id || m.message_id === message.message_id)
          if (index !== -1) {
            this.messages[index] = { ...this.messages[index], ...message }
          }
        }
        this.fetchTickets()
        this.fetchMyTickets()
      })

      this.socket.on('message_reactions_updated', (payload) => {
        if (this.activeTicket) {
          const message = this.messages.find(m => m.id === payload.message_id)
          if (message) {
            message.reactions = payload.reactions
          }
        }
      })

      this.socket.on('ticket_updated', (ticket) => {
        if (this.activeTicket && ticket.id === this.activeTicket.id) {
          this.activeTicket = ticket
        }
        this.fetchTickets()
        this.fetchMyTickets()
      })

      this.socket.on('ticket_deleted', (payload) => {
        const ticketId = payload.id
        if (this.activeTicket && this.activeTicket.id === ticketId) {
          this.activeTicket = null
          this.messages = []
        }
        this.tickets = this.tickets.filter(t => t.id !== ticketId)
        this.myTickets = this.myTickets.filter(t => t.id !== ticketId)
      })

      this.socket.on('connection_update', (payload) => {
        window.dispatchEvent(new CustomEvent('connection-updated', { detail: payload }))
      })

      this.socket.on('reset_conversations', () => {
        this.tickets = []
        this.myTickets = []
        this.activeTicket = null
        this.messages = []
      })

      this.socket.on('status_sync', (payload) => {
        window.dispatchEvent(new CustomEvent('user-status-synced', { detail: payload }))
      })

      this.socket.on('user_status_changed', (payload) => {
        const attendant = this.attendants.find(a => a.id === payload.user_id)
        if (attendant) {
          attendant.status = payload.status
        }
        window.dispatchEvent(new CustomEvent('user-status-changed', { detail: payload }))
      })
    },

    async fetchTickets(filter = null) {
      if (filter) this.currentFilter = filter

      this.loading = true
      try {
        const response = await axios.get(`/api/v1/tickets/`, {
          params: { status_filter: this.currentFilter }
        })
        this.tickets = response.data
      } finally {
        this.loading = false
      }
    },

    async fetchMyTickets() {
      try {
        const response = await axios.get(`/api/v1/tickets/`, {
          params: { status_filter: 'mine' }
        })
        this.myTickets = response.data
      } catch (e) {
        console.error("Erro ao buscar meus tickets", e)
      }
    },

    async acceptTicket(ticketId) {
      await axios.post(`/api/v1/tickets/${ticketId}/accept/`, {})
      await this.fetchTickets()
      await this.fetchMyTickets()
      const newTicket = this.myTickets.find(t => t.id === ticketId)
      if (newTicket) this.selectTicket(newTicket)
    },

    async selectTicket(ticket) {
      this.activeTicket = ticket
      // Reseta contador no backend
      if (ticket.unread_count > 0) {
        axios.post(`/api/v1/tickets/${ticket.id}/reset_unread/`, {})
        ticket.unread_count = 0
      }

      const response = await axios.get(`/api/v1/tickets/${ticket.id}/`)
      this.activeTicket = response.data
      
      const sortedMessages = (response.data.last_messages || []).sort((a, b) => {
        const timeDiff = new Date(a.timestamp) - new Date(b.timestamp)
        if (timeDiff !== 0) return timeDiff
        return a.id - b.id
      })
      this.messages = sortedMessages
    },

    async sendMedia(file) {
      if (!this.activeTicket) return
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`/api/v1/tickets/${this.activeTicket.id}/send_media/`,
        formData,
        {
          headers: {
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
      const response = await axios.post(`/api/v1/tickets/${this.activeTicket.id}/send_message/`,
        { body }
      )

      // Verifica duplicata antes de dar push (caso o socket tenha sido mais rápido)
      const exists = this.messages.some(m => m.id === response.data.id || m.message_id === response.data.message_id)
      if (!exists) {
        this.messages.push(response.data)
      }
    },

    async reactToMessage(ticketId, messageId, emoji) {
      try {
        const response = await axios.post(`/api/v1/tickets/${ticketId}/react_message/`, {
          message_id: messageId,
          emoji
        })
        if (this.activeTicket && this.activeTicket.id === ticketId) {
          const message = this.messages.find(m => m.id === messageId)
          if (message) {
            message.reactions = response.data.reactions
          }
        }
      } catch (e) {
        console.error("Erro ao enviar reação", e)
      }
    },

    async editMessage(ticketId, messageId, newBody) {
      try {
        const response = await axios.post(`/api/v1/tickets/${ticketId}/edit_message/`, {
          message_id: messageId,
          body: newBody
        })
        if (this.activeTicket && this.activeTicket.id === ticketId) {
          const message = this.messages.find(m => m.id === messageId)
          if (message) {
            message.body = response.data.message.body
            message.is_edited = response.data.message.is_edited
            message.edited_at = response.data.message.edited_at
          }
        }
      } catch (e) {
        console.error("Erro ao editar mensagem", e)
      }
    },

    // Ações de CRM
    async createCustomer(payload) {
      const response = await axios.post(`/api/v1/customers/`, payload)
      return response.data
    },

    async updateContact(contactId, payload) {
      const response = await axios.patch(`/api/v1/contacts/${contactId}/`, payload)
      return response.data
    },

    // Configurações da Empresa
    async fetchCompanySettings() {
      const response = await axios.get(`/api/v1/companies/mine/`)
      return response.data
    },

    async updateCompanySettings(payload) {
      const response = await axios.patch(`/api/v1/companies/mine/`, payload)
      return response.data
    },

    async resetConversations() {
      const response = await axios.post(`/api/v1/companies/reset_conversations/`, {})
      this.tickets = []
      this.myTickets = []
      this.activeTicket = null
      this.messages = []
      return response.data
    },

    changeUserStatus(status) {
      if (this.socket && this.socket.connected) {
        this.socket.emit('change_status', { status })
      }
    }
  }
})
