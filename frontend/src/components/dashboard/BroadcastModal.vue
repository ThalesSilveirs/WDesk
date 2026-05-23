<template>
  <div v-if="chatStore.showBroadcastModal" class="modal-overlay animate-fade-in" @click="closeModal">
    <div class="modal-content glass-effect premium-modal" @click.stop>
      <div class="modal-header">
        <div class="header-icon">
          <MegaphoneIcon :size="24" />
        </div>
        <div>
          <h2>Nova Transmissão (Broadcast)</h2>
          <p>Envie mensagens em lote para seus clientes</p>
        </div>
        <button @click="closeModal" class="close-btn-round"><XIcon :size="20" /></button>
      </div>

      <div class="modal-body">
        <!-- Passo 1: Mensagem -->
        <div class="form-group premium">
          <label>Mensagem de Transmissão</label>
          <textarea 
            v-model="message" 
            placeholder="Digite a mensagem que será enviada para todos os contatos selecionados..." 
            rows="4" 
            class="premium-input-textarea"
          ></textarea>
        </div>

        <!-- Passo 2: Seleção de Destinatários -->
        <div class="form-group premium">
          <div class="flex-between">
            <label>Destinatários ({{ selectedCount }} selecionado(s))</label>
            <button @click="toggleSelectAll" class="text-link">
              {{ allSelected ? 'Desmarcar Todos' : 'Selecionar Todos' }}
            </button>
          </div>
          
          <div class="search-wrapper">
            <SearchIcon :size="16" class="search-icon" />
            <input 
              v-model="search" 
              placeholder="Buscar clientes..." 
              class="premium-search-input"
            />
          </div>

          <div class="customers-list-wrapper">
            <div 
              v-for="customer in filteredCustomers" 
              :key="customer.id" 
              class="customer-selection-item"
              :class="{ selected: isSelected(customer.id) }"
              @click="toggleSelect(customer.id)"
            >
              <div class="checkbox-indicator">
                <CheckIcon v-if="isSelected(customer.id)" :size="14" />
              </div>
              <div class="customer-info-mini">
                <span class="name">{{ customer.name }}</span>
                <span class="phone">{{ customer.phone }}</span>
              </div>
            </div>
            <div v-if="filteredCustomers.length === 0" class="no-customers">
              Nenhum cliente encontrado.
            </div>
          </div>
        </div>

        <!-- Alerta de Banimento -->
        <div class="warning-box">
          <AlertTriangleIcon :size="18" class="warning-icon" />
          <div class="warning-text">
            <strong>Atenção:</strong> O sistema envia as mensagens de forma espaçada (intervalo de 1.5s) para reduzir o risco de bloqueio, mas evite enviar mensagens em excesso ou SPAM.
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary-v2">Cancelar</button>
        <button 
          @click="submitBroadcast" 
          class="btn-primary-v2" 
          :disabled="!message.trim() || selectedCount === 0 || loading"
        >
          <LoaderIcon v-if="loading" class="animate-spin" :size="20" />
          <span v-else>Iniciar Disparo ({{ selectedCount }})</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useChatStore } from '../../store/chat'
import { 
  Megaphone as MegaphoneIcon, 
  X as XIcon, 
  Search as SearchIcon, 
  Check as CheckIcon, 
  AlertTriangle as AlertTriangleIcon,
  Loader as LoaderIcon 
} from 'lucide-vue-next'
import axios from 'axios'

const chatStore = useChatStore()
const message = ref('')
const search = ref('')
const customers = ref([])
const selectedIds = ref([])
const loading = ref(false)

const fetchCustomers = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/v1/customers/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    customers.value = response.data
  } catch (e) {
    console.error("Erro ao carregar clientes para transmissão", e)
  }
}

onMounted(() => {
  fetchCustomers()
})

const filteredCustomers = computed(() => {
  if (!search.value) return customers.value
  const s = search.value.toLowerCase()
  return customers.value.filter(c => 
    c.name.toLowerCase().includes(s) || 
    c.phone.includes(s)
  )
})

const selectedCount = computed(() => selectedIds.value.length)

const allSelected = computed(() => {
  return customers.value.length > 0 && selectedIds.value.length === customers.value.length
})

const isSelected = (id) => selectedIds.value.includes(id)

const toggleSelect = (id) => {
  const index = selectedIds.value.indexOf(id)
  if (index === -1) {
    selectedIds.value.push(id)
  } else {
    selectedIds.value.splice(index, 1)
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = customers.value.map(c => c.id)
  }
}

const closeModal = () => {
  chatStore.showBroadcastModal = false
  message.value = ''
  selectedIds.value = []
}

const submitBroadcast = async () => {
  if (!message.value.trim() || selectedIds.value.length === 0) return
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post('/api/v1/tickets/broadcast/', {
      message: message.value,
      customer_ids: selectedIds.value
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    alert(`Sucesso: ${response.data.status} para ${response.data.target_count} destinatários!`)
    closeModal()
  } catch (e) {
    const errorMsg = e.response?.data?.error || e.message
    alert(`Erro ao iniciar transmissão: ${errorMsg}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.premium-modal {
  width: 500px;
  max-width: 90%;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--border);
  background: var(--bg-sidebar);
}

.modal-header {
  padding: 20px 25px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-icon {
  background: #10b981;
  color: white;
  padding: 10px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.modal-header h2 { font-size: 1.25rem; font-weight: 800; margin: 0; color: white; }
.modal-header p { font-size: 0.85rem; color: var(--text-secondary); margin: 3px 0 0 0; }

.close-btn-round {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  color: white;
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

.modal-body {
  padding: 25px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group.premium {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 700;
  color: var(--text-secondary);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-link {
  background: none;
  border: none;
  color: #10b981;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.text-link:hover {
  color: #059669;
}

.premium-input-textarea {
  width: 100%;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border);
  padding: 12px;
  border-radius: 12px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  resize: none;
  transition: all 0.2s;
}

.premium-input-textarea:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-secondary);
  opacity: 0.7;
}

.premium-search-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border);
  padding: 10px 10px 10px 38px;
  border-radius: 10px;
  color: white;
  font-size: 0.9rem;
  outline: none;
}

.premium-search-input:focus {
  border-color: #10b981;
}

.customers-list-wrapper {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border);
  border-radius: 12px;
  max-height: 180px;
  overflow-y: auto;
  padding: 5px;
}

.customer-selection-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.customer-selection-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.customer-selection-item.selected {
  background: rgba(16, 185, 129, 0.08);
}

.checkbox-indicator {
  width: 20px;
  height: 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.customer-selection-item.selected .checkbox-indicator {
  border-color: #10b981;
  background: #10b981;
  color: white;
}

.customer-info-mini {
  display: flex;
  flex-direction: column;
}

.customer-info-mini .name {
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
}

.customer-info-mini .phone {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.no-customers {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
  padding: 20px;
}

.warning-box {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 12px;
  padding: 12px 15px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.warning-icon {
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 2px;
}

.warning-text {
  font-size: 0.8rem;
  color: #f59e0b;
  line-height: 1.4;
  text-align: left;
}

.warning-text strong {
  font-weight: 700;
}

.modal-footer {
  padding: 15px 25px;
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border);
}

.btn-secondary-v2 {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: white;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary-v2 {
  background: #10b981;
  border: none;
  color: white;
  padding: 10px 25px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-primary-v2:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary-v2:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-out forwards;
}
</style>
