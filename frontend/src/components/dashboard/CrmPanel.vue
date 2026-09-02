<template>
  <aside v-if="showCRM" class="crm-sidebar glass-effect animate-slide-in">
    <!-- Top Purple-Pink Gradient Banner -->
    <div class="banner-gradient">
      <button @click="emit('update:showCRM', false)" class="close-btn" title="Fechar Painel">
        <XIcon :size="16" />
      </button>
    </div>

    <!-- Contact Profile Section (Avatar overlaps banner) -->
    <div class="profile-section">
      <div class="profile-avatar-container">
        <div class="profile-avatar">
          <img 
            v-if="chatStore.activeTicket.customer_details?.profile_pic && !chatStore.activeTicket.customer_details?.profile_pic_failed" 
            :src="chatStore.activeTicket.customer_details.profile_pic" 
            class="avatar-img" 
            @error="chatStore.activeTicket.customer_details.profile_pic_failed = true" 
          />
          <img 
            v-else-if="chatStore.activeTicket.contact_details?.profile_pic && !imageError" 
            :src="chatStore.activeTicket.contact_details.profile_pic" 
            class="avatar-img" 
            @error="imageError = true" 
          />
          <span v-else>{{ contactInitials }}</span>
        </div>
      </div>

      <div class="profile-details">
        <h3 class="profile-name">{{ contactName || 'Sem nome' }}</h3>
        <p class="profile-phone" v-if="contactPhone">{{ formatPhone(contactPhone) }}</p>
        <p class="profile-email" v-if="contactEmail">{{ contactEmail }}</p>
        
        <!-- Tags/Badges list -->
        <div class="tags-container">
          <span 
            v-if="chatStore.activeTicket?.customer_details?.is_blocked || chatStore.activeTicket?.contact_details?.customer_details?.is_blocked" 
            class="tag-badge blocked"
            title="Cliente Bloqueado no Cadastro"
            style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); display: inline-flex; align-items: center; gap: 4px;"
          >
            <LockIcon :size="12" /> BLOQUEADO
          </span>
          <span class="tag-badge status" :class="chatStore.activeTicket.status">
            {{ formatStatus(chatStore.activeTicket.status) }}
          </span>
          <span class="tag-badge priority" :class="chatStore.activeTicket.priority">
            Prioridade {{ formatPriority(chatStore.activeTicket.priority) }}
          </span>
        </div>
      </div>
    </div>

    <!-- CRM Navigation Tabs -->
    <div class="crm-tabs-header">
      <button 
        class="crm-tab-btn" 
        :class="{ active: activeTab === 'details' }"
        @click="activeTab = 'details'"
      >
        Detalhes
      </button>
      <button 
        class="crm-tab-btn" 
        :class="{ active: activeTab === 'extras' }"
        @click="activeTab = 'extras'"
      >
        Campos Extras
      </button>
      <button 
        class="crm-tab-btn copilot-tab-btn" 
        :class="{ active: activeTab === 'copilot' }"
        @click="activeTab = 'copilot'"
      >
        <SparklesIcon :size="13" />
        Copilot
      </button>
    </div>

    <!-- Scrollable Tab Content Container -->
    <div class="crm-content">
      <!-- TAB 1: DETALHES -->
      <div class="tab-content" v-if="activeTab === 'details'">
        <!-- Seção de Dados do Ticket -->
        <div class="crm-section-card">
          <h4 class="section-title">Dados do Ticket</h4>
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

        <!-- Dados do Contato -->
        <div class="crm-section-card">
          <h4 class="section-title">Dados do Contato</h4>
          
          <div class="crm-info-item">
            <label>Nome do Contato</label>
            <div class="edit-field-wrapper">
              <input 
                v-if="editingName" 
                v-model="contactName" 
                @blur="saveContactName" 
                @keyup.enter="saveContactName"
                class="input-inline"
                ref="nameInputRef"
              />
              <div v-else @click="startEditingName" class="text-inline clickable">
                <span class="contact-name-highlight">{{ contactName || 'Contato Sem Nome' }}</span>
                <EditIcon :size="14" class="edit-icon" />
              </div>
            </div>
          </div>

          <div class="crm-info-item">
            <label>Cargo / Observação Curta</label>
            <div class="edit-field-wrapper">
              <input 
                v-if="editingNote" 
                v-model="contactNote" 
                @blur="saveContactNote" 
                @keyup.enter="saveContactNote"
                class="input-inline"
                placeholder="Ex: Gerente de TI, Compras..."
                ref="noteInputRef"
                maxlength="150"
              />
              <div v-else @click="startEditingNote" class="text-inline clickable">
                <span v-if="contactNote" class="note-badge">{{ contactNote }}</span>
                <span v-else class="placeholder-text">Adicionar observação...</span>
                <EditIcon :size="14" class="edit-icon" />
              </div>
            </div>
          </div>

          <div class="crm-contact-history-action" style="margin-top: 15px;">
            <button @click="openContactHistory" class="btn-block-outline">Ver Histórico do Contato</button>
          </div>
        </div>

        <!-- Dados do Cliente Vinculado -->
        <div class="crm-section-card">
          <h4 class="section-title">Cliente Vinculado</h4>
          
          <template v-if="chatStore.activeTicket.customer_details">
            <div class="linked-customer-details">
              <div class="crm-info-item">
                <label>Nome Completo</label>
                <p class="linked-text">{{ chatStore.activeTicket.customer_details.name }}</p>
              </div>
              <div class="crm-info-item">
                <label>Telefone Principal</label>
                <p class="linked-text">{{ formatPhone(chatStore.activeTicket.customer_details.phone) }}</p>
              </div>
              <div v-if="chatStore.activeTicket.customer_details.email" class="crm-info-item">
                <label>E-mail</label>
                <p class="linked-text">{{ chatStore.activeTicket.customer_details.email }}</p>
              </div>
              <div v-if="chatStore.activeTicket.customer_details.cnpj || chatStore.activeTicket.customer_details.cpf || chatStore.activeTicket.customer_details.document" class="crm-info-item">
                <label>CPF/CNPJ</label>
                <p class="linked-text">{{ formatDocument(chatStore.activeTicket.customer_details) }}</p>
              </div>
            </div>

            <div class="crm-actions">
              <button @click="openCustomerHistory" class="btn-block-outline">Ver Histórico Completo</button>
              <button @click="unlinkCustomer" class="btn-danger-outline" :disabled="loadingCRM">
                <UserMinusIcon :size="16" /> Desvincular Cliente
              </button>
            </div>
          </template>

          <!-- Fluxo de Vincular a Cliente Existente -->
          <div v-else class="crm-link-customer">
            <p class="link-label-empty">Nenhum cliente cadastrado vinculado a este contato.</p>
            
            <div class="link-search-box glass-effect">
              <h5>Vincular Cliente</h5>
              <div class="search-input-wrapper">
                <input 
                  v-model="customerSearchQuery" 
                  @input="handleSearchInput" 
                  placeholder="Buscar por nome ou telefone..."
                  class="search-input"
                />
                <SearchIcon :size="14" class="search-box-icon" />
              </div>
              
              <!-- Dropdown de Resultados -->
              <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown">
                <div 
                  v-for="cust in searchResults" 
                  :key="cust.id" 
                  @click="selectCustomerToLink(cust)"
                  class="dropdown-item"
                >
                  <span class="cust-name">{{ cust.name }}</span>
                  <span class="cust-detail">{{ formatPhone(cust.phone) }}</span>
                </div>
              </div>
              <div v-else-if="customerSearchQuery.trim().length >= 2 && !searching && searchResults.length === 0" class="no-results">
                Nenhum cliente encontrado.
              </div>
              <div v-else-if="searching" class="searching-text">
                Buscando...
              </div>
            </div>
          </div>
        </div>

        <!-- Ações e Lista de Pendências em Aberto -->
        <div class="crm-section-card">
          <div class="section-title-header">
            <h4 class="section-title">Pendências em Aberto</h4>
            <span v-if="openPendencies.length > 0" class="count-pill">{{ openPendencies.length }}</span>
          </div>

          <!-- Spinner/Loading -->
          <div v-if="loadingPendencies" class="pendency-loading-state">
            <span class="loading-spinner-sm"></span>
            <span>Buscando pendências...</span>
          </div>

          <!-- Lista de Pendências -->
          <div v-else-if="openPendencies.length > 0" class="customer-pendencies-list">
            <div 
              v-for="p in openPendencies" 
              :key="p.id" 
              class="pendency-item-card"
              @click="goToPendenciesModule(p.id)"
              title="Clique para ir ao módulo de pendências"
            >
              <div class="pendency-item-top">
                <span class="pendency-code">#{{ p.id }}</span>
                <span class="pendency-prio-badge" :class="p.priority">
                  {{ p.priority === 'high' ? 'Alta' : (p.priority === 'medium' ? 'Média' : 'Baixa') }}
                </span>
              </div>
              <h5 class="pendency-item-title">{{ p.title }}</h5>
              <div class="pendency-item-footer" v-if="p.forecast_date || p.opening_date">
                <ClockIcon :size="12" />
                <span>Prev: {{ formatDateShort(p.forecast_date || p.opening_date) }}</span>
              </div>
            </div>
          </div>

          <!-- Mensagem Vazia -->
          <div v-else-if="chatStore.activeTicket?.customer_details" class="empty-pendencies-info">
            Nenhuma pendência em aberto para este cliente.
          </div>
          <div v-else class="empty-pendencies-info">
            Vincule um cliente para consultar pendências.
          </div>

          <!-- Botão para Criar Nova Pendência -->
          <div class="crm-actions" style="margin-top: 10px;">
            <button @click="emit('openCreatePendency')" class="btn-block-outline create-pendency-btn">
              <ClipboardListIcon :size="16" />
              Criar Nova Pendência
            </button>
          </div>
        </div>

        <div v-if="chatStore.activeTicket.resolution" class="resolution-view crm-section-card">
          <h4 class="section-title text-success">Resolução Final</h4>
          <p>{{ chatStore.activeTicket.resolution }}</p>
        </div>
      </div>

      <!-- TAB 2: CAMPOS EXTRAS -->
      <div class="tab-content" v-if="activeTab === 'extras'">
        <div class="crm-section-card">
          <h4 class="section-title">Metadados e Campos Adicionais</h4>
          <div class="extra-fields-list">
            <div class="extra-field-row">
              <span class="field-label">ID do Cliente</span>
              <span class="field-val">#{{ chatStore.activeTicket.customer_details?.id || 'Sem cadastro' }}</span>
            </div>
            <div class="extra-field-row">
              <span class="field-label">Origem</span>
              <span class="field-val">WhatsApp Web API</span>
            </div>
            <div class="extra-field-row">
              <span class="field-label">Atendimento Iniciado</span>
              <span class="field-val">{{ formatDateTime(chatStore.activeTicket.created_at) }}</span>
            </div>
            <div class="extra-field-row">
              <span class="field-label">Fila / Canal</span>
              <span class="field-val">Suporte Técnico</span>
            </div>
            <div class="extra-field-row">
              <span class="field-label">Atendente Principal</span>
              <span class="field-val">{{ chatStore.activeTicket.attendant_details ? chatStore.activeTicket.attendant_details.first_name : 'Fila de Espera' }}</span>
            </div>
            <div class="extra-field-row">
              <span class="field-label">ID do Canal</span>
              <span class="field-val">{{ chatStore.activeTicket.channel_id || 'Evolution_API' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 3: COPILOT AI -->
      <div class="tab-content" v-if="activeTab === 'copilot'">
        <!-- Copilot Brand Title -->
        <div class="copilot-card">
          <div class="copilot-card-header">
            <SparklesIcon :size="16" class="sparkle-ai-icon" />
            <h5>WDesk AI Copilot</h5>
          </div>
          <p class="copilot-card-desc">Nosso assistente virtual analisa a conversa em tempo real para sugerir ações e acelerar as respostas.</p>
        </div>

        <!-- Suggestions options -->
        <div class="copilot-suggestions">
          <h6 class="action-heading">Ações Rápidas</h6>
          <div class="actions-grid">
            <button class="copilot-action-btn" @click="runCopilotAction('summary')" :disabled="isCopilotLoading">
              <FileTextIcon :size="14" />
              Resumir conversa
            </button>
            <button class="copilot-action-btn" @click="runCopilotAction('suggest')" :disabled="isCopilotLoading">
              <MessageSquareIcon :size="14" />
              Sugerir resposta
            </button>
            <button class="copilot-action-btn" @click="runCopilotAction('translate')" :disabled="isCopilotLoading">
              <LanguagesIcon :size="14" />
              Traduzir para Inglês
            </button>
          </div>
        </div>

        <!-- Copilot Response Area -->
        <div class="copilot-response-container" v-if="copilotResponse || isCopilotLoading">
          <h6 class="action-heading">Resposta do Copilot</h6>
          
          <div class="copilot-response-box glass-effect">
            <div v-if="isCopilotLoading" class="ai-skeleton">
              <div class="skeleton-line"></div>
              <div class="skeleton-line short"></div>
            </div>
            <div v-else class="ai-text-content" v-html="formattedCopilotResponse"></div>
          </div>
        </div>

        <!-- Custom query input -->
        <div class="copilot-custom-query">
          <h6 class="action-heading">Fazer pergunta à IA</h6>
          <div class="query-input-wrapper">
            <textarea 
              v-model="copilotQuery" 
              placeholder="Ex: Qual foi a última dúvida do cliente sobre pagamento?" 
              rows="3"
              class="query-textarea"
              @keydown.enter.prevent="askCopilot"
            ></textarea>
            <button 
              class="query-submit-btn" 
              @click="askCopilot" 
              :disabled="isCopilotLoading || !copilotQuery.trim()"
            >
              Perguntar
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useChatStore } from '../../store/chat'
import { 
  X as XIcon, 
  Edit as EditIcon, 
  Search as SearchIcon, 
  UserMinus as UserMinusIcon,
  Sparkles as SparklesIcon,
  FileText as FileTextIcon,
  MessageSquare as MessageSquareIcon,
  Languages as LanguagesIcon,
  ClipboardList as ClipboardListIcon,
  Clock as ClockIcon,
  Lock as LockIcon
} from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean,
  activeTabProp: {
    type: String,
    default: 'details'
  }
})

