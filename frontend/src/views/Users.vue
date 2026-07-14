<template>
  <div class="users-page-container">
    <main class="users-content">
      <header class="content-header">
        <h1>Gerenciamento de Equipe</h1>
        <button @click="showAddModal = true" class="add-btn">
          <PlusIcon :size="20" /> Novo Atendente
        </button>
      </header>

      <div class="users-grid">
        <div v-for="user in users" :key="user.id" class="user-card glass-effect">
          <div class="avatar-wrapper">
            <div class="user-avatar">
              {{ user.first_name?.charAt(0) || user.username.charAt(0).toUpperCase() }}
            </div>
            <span class="status-dot-indicator" :class="user.status?.toLowerCase() || 'offline'"></span>
          </div>
          <div class="user-details">
            <h3>{{ user.first_name }} {{ user.last_name }}</h3>
            <p class="department" v-if="user.department">{{ user.department }}</p>
            <p class="username">@{{ user.username }}</p>
            <p class="whatsapp" v-if="user.whatsapp">
              <WhatsAppIcon :size="14" style="vertical-align: middle; margin-right: 4px; color: #25D366;" />
              {{ user.whatsapp }}
            </p>
            <span class="role-badge" :class="user.role">{{ user.role }}</span>
          </div>
          <div class="user-actions">
            <button @click="editUser(user)" class="edit-btn">
              <PencilIcon :size="18" />
            </button>
            <button @click="deleteUser(user.id)" class="delete-btn">
              <TrashIcon :size="18" />
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal Novo Usuário -->
    <Transition name="modal-fade">
      <div v-if="showAddModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <h2>{{ editingId ? 'Editar Atendente' : 'Novo Atendente' }}</h2>
          <form @submit.prevent="saveUser" class="user-form">
            <div class="form-row">
              <input v-model="newUser.first_name" type="text" class="input-glass" placeholder="Nome" required />
              <input v-model="newUser.last_name" type="text" class="input-glass" placeholder="Sobrenome" required />
            </div>
            <input v-model="newUser.department" type="text" class="input-glass" placeholder="Área de Atuação (ex: Vendas, Suporte)" />
            <input v-model="newUser.whatsapp" type="text" class="input-glass" placeholder="WhatsApp (ex: 5511999999999)" />
            <input v-model="newUser.username" type="text" class="input-glass" placeholder="Usuário (login)" required />
            <input v-model="newUser.email" type="email" class="input-glass" placeholder="E-mail" required />
            <input v-model="newUser.password" type="password" class="input-glass" :placeholder="editingId ? 'Senha (deixe em branco para não alterar)' : 'Senha'" :required="!editingId" />
            <select v-model="newUser.role" class="input-glass">
              <option value="attendant">Atendente</option>
              <option value="admin">Administrador</option>
            </select>
            <div class="modal-actions">
              <button type="button" @click="closeModal" class="btn-secondary">Cancelar</button>
              <button type="submit" class="submit-btn">{{ editingId ? 'Salvar Alterações' : 'Criar Usuário' }}</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { 
  Plus as PlusIcon,
  Trash2 as TrashIcon,
  Pencil as PencilIcon,
  MessageSquare as WhatsAppIcon
} from 'lucide-vue-next'
const users = ref([])
const showAddModal = ref(false)
const editingId = ref(null)
const newUser = ref({
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  role: 'attendant',
  department: '',
  whatsapp: ''
})

const fetchUsers = async () => {
  const response = await axios.get(`/api/v1/users/`)
  users.value = response.data
}

const editUser = (user) => {
  editingId.value = user.id
  newUser.value = { ...user, password: '' }
  showAddModal.value = true
}

const closeModal = () => {
  showAddModal.value = false
  editingId.value = null
  newUser.value = { username: '', first_name: '', last_name: '', email: '', password: '', role: 'attendant', department: '', whatsapp: '' }
}

const saveUser = async () => {
  try {
    const payload = { ...newUser.value }
    if (editingId.value && !payload.password) delete payload.password

    if (editingId.value) {
      await axios.patch(`/api/v1/users/${editingId.value}/`, payload)
    } else {
      await axios.post(`/api/v1/users/`, payload)
    }
    
    closeModal()
    fetchUsers()
  } catch (err) {
    alert('Erro ao salvar usuário: ' + (err.response?.data?.username || 'Verifique os dados'))
  }
}

const deleteUser = async (id) => {
  if (!confirm('Deseja realmente remover este usuário?')) return
  await axios.delete(`/api/v1/users/${id}/`)
  fetchUsers()
}
const handleStatusChange = (e) => {
  const { user_id, status } = e.detail
  const user = users.value.find(u => u.id === user_id)
  if (user) {
    user.status = status
  }
}

onMounted(() => {
  fetchUsers()
  window.addEventListener('user-status-changed', handleStatusChange)
})

onUnmounted(() => {
  window.removeEventListener('user-status-changed', handleStatusChange)
})
</script>

<style scoped>
.users-page-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.users-content {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.add-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.user-card {
  padding: 20px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.user-avatar {
  width: 60px;
  height: 60px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.user-details { flex: 1; }
.user-details h3 { margin: 0; font-size: 1.1rem; }
.department { color: var(--accent); font-size: 0.85rem; font-weight: 600; margin: 2px 0; }
.username { color: var(--text-secondary); font-size: 0.85rem; margin: 2px 0; }
.whatsapp {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 2px 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.role-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
  font-weight: 700;
}
.role-badge.admin { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.role-badge.attendant { background: rgba(16, 185, 129, 0.2); color: var(--accent); }

.delete-btn, .edit-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  opacity: 0.6;
  cursor: pointer;
  transition: all 0.2s;
  padding: 5px;
}
.delete-btn:hover { color: #ef4444; opacity: 1; }
.edit-btn:hover { color: var(--accent); opacity: 1; }

.user-form { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
.form-row { display: flex; gap: 10px; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 10px;
}

.submit-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 768px) {
  .users-content {
    padding: 20px;
  }
  .content-header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
    margin-bottom: 25px;
  }
  .content-header h1 {
    font-size: 1.5rem;
    text-align: center;
  }
  .add-btn {
    justify-content: center;
  }
  .users-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .modal-content {
    width: 90%;
    padding: 20px;
  }
  .form-row {
    flex-direction: column;
    gap: 15px;
  }
}

.avatar-wrapper {
  position: relative;
}

.status-dot-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--bg-dark);
}

.status-dot-indicator.online {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.status-dot-indicator.away,
.status-dot-indicator.ausente {
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
}

.status-dot-indicator.offline {
  background: #94a3b8;
}
</style>
