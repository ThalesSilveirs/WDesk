<template>
  <div class="connections-page-container animate-fade-in">

    <main class="connections-content">
      <header class="page-header glass-effect">
        <div class="header-info">
          <h1>Conexões WhatsApp</h1>
          <p>Gerencie suas instâncias da Evolution API</p>
        </div>
        <button @click="showAddModal = true" class="btn-primary">
          <PlusIcon :size="20" /> Nova Conexão
        </button>
      </header>

      <div class="connections-grid">
        <div v-for="conn in connections" :key="conn.id" class="connection-card glass-effect">
          <div class="card-top">
            <div class="status-indicator" :class="conn.status"></div>
            <div class="conn-info">
              <h3>{{ conn.name }}</h3>
              <code>{{ conn.instance_name }}</code>
            </div>
            <div class="card-actions">
              <button @click="syncStatus(conn)" class="icon-btn" title="Sincronizar Status" :disabled="syncing === conn.id">
                <RefreshIcon :class="{'animate-spin': syncing === conn.id}" :size="18" />
              </button>
              <button @click="deleteConn(conn.id)" class="icon-btn delete" title="Remover">
                <TrashIcon :size="18" />
              </button>
            </div>
          </div>

          <div class="card-status-info">
            <span class="status-text">{{ formatStatus(conn.status) }}</span>
          </div>

          <div class="card-footer">
            <button v-if="conn.status !== 'connected'" @click="getQRCode(conn)" class="btn-action primary" :disabled="loadingQR === conn.id">
              <QrCodeIcon :size="18" />
              {{ loadingQR === conn.id ? 'Gerando...' : 'Gerar QR Code' }}
            </button>
            <button v-else @click="disconnect(conn.id)" class="btn-action danger">
              <LogOutIcon :size="18" />
              Desconectar
            </button>
          </div>
        </div>

        <div v-if="connections.length === 0" class="empty-state">
          <WifiOffIcon :size="64" class="empty-icon" />
          <h2>Nenhuma conexão ativa</h2>
          <p>Clique em "Nova Conexão" para começar.</p>
        </div>
      </div>
    </main>

    <!-- Modal Adicionar Conexão (Premium Design) -->
    <Transition name="modal-fade">
      <div v-if="showAddModal" class="modal-overlay" @click="showAddModal = false">
        <div class="modal-content premium-modal" @click.stop>
          <div class="modal-header">
            <div class="header-icon">
              <PlusIcon :size="24" />
            </div>
            <div>
              <h2>Nova Instância</h2>
              <p>Configure uma nova conexão com o WhatsApp</p>
            </div>
            <button @click="showAddModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <div class="modal-body">
            <div class="form-group premium">
              <label>Nome de Exibição</label>
              <div class="input-wrapper">
                <MessageCircleIcon :size="18" class="input-icon" />
                <input 
                  v-model="newConn.name" 
                  placeholder="Ex: Departamento de Vendas" 
                  class="input-glass premium-input-v2" 
                />
              </div>
              <small>Apenas para identificação interna no dashboard.</small>
            </div>

            <div class="form-group premium">
              <label>ID da Instância (Evolution)</label>
              <div class="input-wrapper">
                <ZapIcon :size="18" class="input-icon" />
                <input 
                  v-model="newConn.instance_name" 
                  placeholder="Ex: vendas_01" 
                  class="input-glass premium-input-v2" 
                />
              </div>
              <small>Identificador único na API. Use apenas letras e números.</small>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="showAddModal = false" class="btn-secondary">Cancelar</button>
            <button 
              @click="createConn" 
              class="btn-primary-v2" 
              :disabled="!newConn.name || !newConn.instance_name || creating"
            >
              <LoaderIcon v-if="creating" class="animate-spin" :size="20" />
              <span v-else>Criar Instância</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal QR Code -->
    <Transition name="modal-fade">
      <div v-if="showQRModal" class="modal-overlay" @click="showQRModal = false">
        <div class="modal-content qr-modal" @click.stop>
          <div class="qr-header">
            <h2>Conectar WhatsApp</h2>
            <button @click="showQRModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          <p class="qr-description">Abra o WhatsApp no seu celular, vá em Aparelhos Conectados e escaneie o código abaixo:</p>
          
          <div class="qr-container">
            <img v-if="activeQR" :src="activeQR" alt="QR Code" />
            <div v-else class="qr-placeholder">
              <LoaderIcon class="animate-spin" :size="48" />
            </div>
          </div>
          
          <div class="qr-footer">
            <span class="status-tag connecting">Aguardando leitura...</span>
            <p>O dashboard atualizará automaticamente após a conexão.</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '../store/chat'
import { useRouter } from 'vue-router'
import { 
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Plus as PlusIcon,
  Trash2 as TrashIcon,
  QrCode as QrCodeIcon,
  X as XIcon,
  Loader as LoaderIcon,
  RefreshCw as RefreshIcon,
  Zap as ZapIcon
} from 'lucide-vue-next'
import axios from 'axios'

const router = useRouter()
const chatStore = useChatStore()
const connections = ref([])
const syncing = ref(null)
const showAddModal = ref(false)
const showQRModal = ref(false)
const activeQR = ref(null)
const loadingQR = ref(null)
const creating = ref(false)
const newConn = ref({ name: '', instance_name: '' })

const fetchConnections = async () => {
  const response = await axios.get(`/api/v1/connections/`)
  connections.value = response.data
}