const emit = defineEmits(['update:showCRM', 'openHistory', 'openCreatePendency'])

const router = useRouter()
const chatStore = useChatStore()
const loadingCRM = ref(false)

// Estados de Pendências do Cliente
const openPendencies = ref([])
const loadingPendencies = ref(false)

const fetchCustomerPendencies = async () => {
  const customerId = chatStore.activeTicket?.customer_details?.id || chatStore.activeTicket?.customer
  if (!customerId) {
    openPendencies.value = []
    return
  }
  
  loadingPendencies.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`/api/v1/pendencies/?customer=${customerId}&status=open`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    openPendencies.value = res.data.results || res.data || []
  } catch (err) {
    console.error('Erro ao buscar pendências do cliente:', err)
    openPendencies.value = []
  } finally {
    loadingPendencies.value = false
  }
}

watch(
  () => [chatStore.activeTicket?.id, chatStore.activeTicket?.customer_details?.id],
  () => {
    fetchCustomerPendencies()
  },
  { immediate: true }
)

const formatDateShort = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

const goToPendenciesModule = (pendencyId) => {
  router.push('/pendencies')
}

// Estados de Edição do Contato
const contactName = ref('')
const contactNote = ref('')
const editingName = ref(false)
const editingNote = ref(false)
const nameInputRef = ref(null)
const noteInputRef = ref(null)
const imageError = ref(false)

