<template>
  <div class="dashboard-content">
    <!-- Sidebar -->
    <aside class="sidebar glass-effect">
      <div class="ticket-list-wrapper top">
        <div class="list-header">
          <h3>Meus Atendimentos</h3>
          <span class="badge green">{{ chatStore.myTickets.length }}</span>
        </div>
        <div class="ticket-list">
          <div 
            v-for="ticket in chatStore.myTickets" 
            :key="ticket.id"
            class="ticket-item"
            :class="{ active: chatStore.activeTicket?.id === ticket.id }"
            @click="chatStore.selectTicket(ticket)"
          >
            <div class="avatar">
              <img v-if="ticket.contact_details?.profile_pic" :src="ticket.contact_details.profile_pic" class="avatar-img" />
              <span v-else>{{ ticket.contact_details?.name?.charAt(0) || 'C' }}</span>
            </div>
            <div class="ticket-info">
              <div class="top">
                <span class="name">{{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}</span>
                <div class="time-unread">
                  <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
                  <span class="time">{{ formatTime(ticket.updated_at) }}</span>
                </div>
              </div>
              <p class="last-msg">
                <span v-if="ticket.priority === 'high'" class="priority-dot high"></span>
                <span v-if="ticket.priority === 'medium'" class="priority-dot medium"></span>
                {{ ticket.last_message || 'Nenhuma mensagem' }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="ticket-list-wrapper bottom">
        <div class="list-header">
          <div class="header-main">
            <h3>{{ chatStore.currentFilter === 'closed' ? 'Histórico' : (chatStore.currentFilter === 'all' ? 'Todos' : 'Fila') }}</h3>
            <span class="badge">{{ chatStore.tickets.length }}</span>
          </div>
          <div class="tabs-top-inline">
            <button 
              class="tab-btn-mini" 
              :class="{ active: chatStore.currentFilter === 'unassigned' }"
              @click="chatStore.fetchTickets('unassigned')"
            >
              Fila
            </button>
            <button 
              class="tab-btn-mini" 
              :class="{ active: chatStore.currentFilter === 'closed' }"
              @click="chatStore.fetchTickets('closed')"
            >
              Fechados
            </button>
            <button 
              v-if="chatStore.userRole === 'admin'"
              class="tab-btn-mini" 
              :class="{ active: chatStore.currentFilter === 'all' }"
              @click="chatStore.fetchTickets('all')"
            >
              Todos
            </button>
          </div>
        </div>
        <div class="ticket-list">
          <div 
            v-for="ticket in chatStore.tickets" 
            :key="ticket.id"
            class="ticket-item"
            :class="{ active: chatStore.activeTicket?.id === ticket.id }"
            @click="chatStore.selectTicket(ticket)"
          >
            <div class="avatar">
              <img v-if="ticket.contact_details?.profile_pic" :src="ticket.contact_details.profile_pic" class="avatar-img" />
              <span v-else>{{ ticket.contact_details?.name?.charAt(0) || 'C' }}</span>
            </div>
            <div class="ticket-info">
              <div class="top">
                <span class="name">{{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}</span>
                <div class="time-unread">
                  <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
                  <span class="time">{{ formatTime(ticket.updated_at) }}</span>
                </div>
              </div>
              <p class="last-msg">{{ ticket.last_message || 'Nenhuma mensagem' }}</p>
              <span v-if="ticket.attendant_details" class="attendant-label">
                {{ ticket.status === 'closed' ? 'Atendido por' : 'Com' }} {{ ticket.attendant_details.first_name }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Chat Area -->
    <main class="chat-area" :class="{ 'with-crm': showCRM }">
      <template v-if="chatStore.activeTicket">
        <div class="chat-main-column">
          <header class="chat-header glass-effect">
            <div class="contact-info">
              <div class="avatar small">
                <img v-if="chatStore.activeTicket.contact_details?.profile_pic" :src="chatStore.activeTicket.contact_details.profile_pic" class="avatar-img" />
                <span v-else>{{ chatStore.activeTicket.contact_details?.name?.charAt(0) }}</span>
              </div>
              <div class="header-text">
                <div class="name-status">
                  <h3>{{ chatStore.activeTicket.contact_details?.name }}</h3>
                  <span class="status-tag" :class="chatStore.activeTicket.status">{{ chatStore.activeTicket.status === 'open' ? 'Em aberto' : (chatStore.activeTicket.status === 'pending' ? 'Pendente' : 'Finalizado') }}</span>
                </div>
                <p class="ticket-subject">{{ chatStore.activeTicket.subject || 'Sem assunto definido' }}</p>
              </div>
            </div>
            <div class="header-actions">
              <div v-if="chatStore.activeTicket.status !== 'closed'" class="priority-selector">
                <button @click="showPriorityModal = true" class="btn-outline-sm priority-btn" :class="chatStore.activeTicket.priority">
                  <span class="dot"></span>
                  <span>Prioridade {{ chatStore.activeTicket.priority === 'high' ? 'Alta' : (chatStore.activeTicket.priority === 'medium' ? 'Média' : 'Baixa') }}</span>
                </button>
              </div>
              
              <button @click="showCRM = !showCRM" class="btn-outline-sm" :class="{ active: showCRM }" title="Informações do Cliente">
                <ContactIcon :size="18" />
                <span>Info</span>
              </button>
              
              <template v-if="chatStore.activeTicket.status !== 'closed'">
                <button v-if="!chatStore.activeTicket.user" @click="handleAccept" class="accept-btn">
                  <CheckIcon :size="18" />
                  Aceitar Atendimento
                </button>
                <div v-else class="action-group">
                  <button @click="openTransfer" class="btn-outline-sm" title="Transferir Atendimento">
                    <TransferIcon :size="18" />
                    <span>Transferir</span>
                  </button>
                  <button @click="showCloseModal = true" class="btn-success-sm">
                    <CheckIcon :size="18" />
                    <span>Finalizar</span>
                  </button>
                </div>
              </template>
            </div>
          </header>

          <div class="messages-wrapper">
            <div class="messages-container" ref="messageRef">
            <div v-for="msg in chatStore.messages" :key="msg.id" class="message" :class="{ 'me': msg.from_me }">
              <div class="message-bubble">
                <!-- Media Display -->
                <div v-if="msg.media_type === 'image'" class="media-image clickable" @click="openImage(msg.media_url || msg.body)">
                  <img :src="msg.media_url || msg.body" />
                </div>
                <div v-else-if="msg.media_type === 'audio'" class="media-audio">
                  <audio controls>
                    <source :src="msg.media_url" type="audio/mpeg">
                  </audio>
                </div>
                <div v-else-if="msg.media_type === 'document'" class="media-document clickable" @click="openDocument(msg.media_url)">
                  <div class="doc-card">
                    <FileIcon :size="32" />
                    <div class="doc-info">
                      <span class="doc-name">Ver Documento</span>
                      <span class="doc-ext">PDF / Arquivo</span>
                    </div>
                  </div>
                </div>
                
                <p v-if="msg.body && msg.media_type !== 'audio' && msg.media_type !== 'document'">
                  {{ cleanBody(msg.body, msg.from_me) }}
                </p>
                <span class="msg-time">
                  <span v-if="msg.from_me && msg.user_details" class="msg-attendant">{{ msg.user_details.first_name }} {{ msg.user_details.last_name }} • </span>
                  {{ new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <footer v-if="chatStore.activeTicket.status !== 'closed'" class="chat-input glass-effect">
            <input 
              type="file" 
              ref="fileInput" 
              style="display: none" 
              @change="handleFileUpload"
              accept="image/*,audio/*,application/pdf"
            />
            <button class="attach-btn" @click="fileInput.click()" title="Enviar Mídia">
              <PlusIcon :size="22" />
            </button>
            <input 
              v-model="newMessage" 
              @keyup.enter="send"
              :placeholder="chatStore.activeTicket.user ? 'Digite uma mensagem...' : 'Aceite o atendimento para responder...'" 
              type="text" 
              :disabled="!chatStore.activeTicket.user"
            />
            <button class="send-btn" @click="send" :disabled="!newMessage.trim() || !chatStore.activeTicket.user">
              <SendIcon :size="20" />
            </button>
          </footer>
          <div v-else class="closed-banner">
            Este atendimento foi finalizado em {{ new Date(chatStore.activeTicket.updated_at).toLocaleString() }}.
          </div>
        </div>

        <!-- CRM Sidebar -->
        <aside v-if="showCRM" class="crm-sidebar glass-effect animate-slide-in">
          <div class="crm-header">
            <h3>Dados do Ticket</h3>
            <button @click="showCRM = false" class="close-btn"><XIcon :size="20" /></button>
          </div>
          
          <div class="crm-content">
             <!-- Seção de Dados do Ticket -->
             <div class="ticket-meta-form">
               <div class="form-group-sm">
                 <label>Assunto do Atendimento</label>
                 <input 
                  v-model="chatStore.activeTicket.subject" 
                  @blur="updateTicketSubject"
                  placeholder="Ex: Suporte Financeiro" 
                  :disabled="chatStore.activeTicket.status === 'closed'"
                 />
               </div>
             </div>

             <hr class="crm-divider" />

            <template v-if="chatStore.activeTicket.customer_details">
              <div class="crm-avatar">
                <img v-if="chatStore.activeTicket.customer_details.profile_pic" :src="chatStore.activeTicket.customer_details.profile_pic" class="avatar-img" />
                <span v-else>{{ chatStore.activeTicket.customer_details.name.charAt(0) }}</span>
              </div>
              <h2 class="crm-name">{{ chatStore.activeTicket.customer_details.name }}</h2>
              
              <div class="crm-info-list">
                <div class="crm-info-item">
                  <label>Falar com:</label>
                  <p style="color: #10b981; font-weight: 700;">{{ chatStore.activeTicket.contact_details.name }}</p>
                </div>
                <div class="crm-info-item">
                  <label>Telefone Principal</label>
                  <p>{{ chatStore.activeTicket.customer_details.phone }}</p>
                </div>
                <div v-if="chatStore.activeTicket.customer_details.email" class="crm-info-item">
                  <label>E-mail</label>
                  <p>{{ chatStore.activeTicket.customer_details.email }}</p>
                </div>
                <div v-if="chatStore.activeTicket.customer_details.document" class="crm-info-item">
                  <label>CPF/CNPJ</label>
                  <p>{{ chatStore.activeTicket.customer_details.document }}</p>
                </div>
              </div>

              <button @click="router.push('/customers')" class="btn-block-outline">Ver Histórico Completo</button>
            </template>

            <div v-else class="crm-quick-create">
              <div class="empty-icon">
                <UserXIcon :size="48" />
              </div>
              <p>Contato não vinculado.</p>
              
              <div class="quick-form glass-effect">
                <h4>Cadastro Rápido</h4>
                <div class="form-group-sm">
                  <label>Nome / Empresa</label>
                  <input v-model="quickForm.name" placeholder="Ex: João da Silva" />
                </div>
                <div class="form-group-sm">
                  <label>CPF/CNPJ</label>
                  <input v-model="quickForm.document" placeholder="000.000.000-00" />
                </div>
                <button @click="handleQuickCreate" class="btn-primary-sm block pulse-effect" :disabled="loadingCRM">
                  {{ loadingCRM ? 'Salvando...' : 'Criar e Vincular' }}
                </button>
              </div>
            </div>

            <div v-if="chatStore.activeTicket.resolution" class="resolution-view">
              <hr class="crm-divider" />
              <label>Resolução Final:</label>
              <p>{{ chatStore.activeTicket.resolution }}</p>
            </div>
          </div>
        </aside>
      </template>
      
      <div v-else class="empty-state">
        <div class="empty-content">
          <img src="/logo.png" alt="WDesk Watermark" class="watermark-logo" />
          <h1>WDesk</h1>
          <p>Selecione uma conversa para começar a atender.</p>
        </div>
      </div>
    </main>

    <!-- Modal de Finalização -->
    <div v-if="showCloseModal" class="modal-overlay">
      <div class="modal-content glass-effect">
        <h2>Finalizar Atendimento</h2>
        <p style="color: var(--text-secondary); margin-bottom: 15px;">Descreva brevemente como o caso foi resolvido:</p>
        
        <div class="form-group">
          <textarea 
            v-model="resolutionSummary" 
            placeholder="Ex: O cliente foi orientado a reiniciar o roteador e o sinal voltou ao normal."
            rows="5"
            style="width: 100%; background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--border); border-radius: 10px; padding: 10px; outline: none;"
          ></textarea>
        </div>

        <div class="modal-actions" style="margin-top: 20px;">
          <button @click="showCloseModal = false" class="cancel-btn">Cancelar</button>
          <button @click="confirmClose" class="btn-success-sm" :disabled="!resolutionSummary.trim()">Confirmar e Fechar</button>
        </div>
      </div>
    </div>

    <!-- Modal de Transferência -->
    <div v-if="showTransferModal" class="modal-overlay">
      <div class="modal-content glass-effect">
        <h2>Transferir Atendimento</h2>
        <div class="attendants-list">
          <button 
            v-for="user in chatStore.attendants" 
            :key="user.id" 
            @click="confirmTransfer(user.id)"
            class="attendant-option"
          >
            <div class="avatar small">{{ user.username.charAt(0).toUpperCase() }}</div>
            <div>
              <span class="name">{{ user.first_name }} {{ user.last_name }}</span>
              <span class="dept">{{ user.department }}</span>
            </div>
          </button>
        </div>
        <div class="modal-actions"><button @click="showTransferModal = false" class="cancel-btn">Cancelar</button></div>
      </div>
    </div>

    <!-- Modal de Prioridade -->
    <div v-if="showPriorityModal" class="modal-overlay" @click="showPriorityModal = false">
      <div class="modal-content glass-effect small-modal" @click.stop>
        <h2>Definir Prioridade</h2>
        <div class="priority-options">
          <button @click="setPriority('high')" class="priority-option high">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Alta Prioridade</span>
              <span class="desc">Assuntos urgentes / Críticos</span>
            </div>
          </button>
          <button @click="setPriority('medium')" class="priority-option medium">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Média Prioridade</span>
              <span class="desc">Atendimento padrão</span>
            </div>
          </button>
          <button @click="setPriority('low')" class="priority-option low">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Baixa Prioridade</span>
              <span class="desc">Dúvidas gerais / Informativo</span>
            </div>
          </button>
        </div>
        <div class="modal-actions">
          <button @click="showPriorityModal = false" class="cancel-btn block">Cancelar</button>
        </div>
      </div>
    </div>

    <!-- Visualizador de Imagem -->
    <div v-if="selectedImage" class="modal-overlay image-viewer" @click="selectedImage = null">
      <button class="close-viewer"><XIcon :size="32" /></button>
      <img :src="selectedImage" class="full-image" @click.stop />
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useChatStore } from '../store/chat'
import { useRouter } from 'vue-router'
import { 
  Users as UsersIcon, 
  Search as SearchIcon, 
  Send as SendIcon,
  ArrowRightLeft as TransferIcon,
  Plus as PlusIcon,
  X as XIcon,
  FileText as FileIcon,
  Contact as ContactIcon,
  UserX as UserXIcon,
  Settings as SettingsIcon,
  Wifi as WifiIcon,
  CheckCircle as CheckIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const newMessage = ref('')
const messageRef = ref(null)
const fileInput = ref(null)
const showTransferModal = ref(false)
const showPriorityModal = ref(false)
const showCloseModal = ref(false)
const selectedImage = ref(null)
const showCRM = ref(false)
const loadingCRM = ref(false)
const resolutionSummary = ref('')

const handleAccept = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.acceptTicket(chatStore.activeTicket.id)
  showPriorityModal.value = true
}

const quickForm = ref({
  name: '',
  document: ''
})

watch(() => chatStore.activeTicket?.id, (newId) => {
  if (newId) {
    quickForm.value = {
      name: chatStore.activeTicket.contact_details?.name || '',
      document: ''
    }
  }
})

const updateTicketPriority = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    priority: chatStore.activeTicket.priority
  })
}

const setPriority = async (level) => {
  if (!chatStore.activeTicket) return
  chatStore.activeTicket.priority = level
  await updateTicketPriority()
  showPriorityModal.value = false
}

const updateTicketSubject = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    subject: chatStore.activeTicket.subject
  })
}