const syncStatus = async (conn) => {
  syncing.value = conn.id
  try {
    const response = await axios.post(`/api/v1/connections/${conn.id}/sync_status/`, {})
    const index = connections.value.findIndex(c => c.id === conn.id)
    if (index !== -1) {
      connections.value[index].status = response.data.status
    }
    if (response.data.error) {
      console.warn("Aviso na sincronização:", response.data.error)
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || e.message
    alert(`Erro ao sincronizar status: ${errorMsg}`)
    console.error("Erro ao sincronizar status", e)
  } finally {
    syncing.value = null
  }
}

const formatStatus = (status) => {
  const map = {
    'connected': 'Conectado',
    'disconnected': 'Desconectado',
    'connecting': 'Aguardando QR Code'
  }
  return map[status] || status
}

const createConn = async () => {
  creating.value = true
  try {
    await axios.post(`/api/v1/connections/`, newConn.value)
    showAddModal.value = false
    newConn.value = { name: '', instance_name: '' }
    fetchConnections()
  } catch (e) {
    const errorMsg = e.response?.data?.error || "Verifique se o nome da instância já existe."
    alert("Erro ao criar conexão: " + errorMsg)
  } finally {
    creating.value = false
  }
}

const deleteConn = async (id) => {
  if (!confirm("Deseja realmente remover esta conexão?")) return
  await axios.delete(`/api/v1/connections/${id}/`)
  fetchConnections()
}

const getQRCode = async (conn) => {
  loadingQR.value = conn.id
  activeQR.value = null
  showQRModal.value = true
  try {
    const response = await axios.post(`/api/v1/connections/${conn.id}/connect/`, {})
    activeQR.value = response.data.qrcode
  } catch (e) {
    alert("Erro ao gerar QR Code")
    showQRModal.value = false
  } finally {
    loadingQR.value = null
  }
}

const disconnect = async (id) => {
  if (!confirm("Deseja desconectar esta instância?")) return
  try {
    await axios.post(`/api/v1/connections/${id}/logout/`, {})
    fetchConnections()
  } catch (e) {
    alert("Erro ao desconectar")
  }
}



const handleConnectionUpdate = (event) => {
  const updatedConn = event.detail
  const index = connections.value.findIndex(c => c.id === updatedConn.id)
  if (index !== -1) {
    connections.value[index] = updatedConn
  } else {
    connections.value.push(updatedConn)
  }
  
  // Se estivermos esperando conexão e ela conectou, fecha o modal
  if (showQRModal.value && updatedConn.status === 'connected') {
    showQRModal.value = false
    activeQR.value = null
  }
}

onMounted(async () => {
  await fetchConnections()
  window.addEventListener('connection-updated', handleConnectionUpdate)
  
  // Sincroniza o status de cada conexão ao carregar para garantir precisão
  connections.value.forEach(conn => syncStatus(conn))
})

import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('connection-updated', handleConnectionUpdate)
})
</script>

<style scoped>
.connections-page-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
}

.connections-content {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.page-header {
  padding: 25px 40px;
  border-radius: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.header-info h1 { font-size: 1.8rem; font-weight: 800; margin-bottom: 5px; }
.header-info p { color: var(--text-secondary); }

.connections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 30px;
}

.connection-card {
  padding: 25px;
  border-radius: 24px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-top {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-indicator.connected { background: #10b981; box-shadow: 0 0 10px #10b981; }
.status-indicator.connecting { background: #f59e0b; animation: pulse 1.5s infinite; }
.status-indicator.disconnected { background: #ef4444; }

.conn-info { flex: 1; }
.conn-info h3 { margin: 0; font-size: 1.1rem; }
.conn-info code { font-size: 0.8rem; color: var(--accent); opacity: 0.8; }

.card-status-info {
  background: rgba(255, 255, 255, 0.03);
  padding: 10px 15px;
  border-radius: 12px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  text-align: center;
}

.btn-action {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: none;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action.primary { background: var(--accent); color: white; }
.btn-action.danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
.btn-action:hover { transform: translateY(-2px); }

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 100px 0;
  color: var(--text-secondary);
}

.empty-icon { opacity: 0.2; margin-bottom: 20px; }

/* Premium Modal Styles */
.premium-modal {
  max-width: 450px;
  width: 90%;
  padding: 0 !important;
  overflow: hidden;
}

.modal-header {
  padding: 25px;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid var(--border);
}

.header-icon {
  background: var(--accent);
  padding: 10px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.modal-header h2 { margin: 0; font-size: 1.25rem; }
.modal-header p { margin: 2px 0 0; font-size: 0.85rem; color: var(--text-secondary); }

.close-btn-round {
  margin-left: auto;
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

.modal-body { padding: 25px; }

.form-group.premium { margin-bottom: 20px; }
.form-group.premium label { font-weight: 700; color: var(--text-secondary); font-size: 0.8rem; text-transform: uppercase; margin-bottom: 8px; display: block; }

.input-wrapper { position: relative; display: flex; align-items: center; }
.input-icon { position: absolute; left: 14px; color: var(--accent); opacity: 0.7; }

.premium-input-v2 {
  padding-left: 42px;
}

.modal-footer {
  padding: 20px 25px;
  background: var(--bg-card);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border);
}

.btn-primary-v2 {
  background: var(--accent);
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
.btn-primary-v2:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
  100% { opacity: 1; transform: scale(1); }
}

@media (max-width: 768px) {
  .connections-content {
    padding: 20px;
  }
  .page-header {
    padding: 15px 20px;
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
    margin-bottom: 25px;
  }
  .header-info h1 {
    font-size: 1.5rem;
    text-align: center;
  }
  .header-info p {
    text-align: center;
  }
  .btn-primary {
    justify-content: center;
  }
  .connections-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .premium-modal {
    width: 95%;
  }
  .modal-header {
    padding: 15px;
  }
  .modal-body {
    padding: 15px;
  }
  .modal-footer {
    padding: 15px;
  }
}
</style>