// Active Tab state
const activeTab = ref('details')

// Watch activeTabProp to sync active tab
watch(() => props.activeTabProp, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
}, { immediate: true })

const contactPhone = computed(() => {
  return (
    chatStore.activeTicket?.contact_details?.remote_jid?.split('@')[0] ||
    chatStore.activeTicket?.contact_details?.whatsapp ||
    chatStore.activeTicket?.contact_details?.cellphone ||
    chatStore.activeTicket?.contact_details?.phone ||
    chatStore.activeTicket?.customer_details?.phone ||
    ''
  )
})

const contactEmail = computed(() => {
  return chatStore.activeTicket?.contact_details?.email || chatStore.activeTicket?.customer_details?.email || ''
})

const contactInitials = computed(() => {
  const name = contactName.value || chatStore.activeTicket.contact_details?.name || 'C'
  return name.charAt(0).toUpperCase()
})

const formatStatus = (status) => {
  const map = {
    'open': 'Em aberto',
    'pending': 'Pendente',
    'closed': 'Finalizado'
  }
  return map[status] || status
}

const formatPriority = (prio) => {
  const map = {
    'high': 'Alta',
    'medium': 'Média',
    'low': 'Baixa'
  }
  return map[prio] || 'Padrão'
}

const formatCPF = (val) => {
  if (!val) return ''
  const nums = val.replace(/\D/g, '')
  let formatted = ''
  if (nums.length > 0) formatted += nums.substring(0, 3)
  if (nums.length > 3) formatted += '.' + nums.substring(3, 6)
  if (nums.length > 6) formatted += '.' + nums.substring(6, 9)
  if (nums.length > 9) formatted += '-' + nums.substring(9, 11)
  return formatted
}

