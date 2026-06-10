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
    searchQuery: '',
    quickReplies: [],
    notifyAll: localStorage.getItem('notifyAll') === 'true'
  }),

  actions: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', this.theme)
      document.documentElement.setAttribute('data-theme', this.theme)
    },

    _shouldIncludeTicket(ticket, filter) {
      if (!ticket) return false
      const userId = this.user ? this.user.id : null
      const status = ticket.status
      const ticketUserId = ticket.user ? (typeof ticket.user === 'object' ? ticket.user.id : ticket.user) : null
      
      if (filter === 'mine') {
        return ticketUserId === userId && (status === 'open' || status === 'pending')
      } else if (filter === 'unassigned') {
        return !ticketUserId && (status === 'open' || status === 'pending')
      } else if (filter === 'closed') {
        return status === 'closed'
      } else if (filter === 'all') {
        return this.userRole === 'admin' && (status === 'open' || status === 'pending')
      }
      return false
    },

    _sortTicketsByDate(tickets) {
      return tickets.sort((a, b) => {
        const dateA = a.updated_at || ''
        const dateB = b.updated_at || ''
        if (dateA === dateB) return 0
        return dateA < dateB ? 1 : -1
      })
    },

    _processOrUpdateTicket(ticket) {
      if (!ticket) return
      
      // Update myTickets list
      const myTicketsIndex = this.myTickets.findIndex(t => t.id === ticket.id)
      const belongsToMine = this._shouldIncludeTicket(ticket, 'mine')
      if (belongsToMine) {
        if (myTicketsIndex !== -1) {
          this.myTickets[myTicketsIndex] = { ...this.myTickets[myTicketsIndex], ...ticket }
        } else {
          this.myTickets.unshift(ticket)
        }
        this._sortTicketsByDate(this.myTickets)
      } else {
        if (myTicketsIndex !== -1) {
          this.myTickets.splice(myTicketsIndex, 1)
        }
      }

      // Update tickets list based on currentFilter
      const ticketsIndex = this.tickets.findIndex(t => t.id === ticket.id)
      const belongsToFiltered = this._shouldIncludeTicket(ticket, this.currentFilter)
      if (belongsToFiltered) {
        if (ticketsIndex !== -1) {
          this.tickets[ticketsIndex] = { ...this.tickets[ticketsIndex], ...ticket }
        } else {
          this.tickets.unshift(ticket)
        }
        this._sortTicketsByDate(this.tickets)
      } else {
        if (ticketsIndex !== -1) {
          this.tickets.splice(ticketsIndex, 1)
        }
      }
    },

    _handleIncomingMessage(message) {
      const ticketId = message.ticket
      const isCurrentActive = this.activeTicket && this.activeTicket.id === ticketId
      
      const updateTicketFields = (ticket) => {
        let preview = message.body
        if (!preview && message.media_type) {
          const types = { 'image': '📷 Foto', 'audio': '🎵 Áudio', 'video': '🎥 Vídeo', 'document': '📄 Documento' }
          preview = types[message.media_type] || 'Nova mídia recebida'
        }
        ticket.last_message = preview
        ticket.updated_at = new Date().toISOString()
        if (!message.from_me && !isCurrentActive) {
          ticket.unread_count = (ticket.unread_count || 0) + 1
        }
      }

      // Update active ticket
      if (isCurrentActive) {
        updateTicketFields(this.activeTicket)
      }

      // Find indices
      const myIdx = this.myTickets.findIndex(t => t.id === ticketId)
      const tIdx = this.tickets.findIndex(t => t.id === ticketId)

      // If not in either list, it's a new ticket (e.g. brand new contact) or we need to sync
      if (myIdx === -1 && tIdx === -1) {
        this.fetchTickets()
        this.fetchMyTickets()
        return
      }

      if (myIdx !== -1) {
        updateTicketFields(this.myTickets[myIdx])
        this._sortTicketsByDate(this.myTickets)
      }

      if (tIdx !== -1) {
        updateTicketFields(this.tickets[tIdx])
        this._sortTicketsByDate(this.tickets)
      }
    },

    _handleMessageUpdated(message) {
      const ticketId = message.ticket
      
      const updatePreview = (ticket) => {
        ticket.last_message = message.body
      }

      if (this.activeTicket && this.activeTicket.id === ticketId) {
        const index = this.messages.findIndex(m => m.id === message.id || m.message_id === message.message_id)
        if (index !== -1) {
          this.messages[index] = { ...this.messages[index], ...message }
        }
      }

      const myIdx = this.myTickets.findIndex(t => t.id === ticketId)
      if (myIdx !== -1) {
        updatePreview(this.myTickets[myIdx])
      }

      const tIdx = this.tickets.findIndex(t => t.id === ticketId)
      if (tIdx !== -1) {
        updatePreview(this.tickets[tIdx])
      }
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
    toggleNotifyAll() {
      this.notifyAll = !this.notifyAll
      localStorage.setItem('notifyAll', this.notifyAll)
    },
    async fetchAttendants() {
      const response = await axios.get(`/api/v1/users/`)
      this.attendants = response.data
    },

    async transferTicket(ticketId, userId) {
      const response = await axios.post(`/api/v1/tickets/${ticketId}/transfer/`,
        { user_id: userId }
      )
      this.activeTicket = null
      this.messages = []
      this._processOrUpdateTicket(response.data)
    },

    async closeTicket(ticketId, resolution) {
      const response = await axios.post(`/api/v1/tickets/${ticketId}/close/`,
        { resolution }
      )
      this.activeTicket = null
      this.messages = []
      this._processOrUpdateTicket(response.data)
    },

    async deleteTicket(ticketId) {
      await axios.delete(`/api/v1/tickets/${ticketId}/`)
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = null
        this.messages = []
      }
      this.tickets = this.tickets.filter(t => t.id !== ticketId)
      this.myTickets = this.myTickets.filter(t => t.id !== ticketId)
    },

    async updateTicket(ticketId, payload) {
      const response = await axios.patch(`/api/v1/tickets/${ticketId}/`,
        payload
      )
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = { ...this.activeTicket, ...response.data }
      }
      this._processOrUpdateTicket(response.data)
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
      if (this.socket && this.socket.connected) return

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
        // Determina se esta notificação é relevante para o usuário atual
        if (!message.from_me) {
          const isAdmin = this.userRole === 'admin'
          const notifyAll = isAdmin && this.notifyAll
          const isMyTicket = this.user && message.ticket_user_id === this.user.id
          const isInQueue = !message.ticket_user_id // sem atendente → na fila

          const shouldNotify = notifyAll || isMyTicket || isInQueue

          if (shouldNotify) {
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
        }

        if (this.activeTicket && message.ticket === this.activeTicket.id) {
          const exists = this.messages.some(m => m.id === message.id || m.message_id === message.message_id)
          if (!exists) {
            this.messages.push(message)
          }
        }
        // Otimizado: atualizar localmente em vez de fazer fetch
        this._handleIncomingMessage(message)
      })

      this.socket.on('message_updated', (message) => {
        this._handleMessageUpdated(message)
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
          const messages = this.activeTicket.last_messages
          this.activeTicket = { ...this.activeTicket, ...ticket }
          if (!this.activeTicket.last_messages && messages) {
            this.activeTicket.last_messages = messages
          }
        }
        this._processOrUpdateTicket(ticket)
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
      const response = await axios.post(`/api/v1/tickets/${ticketId}/accept/`, {})
      this._processOrUpdateTicket(response.data)
      this.selectTicket(response.data)
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

    async sendMessage(body, quotedMessageId = null) {
      if (!this.activeTicket) return
      const payload = { body }
      if (quotedMessageId) {
        payload.quoted_message_id = quotedMessageId
      }
      const response = await axios.post(`/api/v1/tickets/${this.activeTicket.id}/send_message/`,
        payload
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

    async searchCustomers(query) {
      const response = await axios.get(`/api/v1/customers/search/`, {
        params: { q: query }
      })
      return response.data
    },

    async updateContact(contactId, payload) {
      const response = await axios.patch(`/api/v1/contacts/${contactId}/`, payload)
      return response.data
    },

    async fetchContactAvatar(contactId, refresh = false) {
      try {
        const response = await axios.get(`/api/v1/contacts/${contactId}/avatar/`, {
          params: { refresh }
        })
        const profilePic = response.data.profile_pic
        
        // Atualiza no activeTicket
        if (this.activeTicket && this.activeTicket.contact_details && this.activeTicket.contact_details.id === contactId) {
          this.activeTicket.contact_details.profile_pic = profilePic
        }
        
        // Atualiza na lista de tickets
        const tIdx = this.tickets.findIndex(t => t.contact_details?.id === contactId)
        if (tIdx !== -1) {
          if (!this.tickets[tIdx].contact_details) this.tickets[tIdx].contact_details = {}
          this.tickets[tIdx].contact_details.profile_pic = profilePic
        }
        
        const myIdx = this.myTickets.findIndex(t => t.contact_details?.id === contactId)
        if (myIdx !== -1) {
          if (!this.myTickets[myIdx].contact_details) this.myTickets[myIdx].contact_details = {}
          this.myTickets[myIdx].contact_details.profile_pic = profilePic
        }
        
        return profilePic
      } catch (e) {
        console.error("Erro ao buscar avatar do contato", e)
        return null
      }
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

    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      if (this.socket) {
        this.socket.disconnect()
        this.socket = null
      }
      this.user = null
      this.tickets = []
      this.myTickets = []
      this.activeTicket = null
      this.messages = []
    },

    changeUserStatus(status) {
      if (this.socket && this.socket.connected) {
        this.socket.emit('change_status', { status })
      }
    },

    // Respostas Rápidas (Quick Replies)
    async fetchQuickReplies() {
      try {
        const response = await axios.get('/api/v1/quick-replies/')
        this.quickReplies = response.data
        return response.data
      } catch (e) {
        console.error("Erro ao buscar respostas rápidas", e)
        return []
      }
    },

    async createQuickReply(payload) {
      const response = await axios.post('/api/v1/quick-replies/', payload)
      this.quickReplies.push(response.data)
      return response.data
    },

    async updateQuickReply(id, payload) {
      const response = await axios.patch(`/api/v1/quick-replies/${id}/`, payload)
      const index = this.quickReplies.findIndex(qr => qr.id === id)
      if (index !== -1) {
        this.quickReplies[index] = response.data
      }
      return response.data
    },

    async deleteQuickReply(id) {
      await axios.delete(`/api/v1/quick-replies/${id}/`)
      this.quickReplies = this.quickReplies.filter(qr => qr.id !== id)
    },

    // Agenda de Ausência (Absence Schedule)
    async fetchAbsenceSchedule() {
      try {
        const response = await axios.get('/api/v1/absence-schedules/mine/')
        return response.data
      } catch (e) {
        console.error("Erro ao buscar agenda de ausência", e)
        return null
      }
    },

    async updateAbsenceSchedule(payload) {
      const response = await axios.patch('/api/v1/absence-schedules/mine/', payload)
      return response.data
    }
  }
})
