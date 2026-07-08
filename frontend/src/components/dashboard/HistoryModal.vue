<template>
  <Transition name="modal-fade">
    <div v-if="show" class="modal-overlay" @click="closeModal">
      <div class="modal-content history-modal-content glass-effect animate-slide-up" @click.stop>
        <!-- Header -->
        <header class="history-modal-header">
          <div class="header-main">
            <div class="title-with-icon">
              <MessageSquareIcon class="title-icon" :size="22" />
              <h2>Histórico de Atendimentos</h2>
            </div>
            <button @click="closeModal" class="close-btn-round" title="Fechar">
              <XIcon :size="20" />
            </button>
          </div>

          <!-- Tabs -->
          <div class="history-tabs" v-if="contactId && customerId">
            <button 
              class="history-tab-btn" 
              :class="{ active: activeTab === 'contact' }"
              @click="setTab('contact')"
            >
              <UserIcon :size="16" />
              <span>Contato: {{ contactName || 'Este Contato' }}</span>
            </button>
            <button 
              class="history-tab-btn" 
              :class="{ active: activeTab === 'customer' }"
              @click="setTab('customer')"
            >
              <BriefcaseIcon :size="16" />
              <span>Empresa: {{ customerName || 'Este Cliente' }}</span>
            </button>
          </div>
          <div class="history-single-tab-title" v-else>
            <span v-if="contactId" class="badge-tab">
              <UserIcon :size="14" /> Contato: {{ contactName || 'Este Contato' }}
            </span>
            <span v-else-if="customerId" class="badge-tab">
              <BriefcaseIcon :size="14" /> Empresa: {{ customerName || 'Este Cliente' }}
            </span>
          </div>
        </header>

        <!-- Body -->
        <div class="history-modal-body">
          <!-- Left Panel: Ticket List -->
          <aside class="tickets-history-list-panel">
            <div v-if="loadingTickets" class="loading-state">
              <div class="spinner"></div>
              <p>Carregando histórico...</p>
            </div>
            <div v-else-if="tickets.length === 0" class="empty-state-history">
              <AlertCircleIcon :size="36" class="empty-icon" />
              <p>Nenhum atendimento anterior encontrado.</p>
            </div>
            <div v-else class="tickets-scroll-container">
              <div 
                v-for="ticket in tickets" 
                :key="ticket.id" 
                class="history-ticket-card"
                :class="{ active: selectedTicket && selectedTicket.id === ticket.id }"
                @click="selectTicket(ticket)"
              >
                <div class="ticket-card-header">
                  <span class="ticket-id">#{{ ticket.id }}</span>
                  <span class="status-badge" :class="ticket.status">
                    {{ getStatusLabel(ticket.status) }}
                  </span>
                </div>
                <h4 class="ticket-subject">{{ ticket.subject || 'Sem Assunto' }}</h4>
                <div class="ticket-meta-info">
                  <div class="meta-row">
                    <CalendarIcon :size="12" />
                    <span>Início: {{ formatDateTime(ticket.created_at) }}</span>
                  </div>
                  <div class="meta-row" v-if="ticket.attendant_details">
                    <UserIcon :size="12" />
                    <span>Atendido por: {{ ticket.attendant_details.first_name }}</span>
                  </div>
                  <div class="meta-row" v-else>
                    <UserIcon :size="12" />
                    <span>Sem atendente (Fila)</span>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          <!-- Right Panel: Ticket Detail & Message Log -->
          <main class="ticket-history-detail-panel">
            <div v-if="!selectedTicket" class="no-selection-state">
              <MessageSquareIcon :size="48" class="no-selection-icon" />
              <h3>Detalhes do Atendimento</h3>
              <p>Selecione um atendimento na lista ao lado para ver o histórico completo de mensagens e sua resolução.</p>
            </div>
            <div v-else class="selected-ticket-content">
              <!-- Meta Card -->
              <div class="detail-meta-card">
                <div class="detail-header-row">
                  <h3>{{ selectedTicket.subject || 'Atendimento Sem Assunto' }}</h3>
                  <span class="status-badge" :class="selectedTicket.status">
                    {{ getStatusLabel(selectedTicket.status) }}
                  </span>
                </div>
                <div class="grid-meta-details">
                  <div class="meta-item">
                    <label>Abertura</label>
                    <span>{{ formatDateTime(selectedTicket.created_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Fechamento / Atualização</label>
                    <span>{{ formatDateTime(selectedTicket.updated_at) }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Atendente</label>
                    <span>{{ selectedTicket.attendant_details ? selectedTicket.attendant_details.first_name : 'Nenhum' }}</span>
                  </div>
                  <div class="meta-item">
                    <label>Prioridade</label>
                    <span class="priority-label" :class="selectedTicket.priority">
                      {{ getPriorityLabel(selectedTicket.priority) }}
                    </span>
                  </div>
                </div>

                <!-- Resolution -->
                <div v-if="selectedTicket.status === 'closed'" class="resolution-box">
                  <div class="resolution-title">
                    <CheckCircleIcon :size="14" class="text-success" />
                    <strong>Resumo da Resolução:</strong>
                  </div>
                  <p>{{ selectedTicket.resolution || 'Nenhuma descrição fornecida para o fechamento.' }}</p>
                </div>
              </div>

              <!-- Message Logs Title -->
              <div class="chat-transcript-title">
                <ClockIcon :size="14" />
                <span>Transcrição da Conversa</span>
              </div>

              <!-- Chat Transcript -->
              <div class="chat-transcript-container">
                <div v-if="loadingMessages" class="loading-state">
                  <div class="spinner"></div>
                  <p>Buscando mensagens...</p>
                </div>
                <div v-else-if="messages.length === 0" class="empty-transcript">
                  <p>Nenhuma mensagem registrada nesse atendimento.</p>
                </div>
                <div v-else class="transcript-scroll-area">
                  <div 
                    v-for="msg in messages" 
                    :key="msg.id || msg.message_id" 
                    class="transcript-msg-row"
                    :class="{ 'sent': msg.from_me, 'received': !msg.from_me }"
                  >
                    <div class="transcript-msg-bubble">
                      <div class="msg-sender" v-if="msg.from_me">
                        {{ msg.user ? msg.user.first_name || msg.user.username : 'Sistema' }}
                      </div>
                      <div class="msg-sender" v-else>
                        {{ contactName || 'Cliente' }}
                      </div>
                      
                      <!-- Media contents -->
                      <div v-if="msg.media_type === 'image'" class="media-body">
                        <img :src="msg.media_url" class="media-img" />
                      </div>
                      <div v-else-if="msg.media_type === 'video'" class="media-body">
                        <video :src="msg.media_url" controls class="media-video"></video>
                      </div>
                      <div v-else-if="msg.media_type === 'audio'" class="media-body">
                        <audio :src="msg.media_url" controls class="media-audio"></audio>
                      </div>
                      
                      <p class="msg-text">{{ msg.body }}</p>
                      <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { 
  X as XIcon, 
  MessageSquare as MessageSquareIcon, 
  User as UserIcon, 
  Briefcase as BriefcaseIcon, 
  Calendar as CalendarIcon, 
  FileText as FileTextIcon,
  CheckCircle2 as CheckCircleIcon,
  Clock as ClockIcon,
  AlertCircle as AlertCircleIcon
} from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  contactId: [Number, String],
  customerId: [Number, String],
  contactName: String,
  customerName: String,
  initialTab: {
    type: String,
    default: 'contact'
  }
})

const emit = defineEmits(['close'])

const activeTab = ref('contact')
const tickets = ref([])
const loadingTickets = ref(false)
const selectedTicket = ref(null)
const messages = ref([])
const loadingMessages = ref(false)

const closeModal = () => {
  emit('close')
}

const setTab = (tab) => {
  activeTab.value = tab
  selectedTicket.value = null
  messages.value = []
  fetchTickets()
}

const fetchTickets = async () => {
  loadingTickets.value = true
  try {
    const params = {}
    if (activeTab.value === 'contact' && props.contactId) {
      params.contact = props.contactId
    } else if (activeTab.value === 'customer' && props.customerId) {
      params.customer = props.customerId
    } else {
      // Fallback
      if (props.contactId) {
        params.contact = props.contactId
      } else if (props.customerId) {
        params.customer = props.customerId
      }
    }

    const response = await axios.get('/api/v1/tickets/', { params })
    tickets.value = response.data
    
    // Auto-select first ticket if available
    if (tickets.value.length > 0) {
      selectTicket(tickets.value[0])
    }
  } catch (err) {
    console.error("Erro ao buscar histórico de atendimentos:", err)
    tickets.value = []
  } finally {
    loadingTickets.value = false
  }
}

const selectTicket = (ticket) => {
  selectedTicket.value = ticket
  fetchMessages(ticket.id)
}

const fetchMessages = async (ticketId) => {
  loadingMessages.value = true
  try {
    const response = await axios.get(`/api/v1/tickets/${ticketId}/messages/`, {
      params: { limit: 100 }
    })
    messages.value = response.data
  } catch (err) {
    console.error("Erro ao buscar mensagens do atendimento:", err)
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    // Determinar aba inicial ativa com base no que está disponível
    if (props.contactId && props.customerId) {
      activeTab.value = props.initialTab || 'contact'
    } else if (props.contactId) {
      activeTab.value = 'contact'
    } else if (props.customerId) {
      activeTab.value = 'customer'
    }
    
    selectedTicket.value = null
    messages.value = []
    fetchTickets()
  }
})

const getStatusLabel = (status) => {
  const map = {
    'open': 'Em aberto',
    'pending': 'Pendente',
    'closed': 'Finalizado'
  }
  return map[status] || status
}

const getPriorityLabel = (priority) => {
  const map = {
    'low': 'Baixa',
    'medium': 'Média',
    'high': 'Alta'
  }
  return map[priority] || 'Média'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.history-modal-content {
  max-width: 950px !important;
  width: 90vw !important;
  height: 80vh !important;
  padding: 0 !important;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
}

.history-modal-header {
  padding: 20px 24px 15px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.01);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: var(--accent);
}

.history-modal-header h2 {
  font-size: 1.4rem;
  margin: 0;
  font-weight: 700;
  color: var(--text-primary);
}

.close-btn-round {
  background: var(--glass);
  border: 1px solid var(--border);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn-round:hover {
  background: var(--border);
  color: var(--text-primary);
  transform: scale(1.05);
}

.history-tabs {
  display: flex;
  gap: 12px;
}

.history-tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.history-tab-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}

.history-tab-btn.active {
  background: rgba(34, 181, 95, 0.1);
  border-color: var(--accent);
  color: var(--accent);
}

.history-single-tab-title {
  display: flex;
}

.badge-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 600;
}

