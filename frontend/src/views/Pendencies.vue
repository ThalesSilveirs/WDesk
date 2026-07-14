<template>
  <div class="pendencies-page-container">
    <main class="main-content">
      <!-- Cabeçalho da Página -->
      <header class="page-header glass-effect animate-in">
        <div class="header-info">
          <h1>Tickets e Pendências</h1>
          <p>Gerencie, priorize e acompanhe as atividades da sua equipe</p>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <SearchIcon :size="20" />
            <input v-model="search" placeholder="Buscar por título ou descrição..." type="text" />
          </div>
          <button @click="showFilters = !showFilters" :class="{ 'btn-filter-active': showFilters || activeFiltersCount > 0 }" class="btn-filter-toggle" title="Filtrar Pendências">
            <FilterIcon :size="18" />
            <span>Filtros</span>
            <span v-if="activeFiltersCount > 0" class="filter-count-badge">{{ activeFiltersCount }}</span>
          </button>
          <div class="view-switcher-toggle">
            <button @click="viewMode = 'grid'" :class="{ active: viewMode === 'grid' }" class="toggle-btn" title="Visualização em Grade">
              <LayoutGridIcon :size="18" />
            </button>
            <button @click="viewMode = 'list'" :class="{ active: viewMode === 'list' }" class="toggle-btn" title="Visualização em Tabela">
              <ListIcon :size="18" />
            </button>
          </div>
          <button @click="openCreateModal" class="btn-primary">
            <PlusIcon :size="20" /> Nova Pendência
          </button>
        </div>
      </header>

      <div class="content-wrapper">
        <!-- Barra de Filtros Expansível -->
        <Transition name="slide-fade">
          <div class="filters-container glass-effect" v-if="showFilters">
            <div class="filter-grid">
              <div class="filter-group">
                <label>Cliente</label>
                <select v-model="filterCustomer" class="select-glass">
                  <option value="all">Todos os Clientes</option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Responsável</label>
                <select v-model="filterUser" class="select-glass">
                  <option value="all">Todos os Usuários</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">
                    {{ u.first_name ? `${u.first_name} ${u.last_name || ''}` : u.username }}
                  </option>
                </select>
              </div>

              <div class="filter-group">
                <label>Tipo de Operação</label>
                <select v-model="filterOperation" class="select-glass">
                  <option value="all">Todos os Tipos</option>
                  <option v-for="(label, key) in operationTypes" :key="key" :value="key">{{ label }}</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Status</label>
                <select v-model="filterStatus" class="select-glass">
                  <option value="all">Todos os Status</option>
                  <option value="open">Aberta</option>
                  <option value="pending">Pendente</option>
                  <option value="closed">Finalizada</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Abertura Início</label>
                <input v-model="filterStartDate" type="date" class="input-glass" />
              </div>

              <div class="filter-group">
                <label>Abertura Fim</label>
                <input v-model="filterEndDate" type="date" class="input-glass" />
              </div>
            </div>

            <div class="filter-actions-row">
              <button v-if="hasActiveFilters" @click="clearFilters" class="btn-clear-filters">
                Limpar Filtros
              </button>
            </div>
          </div>
        </Transition>

        <!-- Loading State -->
        <div v-if="loadingList" class="loading-state glass-effect animate-in">
          <div class="spinner"></div>
          <p>Carregando pendências...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredPendencies.length === 0" class="empty-state glass-effect animate-in">
          <div class="empty-icon">
            <SearchIcon v-if="hasActiveFilters || search.trim()" :size="40" />
            <ClipboardListIcon v-else :size="40" />
          </div>
          <template v-if="hasActiveFilters || search.trim()">
            <h2>Nenhum resultado encontrado</h2>
            <p>Nenhuma pendência corresponde aos filtros ou termos de busca aplicados. Tente ajustar ou limpar os critérios de busca.</p>
            <div class="empty-actions">
              <button @click="clearFiltersAndSearch" class="btn-primary">
                Limpar Filtros e Busca
              </button>
            </div>
          </template>
          <template v-else>
            <h2>Tudo em dia!</h2>
            <p>Você não possui pendências registradas no momento. Que tal começar criando uma nova agora?</p>
            <div class="empty-actions">
              <button @click="openCreateModal" class="btn-primary">
                <PlusIcon :size="18" /> Nova Pendência
              </button>
            </div>
          </template>
        </div>

        <!-- Grade de Cards (Grid Mode) -->
        <div v-else-if="viewMode === 'grid'" class="pendencies-grid">
          <div v-for="item in filteredPendencies" :key="item.id" class="pendency-card glass-effect animate-in" :class="item.priority">
            <!-- Header do Card -->
            <div class="card-header">
              <span class="operation-badge">{{ operationTypes[item.operation_type] }}</span>
              <div class="badge-actions">
                <span class="priority-badge" :class="item.priority">{{ priorityLabels[item.priority] }}</span>
                <div class="card-actions">
                  <button @click="editPendency(item)" class="icon-btn" title="Editar"><EditIcon :size="16" /></button>
                  <button @click="confirmDelete(item)" class="icon-btn delete" title="Excluir"><TrashIcon :size="16" /></button>
                </div>
              </div>
            </div>

            <!-- Corpo do Card -->
            <div class="card-body">
              <h3 class="card-title">{{ item.title }}</h3>
              <p class="card-desc">{{ item.description || 'Sem descrição.' }}</p>

              <div class="card-details">
                <div v-if="item.customer_details" class="detail-row">
                  <ContactIcon :size="14" />
                  <span><strong>Cliente:</strong> {{ item.customer_details.name }}</span>
                </div>
                <div v-if="item.contact_details" class="detail-row">
                  <PhoneIcon :size="14" />
                  <span><strong>Contato:</strong> {{ item.contact_details.name || item.contact_details.remote_jid }}</span>
                </div>
                <div v-if="item.user_details" class="detail-row">
                  <UserIcon :size="14" />
                  <span><strong>Responsável:</strong> {{ item.user_details.first_name ? `${item.user_details.first_name} ${item.user_details.last_name || ''}` : item.user_details.username }}</span>
                </div>
                <div class="detail-row">
                  <CalendarIcon :size="14" />
                  <span><strong>Abertura:</strong> {{ formatDateTime(item.opening_date) }}</span>
                </div>
                <div class="detail-row" :class="{ 'overdue': isOverdue(item) }">
                  <ClockIcon :size="14" />
                  <span><strong>Previsão:</strong> {{ item.forecast_date ? formatDateTime(item.forecast_date) : 'Não informada' }}</span>
                </div>
              </div>

              <!-- Imagens Anexadas -->
              <div v-if="item.images && item.images.length > 0" class="attached-images">
                <div v-for="img in item.images" :key="img.id" class="image-thumb" @click="openLightbox(img.image)">
                  <img :src="img.image" alt="Anexo" />
                </div>
              </div>
            </div>

            <!-- Footer do Card -->
            <div class="card-footer">
              <span class="status-indicator" :class="item.status">{{ statusLabels[item.status] }}</span>
              <span class="created-at">Atualizado: {{ formatDateTime(item.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Tabela (List Mode) -->
        <div v-else class="pendencies-table-view glass-effect animate-in">
          <table class="pendencies-table">
            <thead>
              <tr>
                <th>Título / Operação</th>
                <th>Cliente</th>
                <th>Responsável</th>
                <th>Abertura</th>
                <th>Previsão</th>
                <th>Prioridade</th>
                <th>Status</th>
                <th>Anexos</th>
                <th class="actions-col">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredPendencies" :key="item.id" :class="item.priority">
                <td>
                  <div class="title-cell">
                    <span class="tbl-title">{{ item.title }}</span>
                    <span class="tbl-operation">{{ operationTypes[item.operation_type] }}</span>
                  </div>
                </td>
                <td>
                  <div v-if="item.customer_details" class="client-cell">
                    <span>{{ item.customer_details.name }}</span>
                    <span v-if="item.contact_details" class="subtext">{{ item.contact_details.name || item.contact_details.remote_jid }}</span>
                  </div>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="item.user_details">
                    {{ item.user_details.first_name ? `${item.user_details.first_name} ${item.user_details.last_name || ''}` : item.user_details.username }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>{{ formatDateTime(item.opening_date) }}</td>
                <td :class="{ 'overdue-text': isOverdue(item) }">
                  {{ item.forecast_date ? formatDateTime(item.forecast_date) : '-' }}
                </td>
                <td>
                  <span class="priority-badge" :class="item.priority">{{ priorityLabels[item.priority] }}</span>
                </td>
                <td>
                  <span class="status-indicator" :class="item.status">{{ statusLabels[item.status] }}</span>
                </td>
                <td>
                  <div v-if="item.images && item.images.length > 0" class="table-images">
                    <span class="images-count-badge" @click="openLightbox(item.images[0].image)">
                      <ImageIcon :size="14" /> {{ item.images.length }}
                    </span>
                  </div>
                  <span v-else>-</span>
                </td>
                <td class="actions-col">
                  <div class="table-actions">
                    <button @click="editPendency(item)" class="table-action-btn" title="Editar"><EditIcon :size="16" /></button>
                    <button @click="confirmDelete(item)" class="table-action-btn delete" title="Excluir"><TrashIcon :size="16" /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Modal de Criação / Edição de Pendência -->
    <Transition name="modal-fade">
      <div v-if="showModal" class="modal-overlay" @click="showModal = false">
        <div class="modal-content large-modal" @click.stop>
          <div class="modal-header">
            <h2>{{ editingId ? 'Editar Pendência' : 'Nova Pendência' }}</h2>
            <button @click="showModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <form @submit.prevent="savePendency" class="modal-form-scrollable">
            <div class="grid-2">
              <div class="form-group">
                <label>Título / Assunto *</label>
                <input v-model="form.title" required class="input-glass" placeholder="Ex: Ajuste fiscal ou erro de suporte" />
              </div>

              <div class="form-group">
                <label>Tipo de Operação *</label>
                <select v-model="form.operation_type" required class="select-glass">
                  <option v-for="(label, key) in operationTypes" :key="key" :value="key">{{ label }}</option>
                </select>
              </div>
            </div>

            <!-- Seleção de Cliente com Autocomplete -->
            <div class="grid-2">
              <div class="form-group customer-autocomplete" style="position: relative;">
                <label>Vincular Cliente (Razão Social/Nome)</label>
                <input 
                  v-model="customerSearch" 
                  @input="handleCustomerSearch"
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
                    <span class="sub">{{ formatPhone(c.phone) }}</span>
                  </div>
                </div>
                <div v-if="form.customer" class="selected-badge glass-effect">
                  <span>Selecionado: <strong>{{ selectedCustomerName }}</strong></span>
                  <button type="button" @click="clearSelectedCustomer" class="clear-btn">&times;</button>
                </div>
              </div>

              <!-- Seleção de Contato -->
              <div class="form-group">
                <label>Vincular Contato Específico (Opcional)</label>
                <select v-model="form.contact" class="select-glass" :disabled="!form.customer">
                  <option :value="null">Nenhum contato selecionado</option>
                  <option v-for="ct in availableContacts" :key="ct.id" :value="ct.id">
                    {{ ct.name || ct.remote_jid }}
                  </option>
                </select>
              </div>
            </div>

            <div class="grid-2">
              <!-- Responsável -->
              <div class="form-group">
                <label>Responsável / Usuário *</label>
                <select v-model="form.user" required class="select-glass">
                  <option :value="null">Selecione o responsável</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">
                    {{ u.first_name ? `${u.first_name} ${u.last_name || ''}` : u.username }}
                  </option>
                </select>
              </div>

              <!-- Prioridade -->
              <div class="form-group">
                <label>Prioridade *</label>
                <select v-model="form.priority" required class="select-glass">
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
                <select v-model="form.status" required class="select-glass">
                  <option value="open">Aberta</option>
                  <option value="pending">Pendente</option>
                  <option value="closed">Finalizada</option>
                </select>
              </div>

              <!-- Horário de Abertura -->
              <div class="form-group">
                <label>Horário de Abertura *</label>
                <input v-model="form.opening_date" type="datetime-local" required class="input-glass" />
              </div>

              <!-- Previsão -->
              <div class="form-group">
                <label>Previsão de Entrega</label>
                <input v-model="form.forecast_date" type="datetime-local" class="input-glass" />
              </div>
            </div>

            <div class="form-group">
              <label>Descrição dos Dados / Detalhes</label>
              <textarea v-model="form.description" class="input-glass" placeholder="Forneça os detalhes e dados relevantes da pendência..." rows="4"></textarea>
            </div>

            <!-- Imagens / Upload -->
            <div class="form-group">
              <label>Imagens / Anexos</label>
              <div 
                class="drag-drop-area glass-effect" 
                @dragover.prevent="dragOver = true" 
                @dragleave="dragOver = false" 
                @drop.prevent="handleFileDrop"
                :class="{ 'drag-over': dragOver }"
                @click="triggerFileInput"
              >
                <input type="file" ref="fileInput" multiple accept="image/*" class="hidden-input" @change="handleFileSelect" />
                <UploadCloudIcon :size="32" />
                <p>Clique ou arraste imagens aqui para anexar</p>
                <span class="sub">PNG, JPG, GIF até 5MB</span>
              </div>

              <!-- Lista de Novas Imagens Anexadas -->
              <div v-if="newImages.length > 0" class="images-preview-list">
                <div v-for="(img, idx) in newImages" :key="idx" class="image-preview-item">
                  <img :src="img" alt="Anexo" />
                  <button type="button" @click="removeNewImage(idx)" class="remove-img-btn">&times;</button>
                </div>
              </div>

              <!-- Lista de Imagens Existentes no Banco -->
              <div v-if="existingImages.length > 0" class="images-preview-list existing-images-section">
                <div class="title">Imagens já salvas:</div>
                <div v-for="img in existingImages" :key="img.id" class="image-preview-item">
                  <img :src="img.image" alt="Salva" />
                  <button type="button" @click="deleteExistingImage(img.id)" class="remove-img-btn">&times;</button>
                </div>
              </div>
            </div>

            <!-- Botões de Ação -->
            <div class="modal-actions-container">
              <span class="required-note">* Campos obrigatórios</span>
              <div class="modal-actions">
                <button type="button" @click="showModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="loadingSave">
                  {{ loadingSave ? 'Salvando...' : 'Salvar Pendência' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Modal de Confirmação de Exclusão -->
    <Transition name="modal-fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content small-modal" @click.stop>
          <h2>Excluir Pendência</h2>
          <p>Tem certeza que deseja excluir a pendência <strong>{{ selectedDeleteTitle }}</strong>? Esta ação não pode ser desfeita.</p>
          <div class="modal-actions">
            <button @click="showDeleteModal = false" class="btn-secondary">Cancelar</button>
            <button @click="deletePendency" class="btn-danger-sm" :disabled="loadingDelete">
              {{ loadingDelete ? 'Excluindo...' : 'Excluir' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal Lightbox (Visualizar Imagem cheia) -->
    <Transition name="fade">
      <div v-if="showLightbox" class="lightbox-overlay" @click="showLightbox = false">
        <div class="lightbox-content" @click.stop>
          <img :src="lightboxSrc" alt="Anexo Ampliado" />
          <button @click="showLightbox = false" class="close-lightbox-btn">&times;</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import {
  ClipboardList as ClipboardListIcon,
  Search as SearchIcon,
  Filter as FilterIcon,
  Plus as PlusIcon,
  LayoutGrid as LayoutGridIcon,
  List as ListIcon,
  Edit as EditIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  Contact as ContactIcon,
  User as UserIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
  Phone as PhoneIcon,
  Image as ImageIcon,
  UploadCloud as UploadCloudIcon
} from 'lucide-vue-next'

// Constantes e Labels
const operationTypes = {
  suporte: 'Suporte',
  desenvolvimento: 'Desenvolvimento',
  consultoria: 'Consultoria / Assessoria',
  atualizacao: 'Atualização',
  reuniao: 'Reunião',
  tef: 'TEF',
  reforma_tributaria: 'Reforma Tributária'
}

const priorityLabels = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta'
}

const statusLabels = {
  open: 'Aberta',
  pending: 'Pendente',
  closed: 'Finalizada'
}

// Estados Reativos
const pendencies = ref([])
const customers = ref([])
const users = ref([])
const contacts = ref([]) // Todos os contatos da empresa
const search = ref('')
const viewMode = ref('grid')

// Filtros
const showFilters = ref(false)
const filterCustomer = ref('all')
const filterUser = ref('all')
const filterOperation = ref('all')
const filterStatus = ref('all')
const filterStartDate = ref('')
const filterEndDate = ref('')

// Controle de Loading
const loadingList = ref(false)
const loadingSave = ref(false)
const loadingDelete = ref(false)

// Modais
const showModal = ref(false)
const showDeleteModal = ref(false)
const showLightbox = ref(false)
const lightboxSrc = ref('')

// Form e Cadastro
const editingId = ref(null)
const selectedDeleteId = ref(null)
const selectedDeleteTitle = ref('')
const form = ref({
  title: '',
  operation_type: 'suporte',
  customer: null,
  contact: null,
  user: null,
  priority: 'medium',
  status: 'open',
  opening_date: '',
  forecast_date: '',
  description: ''
})

// Autocomplete de Clientes no Modal
const customerSearch = ref('')
const showCustomerDropdown = ref(false)
const customerSearchResults = ref([])
const selectedCustomerName = ref('')

// Imagens/Anexos
const newImages = ref([]) // Array de strings base64
const existingImages = ref([]) // Array de objetos {id, image, created_at}
const dragOver = ref(false)
const fileInput = ref(null)

// Filtros Ativos
const activeFiltersCount = computed(() => {
  let count = 0
  if (filterCustomer.value !== 'all') count++
  if (filterUser.value !== 'all') count++
  if (filterOperation.value !== 'all') count++
  if (filterStatus.value !== 'all') count++
  if (filterStartDate.value) count++
  if (filterEndDate.value) count++
  return count
})

const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

// Contatos filtrados com base no cliente selecionado
const availableContacts = computed(() => {
  if (!form.value.customer) return []
  return contacts.value.filter(ct => ct.customer === form.value.customer)
})

// Aberturas de pendência ordenadas/filtradas no frontend reativamente
const filteredPendencies = computed(() => {
  return pendencies.value.filter(item => {
    // Busca por texto (titulo/descrição)
    if (search.value.trim()) {
      const query = search.value.toLowerCase()
      const titleMatch = item.title.toLowerCase().includes(query)
      const descMatch = (item.description || '').toLowerCase().includes(query)
      if (!titleMatch && !descMatch) return false
    }

    // Filtro de Cliente
    if (filterCustomer.value !== 'all' && item.customer !== filterCustomer.value) {
      return false
    }

    // Filtro de Responsável
    if (filterUser.value !== 'all' && item.user !== filterUser.value) {
      return false
    }

    // Filtro de Tipo Operação
    if (filterOperation.value !== 'all' && item.operation_type !== filterOperation.value) {
      return false
    }

    // Filtro de Status
    if (filterStatus.value !== 'all' && item.status !== filterStatus.value) {
      return false
    }

    // Filtro de Período (Abertura)
    if (filterStartDate.value) {
      const openDate = new Date(item.opening_date).toISOString().split('T')[0]
      if (openDate < filterStartDate.value) return false
    }
    if (filterEndDate.value) {
      const openDate = new Date(item.opening_date).toISOString().split('T')[0]
      if (openDate > filterEndDate.value) return false
    }

    return true
  })
})

// Funções utilitárias
const formatPhone = (phone) => {
  if (!phone) return ''
  const clean = phone.replace(/\D/g, '')
  if (clean.length === 11) {
    return `(${clean.slice(0, 2)}) ${clean.slice(2, 7)}-${clean.slice(7)}`
  } else if (clean.length === 10) {
    return `(${clean.slice(0, 2)}) ${clean.slice(2, 6)}-${clean.slice(6)}`
  }
  return phone
}

const formatDateTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isOverdue = (item) => {
  if (item.status === 'closed' || !item.forecast_date) return false
  return new Date(item.forecast_date) < new Date()
}

// Limpar Filtros
const clearFilters = () => {
  filterCustomer.value = 'all'
  filterUser.value = 'all'
  filterOperation.value = 'all'
  filterStatus.value = 'all'
  filterStartDate.value = ''
  filterEndDate.value = ''
}

const clearFiltersAndSearch = () => {
  clearFilters()
  search.value = ''
}

// Requisições e Carregamento de Dados
const fetchData = async () => {
  loadingList.value = true
  try {
    const [resPendencies, resCustomers, resUsers, resContacts] = await Promise.all([
      axios.get('/api/v1/pendencies/'),
      axios.get('/api/v1/customers/'),
      axios.get('/api/v1/users/'),
      axios.get('/api/v1/contacts/')
    ])
    pendencies.value = resPendencies.data
    customers.value = resCustomers.data
    users.value = resUsers.data.filter(u => u.role !== 'system') // Ignorar usuários do sistema
    contacts.value = resContacts.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loadingList.value = false
  }
}

// Autocomplete de Clientes
const handleCustomerSearch = () => {
  if (!customerSearch.value.trim()) {
    customerSearchResults.value = []
    return
  }
  const query = customerSearch.value.toLowerCase()
  customerSearchResults.value = customers.value.filter(c => 
    c.name.toLowerCase().includes(query) || 
    (c.fantasy_name || '').toLowerCase().includes(query) || 
    c.phone.includes(query)
  ).slice(0, 5) // Limitar a 5 resultados
}

const selectCustomer = (customer) => {
  form.value.customer = customer.id
  selectedCustomerName.value = customer.name
  customerSearch.value = ''
  customerSearchResults.value = []
  showCustomerDropdown.value = false
  form.value.contact = null // Resetar contato dependente
}

const clearSelectedCustomer = () => {
  form.value.customer = null
  selectedCustomerName.value = ''
  form.value.contact = null
}

const handleClickOutsideAutocomplete = (e) => {
  if (!e.target.closest('.customer-autocomplete')) {
    showCustomerDropdown.value = false
  }
}

// Upload e manipulação de arquivos
const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (e) => {
  const files = e.target.files
  processFiles(files)
}

const handleFileDrop = (e) => {
  dragOver.value = false
  const files = e.dataTransfer.files
  processFiles(files)
}

const processFiles = (files) => {
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file.type.startsWith('image/')) {
      alert('Apenas imagens são permitidas.')
      continue
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('A imagem excede o tamanho limite de 5MB.')
      continue
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      newImages.value.push(e.target.result)
    }
    reader.readAsDataURL(file)
  }
}

const removeNewImage = (idx) => {
  newImages.value.splice(idx, 1)
}

const deleteExistingImage = async (imgId) => {
  if (!confirm('Deseja excluir permanentemente este anexo?')) return
  try {
    await axios.post(`/api/v1/pendencies/${editingId.value}/delete-image/`, { image_id: imgId })
    existingImages.value = existingImages.value.filter(img => img.id !== imgId)
    // Atualizar no objeto local na lista
    const localObj = pendencies.value.find(p => p.id === editingId.value)
    if (localObj) {
      localObj.images = localObj.images.filter(img => img.id !== imgId)
    }
  } catch (error) {
    console.error('Erro ao deletar imagem:', error)
    alert('Erro ao deletar imagem.')
  }
}

// Visualizador de Lightbox
const openLightbox = (src) => {
  lightboxSrc.value = src
  showLightbox.value = true
}

// Criação e Edição
const openCreateModal = () => {
  editingId.value = null
  newImages.value = []
  existingImages.value = []
  clearSelectedCustomer()
  
  // Setar valores padrão do formulário
  const now = new Date()
  const localIsoString = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  
  form.value = {
    title: '',
    operation_type: 'suporte',
    customer: null,
    contact: null,
    user: null,
    priority: 'medium',
    status: 'open',
    opening_date: localIsoString,
    forecast_date: '',
    description: ''
  }
  showModal.value = true
}

const editPendency = (item) => {
  editingId.value = item.id
  newImages.value = []
  existingImages.value = item.images || []
  
  // Setar formulário com dados
  const openDateLocal = item.opening_date ? new Date(item.opening_date) : new Date()
  const openIso = new Date(openDateLocal.getTime() - openDateLocal.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  
  let forecastIso = ''
  if (item.forecast_date) {
    const fDate = new Date(item.forecast_date)
    forecastIso = new Date(fDate.getTime() - fDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  }

  form.value = {
    title: item.title,
    operation_type: item.operation_type,
    customer: item.customer,
    contact: item.contact,
    user: item.user,
    priority: item.priority,
    status: item.status,
    opening_date: openIso,
    forecast_date: forecastIso,
    description: item.description || ''
  }

  if (item.customer_details) {
    selectedCustomerName.value = item.customer_details.name
  } else {
    selectedCustomerName.value = ''
  }

  showModal.value = true
}

const savePendency = async () => {
  loadingSave.value = true
  try {
    const payload = {
      ...form.value,
      uploaded_images: newImages.value
    }

    // Se estiver vazio, define como null para a API
    if (!payload.forecast_date) payload.forecast_date = null

    if (editingId.value) {
      const res = await axios.put(`/api/v1/pendencies/${editingId.value}/`, payload)
      // Substituir na lista
      const idx = pendencies.value.findIndex(p => p.id === editingId.value)
      if (idx !== -1) {
        pendencies.value[idx] = res.data
      }
    } else {
      const res = await axios.post('/api/v1/pendencies/', payload)
      pendencies.value.push(res.data)
    }

    showModal.value = false
    await fetchData() // Recarregar para garantir a ordenação correta vinda do banco
  } catch (error) {
    console.error('Erro ao salvar pendência:', error)
    alert('Erro ao salvar pendência. Verifique se todos os campos obrigatórios estão corretos.')
  } finally {
    loadingSave.value = false
  }
}

// Exclusão
const confirmDelete = (item) => {
  selectedDeleteId.value = item.id
  selectedDeleteTitle.value = item.title
  showDeleteModal.value = true
}

const deletePendency = async () => {
  loadingDelete.value = true
  try {
    await axios.delete(`/api/v1/pendencies/${selectedDeleteId.value}/`)
    pendencies.value = pendencies.value.filter(p => p.id !== selectedDeleteId.value)
    showDeleteModal.value = false
  } catch (error) {
    console.error('Erro ao excluir:', error)
    alert('Erro ao excluir pendência.')
  } finally {
    loadingDelete.value = false
  }
}

// Ciclo de Vida
onMounted(() => {
  fetchData()
  window.addEventListener('click', handleClickOutsideAutocomplete)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutsideAutocomplete)
})
</script>

<style scoped>
.pendencies-page-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background: var(--bg-dark);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 30px;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-info h1 {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 4px;
  background: linear-gradient(135deg, var(--text-primary) 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-info p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-bar {
  display: flex;
  align-items: center;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  width: 300px;
  transition: all 0.3s ease;
}

.search-bar:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.search-bar input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  margin-left: 10px;
  outline: none;
  font-size: 0.9rem;
  width: 100%;
}

.search-bar svg {
  color: var(--text-secondary);
}

/* Filtros */
.btn-filter-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
}

.btn-filter-toggle:hover {
  background: var(--border);
  color: var(--text-primary);
}

.btn-filter-active {
  border-color: var(--accent);
  color: var(--accent) !important;
  background: rgba(16, 185, 129, 0.05);
}

.filter-count-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: var(--accent);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}

.filters-container {
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
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

.filter-actions-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.btn-clear-filters {
  background: transparent;
  border: none;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-clear-filters:hover {
  text-decoration: underline;
}

/* View Mode Toggle */
.view-switcher-toggle {
  display: flex;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 2px;
  border-radius: 8px;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background: var(--border);
  color: var(--accent);
}

/* Grid layout cards */
.pendencies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.pendency-card {
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 280px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.pendency-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

.pendency-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.pendency-card.high::before { background: #ef4444; }
.pendency-card.medium::before { background: #f59e0b; }
.pendency-card.low::before { background: #10b981; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.operation-badge {
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(255,255,255,0.06);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.badge-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.priority-badge {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
}

.priority-badge.high { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.priority-badge.medium { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.priority-badge.low { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }

.card-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.pendency-card:hover .card-actions {
  opacity: 1;
}

.icon-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}

.icon-btn.delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.card-desc {
  color: var(--text-secondary);
  font-size: 0.88rem;
  line-height: 1.4;
  margin-bottom: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 15px;
  background: rgba(0, 0, 0, 0.15);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.02);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.detail-row svg {
  color: var(--accent);
}

.detail-row.overdue svg {
  color: #ef4444;
}

.detail-row.overdue span {
  color: #f87171;
  font-weight: 600;
}

.attached-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 5px;
}

.image-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.image-thumb:hover {
  transform: scale(1.08);
}

.image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.status-indicator {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

.status-indicator.open { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.status-indicator.pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.status-indicator.closed { background: rgba(16, 185, 129, 0.15); color: #34d399; }

.created-at {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* List view style */
.pendencies-table-view {
  border-radius: 12px;
  overflow-x: auto;
}

.pendencies-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.pendencies-table th {
  padding: 16px 20px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
}

.pendencies-table td {
  padding: 16px 20px;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.pendencies-table tr:hover {
  background: rgba(255,255,255,0.01);
}

.title-cell {
  display: flex;
  flex-direction: column;
}

.tbl-title {
  font-weight: 700;
  color: var(--text-primary);
}

.tbl-operation {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.client-cell {
  display: flex;
  flex-direction: column;
}

.client-cell .subtext {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.overdue-text {
  color: #ef4444;
  font-weight: 600;
}

.table-images {
  display: inline-block;
}

.images-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: 20px;
  cursor: zoom-in;
  font-weight: 600;
}

.images-count-badge:hover {
  background: var(--border);
}

.table-actions {
  display: flex;
  gap: 4px;
}

.table-action-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.table-action-btn:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}

.table-action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Modal extra styles */
.large-modal {
  max-width: 650px;
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
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
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

/* Drag Drop styles */
.drag-drop-area {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.drag-drop-area:hover, .drag-drop-area.drag-over {
  border-color: var(--accent);
  background: rgba(16, 185, 129, 0.03);
}

.drag-drop-area svg {
  color: var(--text-secondary);
  transition: color 0.3s;
}

.drag-drop-area:hover svg {
  color: var(--accent);
}

.drag-drop-area p {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.drag-drop-area .sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.hidden-input {
  display: none;
}

.images-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 15px;
}

.image-preview-item {
  width: 70px;
  height: 70px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border);
}

.image-preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-img-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.85);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
}

.remove-img-btn:hover {
  background: #ef4444;
}

.existing-images-section {
  flex-direction: column;
  width: 100%;
  align-items: flex-start;
  gap: 8px;
}

.existing-images-section .title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Modal Actions */
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

/* Lightbox overlay */
.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 20px;
}

.lightbox-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.lightbox-content img {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  display: block;
}

.close-lightbox-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 2rem;
  color: white;
  background: rgba(0,0,0,0.5);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-lightbox-btn:hover {
  background: rgba(0,0,0,0.7);
}

/* Animations */
.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-state, .spinner-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  border-radius: 16px;
  gap: 15px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-fade-enter-from, .slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Empty State Stylings */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 40px;
  border-radius: 16px;
  max-width: 600px;
  margin: 40px auto;
  border: 1px solid var(--border);
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.03) 0%, transparent 80%), var(--bg-card);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  margin-bottom: 24px;
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
}

.empty-state:hover .empty-icon {
  transform: translateY(-4px) scale(1.05);
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: 0 10px 20px rgba(34, 181, 95, 0.15), inset 0 0 20px rgba(34, 181, 95, 0.05);
}

.empty-state h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  max-width: 400px;
  margin-bottom: 24px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 12px;
}
</style>