const formatCNPJ = (val) => {
  if (!val) return ''
  const nums = val.replace(/\D/g, '')
  let formatted = ''
  if (nums.length > 0) formatted += nums.substring(0, 2)
  if (nums.length > 2) formatted += '.' + nums.substring(2, 5)
  if (nums.length > 5) formatted += '.' + nums.substring(5, 8)
  if (nums.length > 8) formatted += '/' + nums.substring(8, 12)
  if (nums.length > 12) formatted += '-' + nums.substring(12, 14)
  return formatted
}

const formatDocument = (customer) => {
  if (!customer) return ''
  if (customer.cnpj) return formatCNPJ(customer.cnpj)
  if (customer.cpf) return formatCPF(customer.cpf)
  if (customer.document) {
    const cleanDoc = customer.document.replace(/\D/g, '')
    if (cleanDoc.length === 11) return formatCPF(cleanDoc)
    if (cleanDoc.length === 14) return formatCNPJ(cleanDoc)
    return customer.document
  }
  return ''
}

const formatPhone = (val) => {
  if (!val) return ''
  let nums = String(val).replace(/\D/g, '')
  if (nums.startsWith('55') && nums.length >= 12) {
    nums = nums.substring(2)
  }
  if (nums.length === 0) return ''
  
  if (nums.length <= 10) {
    let formatted = '(' + nums.substring(0, 2)
    if (nums.length > 2) {
      formatted += ') ' + nums.substring(2, 6)
    }
    if (nums.length > 6) {
      formatted += '-' + nums.substring(6, 10)
    }
    return formatted
  } else {
    let formatted = '(' + nums.substring(0, 2)
    if (nums.length > 2) {
      formatted += ') ' + nums.substring(2, 7)
    }
    if (nums.length > 7) {
      formatted += '-' + nums.substring(7, 11)
    }
    return formatted
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const openContactHistory = () => {
  const t = chatStore.activeTicket
  if (!t) return
  emit('openHistory', {
    type: 'contact',
    id: t.contact_details?.id,
    name: contactName.value || t.contact_details?.name
  })
}

const openCustomerHistory = () => {
  const t = chatStore.activeTicket
  if (!t || !t.customer_details) return
  emit('openHistory', {
    type: 'customer',
    id: t.customer_details.id,
    name: t.customer_details.name
  })
}

// Estados de Busca e Vínculo de Clientes
const customerSearchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const showDropdown = ref(false)

watch(() => chatStore.activeTicket?.id, (newId) => {
  if (newId) {
    contactName.value = chatStore.activeTicket.contact_details?.name || ''
    contactNote.value = chatStore.activeTicket.contact_details?.note || ''
    editingName.value = false
    editingNote.value = false
    customerSearchQuery.value = ''
    searchResults.value = []
    showDropdown.value = false
    imageError.value = false
    copilotResponse.value = ''
    copilotQuery.value = ''
  }
}, { immediate: true })

// Sincronização via WebSocket em background
watch(() => chatStore.activeTicket?.contact_details, (newDetails) => {
  if (newDetails && !editingName.value && !editingNote.value) {
    contactName.value = newDetails.name || ''
    contactNote.value = newDetails.note || ''
  }
}, { deep: true })

const updateTicketSubject = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    subject: chatStore.activeTicket.subject
  })
}

