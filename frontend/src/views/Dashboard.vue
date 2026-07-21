<template>
  <div class="dashboard-page animate-fade-in">

    <!-- Dashboard Grid -->
    <div class="dashboard-grid">
      <!-- Row 1: Instance Status & Quick Actions -->
      <div class="row-top">
        <!-- Instance Widget -->
        <div class="widget-card glass-effect instance-widget">
          <div class="widget-header">
            <div class="instance-icon-wrapper" :class="connectionStatus">
              <ServerIcon :size="24" />
            </div>
            <div class="instance-details">
              <h3>{{ stats.connection?.name || 'Sem Conexão WhatsApp' }}</h3>
              <p>#{{ stats.connection?.instance_name || 'nenhuma_ativa' }}</p>
            </div>
            <span class="badge-status" :class="connectionStatus">
              {{ formatConnectionStatus(stats.connection?.status) }}
            </span>
            <button @click="verifyInstance" class="btn-verify" :disabled="verifying">
              <RefreshCwIcon :class="{'animate-spin': verifying}" :size="16" />
              <span>{{ verifying ? 'Verificando...' : 'Verificar Instância' }}</span>
            </button>
          </div>
          <div class="widget-metrics">
            <div class="metric-item">
              <LatencyIcon :size="16" />
              <div class="metric-text">
                <span>Latência da API:</span>
                <strong>{{ stats.connection?.latency || '0ms' }}</strong>
              </div>
            </div>
            <div class="metric-item">
              <ProtocolIcon :size="16" />
              <div class="metric-text">
                <span>Protocolo:</span>
                <strong>{{ stats.connection?.protocol || 'HTTP REST' }}</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions Card -->
        <div class="widget-card glass-effect quick-actions-card">
          <h4>AÇÕES RÁPIDAS</h4>
          <div class="actions-buttons">
            <button @click="openBroadcast" class="quick-btn broadcast">
              <MegaphoneIcon :size="18" />
              <span>Nova Transmissão</span>
              <ChevronRightIcon :size="16" class="arrow" />
            </button>
            <button @click="downloadReport" class="quick-btn report">
              <FileSpreadsheetIcon :size="18" />
              <span>Gerar Relatório</span>
              <ChevronRightIcon :size="16" class="arrow" />
            </button>
          </div>
        </div>
      </div>

      <!-- Row 2: Statistics Cards -->
      <div class="row-stats">
        <!-- Card 1: Active Chats -->
        <div class="stat-card glass-effect">
          <div class="card-header-row">
            <div class="icon-box green">
              <MessageCircleIcon :size="20" />
            </div>
            <span class="trend-badge positive">+12%</span>
          </div>
          <div class="card-body-row">
            <span class="label">ATENDIMENTOS ATIVOS</span>
            <h2>{{ stats.active_chats || 0 }}</h2>
            <span class="subtext">Ativos agora</span>
            <div class="progress-bar">
              <div class="progress-fill green" style="width: 65%"></div>
            </div>
          </div>
        </div>

        <!-- Card 2: Avg Response Time -->
        <div class="stat-card glass-effect">
          <div class="card-header-row">
            <div class="icon-box blue">
              <ClockIcon :size="20" />
            </div>
            <span class="trend-badge negative">-2m</span>
          </div>
          <div class="card-body-row">
            <span class="label">TEMPO MÉDIO DE RESPOSTA</span>
            <h2>{{ stats.avg_response_time || '4m 12s' }}</h2>
            <div class="mini-bar-chart">
              <div class="chart-bar" style="height: 40%"></div>
              <div class="chart-bar" style="height: 55%"></div>
              <div class="chart-bar" style="height: 35%"></div>
              <div class="chart-bar" style="height: 70%"></div>
              <div class="chart-bar active" style="height: 45%"></div>
              <div class="chart-bar" style="height: 60%"></div>
            </div>
          </div>
        </div>

        <!-- Card 3: Resolution Rate -->
        <div class="stat-card glass-effect">
          <div class="card-header-row">
            <div class="icon-box green">
              <ShieldCheckIcon :size="20" />
            </div>
            <span class="target-label">Meta: 95%</span>
          </div>
          <div class="card-body-row">
            <span class="label">TAXA DE RESOLUÇÃO</span>
            <h2>{{ stats.resolution_rate || 92.4 }}%</h2>
            <div class="segmented-progress">
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment active"></div>
              <div class="segment"></div>
            </div>
          </div>
        </div>

        <!-- Card 4: Messages Sent Today -->
        <div class="stat-card glass-effect">
          <div class="card-header-row">
            <div class="icon-box purple">
              <SendIcon :size="20" />
            </div>
            <TrendingUpIcon :size="18" class="trend-icon" />
          </div>
          <div class="card-body-row">
            <span class="label">MENSAGENS ENVIADAS HOJE</span>
            <h2>{{ stats.messages_sent_today || 0 }}</h2>
            <span class="subtext">Pico: 10h - 14h</span>
          </div>
        </div>
      </div>

      <!-- Row 3: Trends Chart & Team Activity -->
      <div class="row-bottom-layout">
        <!-- Chart Widget -->
        <div class="widget-card glass-effect chart-widget">
          <div class="chart-header">
            <h4>Evolução de Conversas</h4>
            <div class="toggle-group">
              <button :class="{ active: chartRange === '7' }" @click="chartRange = '7'">7 Dias</button>
              <button :class="{ active: chartRange === '30' }" @click="chartRange = '30'">30 Dias</button>
            </div>
          </div>
          <div class="chart-container">
            <div class="bar-chart-visual">
              <div v-for="(item, index) in stats.trends" :key="index" class="bar-col">
                <div class="bar-tooltip">{{ item.count }} chamados</div>
                <div class="bar-wrapper">
                  <div 
                    class="bar-fill" 
                    :style="{ height: getBarHeight(item.count) }"
                    :class="{ active: index === 3 }"
                  ></div>
                </div>
                <span class="bar-label">{{ item.day }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Team Activity Widget -->
        <div class="widget-card glass-effect team-widget">
          <div class="team-header">
            <h4>Atividade da Equipe</h4>
            <span class="active-badge">{{ activeAgentsCount }} Ativos</span>
          </div>
          <div class="team-list">
            <div v-for="agent in stats.team_activity" :key="agent.id" class="team-member-item">
              <div class="avatar-wrapper">
                <div class="member-avatar">
                  {{ agent.first_name?.charAt(0).toUpperCase() || agent.username?.charAt(0).toUpperCase() }}
                </div>
                <span class="status-dot-indicator" :class="agent.status?.toLowerCase() || 'offline'"></span>
              </div>
              <div class="member-info">
                <h5>{{ agent.first_name }} {{ agent.last_name }}</h5>
                <p v-if="agent.status === 'Online'">
                  {{ agent.active_chats > 0 ? `Atendendo: ${agent.active_chats} ${agent.active_chats === 1 ? 'chat' : 'chats'}` : 'Disponível' }}
                </p>
                <p v-else-if="agent.status === 'Ausente'" class="away">Ausente</p>
                <p v-else class="offline">Offline</p>
              </div>
            </div>
          </div>
          <div class="team-footer">
            <router-link to="/users" class="view-all-link">Ver Todos os Membros</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useChatStore } from '../store/chat'