const confirmClose = async () => {
  if (!resolutionSummary.value.trim()) return
  await chatStore.closeTicket(chatStore.activeTicket.id, resolutionSummary.value)
  showCloseModal.value = false
  resolutionSummary.value = ''
}

const handleQuickCreate = async () => {
  if (!quickForm.value.name) return
  loadingCRM.value = true
  try {
    const customer = await chatStore.createCustomer({
      name: quickForm.value.name,
      document: quickForm.value.document,
      phone: chatStore.activeTicket.contact_details.remote_jid.split('@')[0]
    })
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: customer.id
    })
    await chatStore.selectTicket(chatStore.activeTicket)
  } catch (e) {
    alert("Erro ao criar cliente rápido")
  } finally {
    loadingCRM.value = false
  }
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { day: '2-digit', month: '2-digit' })
}

const cleanBody = (body, fromMe) => {
  if (!fromMe || !body) return body
  const parts = body.split(/:\*\n\n/)
  return parts.length > 1 ? parts.slice(1).join(/:\*\n\n/) : body
}

const openImage = (url) => { selectedImage.value = url }
const openDocument = (url) => { window.open(url, '_blank') }

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    await chatStore.sendMedia(file)
    event.target.value = '' 
  }
}

const openTransfer = () => {
  chatStore.fetchAttendants()
  showTransferModal.value = true
}