// Ações de edição do Contato
const startEditingName = () => {
  editingName.value = true
  setTimeout(() => {
    nameInputRef.value?.focus()
  }, 50)
}

const startEditingNote = () => {
  editingNote.value = true
  setTimeout(() => {
    noteInputRef.value?.focus()
  }, 50)
}

const saveContactName = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  editingName.value = false
  try {
    const updatedContact = await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      name: contactName.value
    })
    chatStore.activeTicket.contact_details.name = updatedContact.name
  } catch (err) {
    alert('Erro ao atualizar nome do contato')
  }
}

const saveContactNote = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  editingNote.value = false
  try {
    const updatedContact = await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      note: contactNote.value
    })
    chatStore.activeTicket.contact_details.note = updatedContact.note
  } catch (err) {
    alert('Erro ao atualizar observação do contato')
  }
}

// Busca Incremental
const handleSearchInput = async () => {
  const query = customerSearchQuery.value.trim()
  if (query.length < 2) {
    searchResults.value = []
    showDropdown.value = false
    return
  }
  searching.value = true
  try {
    const res = await chatStore.searchCustomers(query)
    searchResults.value = res
    showDropdown.value = res.length > 0
  } catch (err) {
    console.error(err)
  } finally {
    searching.value = false
  }
}

// Vincular Cliente
const selectCustomerToLink = async (customer) => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  loadingCRM.value = true
  try {
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: customer.id
    })
    chatStore.activeTicket.customer_details = customer
    chatStore.activeTicket.contact_details.customer = customer.id
    
    customerSearchQuery.value = ''
    searchResults.value = []
    showDropdown.value = false
  } catch (e) {
    alert('Erro ao vincular cliente')
  } finally {
    loadingCRM.value = false
  }
}