import { 
  ChevronDown as ChevronDownIcon,
  Search as SearchIcon,
  Bell as BellIcon,
  History as HistoryIcon,
  Server as ServerIcon,
  RefreshCw as RefreshCwIcon,
  Activity as LatencyIcon,
  Shield as ProtocolIcon,
  ChevronRight as ChevronRightIcon,
  MessageCircle as MessageCircleIcon,
  Clock as ClockIcon,
  ShieldAlert as ShieldCheckIcon,
  Send as SendIcon,
  TrendingUp as TrendingUpIcon,
  Megaphone as MegaphoneIcon,
  FileText as FileSpreadsheetIcon
} from 'lucide-vue-next'
import axios from 'axios'

const chatStore = useChatStore()
const currentStatus = ref('online')
const showStatusMenu = ref(false)
const verifying = ref(false)
const chartRange = ref('7')

// Computes display name
const userDisplayName = computed(() => {
  if (!chatStore.user) return 'Carregando...'
  return chatStore.user.first_name 
    ? `${chatStore.user.first_name} ${chatStore.user.last_name || ''}` 
    : chatStore.user.username
})

// Computes profile initials
const userInitials = computed(() => {
  if (!chatStore.user) return '?'
  const name = chatStore.user.first_name || chatStore.user.username
  return name.charAt(0).toUpperCase()
})

const stats = ref({
  active_chats: 0,
  avg_response_time: '4m 12s',
  avg_response_seconds: 252,
  resolution_rate: 92.4,
  messages_sent_today: 0,
  connection: null,
  trends: [
    { day: 'Mon', count: 4 },
    { day: 'Tue', count: 6 },
    { day: 'Wed', count: 5 },
    { day: 'Thu', count: 10 },
    { day: 'Fri', count: 8 },
    { day: 'Sat', count: 3 },
    { day: 'Sun', count: 6 }
  ],
  team_activity: []
})

