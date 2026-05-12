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
    userRole: localStorage.getItem('role') || 'attendant'
  }),

  actions: {
    async fetchAttendants() {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://${window.location.hostname}:8000/api/v1/users/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      this.attendants = response.data
    },

    async transferTicket(ticketId, userId) {
      const token = localStorage.getItem('token')
      await axios.post(`http://${window.location.hostname}:8000/api/v1/tickets/${ticketId}/transfer/`, 
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
      await axios.post(`http://${window.location.hostname}:8000/api/v1/tickets/${ticketId}/close/`, 
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
      const response = await axios.patch(`http://${window.location.hostname}:8000/api/v1/tickets/${ticketId}/`, 
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (this.activeTicket && this.activeTicket.id === ticketId) {
        this.activeTicket = { ...this.activeTicket, ...response.data }
      }
      return response.data
    },

    async login(username, password) {
      const response = await axios.post(`http://${window.location.hostname}:8000/api/token/`, { username, password })
      localStorage.setItem('token', response.data.access)
      localStorage.setItem('role', response.data.role)
      this.userRole = response.data.role
      this.initSocket()
      return response.data
    },

    initSocket() {
      const token = localStorage.getItem('token')
      if (!token) return

      const socketUrl = `http://${window.location.hostname}:3000`
      this.socket = io(socketUrl, {
        auth: { token },
        transports: ['websocket']
      })

      this.socket.on('new_message', (message) => {
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

      this.socket.on('connection_update', (payload) => {
        // Dispara um evento customizado que as views podem ouvir ou atualiza o estado se necessário
        // Por simplificação, vamos apenas emitir um evento no bus global ou as views podem ter seu próprio listener
        // Mas como as conexões não estão no estado global do chat, vamos usar o dispatch de eventos
        window.dispatchEvent(new CustomEvent('connection-updated', { detail: payload }))
      })
    },

    async fetchTickets(filter = null) {
      if (filter) this.currentFilter = filter
      
      this.loading = true
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(`http://${window.location.hostname}:8000/api/v1/tickets/`, {
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
        const response = await axios.get(`http://${window.location.hostname}:8000/api/v1/tickets/`, {
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
      await axios.post(`http://${window.location.hostname}:8000/api/v1/tickets/${ticketId}/accept/`, {}, {
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
      const response = await axios.get(`http://${window.location.hostname}:8000/api/v1/tickets/${ticket.id}/`, {
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
      
      const response = await axios.post(`http://${window.location.hostname}:8000/api/v1/tickets/${this.activeTicket.id}/send_media/`, 
        formData,
        { headers: { 
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
      const response = await axios.post(`http://${window.location.hostname}:8000/api/v1/tickets/${this.activeTicket.id}/send_message/`, 
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
      const response = await axios.post(`http://${window.location.hostname}:8000/api/v1/customers/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async updateContact(contactId, payload) {
      const token = localStorage.getItem('token')
      const response = await axios.patch(`http://${window.location.hostname}:8000/api/v1/contacts/${contactId}/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    // Configurações da Empresa
    async fetchCompanySettings() {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://${window.location.hostname}:8000/api/v1/companies/mine/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async updateCompanySettings(payload) {
      const token = localStorage.getItem('token')
      const response = await axios.patch(`http://${window.location.hostname}:8000/api/v1/companies/mine/`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },

    async resetConversations() {
      const token = localStorage.getItem('token')
      await axios.post(`http://${window.location.hostname}:8000/api/v1/companies/reset_conversations/`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      this.tickets = []
      this.myTickets = []
      this.activeTicket = null
      this.messages = []
    }
  }
})
