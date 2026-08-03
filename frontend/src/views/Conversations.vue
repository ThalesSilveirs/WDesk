<template>
  <div class="dashboard-content" :class="{ 'has-active-ticket': !!chatStore.activeTicket, 'has-crm-open': showCRM }">
    <!-- Sidebar -->
    <div class="sidebar-wrapper" :class="{ 'hidden-on-mobile': !!chatStore.activeTicket }">
      <TicketSidebar />
    </div>

    <!-- Chat Area -->
    <main class="chat-area" :class="{ 'with-crm': showCRM }">
      <template v-if="chatStore.activeTicket">
        <ChatWindow 
          :showCRM="showCRM"
          @update:showCRM="showCRM = $event"
          @openPriorityModal="showPriorityModal = true"
          @openTransferModal="openTransfer"
          @openCloseModal="showCloseModal = true"
          @openDeleteModal="showDeleteModal = true"
          @openImage="openImage"
          @openVideo="openVideo"
          @setCRMTab="crmTab = $event; showCRM = true"
          @openCreatePendencyModal="openCreatePendencyModal"
        />

        <CrmPanel 
          :showCRM="showCRM"
          :activeTabProp="crmTab"
          @update:showCRM="showCRM = $event"
          @openHistory="openHistory"
          @openCreatePendency="openCreatePendencyModal"
        />
      </template>
      
      <div v-else class="empty-state">
        <div class="empty-content">
          <img src="/logo.png" alt="WDesk Watermark" class="watermark-logo" />
          <p>Selecione uma conversa para começar a atender.</p>
        </div>
      </div>
    </main>

    <!-- Modal de Finalização -->
    <Transition name="modal-fade">
      <div v-if="showCloseModal" class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="close-modal-title" @click="showCloseModal = false">
        <div class="modal-content" @click.stop>
          <h2 id="close-modal-title">Finalizar Atendimento</h2>
          <p style="color: var(--text-secondary); margin-bottom: 15px;">Descreva brevemente como o caso foi resolvido:</p>
          
          <div class="form-group">
            <textarea 
              v-model="resolutionSummary" 
              placeholder="Ex: O cliente foi orientado a reiniciar o roteador e o sinal voltou ao normal."
              rows="5"
              class="input-glass"
              style="width: 100%; resize: vertical;"
            ></textarea>
          </div>

          <div class="modal-actions" style="margin-top: 20px;">
            <button @click="showCloseModal = false" class="btn-secondary" :disabled="isClosing">Cancelar</button>
            <button @click="confirmClose" class="btn-success-sm" :disabled="!resolutionSummary.trim() || isClosing">
              {{ isClosing ? 'Finalizando...' : 'Confirmar e Fechar' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Transferência -->
    <Transition name="modal-fade">
      <div v-if="showTransferModal" class="modal-overlay" @click="showTransferModal = false">
        <div class="modal-content" @click.stop>
          <h2>Transferir Atendimento</h2>
          <div class="attendants-list">
            <button 
              v-for="user in chatStore.attendants" 
              :key="user.id" 
              @click="confirmTransfer(user.id)"
              class="attendant-option"
            >
              <div class="avatar small">{{ user.username.charAt(0).toUpperCase() }}</div>
              <div class="attendant-info">
                <span class="name">{{ user.first_name }} {{ user.last_name }}</span>
                <span class="dept">{{ user.department || 'Sem departamento' }}</span>
              </div>
              <div class="attendant-status" :class="user.status?.toLowerCase() || 'offline'">
                <span class="status-dot"></span>
                <span class="status-text">{{ user.status || 'Offline' }}</span>
              </div>
            </button>
          </div>
          <div class="modal-actions">
            <button @click="showTransferModal = false" class="btn-secondary">Cancelar</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Prioridade -->
    <Transition name="modal-fade">
      <div v-if="showPriorityModal" class="modal-overlay" @click="showPriorityModal = false">
        <div class="modal-content small-modal" @click.stop>
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
            <button @click="showPriorityModal = false" class="btn-secondary block">Cancelar</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Confirmação de Exclusão -->
    <Transition name="modal-fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content small-modal" @click.stop>
          <h2 style="color: #ef4444; display: flex; align-items: center; gap: 8px;">
            <TrashIcon :size="24" />
            Excluir Atendimento
          </h2>
          <p style="color: var(--text-secondary); margin: 15px 0; line-height: 1.5; font-size: 0.9rem;">
            Tem certeza que deseja excluir permanentemente este atendimento? Esta ação apagará todas as mensagens associadas e não pode ser desfeita.
          </p>
          <div class="modal-actions" style="margin-top: 20px;">
            <button @click="showDeleteModal = false" class="btn-secondary">Cancelar</button>
            <button @click="confirmDelete" class="btn-danger" :disabled="isDeleting">
              {{ isDeleting ? 'Excluindo...' : 'Confirmar e Excluir' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Visualizador de Imagem -->
    <Transition name="fade">
      <div v-if="selectedImage" class="modal-overlay image-viewer" @click="selectedImage = null">
        <button class="close-viewer"><XIcon :size="32" /></button>
        <img :src="selectedImage" class="full-image" @click.stop />
      </div>
    </Transition>

    <!-- Visualizador de Vídeo -->
    <Transition name="fade">
      <div v-if="selectedVideo" class="modal-overlay image-viewer" @click="selectedVideo = null">
        <button class="close-viewer"><XIcon :size="32" /></button>
        <video :src="selectedVideo" class="full-video" controls autoplay playsinline @click.stop></video>
      </div>
    </Transition>

    <!-- Modal de Criar Pendência a partir do Chat -->
    <Transition name="modal-fade">
      <div v-if="showCreatePendencyModal" class="modal-overlay" @click="showCreatePendencyModal = false">
        <div class="modal-content large-modal" @click.stop>
          <div class="modal-header">
            <h2>Criar Pendência do Chat</h2>
            <button @click="showCreatePendencyModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <form @submit.prevent="savePendencyFromChat" class="modal-form-scrollable">
            <div class="grid-2">
              <div class="form-group">
                <label>Título / Assunto *</label>
                <input v-model="pendencyForm.title" required class="input-glass" placeholder="Ex: Ajuste fiscal ou erro de suporte" />
              </div>

              <div class="form-group">
                <label>Tipo de Operação *</label>
                <select v-model="pendencyForm.operation_type" required class="select-glass">
                  <option v-for="(label, key) in operationTypes" :key="key" :value="key">{{ label }}</option>
                </select>
              </div>
            </div>

            <div class="grid-2">
              <!-- Cliente -->
              <div class="form-group customer-autocomplete" style="position: relative;">
                <label>Vincular Cliente (Razão Social/Nome) *</label>
                <input 
                  v-model="customerSearchText" 
                  @input="searchCustomersForPendency"
                  @focus="showCustomerDropdown = true"
                  class="input-glass" 
                  placeholder="Digite para buscar clientes..." 
                />
                <!-- Dropdown Autocomplete -->
                <div v-if="showCustomerDropdown && customerSearchResults.length > 0" class="autocomplete-dropdown glass-effect">
                  <div 
                    v-for="c in customerSearchResults" 
                    :key="c.id" 
                    @click="selectCustomer(c)"
                    class="dropdown-item"
                  >
                    <span>{{ c.name }}</span>
                    <span class="sub">{{ c.phone }}</span>
                  </div>
                </div>
                <div v-if="selectedCustomer" class="selected-badge glass-effect">
                  <span>Selecionado: <strong>{{ selectedCustomer.name }}</strong></span>
                  <button type="button" @click="clearSelectedCustomer" class="clear-btn">&times;</button>
                </div>
              </div>

              <!-- Contato -->
              <div class="form-group">
                <label>Contato Vinculado</label>
                <input :value="chatStore.activeTicket?.contact_details?.name || chatStore.activeTicket?.contact_details?.remote_jid" disabled class="input-glass" style="opacity: 0.7;" />
              </div>
            </div>

            <div class="grid-2">
              <!-- Responsável -->
              <div class="form-group">
                <label>Responsável / Usuário *</label>
                <select v-model="pendencyForm.user" required class="select-glass">
                  <option value="" disabled>Selecione o responsável</option>
                  <option v-for="user in chatStore.attendants" :key="user.id" :value="user.id">
                    {{ user.first_name ? `${user.first_name} ${user.last_name || ''}` : user.username }}
                  </option>
                </select>
              </div>

              <!-- Prioridade -->
              <div class="form-group">
                <label>Prioridade *</label>
                <select v-model="pendencyForm.priority" required class="select-glass">
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                </select>
              </div>
            </div>

            <div class="grid-3">
              <!-- Status -->
              <div class="form-group">
                <label>Status *</label>
                <select v-model="pendencyForm.status" required class="select-glass">
                  <option value="open">Aberta</option>
                  <option value="closed">Finalizada</option>
                </select>
              </div>

              <!-- Horário de Abertura -->
              <div class="form-group">
                <label>Horário de Abertura *</label>
                <input v-model="pendencyForm.opening_date" type="datetime-local" required class="input-glass" />
              </div>

              <!-- Previsão -->
              <div class="form-group">
                <label>Previsão de Entrega (Opcional)</label>
                <input v-model="pendencyForm.forecast_date" type="datetime-local" class="input-glass" />
              </div>
            </div>

            <div class="form-group">
              <label>Descrição dos Dados / Detalhes *</label>
              <textarea v-model="pendencyForm.description" required class="input-glass" placeholder="Forneça os detalhes e dados relevantes da pendência..." rows="4"></textarea>
            </div>

            <!-- Botões de Ação -->
            <div class="modal-actions-container">
              <span class="required-note">* Campos obrigatórios</span>
              <div class="modal-actions">
                <button type="button" @click="showCreatePendencyModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="savingPendency">
                  {{ savingPendency ? 'Criando...' : 'Criar Pendência' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Modal de Histórico de Atendimento -->
    <HistoryModal
      :show="showHistoryModal"
      :contactId="historyParams.contactId"
      :customerId="historyParams.customerId"
      :contactName="historyParams.contactName"
      :customerName="historyParams.customerName"
      :initialTab="historyParams.type"
      @close="showHistoryModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useChatStore } from '../store/chat'
import { X as XIcon, Trash2 as TrashIcon, ClipboardList as ClipboardListIcon } from 'lucide-vue-next'
import TicketSidebar from '../components/dashboard/TicketSidebar.vue'
import ChatWindow from '../components/dashboard/ChatWindow.vue'
import CrmPanel from '../components/dashboard/CrmPanel.vue'
import HistoryModal from '../components/dashboard/HistoryModal.vue'

const chatStore = useChatStore()

const crmTab = ref('details')
const showTransferModal = ref(false)
const showPriorityModal = ref(false)
const showCloseModal = ref(false)
const showDeleteModal = ref(false)
const showHistoryModal = ref(false)
const selectedImage = ref(null)
const selectedVideo = ref(null)
const showCRM = ref(window.innerWidth > 768)
const resolutionSummary = ref('')
const isDeleting = ref(false)
const isClosing = ref(false)

const historyParams = ref({
  contactId: null,
  customerId: null,
  contactName: '',
  customerName: '',
  type: 'contact'
})

const handleModalEsc = (e) => {
  if (e.key === 'Escape') {
    if (showCloseModal.value) showCloseModal.value = false
    else if (showTransferModal.value) showTransferModal.value = false
    else if (showPriorityModal.value) showPriorityModal.value = false
    else if (showDeleteModal.value) showDeleteModal.value = false
    else if (selectedImage.value) selectedImage.value = null
    else if (selectedVideo.value) selectedVideo.value = null
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleModalEsc)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleModalEsc)
})

const openHistory = (params) => {
  historyParams.value = {
    contactId: chatStore.activeTicket?.contact_details?.id || null,
    customerId: chatStore.activeTicket?.customer_details?.id || null,
    contactName: chatStore.activeTicket?.contact_details?.name || '',
    customerName: chatStore.activeTicket?.customer_details?.name || '',
    type: params.type
  }
  showHistoryModal.value = true
}

const openTransfer = () => {
  chatStore.fetchAttendants()
  showTransferModal.value = true
}

const confirmTransfer = async (userId) => {
  if (!chatStore.activeTicket) return
  const ticketId = chatStore.activeTicket.id
  showTransferModal.value = false
  try {
    await chatStore.transferTicket(ticketId, userId)
  } catch (e) {
    console.error("Erro ao transferir atendimento:", e)
  }
}

const confirmClose = async () => {
  if (!resolutionSummary.value.trim() || isClosing.value) return
  isClosing.value = true
  try {
    await chatStore.closeTicket(chatStore.activeTicket.id, resolutionSummary.value)
    showCloseModal.value = false
    resolutionSummary.value = ''
  } catch (e) {
    console.error("Erro ao finalizar atendimento:", e)
  } finally {
    isClosing.value = false
  }
}

const confirmDelete = async () => {
  if (!chatStore.activeTicket) return
  isDeleting.value = true
  try {
    await chatStore.deleteTicket(chatStore.activeTicket.id)
    showDeleteModal.value = false
  } catch (e) {
    console.error("Erro ao excluir atendimento:", e)
    alert("Erro ao excluir atendimento: " + (e.response?.data?.error || e.message))
  } finally {
    isDeleting.value = false
  }
}

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

const openImage = (url) => { selectedImage.value = url }
const openVideo = (url) => { selectedVideo.value = url }

// Ações de Criar Pendência a partir do Chat
const showCreatePendencyModal = ref(false)
const savingPendency = ref(false)
const customerSearchText = ref('')
const customerSearchResults = ref([])
const showCustomerDropdown = ref(false)
const selectedCustomer = ref(null)

const pendencyForm = ref({
  title: '',
  operation_type: 'suporte',
  user: '',
  priority: 'medium',
  status: 'open',
  opening_date: '',
  forecast_date: '',
  description: ''
})

const operationTypes = {
  suporte: 'Suporte',
  desenvolvimento: 'Desenvolvimento',
  consultoria: 'Consultoria / Assessoria',
  atualizacao: 'Atualização',
  reuniao: 'Reunião',
  tef: 'TEF',
  reforma_tributaria: 'Reforma Tributária'
}

const openCreatePendencyModal = async () => {
  const activeTicket = chatStore.activeTicket
  if (!activeTicket) return

  // Fetch attendants list if empty
  if (chatStore.attendants.length === 0) {
    await chatStore.fetchAttendants()
  }

  // Pre-fill fields
  let latestMsg = ''
  if (chatStore.messages && chatStore.messages.length > 0) {
    latestMsg = chatStore.messages[chatStore.messages.length - 1].body || ''
  }

  // Date formatted to local ISO
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  const localISOTime = new Date(now.getTime() - offset).toISOString().slice(0, 16)

  pendencyForm.value = {
    title: '',
    operation_type: 'suporte',
    user: chatStore.user?.id || '',
    priority: 'medium',
    status: 'open',
    opening_date: localISOTime,
    forecast_date: '',
    description: ''
  }

  selectedCustomer.value = activeTicket.customer_details || null
  customerSearchText.value = ''
  customerSearchResults.value = []
  
  showCreatePendencyModal.value = true
}

const searchCustomersForPendency = async () => {
  const query = customerSearchText.value.trim()
  if (query.length < 2) {
    customerSearchResults.value = []
    showCustomerDropdown.value = false
    return
  }
  try {
    const res = await chatStore.searchCustomers(query)
    customerSearchResults.value = res
    showCustomerDropdown.value = true
  } catch (err) {
    console.error(err)
  }
}

const selectCustomer = (c) => {
  selectedCustomer.value = c
  showCustomerDropdown.value = false
  customerSearchText.value = ''
  customerSearchResults.value = []
}

const clearSelectedCustomer = () => {
  selectedCustomer.value = null
}

const savePendencyFromChat = async () => {
  if (!selectedCustomer.value) {
    alert('Por favor, selecione e vincule um Cliente.')
    return
  }
  if (!pendencyForm.value.title) {
    alert('Por favor, digite o Título / Assunto.')
    return
  }
  if (!pendencyForm.value.description) {
    alert('Por favor, preencha a Descrição dos Dados / Detalhes.')
    return
  }
  if (!pendencyForm.value.user) {
    alert('Por favor, selecione um Responsável.')
    return
  }
  
  savingPendency.value = true
  try {
    const payload = {
      title: pendencyForm.value.title,
      operation_type: pendencyForm.value.operation_type,
      customer: selectedCustomer.value.id,
      contact: chatStore.activeTicket?.contact_details?.id || null,
      user: pendencyForm.value.user,
      priority: pendencyForm.value.priority,
      status: pendencyForm.value.status,
      opening_date: pendencyForm.value.opening_date,
      forecast_date: pendencyForm.value.forecast_date || null,
      description: pendencyForm.value.description,
      uploaded_images: []
    }
    
    await axios.post('/api/v1/pendencies/', payload)
    
    // Se o contato do ticket não tiver cliente vinculado ainda,
    // e o usuário selecionou um cliente no modal, vincula automaticamente!
    if (chatStore.activeTicket?.contact_details && !chatStore.activeTicket.customer_details) {
      try {
        await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
          customer: selectedCustomer.value.id
        })
        chatStore.activeTicket.customer_details = selectedCustomer.value
        chatStore.activeTicket.contact_details.customer = selectedCustomer.value.id
      } catch (linkErr) {
        console.error('Erro ao vincular cliente ao contato:', linkErr)
      }
    }
    
    alert('Pendência criada com sucesso!')
    showCreatePendencyModal.value = false
  } catch (error) {
    console.error('Erro ao criar pendência a partir do chat:', error)
    alert('Erro ao criar pendência. Verifique os dados informados.')
  } finally {
    savingPendency.value = false
  }
}


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
  height: 100%;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  display: flex;
  background: var(--bg-dark);
  position: relative;
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
  display: flex;
  flex-direction: column;
  align-items: center;
}

.watermark-logo {
  width: 380px;
  height: 380px;
  object-fit: contain;
  margin-bottom: 20px;
  filter: drop-shadow(0 0 35px rgba(16, 185, 129, 0.25));
  transition: all 0.5s ease;
}

.empty-content:hover .watermark-logo {
  transform: scale(1.03);
}

.empty-content p {
  font-size: 1.15rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin: 0;
}

.attendants-list {
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px;
}

.attendant-option { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
  padding: 12px; 
  width: 100%; 
  background: var(--glass); 
  border: 1px solid var(--border); 
  color: var(--text-primary); 
  border-radius: 12px; 
  cursor: pointer; 
  margin-bottom: 10px; 
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

.attendant-option:hover {
  background: rgba(16, 185, 129, 0.1);
  border-color: var(--accent);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.attendant-info {
  flex: 1;
  text-align: left;
}

.attendant-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  margin-left: auto;
}

.attendant-status .status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.attendant-status.online {
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.2);
  background: rgba(16, 185, 129, 0.06);
}
.attendant-status.online .status-dot {
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.attendant-status.ausente {
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.2);
  background: rgba(245, 158, 11, 0.06);
}
.attendant-status.ausente .status-dot {
  background: #f59e0b;
  box-shadow: 0 0 6px #f59e0b;
}

.attendant-status.offline {
  color: var(--text-secondary);
  border-color: var(--border);
  background: rgba(148, 163, 184, 0.05);
}
.attendant-status.offline .status-dot {
  background: #94a3b8;
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
  color: white;
}

.avatar.small { width: 40px; height: 40px; font-size: 1rem; }

.attendant-option .name { font-weight: 600; display: block; text-align: left; }
.attendant-option .dept { font-size: 0.75rem; color: var(--text-secondary); display: block; text-align: left; }

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

.btn-success-sm:hover:not(:disabled) { 
  background: #059669; 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.btn-success-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2);
}

.btn-danger:hover:not(:disabled) { 
  background: #dc2626; 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(239, 68, 68, 0.3);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 15px;
  cursor: pointer;
  color: var(--text-primary);
  transition: all 0.2s ease;
  text-align: left;
}

.priority-option:hover {
  background: var(--border);
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

.image-viewer {
  display: flex;
  flex-direction: column;
}
.full-image {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  border-radius: 12px;
}
.full-video {
  max-width: 90%;
  max-height: 90%;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  background: #000;
  outline: none;
}
.close-viewer {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
}
.close-viewer:hover {
  opacity: 1;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .sidebar-wrapper {
    width: 100%;
    display: flex;
  }
  .sidebar-wrapper.hidden-on-mobile {
    display: none !important;
  }

  .dashboard-content:not(.has-active-ticket) .chat-area {
    display: none;
  }

  .dashboard-content.has-active-ticket .chat-area {
    display: flex;
    width: 100%;
  }

  .dashboard-content.has-crm-open :deep(.crm-sidebar) {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 100;
  }
}

/* Modal extra styles matching Pendencies.vue */
.large-modal {
  max-width: 650px;
  width: 100%;
}

.modal-form-scrollable {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 5px;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

@media (max-width: 600px) {
  .grid-2, .grid-3 {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.form-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.select-glass, .input-glass {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 14px;
  border-radius: 8px;
  outline: none;
  font-size: 0.9rem;
  width: 100%;
}

.select-glass option {
  background: #18181b;
  color: var(--text-primary);
}

.modal-actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.required-note {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.close-btn-round {
  background: var(--glass);
  border: none;
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn-round:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* Autocomplete styling */
.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1010;
  max-height: 180px;
  overflow-y: auto;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.4);
  background: #18181b;
}

.dropdown-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.2s;
  display: flex;
  flex-direction: column;
}

.dropdown-item:hover {
  background: rgba(255,255,255,0.05);
}

.dropdown-item span {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.dropdown-item .sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.selected-badge {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 6px;
  font-size: 0.85rem;
}

.clear-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  font-size: 1.2rem;
  cursor: pointer;
  line-height: 1;
}
</style>
