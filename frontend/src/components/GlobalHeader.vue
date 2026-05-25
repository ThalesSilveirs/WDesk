<template>
  <!-- Unified Global Header Bar -->
  <header class="global-header glass-effect">
    <div class="header-left">
      <h1>{{ pageTitle }}</h1>
      
      <!-- User Status Dropdown -->
      <div class="status-dropdown" @click.stop>
        <button @click="showStatusMenu = !showStatusMenu" class="status-btn" :class="currentStatus">
          <span class="status-dot"></span>
          <span class="status-text-label">{{ formatStatusName(currentStatus) }}</span>
          <ChevronDownIcon :size="16" />
        </button>
        <div v-if="showStatusMenu" class="status-menu glass-effect">
          <button @click="changeStatus('online')" class="status-option online">
            <span class="status-dot"></span> Online
          </button>
          <button @click="changeStatus('away')" class="status-option away">
            <span class="status-dot"></span> Ausente
          </button>
          <button @click="changeStatus('offline')" class="status-option offline">
            <span class="status-dot"></span> Offline
          </button>
        </div>
      </div>
    </div>

    <div class="header-right">
      <!-- Global Search -->
      <div class="header-search">
        <SearchIcon :size="18" class="search-icon" />
        <input v-model="chatStore.searchQuery" type="text" placeholder="Buscar conversas ou logs..." />
      </div>

      <!-- Notification Bell with Dropdown -->
      <div class="notification-container">
        <button @click="toggleNotificationDropdown" class="header-icon-btn" title="Notificações">
          <BellIcon :size="20" />
          <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
        </button>
        
        <!-- Realtime Notifications Dropdown -->
        <div v-if="showNotificationDropdown" class="notification-dropdown glass-effect" @click.stop>
          <div class="dropdown-header">
            <h4>Notificações Recentes</h4>
            <button v-if="chatStore.notifications.length > 0" @click="clearAllNotifications" class="clear-btn">
              Limpar
            </button>
          </div>
          
          <div class="dropdown-list">
            <div 
              v-for="notif in chatStore.notifications" 
              :key="notif.id" 
              class="notif-item" 
              :class="{ unread: !notif.read }"
              @click="handleNotificationClick(notif)"
            >
              <div class="notif-icon">
                <MessageSquareIcon :size="16" />
              </div>
              <div class="notif-content">
                <h5>{{ notif.title }}</h5>
                <p>{{ notif.body }}</p>
                <span class="notif-time">{{ formatTime(notif.timestamp) }}</span>
              </div>
            </div>
            
            <div v-if="chatStore.notifications.length === 0" class="empty-notif">
              Nenhuma notificação nova
            </div>
          </div>
        </div>
      </div>

      <button class="header-icon-btn history-btn" title="Histórico">
        <HistoryIcon :size="20" />
      </button>
      
      <!-- Logged In User Profile Dropdown -->
      <div class="profile-dropdown-container" @click.stop>
        <button @click="showProfileMenu = !showProfileMenu" class="profile-avatar-btn" title="Menu do Usuário">
          <div class="profile-avatar">
            <div class="profile-initials">
              {{ userInitials }}
            </div>
            <span class="profile-name">{{ userDisplayName }}</span>
          </div>
          <ChevronDownIcon :size="14" class="profile-arrow" />
        </button>
        
        <Transition name="modal-fade">
          <div v-if="showProfileMenu" class="profile-menu glass-effect">
            <div class="profile-menu-header">
              <strong>{{ userDisplayName }}</strong>
              <span class="profile-role">{{ chatStore.userRole === 'admin' ? 'Administrador' : 'Atendente' }}</span>
            </div>
            <div class="profile-menu-items">
              <!-- Mobile only menu items (normally in Sidebar bottom-section) -->
              <div class="mobile-only-items">
                <button @click="toggleTheme" class="menu-item">
                  <SunIcon v-if="chatStore.theme === 'dark'" :size="16" />
                  <MoonIcon v-else :size="16" />
                  <span>Tema: {{ chatStore.theme === 'dark' ? 'Claro' : 'Escuro' }}</span>
                </button>
                <button @click="triggerHelp" class="menu-item">
                  <HelpCircleIcon :size="16" />
                  <span>Ajuda</span>
                </button>
              </div>
              <button @click="triggerLogout" class="menu-item logout">
                <LogOutIcon :size="16" />
                <span>Sair</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Logout Modal -->
    <Transition name="modal-fade">
      <div v-if="showLogoutModal" class="modal-overlay" @click="showLogoutModal = false">
        <div class="modal-content small-modal" @click.stop>
          <h2>Sair do Sistema</h2>
          <p style="color: var(--text-secondary); margin-bottom: 20px;">Tem certeza que deseja encerrar sua sessão?</p>
          <div class="modal-actions">
            <button @click="showLogoutModal = false" class="btn-secondary">Cancelar</button>
            <button @click="logout" class="btn-danger-sm">Confirmar Sair</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Help Modal -->
    <Transition name="modal-fade">
      <div v-if="showHelpModal" class="modal-overlay" @click="showHelpModal = false">
        <div class="modal-content" @click.stop>
          <h2>Central de Ajuda</h2>
          <p style="color: var(--text-secondary); margin-bottom: 20px;">Precisa de auxílio no OmniChat?</p>
          <div style="display: flex; flex-direction: column; gap: 10px; text-align: left; color: var(--text-secondary);">
            <p>• Para conectar seu WhatsApp, acesse <strong>Conexões</strong> no menu Configurações.</p>
            <p>• Use a aba <strong>Conversas</strong> para responder aos seus clientes em tempo real.</p>
            <p>• Crie campanhas em massa usando o botão <strong>Nova Transmissão</strong>.</p>
          </div>
          <div class="modal-actions" style="margin-top: 25px;">
            <button @click="showHelpModal = false" class="btn-success-sm">Entendido</button>
          </div>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'