const confirmTransfer = async (userId) => {
  await chatStore.transferTicket(chatStore.activeTicket.id, userId)
  showTransferModal.value = false
}

const send = async () => {
  if (!newMessage.value.trim()) return
  const text = newMessage.value
  newMessage.value = ''
  await chatStore.sendMessage(text)
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => { if (messageRef.value) messageRef.value.scrollTop = messageRef.value.scrollHeight })
}

watch(() => chatStore.messages.length, scrollToBottom)

onMounted(() => {
  chatStore.fetchTickets()
  chatStore.fetchMyTickets()
  chatStore.initSocket()
})
</script>

<style scoped>
.dashboard-content {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.ticket-list {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  padding: 15px 20px;
  display: flex;
  gap: 15px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border);
}

.ticket-item:hover { background: var(--glass); }

.ticket-item.active {
  background: rgba(16, 185, 129, 0.1);
  border-left: 3px solid var(--accent);
}

.avatar {
  width: 50px;
  height: 50px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  overflow: hidden;
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.avatar.small { width: 40px; height: 40px; font-size: 1rem; }

.ticket-info { flex: 1; overflow: hidden; }
.ticket-info .top { display: flex; justify-content: space-between; margin-bottom: 5px; }
.name { font-weight: 600; color: var(--text-primary); }
.time { font-size: 0.8rem; color: var(--text-secondary); }
.last-msg {
  font-size: 0.9rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 5px;
}

.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.priority-dot.high { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.priority-dot.medium { background: #f59e0b; }

.time-unread {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.unread-badge {
  background: var(--accent);
  color: white;
  font-size: 0.7rem;
  font-weight: 800;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
  animation: badge-pulse 2s infinite;
}

@keyframes badge-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.chat-area {
  flex: 1;
  display: flex;
  background: var(--bg-dark);
  position: relative;
}

.chat-main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
}

.header-text { margin-left: 10px; }
.name-status { display: flex; align-items: center; gap: 10px; }
.status-tag {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  text-transform: uppercase;
  font-weight: 700;
}
.status-tag.open { color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.status-tag.pending { color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
.status-tag.closed { color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ticket-subject { font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }

.priority-selector {
  display: flex;
  align-items: center;
}

.priority-btn .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

.priority-btn.low .dot { background: #94a3b8; }
.priority-btn.medium .dot { background: #f59e0b; box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }
.priority-btn.high .dot { background: #ef4444; box-shadow: 0 0 12px rgba(239, 68, 68, 0.5); }

.priority-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 15px;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease;
  text-align: left;
}

.priority-option:hover {
  background: rgba(255, 255, 255, 0.07);
  transform: scale(1.02);
}

.priority-option .dot { width: 12px; height: 12px; border-radius: 50%; }
.priority-option.high { border-left: 4px solid #ef4444; }
.priority-option.high .dot { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
.priority-option.medium { border-left: 4px solid #f59e0b; }
.priority-option.medium .dot { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
.priority-option.low { border-left: 4px solid #94a3b8; }
.priority-option.low .dot { background: #94a3b8; }

.priority-option .opt-text { display: flex; flex-direction: column; }
.priority-option .label { font-weight: 700; font-size: 1rem; }
.priority-option .desc { font-size: 0.8rem; color: var(--text-secondary); }

.small-modal { width: 400px !important; }
.cancel-btn.block { width: 100%; margin-top: 10px; }

.btn-outline-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-outline-sm:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.btn-outline-sm.active {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
  border-color: var(--accent);
}

.icon-btn-outline {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-btn-outline:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.icon-btn-outline.active {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
  border-color: var(--accent);
}

.messages-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1;
}

.messages-wrapper::before {
  content: "";
  position: absolute;
  top: -50%; left: -50%; width: 200%; height: 200%;
  background-image: url('/favicon.png');
  background-repeat: repeat;
  background-size: 80px;
  opacity: var(--pattern-opacity);
  filter: var(--pattern-filter);
  transform: rotate(-15deg);
  pointer-events: none;
  z-index: 0;
}

.message { display: flex; width: 100%; position: relative; z-index: 1; }
.message.me { justify-content: flex-end; }
.message-bubble {
  max-width: 65%;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.message.me .message-bubble { background: var(--accent); }

.media-image {
  margin: 8px 0 !important;
  max-width: 250px !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 2px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
  transition: transform 0.2s !important;
  cursor: pointer !important;
}

.media-image:hover {
  transform: scale(1.03) !important;
}

.media-image img {
  width: 100% !important;
  height: auto !important;
  display: block !important;
  object-fit: cover !important;
  max-height: 300px !important;
}

.attach-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.attach-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.05) rotate(90deg);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.chat-input {
  padding: 15px 25px;
  display: flex;
  gap: 15px;
  align-items: center;
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border);
}

.chat-input input {
  flex: 1;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 12px;
  border-radius: 12px;
  color: var(--text-primary);
  outline: none;
}

.chat-input input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.1);
}

.send-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05) translateX(2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  background: #64748b;
  cursor: not-allowed;
  box-shadow: none;
}

.closed-banner {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.crm-sidebar {
  width: 320px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
}

.crm-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
}

.crm-content {
  padding: 20px;
  overflow-y: auto;
}

.ticket-meta-form { margin-bottom: 20px; }
.crm-divider { border: 0; border-top: 1px solid var(--border); margin: 20px 0; }

.resolution-view label { font-size: 0.75rem; color: var(--accent); text-transform: uppercase; font-weight: 700; }
.resolution-view p { font-size: 0.9rem; color: #94a3b8; margin-top: 5px; font-style: italic; }

.btn-success-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.btn-success-sm:hover { 
  background: #059669; 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
}
.badge.green { background: var(--accent); }

.ticket-list-wrapper { display: flex; flex-direction: column; overflow: hidden; }
.ticket-list-wrapper.top { flex: 1; }
.ticket-list-wrapper.bottom { height: 45%; border-top: 1px solid var(--border); background: rgba(0, 0, 0, 0.1); }
.list-header { 
  padding: 12px 20px; 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  background: var(--glass);
}

.list-header h3 { 
  font-size: 0.85rem; 
  font-weight: 700; 
  text-transform: uppercase; 
  color: var(--text-secondary); 
}

.tabs-top-inline { 
  display: flex; 
  background: var(--bg-dark); 
  padding: 3px; 
  border-radius: 8px; 
  margin-left: auto; 
  border: 1px solid var(--border);
}
.tab-btn-mini { 
  padding: 6px 10px; 
  border: none; 
  background: none; 
  color: var(--text-secondary); 
  font-size: 0.75rem; 
  font-weight: 600; 
  cursor: pointer; 
  border-radius: 6px; 
  transition: all 0.2s;
}

.tab-btn-mini.active { 
  background: var(--accent); 
  color: white; 
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.2);
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-content { 
  background: var(--bg-sidebar); 
  padding: 30px; 
  border-radius: 24px; 
  width: 450px; 
  border: 1px solid var(--border);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  color: var(--text-primary);
}
.attendant-option { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
  padding: 12px; 
  width: 100%; 
  background: rgba(255, 255, 255, 0.03); 
  border: 1px solid var(--border); 
  color: white; 
  border-radius: 12px; 
  cursor: pointer; 
  margin-bottom: 10px; 
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.attendant-option:hover {
  background: rgba(16, 185, 129, 0.1);
  border-color: var(--accent);
  transform: translateX(8px);
}

.attendant-option .name { font-weight: 600; display: block; text-align: left; }
.attendant-option .dept { font-size: 0.75rem; color: var(--text-secondary); display: block; text-align: left; }

.action-group { display: flex; align-items: center; gap: 10px; }
.cancel-btn { 
  background: none; 
  border: 1px solid var(--border); 
  color: var(--text-primary); 
  padding: 8px 16px; 
  border-radius: 8px; 
  cursor: pointer; 
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: var(--glass);
  border-color: var(--text-secondary);
}

.crm-avatar { width: 60px; height: 60px; background: var(--accent); border-radius: 20px; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; }
.crm-name { font-size: 1.2rem; text-align: center; margin-bottom: 20px; }
.crm-info-item label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; }
.crm-info-item p { font-size: 0.9rem; margin-bottom: 12px; }

.form-group-sm { margin-bottom: 15px; }
.form-group-sm label { 
  font-size: 0.75rem; 
  color: #94a3b8; 
  margin-bottom: 6px; 
  display: block; 
  font-weight: 600; 
  text-transform: uppercase; 
  letter-spacing: 0.5px; 
}
.form-group-sm input { 
  width: 100%; 
  background: rgba(255, 255, 255, 0.03); 
  border: 1px solid var(--border); 
  border-radius: 10px; 
  padding: 10px 12px; 
  color: white; 
  outline: none; 
  transition: all 0.3s ease;
}
.form-group-sm input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.btn-primary-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary-sm:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-primary-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary-sm.block { width: 100%; }

.btn-danger-sm {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s ease;
}
.btn-danger-sm:hover { background: #dc2626; transform: translateY(-2px); }

.accept-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 18px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
  display: flex;
  align-items: center;
  gap: 8px;
}

.accept-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

.accept-btn:active {
  transform: translateY(0) scale(0.98);
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at center, var(--empty-bg-inner) 0%, var(--empty-bg-outer) 100%);
}

.empty-content {
  text-align: center;
  opacity: 0.5;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.watermark-logo {
  width: 280px;
  height: 280px;
  object-fit: contain;
  margin-bottom: 30px;
  filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.15));
  opacity: 0.7;
  transition: all 0.5s ease;
}

.empty-content:hover .watermark-logo {
  transform: scale(1.05);
  opacity: 0.9;
}

.empty-content h1 {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(to bottom, #ffffff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