const connectionStatus = computed(() => {
  const status = stats.value.connection?.status?.toLowerCase() || 'disconnected'
  return status === 'connected' ? 'connected' : (status === 'connecting' ? 'connecting' : 'disconnected')
})

const activeAgentsCount = computed(() => {
  return stats.value.team_activity.filter(a => a.status === 'Online').length
})

const formatStatusName = (status) => {
  const map = {
    'online': 'Online',
    'away': 'Ausente',
    'offline': 'Offline'
  }
  return map[status] || status
}

const formatConnectionStatus = (status) => {
  if (!status) return 'DESCONECTADO'
  const map = {
    'CONNECTED': 'CONECTADO',
    'CONNECTING': 'CONECTANDO',
    'DISCONNECTED': 'DESCONECTADO'
  }
  return map[status.toUpperCase()] || status.toUpperCase()
}

const changeStatus = (status) => {
  currentStatus.value = status
  showStatusMenu.value = false
}

const fetchDashboardStats = async () => {
  try {
    const response = await axios.get('/api/v1/tickets/stats/')
    stats.value = response.data
  } catch (e) {
    console.error("Erro ao carregar estatísticas do dashboard", e)
  }
}

const verifyInstance = async () => {
  verifying.value = true
  try {
    const response = await axios.get('/api/v1/connections/')
    if (response.data && response.data.length > 0) {
      const conn = response.data[0]
      alert(`Instância "${conn.name}" (${conn.instance_name}) está com status: ${conn.status.toUpperCase()}`)
    } else {
      alert("Nenhuma conexão WhatsApp cadastrada.")
    }
    await fetchDashboardStats()
  } catch (e) {
    alert("Erro ao verificar o status da instância WhatsApp.")
  } finally {
    verifying.value = false
  }
}

const openBroadcast = () => {
  chatStore.showBroadcastModal = true
}