// Desvincular Cliente
const unlinkCustomer = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  if (!confirm('Deseja realmente desvincular este cliente do contato?')) return
  loadingCRM.value = true
  try {
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: null
    })
    chatStore.activeTicket.customer_details = null
    chatStore.activeTicket.contact_details.customer = null
  } catch (e) {
    alert('Erro ao desvincular cliente')
  } finally {
    loadingCRM.value = false
  }
}

// COPILOT LOGIC
const copilotResponse = ref('')
const isCopilotLoading = ref(false)
const copilotQuery = ref('')

const formattedCopilotResponse = computed(() => {
  if (!copilotResponse.value) return ''
  // Convert markdown-like symbols to HTML safely
  return copilotResponse.value
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br />')
})

const runCopilotAction = async (action) => {
  isCopilotLoading.value = true
  copilotResponse.value = ''
  
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  if (action === 'summary') {
    const msgs = chatStore.messages
    if (msgs.length > 0) {
      const summaryItems = []
      const customerName = chatStore.activeTicket?.contact_details?.name || 'Cliente'
      summaryItems.push(`**Resumo da Conversa com ${customerName}:**`)
      summaryItems.push(`• **Início:** O contato enviou as primeiras mensagens solicitando informações sobre o serviço.`)
      
      const lastMsgText = msgs[msgs.length - 1]?.body || 'Sem corpo de mensagem'
      summaryItems.push(`• **Status Recente:** O cliente aguarda retorno. A última mensagem recebida diz: *"${lastMsgText}"*.`)
      summaryItems.push(`• **Ação Recomendada:** Entrar em contato esclarecendo as dúvidas ou agendando uma ligação de suporte.`)
      copilotResponse.value = summaryItems.join('\n')
    } else {
      copilotResponse.value = '• Sem mensagens suficientes na conversa ativa para gerar um resumo do histórico.'
    }
  } else if (action === 'suggest') {
    copilotResponse.value = '**Sugestão de Resposta:**\n\n"Olá! Entendi a sua dúvida. Vou verificar as informações aqui no nosso painel de suporte e já te retorno com uma resposta completa em poucos instantes. Por favor, aguarde."'
  } else if (action === 'translate') {
    const msgs = chatStore.messages
    const lastMsgText = msgs.length > 0 ? msgs[msgs.length - 1].body : 'Olá, como posso ajudar?'
    copilotResponse.value = `**Tradução para Inglês:**\n\n"${lastMsgText}" \n-> \n*"Hello, how can I help you?"*`
  }
  isCopilotLoading.value = false
}

const askCopilot = async () => {
  if (!copilotQuery.value.trim()) return
  const query = copilotQuery.value
  copilotQuery.value = ''
  isCopilotLoading.value = true
  copilotResponse.value = ''
  
  await new Promise(resolve => setTimeout(resolve, 1200))
  
  copilotResponse.value = `**WDesk AI Copilot Resposta:**\n\nRespondendo à pergunta *"Recuperar dados sobre a conversa"*: \n\nCom base no histórico analisado, o cliente parece interessado em resolver uma pendência técnica. Sugiro iniciar a conversa oferecendo um teste de conexão ou confirmando o ID do usuário cadastrado.`
  isCopilotLoading.value = false
}
</script>

