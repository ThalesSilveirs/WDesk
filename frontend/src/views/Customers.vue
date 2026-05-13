<template>
  <div class="app-layout">
    <aside class="mini-sidebar glass-effect">
      <router-link to="/" class="nav-item">
        <MessageCircleIcon :size="24" />
      </router-link>
      <router-link to="/customers" class="nav-item active">
        <ContactIcon :size="24" />
      </router-link>
      <router-link v-if="userRole === 'admin'" to="/users" class="nav-item">
        <UsersIcon :size="24" />
      </router-link>
      <router-link v-if="userRole === 'admin'" to="/connections" class="nav-item">
        <WifiIcon :size="24" />
      </router-link>
      <router-link v-if="userRole === 'admin'" to="/settings" class="nav-item">
        <SettingsIcon :size="24" />
      </router-link>
      <div class="bottom-actions">
        <button @click="chatStore.toggleTheme" class="nav-item theme-toggle" :title="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
          <SunIcon v-if="chatStore.theme === 'dark'" :size="24" />
          <MoonIcon v-else :size="24" />
        </button>
        <button @click="logout" class="nav-item logout">
          <LogOutIcon :size="24" />
        </button>
      </div>
    </aside>

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
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-content glass-effect">
        <div class="modal-header">
          <h2>{{ editingId ? 'Editar Cliente' : 'Novo Cliente' }}</h2>
          <button @click="showModal = false" class="close-btn"><XIcon :size="24" /></button>
        </div>
        <form @submit.prevent="saveCustomer" class="modal-form">
          <div class="form-group">
            <label>Nome da Empresa / Cliente</label>
            <input v-model="form.name" required placeholder="Ex: Confetti Eventos" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Telefone Principal</label>
              <input v-model="form.phone" required placeholder="Ex: 5511999999999" />
            </div>
            <div class="form-group">
              <label>CPF/CNPJ</label>
              <input v-model="form.document" placeholder="00.000.000/0001-00" />
            </div>
          </div>
          <div class="form-group">
            <label>E-mail</label>
            <input v-model="form.email" type="email" placeholder="contato@empresa.com" />
          </div>
          <div class="form-group">
            <label>Endereço</label>
            <textarea v-model="form.address" placeholder="Rua, Número, Bairro..."></textarea>
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

    <!-- Modal de Gerenciamento de Contatos Adicionais -->
    <div v-if="showContactsModal" class="modal-overlay">
      <div class="modal-content glass-effect contacts-modal">
        <div class="modal-header">
          <div>
            <h2>Contatos de {{ selectedCustomer.name }}</h2>
            <p style="color: #94a3b8; font-size: 0.9rem;">Gerencie as pessoas vinculadas a esta empresa</p>
          </div>
          <button @click="showContactsModal = false" class="close-btn"><XIcon :size="24" /></button>
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
            <input v-model="newContact.name" placeholder="Nome da Pessoa" />
            <input v-model="newContact.phone" placeholder="WhatsApp (55...)" />
          </div>
          <button @click="addContact" class="btn-primary-sm block" :disabled="loadingContact">
            {{ loadingContact ? 'Adicionando...' : 'Adicionar Contato' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { 
  MessageCircle as MessageCircleIcon, 
  Users as UsersIcon, 
  LogOut as LogOutIcon,
  Search as SearchIcon, 
  Plus as PlusIcon,
  Contact as ContactIcon,
  Phone as PhoneIcon,
  Mail as MailIcon,
  FileText as FileTextIcon,
  Edit as EditIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  MessageSquarePlus as MessageSquarePlusIcon,
  Settings as SettingsIcon,
  Wifi as WifiIcon,
  Sun as SunIcon,
  Moon as MoonIcon
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
const editingId = ref(null)
const userRole = ref(localStorage.getItem('role'))
const selectedCustomer = ref(null)

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
    const token = localStorage.getItem('token')
    const response = await axios.get(`/api/v1/customers/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
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
    const token = localStorage.getItem('token')
    const config = { headers: { Authorization: `Bearer ${token}` } }
    
    if (editingId.value) {
      await axios.put(`/api/v1/customers/${editingId.value}/`, form.value, config)
    } else {
      await axios.post(`/api/v1/customers/`, form.value, config)
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
    const token = localStorage.getItem('token')
    await axios.post(`/api/v1/customer-contacts/`, newContact.value, {
      headers: { Authorization: `Bearer ${token}` }
    })
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
    const token = localStorage.getItem('token')
    await axios.delete(`/api/v1/customer-contacts/${id}/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    await fetchCustomers()
    selectedCustomer.value = customers.value.find(c => c.id === selectedCustomer.value.id)
  } catch (e) {
    alert("Erro ao excluir contato")
  }
}

const confirmDelete = async (customer) => {
  if (confirm(`Deseja realmente excluir o cliente ${customer.name}?`)) {
    try {
      const token = localStorage.getItem('token')
      await axios.delete(`/api/v1/customers/${customer.id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await fetchCustomers()
    } catch (e) {
      alert("Erro ao excluir cliente")
    }
  }
}

const openTicket = async (customer) => {
  try {
    const token = localStorage.getItem('token')
    await axios.post(`/api/v1/customers/${customer.id}/open_ticket/`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    router.push('/')
  } catch (e) {
    alert("Erro ao abrir ticket")
  }
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

onMounted(fetchCustomers)
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  background: var(--bg-dark);
  color: var(--text-primary);
}

.mini-sidebar {
  width: 70px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  gap: 20px;
}

.nav-item {
  color: var(--text-secondary);
  padding: 12px;
  border-radius: 12px;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-item:hover, .nav-item.active {
  background: var(--accent);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.logout { color: #ef4444; border: none; background: none; cursor: pointer; }
.theme-toggle { border: none; background: none; cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { color: var(--accent); }

.bottom-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
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
  color: #94a3b8;
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
  color: #94a3b8;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.2;
}

/* Modais */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  width: 100%;
  max-width: 550px;
  padding: 35px;
  border-radius: 30px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  color: var(--text-primary);
}

.contacts-modal {
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.close-btn { background: none; border: none; color: #94a3b8; cursor: pointer; }

.modal-form { display: flex; flex-direction: column; gap: 20px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.form-group { display: flex; flex-direction: column; gap: 8px; }

.form-group label { font-size: 0.85rem; font-weight: 600; color: #94a3b8; }

.form-group input, .form-group textarea {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px;
  border-radius: 12px;
  color: white;
  outline: none;
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
  background: rgba(255, 255, 255, 0.03);
  padding: 10px 15px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.contact-avatar {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
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
.contact-details-mini span { font-size: 0.8rem; color: #94a3b8; }

.add-contact-form {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 20px;
}

.add-contact-form h4 { margin-bottom: 15px; font-size: 1rem; }

.add-contact-form input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px;
  border-radius: 10px;
  color: white;
  margin-bottom: 10px;
  width: 100%;
}

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

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  cursor: pointer;
}

.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-mini { text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 20px; }
</style>
