<template>
  <div class="customers-page-container">
    <main class="main-content">
      <header class="page-header glass-effect">
        <div class="header-info">
          <h1>Clientes</h1>
          <p>Gerencie sua base de contatos e CRM</p>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <SearchIcon :size="20" />
            <input v-model="search" placeholder="Buscar por nome ou telefone..." type="text" />
          </div>
          <button @click="openCreateModal" class="btn-primary">
            <PlusIcon :size="20" /> Novo Cliente
          </button>
        </div>
      </header>

      <div class="content-wrapper">
        <div class="customers-grid" v-if="filteredCustomers.length > 0">
          <div v-for="customer in filteredCustomers" :key="customer.id" class="customer-card glass-effect animate-in" :class="{ 'blocked-card': customer.is_blocked }">
            <div class="card-header">
              <div class="avatar" :class="{ 'blocked-avatar': customer.is_blocked }">
                {{ customer.name.charAt(0).toUpperCase() }}
              </div>
              <div class="card-actions">
                <button @click="openTicket(customer)" class="icon-btn" title="Abrir Ticket">
                  <MessageSquarePlusIcon :size="18" />
                </button>
                <button @click="manageContacts(customer)" class="icon-btn" title="Contatos Adicionais">
                  <UsersIcon :size="18" />
                </button>
                <button @click="editCustomer(customer)" class="icon-btn" title="Editar">
                  <EditIcon :size="18" />
                </button>
                <button @click="confirmDelete(customer)" class="icon-btn delete" title="Excluir">
                  <TrashIcon :size="18" />
                </button>
              </div>
            </div>
            <div class="card-body">
              <div class="name-block">
                <h3>{{ customer.name }}</h3>
                <span v-if="customer.is_blocked" class="blocked-badge">Bloqueado</span>
              </div>
              <div v-if="customer.fantasy_name" class="fantasy-name">{{ customer.fantasy_name }}</div>
              
              <div class="info-item">
                <PhoneIcon :size="16" />
                <span>{{ customer.phone }}</span>
              </div>
              <div v-if="customer.email" class="info-item">
                <MailIcon :size="16" />
                <span>{{ customer.email }}</span>
              </div>
              <div v-if="customer.cnpj || customer.cpf" class="info-item document-item">
                <FileTextIcon :size="16" />
                <span>{{ customer.cnpj ? 'CNPJ: ' + customer.cnpj : 'CPF: ' + customer.cpf }}</span>
              </div>
              <div v-if="customer.additional_contacts?.length > 0" class="additional-count">
                {{ customer.additional_contacts.length }} contato(s) adicional(is)
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state animate-in">
          <div class="empty-icon">
            <UsersIcon :size="64" />
          </div>
          <h2>Nenhum cliente encontrado</h2>
          <p>Comece adicionando seu primeiro cliente no botão acima.</p>
        </div>
      </div>
    </main>

    <!-- Modal de Cadastro/Edição de Cliente -->
    <Transition name="modal-fade">
      <div v-if="showModal" class="modal-overlay" @click="showModal = false">
        <div class="modal-content large-modal" @click.stop>
          <div class="modal-header-container">
            <div class="modal-header">
              <h2>{{ editingId ? 'Editar Cliente' : 'Novo Cliente' }}</h2>
              <button @click="showModal = false" class="close-btn-round"><XIcon :size="20" /></button>
            </div>
            
            <!-- Abas do Formulário -->
            <div class="tabs-nav">
              <button type="button" :class="{ active: activeTab === 'geral' }" @click="activeTab = 'geral'">Dados Gerais</button>
              <button type="button" :class="{ active: activeTab === 'contatos' }" @click="activeTab = 'contatos'">Contatos</button>
              <button type="button" :class="{ active: activeTab === 'enderecos' }" @click="activeTab = 'enderecos'">Endereços</button>
              <button type="button" :class="{ active: activeTab === 'financeiro' }" @click="activeTab = 'financeiro'">Financeiro</button>
              <button type="button" :class="{ active: activeTab === 'extra' }" @click="activeTab = 'extra'">Outros / CRM</button>
            </div>
          </div>

          <form @submit.prevent="saveCustomer" class="modal-form-scrollable">
            <!-- ABA 1: DADOS GERAIS -->
            <div v-if="activeTab === 'geral'" class="tab-pane">
              <div class="form-group">
                <label>Razão Social / Nome Completo *</label>
                <input v-model="form.name" required class="input-glass" placeholder="Ex: Confetti Eventos Ltda" />
              </div>

              <div class="form-group">
                <label>Nome Fantasia</label>
                <input v-model="form.fantasy_name" class="input-glass" placeholder="Ex: Confetti Eventos" />
              </div>

              <div class="grid-3">
                <div class="form-group">
                  <label>CNPJ</label>
                  <input v-model="form.cnpj" class="input-glass" placeholder="Ex: 00000000000000" maxlength="14" />
                </div>
                <div class="form-group">
                  <label>CPF</label>
                  <input v-model="form.cpf" class="input-glass" placeholder="Ex: 00000000000" maxlength="11" />
                </div>
                <div class="form-group">
                  <label>RG</label>
                  <input v-model="form.rg" class="input-glass" placeholder="Ex: 000000000" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Inscrição Estadual</label>
                  <input v-model="form.state_inscription" class="input-glass" placeholder="Isento ou Número" />
                </div>
                <div class="form-group">
                  <label>Inscrição Municipal</label>
                  <input v-model="form.municipal_inscription" class="input-glass" placeholder="Número" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Data de Nascimento</label>
                  <input v-model="form.birth_date" type="date" class="input-glass" />
                </div>
                <div class="form-group">
                  <label>Data de Fundação</label>
                  <input v-model="form.foundation_date" type="date" class="input-glass" />
                </div>
              </div>

              <div class="checkbox-row">
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.optante_simples" />
                  <span class="checkmark"></span>
                  Optante pelo Simples Nacional
                </label>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.consumidor_final" />
                  <span class="checkmark"></span>
                  Consumidor Final
                </label>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.nao_contribuinte" />
                  <span class="checkmark"></span>
                  Não Contribuinte
                </label>
              </div>
            </div>

            <!-- ABA 2: CONTATOS -->
            <div v-if="activeTab === 'contatos'" class="tab-pane">
              <div class="grid-2">
                <div class="form-group">
                  <label>Telefone Principal *</label>
                  <input v-model="form.phone" required class="input-glass" placeholder="Ex: 5511999999999" />
                </div>
                <div class="form-group">
                  <label>WhatsApp</label>
                  <input v-model="form.whatsapp" class="input-glass" placeholder="Ex: 5511999999999" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Celular</label>
                  <input v-model="form.mobile" class="input-glass" placeholder="Ex: 5511999999999" />
                </div>
                <div class="form-group">
                  <label>Telefone 2 (Fixo/Outro)</label>
                  <input v-model="form.phone2" class="input-glass" placeholder="Ex: 551133333333" />
                </div>
              </div>

              <div class="form-group">
                <label>E-mail Geral</label>
                <input v-model="form.email" type="email" class="input-glass" placeholder="contato@empresa.com" />
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>E-mail Comercial</label>
                  <input v-model="form.email_commercial" type="email" class="input-glass" placeholder="comercial@empresa.com" />
                </div>
                <div class="form-group">
                  <label>E-mail Financeiro</label>
                  <input v-model="form.email_financial" type="email" class="input-glass" placeholder="financeiro@empresa.com" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Contato Principal (Nome)</label>
                  <input v-model="form.contact_name" class="input-glass" placeholder="Ex: João Silva" />
                </div>
                <div class="form-group">
                  <label>Contato Secundário (Nome)</label>
                  <input v-model="form.contact_name2" class="input-glass" placeholder="Ex: Maria Souza" />
                </div>
              </div>
            </div>

            <!-- ABA 3: ENDEREÇOS -->
            <div v-if="activeTab === 'enderecos'" class="tab-pane">
              <div class="address-subtabs">
                <button type="button" :class="{ active: activeAddressTab === 'principal' }" @click="activeAddressTab = 'principal'">Principal</button>
                <button type="button" :class="{ active: activeAddressTab === 'cobranca' }" @click="activeAddressTab = 'cobranca'">Cobrança</button>
                <button type="button" :class="{ active: activeAddressTab === 'entrega' }" @click="activeAddressTab = 'entrega'">Entrega</button>
              </div>

              <!-- Endereço Principal -->
              <div v-if="activeAddressTab === 'principal'" class="subtab-pane">
                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP</label>
                    <input v-model="form.zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado (UF)</label>
                    <input v-model="form.state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group">
                    <label>Cidade</label>
                    <input v-model="form.city" class="input-glass" placeholder="São Paulo" />
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro / Endereço</label>
                    <input v-model="form.address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número</label>
                    <input v-model="form.number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Complemento</label>
                    <input v-model="form.complement" class="input-glass" placeholder="Apto 42" />
                  </div>
                  <div class="form-group">
                    <label>Bairro</label>
                    <input v-model="form.neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>

              <!-- Endereço de Cobrança -->
              <div v-if="activeAddressTab === 'cobranca'" class="subtab-pane">
                <div class="subtab-header">
                  <h4>Endereço de Cobrança</h4>
                  <button type="button" @click="copyPrincipalToBilling" class="btn-secondary-sm">
                    <CopyIcon :size="14" /> Copiar do Principal
                  </button>
                </div>

                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP Cobrança</label>
                    <input v-model="form.billing_zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado Cobrança</label>
                    <input v-model="form.billing_state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group">
                    <label>Cidade Cobrança</label>
                    <input v-model="form.billing_city" class="input-glass" placeholder="São Paulo" />
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro Cobrança</label>
                    <input v-model="form.billing_address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número Cobrança</label>
                    <input v-model="form.billing_number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Bairro Cobrança</label>
                    <input v-model="form.billing_neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>

              <!-- Endereço de Entrega -->
              <div v-if="activeAddressTab === 'entrega'" class="subtab-pane">
                <div class="subtab-header">
                  <h4>Endereço de Entrega</h4>
                  <button type="button" @click="copyPrincipalToDelivery" class="btn-secondary-sm">
                    <CopyIcon :size="14" /> Copiar do Principal
                  </button>
                </div>

                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP Entrega</label>
                    <input v-model="form.delivery_zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado Entrega</label>
                    <input v-model="form.delivery_state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group">
                    <label>Cidade Entrega</label>
                    <input v-model="form.delivery_city" class="input-glass" placeholder="São Paulo" />
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro Entrega</label>
                    <input v-model="form.delivery_address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número Entrega</label>
                    <input v-model="form.delivery_number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Bairro Entrega</label>
                    <input v-model="form.delivery_neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>
            </div>

            <!-- ABA 4: FINANCEIRO -->
            <div v-if="activeTab === 'financeiro'" class="tab-pane">
              <div class="grid-2">
                <div class="form-group">
                  <label>Limite de Crédito (R$)</label>
                  <input v-model.number="form.credit_limit" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
                <div class="form-group">
                  <label>Vencimento do Limite de Crédito</label>
                  <input v-model="form.credit_limit_expiry" type="date" class="input-glass" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Percentual de Comissão (%)</label>
                  <input v-model.number="form.commission_rate" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
                <div class="form-group">
                  <label>Percentual Máximo Desconto (%)</label>
                  <input v-model.number="form.discount_rate" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
              </div>

              <div class="grid-3">
                <div class="form-group">
                  <label>Código do Banco</label>
                  <input v-model.number="form.bank_code" type="number" class="input-glass" placeholder="341" />
                </div>
                <div class="form-group">
                  <label>Agência Bancária</label>
                  <input v-model="form.bank_agency" class="input-glass" placeholder="0001" />
                </div>
                <div class="form-group">
                  <label>Conta Bancária</label>
                  <input v-model="form.bank_account" class="input-glass" placeholder="12345-6" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Dia de Vencimento Fatura</label>
                  <input v-model.number="form.due_day" type="number" min="1" max="31" class="input-glass" placeholder="10" />
                </div>
                <div class="form-group">
                  <label>Forma/Condição de Pagamento</label>
                  <input v-model="form.payment_method" class="input-glass" placeholder="Boleto 30 dias, PIX" />
                </div>
              </div>

              <div class="form-group">
                <label>Observação Financeira</label>
                <textarea v-model="form.obs_financial" class="input-glass" placeholder="Restrições, formas específicas de faturamento..." rows="3" style="resize: vertical;"></textarea>
              </div>
            </div>

            <!-- ABA 5: OUTROS / CRM -->
            <div v-if="activeTab === 'extra'" class="tab-pane">
              <div class="grid-4">
                <div class="form-group">
                  <label>Código Representante</label>
                  <input v-model.number="form.representative_id" type="number" class="input-glass" placeholder="ID" />
                </div>
                <div class="form-group">
                  <label>Código Transportadora</label>
                  <input v-model.number="form.carrier_id" type="number" class="input-glass" placeholder="ID" />
                </div>
                <div class="form-group">
                  <label>Região Operacional</label>
                  <input v-model.number="form.region_id" type="number" class="input-glass" placeholder="Código" />
                </div>
                <div class="form-group">
                  <label>Grupo de Clientes</label>
                  <input v-model.number="form.group_id" type="number" class="input-glass" placeholder="Código" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Parecer de Análise de Crédito</label>
                  <textarea v-model="form.credit_opinion" class="input-glass" placeholder="Histórico ou parecer do departamento de crédito..." rows="3" style="resize: vertical;"></textarea>
                </div>
                <div class="form-group">
                  <label>Observação para Nota Fiscal</label>
                  <textarea v-model="form.obs_invoice" class="input-glass" placeholder="Textos fixos para NF..." rows="3" style="resize: vertical;"></textarea>
                </div>
              </div>

              <div class="form-group">
                <label>Observações Gerais</label>
                <textarea v-model="form.obs" class="input-glass" placeholder="Outras informações do cliente..." rows="3" style="resize: vertical;"></textarea>
              </div>

              <div class="checkbox-row" style="margin-top: 10px;">
                <label class="checkbox-container blocked-label">
                  <input type="checkbox" v-model="form.is_blocked" />
                  <span class="checkmark red-check"></span>
                  <strong>Bloquear Cliente (Bloqueia emissão de pedidos/tickets de forma automática)</strong>
                </label>
              </div>
            </div>

            <!-- Botões de Ação do Modal -->
            <div class="modal-actions-container">
              <span class="required-note">* Campos obrigatórios</span>
              <div class="modal-actions">
                <button type="button" @click="showModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="loading">
                  {{ loading ? 'Salvando...' : 'Salvar Cliente' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Modal de Gerenciamento de Contatos Adicionais -->
    <Transition name="modal-fade">
      <div v-if="showContactsModal" class="modal-overlay" @click="showContactsModal = false">
        <div class="modal-content contacts-modal" @click.stop>
          <div class="modal-header">
            <div>
              <h2>Contatos de {{ selectedCustomer.name }}</h2>
              <p style="color: var(--text-secondary); font-size: 0.9rem;">Gerencie as pessoas vinculadas a esta empresa</p>
            </div>
            <button @click="showContactsModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          
          <div class="contacts-list">
            <div v-for="contact in selectedCustomer.additional_contacts" :key="contact.id" class="contact-item-row">
              <div class="contact-avatar">
                {{ contact.name.charAt(0) }}
              </div>
              <div class="contact-details-mini">
                <strong>{{ contact.name }}</strong>
                <span>{{ contact.phone }}</span>
              </div>
              <button @click="deleteContact(contact.id)" class="icon-btn delete small" title="Excluir contato">
                <TrashIcon :size="14" />
              </button>
            </div>

            <div v-if="!selectedCustomer.additional_contacts?.length" class="empty-mini">
              Nenhum contato adicional cadastrado.
            </div>
          </div>

          <div class="add-contact-form">
            <h4>Adicionar Novo Contato</h4>
            <div class="form-row">
              <input v-model="newContact.name" class="input-glass" placeholder="Nome da Pessoa" />
              <input v-model="newContact.phone" class="input-glass" placeholder="WhatsApp (55...)" />
            </div>
            <button @click="addContact" class="btn-primary-sm block" :disabled="loadingContact">
              {{ loadingContact ? 'Adicionando...' : 'Adicionar Contato' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { 
  Users as UsersIcon, 
  Search as SearchIcon, 
  Plus as PlusIcon,
  Phone as PhoneIcon,
  Mail as MailIcon,
  FileText as FileTextIcon,
  Edit as EditIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  MessageSquarePlus as MessageSquarePlusIcon,
  Copy as CopyIcon
} from 'lucide-vue-next'
import { useChatStore } from '../store/chat'

const chatStore = useChatStore()
const router = useRouter()
const customers = ref([])
const search = ref('')
const showModal = ref(false)
const showContactsModal = ref(false)
const loading = ref(false)
const loadingContact = ref(false)
const selectedCustomer = ref(null)
const editingId = ref(null)

// Abas de navegação
const activeTab = ref('geral')
const activeAddressTab = ref('principal')

const defaultForm = () => ({
  name: '',
  fantasy_name: '',
  cnpj: '',
  cpf: '',
  rg: '',
  state_inscription: '',
  municipal_inscription: '',
  birth_date: '',
  foundation_date: '',
  phone: '',
  phone2: '',
  mobile: '',
  whatsapp: '',
  email: '',
  email_commercial: '',
  email_financial: '',
  contact_name: '',
  contact_name2: '',
  address: '',
  zip_code: '',
  number: '',
  complement: '',
  neighborhood: '',
  city: '',
  state: '',
  billing_zip_code: '',
  billing_address: '',
  billing_number: '',
  billing_neighborhood: '',
  billing_city: '',
  billing_state: '',
  delivery_zip_code: '',
  delivery_address: '',
  delivery_number: '',
  delivery_neighborhood: '',
  delivery_city: '',
  delivery_state: '',
  credit_limit: null,
  credit_limit_expiry: '',
  commission_rate: null,
  discount_rate: null,
  bank_code: null,
  bank_agency: '',
  bank_account: '',
  due_day: null,
  payment_method: '',
  optante_simples: false,
  consumidor_final: true,
  nao_contribuinte: false,
  representative_id: null,
  carrier_id: null,
  region_id: null,
  group_id: null,
  obs: '',
  obs_financial: '',
  obs_invoice: '',
  credit_opinion: '',
  is_blocked: false,
  document: '' // Mantido para compatibilidade histórica do backend
})

const form = ref(defaultForm())

const newContact = ref({
  name: '',
  phone: '',
  email: ''
})

const filteredCustomers = computed(() => {
  if (!search.value) return customers.value
  const s = search.value.toLowerCase()
  return customers.value.filter(c => 
    c.name.toLowerCase().includes(s) || 
    c.phone.includes(s) || 
    (c.email && c.email.toLowerCase().includes(s)) ||
    (c.fantasy_name && c.fantasy_name.toLowerCase().includes(s)) ||
    (c.cnpj && c.cnpj.includes(s)) ||
    (c.cpf && c.cpf.includes(s))
  )
})

const fetchCustomers = async () => {
  try {
    const response = await axios.get(`/api/v1/customers/`)
    customers.value = response.data
  } catch (e) {
    console.error("Erro ao buscar clientes", e)
  }
}

const openCreateModal = () => {
  editingId.value = null
  form.value = defaultForm()
  activeTab.value = 'geral'
  activeAddressTab.value = 'principal'
  showModal.value = true
}

const editCustomer = (customer) => {
  editingId.value = customer.id
  // Garante que campos não preenchidos fiquem devidamente inicializados
  const merged = { ...defaultForm(), ...customer }
  form.value = merged
  activeTab.value = 'geral'
  activeAddressTab.value = 'principal'
  showModal.value = true
}

const copyPrincipalToBilling = () => {
  form.value.billing_zip_code = form.value.zip_code
  form.value.billing_address = form.value.address
  form.value.billing_number = form.value.number
  form.value.billing_neighborhood = form.value.neighborhood
  form.value.billing_city = form.value.city
  form.value.billing_state = form.value.state
}

const copyPrincipalToDelivery = () => {
  form.value.delivery_zip_code = form.value.zip_code
  form.value.delivery_address = form.value.address
  form.value.delivery_number = form.value.number
  form.value.delivery_neighborhood = form.value.neighborhood
  form.value.delivery_city = form.value.city
  form.value.delivery_state = form.value.state
}

const saveCustomer = async () => {
  loading.value = true
  
  // Limpeza de campos vazios numéricos ou de data para não violar tipos do backend
  const payload = { ...form.value }
  
  // Garante sincronização de document para compatibilidade histórica do backend
  payload.document = payload.cnpj || payload.cpf || ''
  
  const numericFields = [
    'credit_limit', 'commission_rate', 'discount_rate', 'bank_code', 
    'due_day', 'representative_id', 'carrier_id', 'region_id', 'group_id'
  ]
  numericFields.forEach(field => {
    if (payload[field] === '' || payload[field] === undefined || payload[field] === null) {
      payload[field] = null
    }
  })
  
  const dateFields = ['birth_date', 'foundation_date', 'credit_limit_expiry']
  dateFields.forEach(field => {
    if (!payload[field]) {
      payload[field] = null
    }
  })

  try {
    if (editingId.value) {
      await axios.put(`/api/v1/customers/${editingId.value}/`, payload)
    } else {
      await axios.post(`/api/v1/customers/`, payload)
    }
    
    showModal.value = false
    await fetchCustomers()
  } catch (e) {
    console.error("Erro ao salvar cliente", e.response?.data)
    alert("Erro ao salvar cliente. Verifique o preenchimento dos campos.")
  } finally {
    loading.value = false
  }
}

const manageContacts = (customer) => {
  selectedCustomer.value = customer
  newContact.value = { name: '', phone: '', email: '', customer: customer.id }
  showContactsModal.value = true
}

const addContact = async () => {
  if (!newContact.value.name || !newContact.value.phone) return
  loadingContact.value = true
  try {
    await axios.post(`/api/v1/customer-contacts/`, newContact.value)
    newContact.value = { name: '', phone: '', email: '', customer: selectedCustomer.value.id }
    await fetchCustomers()
    selectedCustomer.value = customers.value.find(c => c.id === selectedCustomer.value.id)
  } catch (e) {
    alert("Erro ao adicionar contato")
  } finally {
    loadingContact.value = false
  }
}

const deleteContact = async (id) => {
  if (!confirm("Excluir este contato?")) return
  try {
    await axios.delete(`/api/v1/customer-contacts/${id}/`)
    await fetchCustomers()
    selectedCustomer.value = customers.value.find(c => c.id === selectedCustomer.value.id)
  } catch (e) {
    alert("Erro ao excluir contato")
  }
}

const confirmDelete = async (customer) => {
  if (confirm(`Deseja realmente excluir o cliente ${customer.name}?`)) {
    try {
      await axios.delete(`/api/v1/customers/${customer.id}/`)
      await fetchCustomers()
    } catch (e) {
      alert("Erro ao excluir cliente")
    }
  }
}

const openTicket = async (customer) => {
  try {
    await axios.post(`/api/v1/customers/${customer.id}/open_ticket/`, {})
    router.push('/')
  } catch (e) {
    alert("Erro ao abrir ticket")
  }
}

onMounted(fetchCustomers)
</script>

<style scoped>
.customers-page-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  padding: 25px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-info h1 {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.header-info p { color: var(--text-secondary); font-size: 0.95rem; }

.header-actions {
  display: flex;
  gap: 20px;
  align-items: center;
}

.search-bar {
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 300px;
}

.search-bar input {
  background: none;
  border: none;
  color: var(--text-primary);
  width: 100%;
  outline: none;
}

.btn-primary {
  background: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-primary:hover { transform: translateY(-2px); }

.content-wrapper {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.customers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 25px;
}

.customer-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 25px;
  border-radius: 24px;
  transition: all 0.3s;
  position: relative;
}

.customer-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-5px);
  border-color: rgba(16, 185, 129, 0.3);
}

.blocked-card {
  border-color: rgba(239, 68, 68, 0.4) !important;
  background: rgba(239, 68, 68, 0.02) !important;
}

.blocked-card:hover {
  border-color: rgba(239, 68, 68, 0.7) !important;
  background: rgba(239, 68, 68, 0.05) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 800;
}

.blocked-avatar {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
}

.card-actions { display: flex; gap: 8px; }

.icon-btn {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.icon-btn.delete:hover { background: #ef4444; border-color: #ef4444; }

.icon-btn.small { padding: 4px; }

.name-block {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.name-block h3 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

.blocked-badge {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.fantasy-name {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 15px;
  font-style: italic;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.document-item {
  margin-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.03);
  padding-top: 6px;
}

.additional-count {
  margin-top: 15px;
  font-size: 0.75rem;
  color: #10b981;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  display: inline-block;
  padding: 2px 8px;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding-top: 100px;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.2;
}

/* Modais e Layouts de Formulário Complexo */
.large-modal {
  width: 850px !important;
  max-width: 95% !important;
  height: 90vh;
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  overflow: hidden;
}

.modal-header-container {
  padding: 30px 30px 10px 30px;
  background: rgba(255, 255, 255, 0.01);
  border-bottom: 1px solid var(--border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
.close-btn-round:hover { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

/* Tabs de Navegação */
.tabs-nav {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.tabs-nav button {
  background: none;
  border: 1px solid transparent;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.tabs-nav button:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.03);
}

.tabs-nav button.active {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

/* Área de formulário rolável */
.modal-form-scrollable {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.25s ease-out forwards;
}

/* Sub-abas de Endereços */
.address-subtabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
}

.address-subtabs button {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.address-subtabs button.active {
  border-bottom-color: #10b981;
  color: #10b981;
}

.subtab-pane {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.2s ease-out forwards;
}

.subtab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 10px;
}

.subtab-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

/* Campos de Endereço Customizados */
.address-main-row {
  display: flex;
  gap: 20px;
}
.address-field { flex: 3; }
.number-field { flex: 1; }

/* Grid Auxiliares */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.checkbox-row {
  display: flex;
  flex-wrap: wrap;
  gap: 25px;
  margin-top: 10px;
  padding: 10px 0;
}

/* Checkbox estilizado */
.checkbox-container {
  display: flex;
  align-items: center;
  position: relative;
  padding-left: 30px;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--text-primary);
  user-select: none;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 20px;
  width: 20px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 6px;
  transition: all 0.2s;
}

.checkbox-container:hover input ~ .checkmark {
  border-color: #10b981;
}

.checkbox-container input:checked ~ .checkmark {
  background-color: #10b981;
  border-color: #10b981;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-container .checkmark:after {
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.blocked-label {
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 12px 15px 12px 45px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.05);
  flex: 1;
}

.red-check {
  left: 15px;
  top: 12px;
}

.checkbox-container:hover input ~ .red-check {
  border-color: #ef4444;
}

.checkbox-container input:checked ~ .red-check {
  background-color: #ef4444;
  border-color: #ef4444;
}

/* Rodapé das Ações do Modal */
.modal-actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border);
  padding-top: 25px;
  margin-top: 10px;
}

.required-note {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.modal-actions {
  display: flex;
  gap: 15px;
}

.btn-secondary {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--border);
}

.btn-secondary-sm {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-secondary-sm:hover {
  background: var(--border);
}

/* Contacts Modal Específicos */
.contacts-modal {
  max-width: 500px;
}

.contacts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
  max-height: 250px;
  overflow-y: auto;
  padding-right: 10px;
}

.contact-item-row {
  display: flex;
  align-items: center;
  gap: 15px;
  background: var(--glass);
  padding: 10px 15px;
  border-radius: 12px;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.contact-avatar {
  width: 36px;
  height: 36px;
  background: var(--border);
  color: var(--text-primary);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.contact-details-mini {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.contact-details-mini strong { font-size: 0.9rem; }
.contact-details-mini span { font-size: 0.8rem; color: var(--text-secondary); }

.add-contact-form {
  border-top: 1px solid var(--border);
  padding-top: 20px;
}

.add-contact-form h4 { margin-bottom: 15px; font-size: 1rem; }

.btn-primary-sm {
  background: #10b981;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary-sm.block { width: 100%; margin-top: 10px; }

.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-mini { text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 20px; }

@media (max-width: 768px) {
  .page-header {
    padding: 15px 20px;
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .search-bar {
    width: 100%;
  }
  .btn-primary {
    justify-content: center;
  }
  .content-wrapper {
    padding: 15px;
  }
  .customers-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .large-modal {
    width: 95% !important;
    height: 95vh;
  }
  .modal-form-scrollable {
    padding: 20px;
  }
  .grid-2, .grid-3, .grid-4 {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .address-main-row {
    flex-direction: column;
    gap: 15px;
  }
  .checkbox-row {
    flex-direction: column;
    gap: 15px;
  }
  .modal-actions-container {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
    text-align: center;
  }
  .modal-actions {
    justify-content: center;
  }
  .tabs-nav {
    padding-bottom: 5px;
  }
}
</style>