import { 
  ChevronDown as ChevronDownIcon,
  Search as SearchIcon,
  Bell as BellIcon,
  History as HistoryIcon,
  MessageSquare as MessageSquareIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
  HelpCircle as HelpCircleIcon,
  LogOut as LogOutIcon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const showProfileMenu = ref(false)
const showLogoutModal = ref(false)
const showHelpModal = ref(false)

const toggleTheme = () => {
  chatStore.toggleTheme()
}

const triggerLogout = () => {
  showProfileMenu.value = false
  showLogoutModal.value = true
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

const triggerHelp = () => {
  showProfileMenu.value = false
  showHelpModal.value = true
}

const currentStatus = ref('online')
const showStatusMenu = ref(false)
const showNotificationDropdown = ref(false)

// Redirect to Conversations view when search query is typed from elsewhere
watch(() => chatStore.searchQuery, (newQuery) => {
  if (newQuery && route.path !== '/conversations') {
    router.push('/conversations')
  }
})

// Computes dynamic page title based on active route
const pageTitle = computed(() => {
  switch (route.name) {
    case 'Dashboard': return 'Painel do Agente'
    case 'Conversations': return 'Painel de Conversas'
    case 'Users': return 'Gerenciamento de Equipe'
    case 'Analytics': return 'Métricas & Relatórios'
    case 'Settings': return 'Configurações do Sistema'
    default: return 'wDesk'
  }
})

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

const unreadCount = computed(() => {
  return chatStore.notifications.filter(n => !n.read).length
})

const formatStatusName = (status) => {
  const map = {
    'online': 'Online',
    'away': 'Ausente',
    'offline': 'Offline'
  }
  return map[status] || status
}

const changeStatus = (status) => {
  currentStatus.value = status
  showStatusMenu.value = false
  chatStore.changeUserStatus(status)
}

const toggleNotificationDropdown = (e) => {
  e.stopPropagation()
  showNotificationDropdown.value = !showNotificationDropdown.value
  if (showNotificationDropdown.value) {
    chatStore.markAllNotificationsAsRead()
  }
}

const clearAllNotifications = () => {
  chatStore.clearNotifications()
}

const handleNotificationClick = async (notif) => {
  notif.read = true
  showNotificationDropdown.value = false
  if (notif.ticket_id) {
    try {
      chatStore.currentFilter = 'all'
      await chatStore.fetchTickets()
      
      const foundTicket = chatStore.tickets.find(t => t.id === notif.ticket_id) || 
                          chatStore.myTickets.find(t => t.id === notif.ticket_id)
      
      if (foundTicket) {
        chatStore.activeTicket = foundTicket
      } else {
        chatStore.activeTicket = { id: notif.ticket_id }
      }
      
      chatStore.fetchMessages(notif.ticket_id)
      router.push('/conversations')
    } catch (e) {
      console.error("Erro ao redirecionar da notificação:", e)
    }
  }
}

const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const handleStatusSynced = (e) => {
  currentStatus.value = e.detail.status
}

// Close dropdown on window click
onMounted(() => {
  window.addEventListener('click', () => {
    showNotificationDropdown.value = false
    showStatusMenu.value = false
    showProfileMenu.value = false
  })

  window.addEventListener('user-status-synced', handleStatusSynced)
})

onUnmounted(() => {
  window.removeEventListener('user-status-synced', handleStatusSynced)
})
</script>

<style scoped>
/* Global Top Header Bar */
.global-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-sidebar);
  height: 70px;
  flex-shrink: 0;
  position: relative; /* Stacking context */
  z-index: 999; /* Ensure notifications dropdown is above content */
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h1 {
  font-size: 1.4rem;
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
  z-index: 1000;
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
  width: 240px;
  font-size: 0.85rem;
}

.header-search input:focus {
  border-color: #10b981;
}

.notification-container {
  position: relative;
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

/* Notifications Dropdown Panel */
.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  width: 320px;
  max-height: 400px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-sidebar);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
  z-index: 1010;
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  padding: 15px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
}