<style scoped>
.crm-sidebar {
  width: 330px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  height: 100%;
}

/* Banner gradient navy brand */
.banner-gradient {
  height: 90px;
  background: var(--brand-gradient);
  width: 100%;
  position: relative;
  flex-shrink: 0;
}

.banner-gradient .close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease;
  z-index: 10;
}

.banner-gradient .close-btn:hover {
  background: rgba(0, 0, 0, 0.4);
}

/* Profile overlaps banner */
.profile-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 20px 20px;
  border-bottom: 1px solid var(--border);
  position: relative;
}

.profile-avatar-container {
  margin-top: -36px;
  display: flex;
  justify-content: center;
  position: relative;
  z-index: 5;
  margin-bottom: 12px;
}

.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 4px solid var(--bg-sidebar);
  background: #db2777; /* Rosa chamativo */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.8rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-details {
  text-align: center;
  width: 100%;
}

.profile-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-phone,
.profile-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 2px 0;
}

.tags-container {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.tag-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}

.tag-badge.status {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.tag-badge.status.open {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.2);
}

.tag-badge.status.pending {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.2);
}

.tag-badge.priority.high {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.tag-badge.priority.medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.tag-badge.priority.low {
  background: rgba(113, 113, 122, 0.1);
  color: #a1a1aa;
  border: 1px solid rgba(113, 113, 122, 0.2);
}

/* Tab selection bar */
.crm-tabs-header {
  display: flex;
  background: rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid var(--border);
  padding: 4px;
}

.crm-tab-btn {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 10px 4px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.crm-tab-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.02);
}

.crm-tab-btn.active {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  box-shadow: inset 0 0 0 1px var(--border);
}

.copilot-tab-btn.active {
  color: #c084fc;
  background: rgba(168, 85, 247, 0.08);
}

.crm-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* CRM Section Cards */
.crm-section-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}

.section-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0 0 14px 0;
  letter-spacing: 0.5px;
}

.section-title.text-success {
  color: var(--accent);
}