const downloadReport = async () => {
  try {
    const response = await axios.get('/api/v1/tickets/generate_report/', {
      responseType: 'blob'
    })
    const fileUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = fileUrl
    link.setAttribute('download', 'relatorio_atendimentos.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (e) {
    alert("Erro ao baixar o relatório CSV.")
  }
}

const getBarHeight = (count) => {
  const max = Math.max(...stats.value.trends.map(t => t.count), 1)
  return `${(count / max) * 100}%`
}

let intervalId = null

const handleStatusChange = (e) => {
  const { user_id, status } = e.detail
  const agent = stats.value.team_activity.find(a => a.id === user_id)
  if (agent) {
    agent.status = status
  }
}

const fetchStatsIfVisible = () => {
  if (!document.hidden) {
    fetchDashboardStats()
  }
}

const handleVisibilityChange = () => {
  if (!document.hidden) {
    fetchDashboardStats()
  }
}

onMounted(() => {
  fetchDashboardStats()
  intervalId = setInterval(fetchStatsIfVisible, 10000)
  window.addEventListener('user-status-changed', handleStatusChange)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
  window.removeEventListener('user-status-changed', handleStatusChange)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.dashboard-page {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  gap: 30px;
  height: 100%;
}

/* Header Bar Styling */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h1 {
  font-size: 1.6rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
  color: var(--text-primary);
}

.status-dropdown {
  position: relative;
}

.status-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.status-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-btn.online .status-dot, .status-option.online .status-dot { background: #10b981; box-shadow: 0 0 8px #10b981; }
.status-btn.away .status-dot, .status-option.away .status-dot { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
.status-btn.offline .status-dot, .status-option.offline .status-dot { background: #94a3b8; }

.status-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  border-radius: 12px;
  overflow: hidden;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 140px;
  border: 1px solid var(--border);
  background: var(--bg-sidebar);
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}

.status-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  border: none;
  background: none;
  color: var(--text-primary);
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-weight: 500;
}

.status-option:hover {
  background: rgba(255, 255, 255, 0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-search {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-secondary);
}

.header-search input {
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px 12px 8px 38px;
  color: var(--text-primary);
  outline: none;
  width: 260px;
  font-size: 0.9rem;
}

.header-search input:focus {
  border-color: #10b981;
}

.header-icon-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.header-icon-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
}

.header-icon-btn .badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: bold;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-avatar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 10px;
  border-left: 1px solid var(--border);
}

.profile-initials {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-weight: bold;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
}

.profile-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
}

/* Grid Layout */
.dashboard-grid {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

/* Row 1 Layout */
.row-top {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 25px;
}

.widget-card {
  border-radius: 24px;
  border: 1px solid var(--border);
  padding: 25px;
  background: var(--bg-card);
}

/* Instance status card */
.instance-widget {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 20px;
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.instance-icon-wrapper {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.instance-icon-wrapper.connected {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.2);
}

.instance-details {
  flex: 1;
}

.instance-details h3 {
  font-size: 1.15rem;
  font-weight: 800;
  margin: 0;
  color: var(--text-primary);
}

.instance-details p {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 2px 0 0 0;
  font-family: monospace;
}

.badge-status {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.badge-status.connected { background: rgba(16, 185, 129, 0.12); color: #10b981; }
.badge-status.connecting { background: rgba(245, 158, 11, 0.12); color: #f59e0b; }
.badge-status.disconnected { background: rgba(239, 68, 68, 0.12); color: #ef4444; }

.btn-verify {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 12px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-verify:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.widget-metrics {
  display: flex;
  gap: 40px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.metric-text {
  display: flex;
  gap: 5px;
}

.metric-text strong {
  color: var(--text-primary);
}

/* Quick Actions card */
.quick-actions-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.quick-actions-card h4 {
  font-size: 0.8rem;
  text-transform: uppercase;
  color: var(--text-secondary);
  letter-spacing: 1px;
  margin-bottom: 15px;
}

.actions-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  justify-content: center;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 20px;
  border-radius: 14px;
  border: 1px solid var(--border);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn.broadcast {
  background: rgba(34, 181, 95, 0.08);
  border-color: rgba(34, 181, 95, 0.2);
  color: var(--accent);
}

.quick-btn.broadcast:hover {
  background: var(--brand-gradient);
  color: white;
  box-shadow: 0 4px 12px rgba(34, 181, 95, 0.25);
  border-color: transparent;
}

.quick-btn.report {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
}

.quick-btn.report:hover {
  background: rgba(255, 255, 255, 0.08);
}

.quick-btn .arrow {
  margin-left: auto;
  opacity: 0.6;
}

/* Row 2 Layout: Stat Cards */
.row-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 25px;
}

.stat-card {
  border-radius: 24px;
  border: 1px solid var(--border);
  padding: 25px;
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 170px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.icon-box {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-box.green { background: rgba(16, 185, 129, 0.12); color: #10b981; }
.icon-box.blue { background: rgba(59, 130, 246, 0.12); color: #3b82f6; }
.icon-box.purple { background: rgba(139, 92, 246, 0.12); color: #8b5cf6; }

.trend-badge {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
}

.trend-badge.positive { background: rgba(16, 185, 129, 0.1); color: #10b981; }
.trend-badge.negative { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

.target-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.trend-icon {
  color: var(--text-secondary);
  opacity: 0.6;
}

.card-body-row {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-body-row .label {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.card-body-row h2 {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
  color: var(--text-primary);
}

.card-body-row .subtext {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.progress-bar {
  background: rgba(255, 255, 255, 0.05);
  height: 5px;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 10px;
}

.progress-fill {
  height: 100%;
  border-radius: 10px;
}

.progress-fill.green { background: #10b981; }

.segmented-progress {
  display: flex;
  gap: 3px;
  margin-top: 10px;
}

.segmented-progress .segment {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
}

.segmented-progress .segment.active {
  background: #10b981;
}

.mini-bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 32px;
  margin-top: 8px;
}

.chart-bar {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px 3px 0 0;
}

.chart-bar.active {
  background: #3b82f6;
}

/* Row 3 Layout: Chart & Team Widget */
.row-bottom-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 25px;
}

.chart-widget {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h4 {
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}

.toggle-group {
  display: flex;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  padding: 2px;
  border-radius: 10px;
}

.toggle-group button {
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-group button.active {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}

.chart-container {
  flex: 1;
  min-height: 200px;
  display: flex;
  align-items: flex-end;
}

/* CSS Bar Chart */
.bar-chart-visual {
  width: 100%;
  height: 220px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-bottom: 20px;
}

.bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.bar-wrapper {
  width: 45px;
  height: 180px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.bar-fill {
  width: 100%;
  background: rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  transition: all 0.5s ease-out;
}

.bar-fill.active {
  background: #10b981;
}

.bar-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 10px;
  font-weight: 600;
}

.bar-tooltip {
  position: absolute;
  bottom: 100%;
  margin-bottom: 5px;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transform: translateY(5px);
  transition: all 0.2s;
}

.bar-col:hover .bar-tooltip {
  opacity: 1;
  transform: translateY(0);
}

.bar-col:hover .bar-fill {
  background: #10b981;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}

/* Team Widget Styling */
.team-widget {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-header h4 {
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}

.active-badge {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
}

.team-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
  max-height: 240px;
  overflow-y: auto;
}

.team-member-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}

.team-member-item:last-child {
  border-bottom: none;
}

.avatar-wrapper {
  position: relative;
}

.member-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
}

.status-dot-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-sidebar);
}

.status-dot-indicator.online { background: #10b981; }
.status-dot-indicator.away,
.status-dot-indicator.ausente { background: #f59e0b; }
.status-dot-indicator.offline { background: #94a3b8; }

.member-info h5 {
  font-size: 0.9rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.member-info p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 2px 0 0 0;
}

.member-info p.offline {
  color: var(--text-secondary);
  opacity: 0.6;
}

.team-footer {
  text-align: center;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.view-all-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  transition: color 0.2s;
}

.view-all-link:hover {
  color: var(--text-primary);
}

/* Animations */
.animate-fade-in {
  animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1024px) {
  .row-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 15px;
    gap: 20px;
  }
  .widget-card {
    padding: 15px;
    border-radius: 20px;
  }
  .row-top {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  /* Instance Widget Mobile layout */
  .instance-widget .widget-header {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    align-items: center;
  }
  .instance-widget .instance-details h3 {
    font-size: 1rem;
  }
  .instance-widget .badge-status {
    grid-column: 3;
    padding: 4px 8px;
    font-size: 0.7rem;
  }
  .instance-widget .btn-verify {
    grid-column: 1 / -1;
    width: 100%;
    justify-content: center;
    margin-top: 5px;
    padding: 10px;
    font-size: 0.8rem;
  }
  .widget-metrics {
    gap: 10px;
    justify-content: space-between;
    padding-top: 12px;
  }
  .metric-item {
    font-size: 0.75rem;
  }

  /* Quick Actions Mobile */
  .quick-actions-card {
    gap: 15px;
  }
  .quick-actions-card h4 {
    margin-bottom: 5px;
  }
  .quick-btn {
    padding: 10px 14px;
    font-size: 0.85rem;
    border-radius: 12px;
  }

  /* 2x2 Stats Grid for Mobile */
  .row-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .stat-card {
    padding: 15px;
    min-height: 130px;
    border-radius: 20px;
  }
  .icon-box {
    width: 32px;
    height: 32px;
    border-radius: 8px;
  }
  .icon-box svg {
    width: 16px;
    height: 16px;
  }
  .trend-badge {
    font-size: 0.7rem;
    padding: 2px 6px;
  }
  .target-label {
    font-size: 0.65rem;
  }
  .card-body-row {
    margin-top: 10px;
    gap: 2px;
  }
  .card-body-row .label {
    font-size: 0.6rem;
  }
  .card-body-row h2 {
    font-size: 1.35rem;
  }
  .card-body-row .subtext {
    font-size: 0.65rem;
  }
  .progress-bar {
    margin-top: 6px;
    height: 4px;
  }
  .segmented-progress {
    margin-top: 6px;
    gap: 2px;
  }
  .segmented-progress .segment {
    height: 4px;
  }
  .mini-bar-chart {
    height: 20px;
    margin-top: 4px;
    gap: 4px;
  }

  /* Charts & Team Widgets Mobile */
  .row-bottom-layout {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .chart-header h4, .team-header h4 {
    font-size: 0.9rem;
  }
  .toggle-group button {
    padding: 4px 8px;
    font-size: 0.75rem;
  }
  .bar-chart-visual {
    height: 180px;
    padding-bottom: 10px;
  }
  .bar-wrapper {
    width: 26px;
    height: 140px;
  }
  .bar-label {
    font-size: 0.7rem;
    margin-top: 6px;
  }
  .team-list {
    max-height: 220px;
    gap: 12px;
  }
  .team-member-item {
    gap: 10px;
    padding-bottom: 8px;
  }
  .member-avatar {
    width: 32px;
    height: 32px;
    font-size: 0.8rem;
  }
  .member-info h5 {
    font-size: 0.8rem;
  }
  .member-info p {
    font-size: 0.75rem;
  }
  .view-all-link {
    font-size: 0.8rem;
  }
}
</style>