.clear-btn {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

.dropdown-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.notif-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.notif-item:hover {
  background: var(--glass);
}

.notif-item.unread {
  background: rgba(16, 185, 129, 0.05);
}

.notif-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notif-content {
  flex: 1;
  text-align: left;
}

.notif-content h5 {
  margin: 0 0 4px 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
}

.notif-content p {
  margin: 0 0 6px 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

.notif-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  opacity: 0.7;
}

.empty-notif {
  padding: 30px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.history-btn {
  color: var(--text-secondary);
}

/* Logged In User Profile & Dropdown */
.profile-dropdown-container {
  position: relative;
  display: flex;
  align-items: center;
  padding-left: 15px;
  border-left: 1px solid var(--border);
}

.profile-avatar-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 12px;
  transition: background 0.2s;
  color: var(--text-primary);
}

.profile-avatar-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.profile-arrow {
  color: var(--text-secondary);
  opacity: 0.7;
}

.profile-avatar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.profile-initials {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
}

.profile-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.profile-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  width: 220px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-sidebar);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
  z-index: 1010;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.profile-menu-header {
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}

.profile-menu-header strong {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.profile-role {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.profile-menu-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background 0.2s;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.menu-item.logout {
  color: #ef4444;
}

.menu-item.logout:hover {
  background: rgba(239, 68, 68, 0.1);
}

.mobile-only-items {
  display: none;
  flex-direction: column;
  gap: 4px;
}

/* Modal styling copy for global header integration */
.small-modal {
  max-width: 400px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-danger-sm {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger-sm:hover {
  background: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.btn-success-sm {
  background: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 768px) {
  .global-header {
    padding: 12px 15px;
    height: auto;
    display: grid;
    grid-template-columns: auto auto 1fr auto;
    grid-template-rows: auto auto;
    gap: 12px;
  }
  
  .header-left, .header-right {
    display: contents;
  }
  
  .global-header h1 {
    grid-row: 1;
    grid-column: 1 / span 3;
    font-size: 1.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    align-self: center;
    margin: 0;
  }

  .profile-dropdown-container {
    grid-row: 1;
    grid-column: 4;
    justify-self: end;
    align-self: center;
    border-left: none !important;
    padding-left: 0 !important;
  }

  .status-dropdown {
    grid-row: 2;
    grid-column: 1;
    align-self: center;
  }

  .notification-container {
    grid-row: 2;
    grid-column: 2;
    align-self: center;
  }

  .header-search {
    grid-row: 2;
    grid-column: 3 / span 2;
    display: flex !important;
    width: 100% !important;
    max-width: none !important;
    align-self: center;
  }

  .status-btn span.status-text-label {
    display: none;
  }

  .history-btn {
    display: none !important;
  }
  
  .profile-name {
    display: none;
  }

  .mobile-only-items {
    display: flex;
    border-bottom: 1px solid var(--border);
    padding-bottom: 4px;
    margin-bottom: 4px;
  }
}
</style>
