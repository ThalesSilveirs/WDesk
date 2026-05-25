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
          <div v-for="customer in filteredCustomers" :key="customer.id" class="customer-card glass-effect animate-in">
            <div class="card-header">
              <div class="avatar">
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
              <h3>{{ customer.name }}</h3>
              <div class="info-item">
                <PhoneIcon :size="16" />
                <span>{{ customer.phone }}</span>
              </div>
              <div v-if="customer.email" class="info-item">
                <MailIcon :size="16" />
                <span>{{ customer.email }}</span>
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
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>{{ editingId ? 'Editar Cliente' : 'Novo Cliente' }}</h2>
            <button @click="showModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          <form @submit.prevent="saveCustomer" class="modal-form">
            <div class="form-group">
              <label>Nome da Empresa / Cliente</label>
              <input v-model="form.name" required class="input-glass" placeholder="Ex: Confetti Eventos" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Telefone Principal</label>
                <input v-model="form.phone" required class="input-glass" placeholder="Ex: 5511999999999" />
              </div>
              <div class="form-group">
                <label>CPF/CNPJ</label>
                <input v-model="form.document" class="input-glass" placeholder="00.000.000/0001-00" />
              </div>
            </div>
            <div class="form-group">
              <label>E-mail</label>
              <input v-model="form.email" type="email" class="input-glass" placeholder="contato@empresa.com" />
            </div>
            <div class="form-group">
              <label>Endereço</label>
              <textarea v-model="form.address" class="input-glass" placeholder="Rua, Número, Bairro..." style="resize: vertical;"></textarea>
            </div>
            <div class="modal-actions">
              <button type="button" @click="showModal = false" class="btn-secondary">Cancelar</button>
              <button type="submit" class="btn-primary" :disabled="loading">
                {{ loading ? 'Salvando...' : 'Salvar Cliente' }}
              </button>
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
              <button @click="deleteContact(contact.id)" class="icon-btn delete small">
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
  MessageSquarePlus as MessageSquarePlusIcon
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

const form = ref({
  name: '',
  phone: '',
  email: '',
  document: '',
  address: ''
})

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
    (c.email && c.email.toLowerCase().includes(s))
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
  form.value = { name: '', phone: '', email: '', document: '', address: '' }
  showModal.value = true
}

const editCustomer = (customer) => {
  editingId.value = customer.id
  form.value = { ...customer }
  showModal.value = true
}

const saveCustomer = async () => {
  loading.value = true
  try {
    if (editingId.value) {
      await axios.put(`/api/v1/customers/${editingId.value}/`, form.value)
    } else {
      await axios.post(`/api/v1/customers/`, form.value)
    }
    
    showModal.value = false
    await fetchCustomers()
  } catch (e) {
    alert("Erro ao salvar cliente")
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
    // Atualiza o selecionado
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
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
}

.customer-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 25px;
  border-radius: 24px;
  transition: all 0.3s;
}

.customer-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-5px);
  border-color: rgba(16, 185, 129, 0.3);
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

.card-body h3 {
  font-size: 1.2rem;
  margin-bottom: 15px;
  font-weight: 700;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 8px;
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

/* Modais */
.contacts-modal {
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
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

.modal-form { display: flex; flex-direction: column; gap: 20px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.form-group { display: flex; flex-direction: column; gap: 8px; }

.form-group label { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }

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

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 15px;
}

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
  .modal-content {
    padding: 20px;
    border-radius: 20px;
    width: 90%;
  }
  .form-row {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}
</style>
