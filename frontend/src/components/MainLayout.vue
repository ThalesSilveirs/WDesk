<template>
  <div class="app-layout">
    <Sidebar />
    
    <div class="main-content-wrapper">
      <!-- Unified Global Header Bar -->
      <header class="global-header glass-effect">
        <div class="header-left">
          <h1>{{ pageTitle }}</h1>
          
          <!-- User Status Dropdown -->
          <div class="status-dropdown">
            <button @click="showStatusMenu = !showStatusMenu" class="status-btn" :class="currentStatus">
              <span class="status-dot"></span>
              {{ formatStatusName(currentStatus) }}
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
            <input type="text" placeholder="Buscar conversas ou logs..." />
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

          <button class="header-icon-btn" title="Histórico">
            <HistoryIcon :size="20" />
          </button>
          
          <!-- Logged In User Profile -->
          <div class="profile-avatar">
            <div class="profile-initials">
              {{ userInitials }}
            </div>
            <span class="profile-name">{{ userDisplayName }}</span>
          </div>
        </div>
      </header>

      <!-- Main Router View with Page Transitions -->
      <div class="page-content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    
    <BroadcastModal />
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'
import Sidebar from './Sidebar.vue'
import BroadcastModal from './dashboard/BroadcastModal.vue'
import { 
  ChevronDown as ChevronDownIcon,
  Search as SearchIcon,
  Bell as BellIcon,
  History as HistoryIcon,
  MessageSquare as MessageSquareIcon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const currentStatus = ref('online')
const showStatusMenu = ref(false)
const showNotificationDropdown = ref(false)

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

// Close dropdown on window click
onMounted(() => {
  document.documentElement.setAttribute('data-theme', chatStore.theme)
  chatStore.fetchCurrentUser()
  
  window.addEventListener('click', () => {
    showNotificationDropdown.value = false
    showStatusMenu.value = false
  })
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  height: 100dvh;
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
}

.main-content-wrapper {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.page-content-wrapper {
  flex: 1;
  overflow: hidden;
  height: 100%;
}

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
  font-weight: 800;
  color: var(--text-primary);
}

.clear-btn {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.dropdown-list {
  overflow-y: auto;
  flex: 1;
}

.notif-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.2s;
}

.notif-item:hover {
  background: rgba(255, 255, 255, 0.03);
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
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
}

.notif-content h5 {
  font-size: 0.85rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.notif-content p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
  word-break: break-word;
}

.notif-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  opacity: 0.6;
  margin-top: 4px;
}

.empty-notif {
  padding: 30px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

/* Profile Badge styling */
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
  font-size: 0.9rem;
  color: var(--text-primary);
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column-reverse;
  }
  .main-content-wrapper {
    height: calc(100vh - 60px);
    height: calc(100dvh - 60px);
  }
  .global-header {
    padding: 10px 15px;
    height: auto;
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  .header-left {
    justify-content: space-between;
  }
  .header-right {
    justify-content: space-between;
  }
  .header-search input {
    width: 100%;
  }
  .profile-avatar {
    border-left: none;
    padding-left: 0;
  }
}
</style>