.history-modal-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
}

/* Left Panel */
.tickets-history-list-panel {
  width: 320px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
  overflow: hidden;
}

.tickets-scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-ticket-card {
  padding: 14px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.history-ticket-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.history-ticket-card.active {
  background: rgba(34, 181, 95, 0.05);
  border-color: var(--accent);
  box-shadow: 0 4px 12px rgba(34, 181, 95, 0.05);
}

.ticket-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ticket-id {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  opacity: 0.7;
}

.status-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-badge.open {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status-badge.closed {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.ticket-subject {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 10px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-meta-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Right Panel */
.ticket-history-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
}

.no-selection-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.no-selection-icon {
  color: var(--text-secondary);
  opacity: 0.3;
  margin-bottom: 16px;
}

.no-selection-state h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.no-selection-state p {
  color: var(--text-secondary);
  max-width: 400px;
  font-size: 0.9rem;
  line-height: 1.5;
}

.selected-ticket-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.detail-meta-card {
  padding: 20px 24px;
  background: var(--glass);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.detail-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.detail-header-row h3 {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0;
}

.grid-meta-details {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.meta-item span {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 500;
}

.priority-label {
  display: inline-block;
  font-weight: 600;
}
.priority-label.high { color: #ef4444; }
.priority-label.medium { color: #f59e0b; }
.priority-label.low { color: #94a3b8; }

.resolution-box {
  margin-top: 15px;
  padding: 12px 16px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 8px;
}

.resolution-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  margin-bottom: 4px;
}

.resolution-box p {
  font-size: 0.85rem;
  margin: 0;
  color: var(--text-primary);
  line-height: 1.4;
}

.chat-transcript-title {
  padding: 12px 24px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.1);
}

/* Chat Transcript Areas */
.chat-transcript-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.transcript-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.transcript-msg-row {
  display: flex;
  width: 100%;
}

.transcript-msg-row.sent {
  justify-content: flex-end;
}

.transcript-msg-row.received {
  justify-content: flex-start;
}

.transcript-msg-bubble {
  max-width: 65%;
  padding: 10px 14px;
  border-radius: 12px;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.sent .transcript-msg-bubble {
  background: var(--msg-bubble-sent);
  color: var(--msg-text-sent);
  border-bottom-right-radius: 2px;
}

.received .transcript-msg-bubble {
  background: var(--msg-bubble-received);
  color: var(--msg-text-received);
  border-bottom-left-radius: 2px;
}

.msg-sender {
  font-size: 0.7rem;
  font-weight: 700;
  opacity: 0.8;
  margin-bottom: 2px;
}

.msg-text {
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0;
  word-break: break-word;
  white-space: pre-wrap;
}

.msg-time {
  font-size: 0.65rem;
  align-self: flex-end;
  opacity: 0.6;
}

.media-body {
  margin-bottom: 4px;
  max-width: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.media-img {
  max-width: 100%;
  max-height: 180px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}

.media-video {
  max-width: 100%;
  max-height: 180px;
  border-radius: 6px;
  display: block;
}

.media-audio {
  width: 100%;
  min-width: 200px;
  border-radius: 6px;
  display: block;
}

/* Loading & Empty States */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-secondary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-state-history .empty-icon {
  opacity: 0.4;
  margin-bottom: 12px;
}

.empty-state-history p {
  font-size: 0.85rem;
  line-height: 1.4;
  max-width: 200px;
}

.empty-transcript {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .history-modal-content {
    height: 90vh !important;
    width: 95vw !important;
  }
  
  .history-modal-body {
    flex-direction: column;
  }
  
  .tickets-history-list-panel {
    width: 100%;
    height: 180px;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  
  .tickets-scroll-container {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 10px;
  }
  
  .history-ticket-card {
    width: 240px;
    flex-shrink: 0;
    padding: 10px;
  }
  
  .grid-meta-details {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
}
</style>