.form-group-sm {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group-sm label {
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-group-sm input {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.88rem;
  transition: all 0.2s ease;
}

.form-group-sm input:focus {
  border-color: rgba(16, 185, 129, 0.4);
}

/* Contact edit inline fields */
.crm-info-item {
  margin-bottom: 12px;
}

.crm-info-item label {
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.edit-field-wrapper {
  margin-top: 4px;
  width: 100%;
}

.input-inline {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 6px 10px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.88rem;
}

.text-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 6px 0;
  cursor: pointer;
  border-bottom: 1px dashed transparent;
}

.text-inline:hover {
  border-bottom-color: var(--accent);
}

.contact-name-highlight {
  color: var(--accent);
  font-weight: 700;
}

.edit-icon {
  opacity: 0.2;
  transition: opacity 0.2s;
}

.text-inline:hover .edit-icon {
  opacity: 0.8;
}

.note-badge {
  background: rgba(16, 185, 129, 0.1);
  color: var(--accent);
  border: 1px solid rgba(16, 185, 129, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.placeholder-text {
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-style: italic;
}

/* Linked customer styling */
.linked-customer-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.linked-text {
  font-size: 0.88rem;
  color: var(--text-primary);
  margin: 2px 0 0 0;
  font-weight: 600;
}

.crm-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-block-outline {
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.84rem;
  transition: all 0.2s ease;
}

.btn-block-outline:hover {
  background: rgba(255, 255, 255, 0.04);
}

.btn-danger-outline {
  width: 100%;
  padding: 10px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.84rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn-danger-outline:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}

/* Linking flow Empty state */
.link-label-empty {
  font-size: 0.84rem;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 12px;
}

.link-search-box {
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
  position: relative;
}

.link-search-box h5 {
  font-size: 0.82rem;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.search-input-wrapper {
  position: relative;
}

.link-search-box .search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px 8px 30px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.82rem;
}

.search-box-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #18181b;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-top: 4px;
  max-height: 150px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.cust-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-primary);
}

.cust-detail {
  font-size: 0.74rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.searching-text,
.no-results {
  font-size: 0.78rem;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 8px;
  font-style: italic;
}

/* Extra fields metadata styling */
.extra-fields-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.extra-field-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.extra-field-row:last-child {
  border-bottom: none;
}

.field-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.field-val {
  font-size: 0.84rem;
  color: var(--text-primary);
  font-weight: 600;
}

/* COPILOT AI STYLING */
.copilot-card {
  background: var(--brand-gradient);
  border-radius: 12px;
  padding: 16px;
  color: white;
  margin-bottom: 16px;
  box-shadow: 0 4px 15px rgba(34, 181, 95, 0.25);
}

.copilot-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.sparkle-ai-icon {
  color: white;
  filter: drop-shadow(0 0 6px white);
}

.copilot-card h5 {
  font-size: 1rem;
  font-weight: 800;
  margin: 0;
}

.copilot-card-desc {
  font-size: 0.76rem;
  line-height: 1.4;
  margin: 0;
  opacity: 0.9;
}

.action-heading {
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
  letter-spacing: 0.5px;
}

.copilot-suggestions {
  margin-bottom: 16px;
}

.actions-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.copilot-action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.copilot-action-btn:hover:not(:disabled) {
  background: rgba(168, 85, 247, 0.08);
  border-color: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.copilot-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.copilot-response-container {
  margin-bottom: 16px;
}

.copilot-response-box {
  background: rgba(168, 85, 247, 0.03);
  border: 1px solid rgba(168, 85, 247, 0.15);
  border-radius: 12px;
  padding: 14px;
}

.ai-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  height: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  width: 100%;
  position: relative;
  overflow: hidden;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  height: 100%;
  width: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
  animation: loading-shimmer 1.5s infinite;
}

@keyframes loading-shimmer {
  100% { left: 100%; }
}

.ai-text-content {
  font-size: 0.84rem;
  line-height: 1.5;
  color: var(--text-primary);
}

.copilot-custom-query {
  margin-top: 10px;
}

.query-input-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.query-textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px;
  color: var(--text-primary);
  font-size: 0.84rem;
  outline: none;
  resize: none;
  line-height: 1.4;
}

.query-textarea:focus {
  border-color: rgba(168, 85, 247, 0.4);
}

.query-submit-btn {
  align-self: flex-end;
  background: #a855f7;
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s ease;
}

.query-submit-btn:hover:not(:disabled) {
  background: #9333ea;
}

.query-submit-btn:disabled {
  background: var(--border);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.section-title-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.count-pill {
  background: var(--accent);
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 12px;
}

.pendency-loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  padding: 10px 0;
}

.loading-spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin-loader 0.8s linear infinite;
}

@keyframes spin-loader {
  to { transform: rotate(360deg); }
}

.customer-pendencies-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 2px;
}

.pendency-item-card {
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--glass);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pendency-item-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.pendency-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.pendency-code {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--accent);
}

.pendency-prio-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
}

.pendency-prio-badge.high {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.pendency-prio-badge.medium {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.pendency-prio-badge.low {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.pendency-item-title {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  line-height: 1.3;
  word-break: break-word;
}

.pendency-item-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.empty-pendencies-info {
  font-size: 0.8rem;
  color: var(--text-secondary);
  padding: 10px 0;
  text-align: center;
  font-style: italic;
}

.create-pendency-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  font-weight: 700;
  transition: all 0.2s ease;
}

.create-pendency-btn:hover {
  background: rgba(34, 181, 95, 0.1) !important;
}

/* Light Mode Overrides */
:deep([data-theme='light']) .pendency-item-card,
[data-theme='light'] .pendency-item-card {
  background: #f8fafc !important;
  border-color: #e2e8f0 !important;
}

:deep([data-theme='light']) .pendency-item-card:hover,
[data-theme='light'] .pendency-item-card:hover {
  background: #f1f5f9 !important;
  border-color: var(--accent) !important;
}

:deep([data-theme='light']) .pendency-item-title,
[data-theme='light'] .pendency-item-title {
  color: #0f172a !important;
}

/* Animations */
.animate-slide-in {
  animation: slide-in 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slide-in {
  from { transform: translateX(50px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
</style>