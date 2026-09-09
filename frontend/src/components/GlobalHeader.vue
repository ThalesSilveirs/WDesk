<template>
  <!-- Unified Global Header Bar -->
  <header class="global-header glass-effect">
    <div class="header-left">
      <button @click.stop="toggleMobileMenu" class="mobile-menu-toggle-btn" title="Menu principal">
        <MenuIcon :size="22" />
      </button>
      <h1>{{ pageTitle }}</h1>
    </div>

    <div class="header-right">
      <!-- Global Advanced Search Suite / Spotlight Trigger -->
      <div class="header-search-container" @click="chatStore.openCommandPalette()">
        <div class="header-search">
          <SearchIcon :size="18" class="search-icon" />
          <input 
            type="text" 
            placeholder="Buscar ou pressionar comandos..." 
            readonly
            tabindex="-1"
            class="header-search-trigger-input"
          />
          <span class="search-shortcut-hint">Ctrl K</span>
        </div>
      </div>

      <!-- Density Mode Toggle Button (P1 UI/UX) -->
      <button 
        @click="chatStore.toggleDensityMode()" 
        class="header-icon-btn" 
        :title="chatStore.densityMode === 'compact' ? 'Modo de exibição: Compacto (Clique para Confortável)' : 'Modo de exibição: Confortável (Clique para Compacto)'"
        :class="{ active: chatStore.densityMode === 'compact' }"
      >
        <Minimize2Icon v-if="chatStore.densityMode === 'compact'" :size="18" />
        <Maximize2Icon v-else :size="18" />
      </button>

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
    </div>
  </header>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'
import axios from 'axios'
import { 
  Search as SearchIcon,
  Bell as BellIcon,
  MessageSquare as MessageSquareIcon,
  Users as UsersIcon,
  CheckSquare as CheckSquareIcon,
  X as XIcon,
  Menu as MenuIcon,
  Minimize2 as Minimize2Icon,
  Maximize2 as Maximize2Icon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const showNotificationDropdown = ref(false)

const toggleMobileMenu = () => {
  chatStore.toggleMobileMenu()
}

// Page title
const pageTitle = computed(() => {
  switch (route.name) {
    case 'Dashboard': return 'Painel do Agente'
    case 'Conversations': return 'Painel de Conversas'
    case 'Users': return 'Gerenciamento de Equipe'
    case 'Analytics': return 'Métricas & Relatórios'
    case 'Settings': return 'Configurações do Sistema'
    case 'Customers': return 'Clientes & Contatos'
    case 'Pendencies': return 'Gestão de Pendências'
    default: return 'wDesk'
  }
})

const unreadCount = computed(() => {
  return chatStore.notifications.filter(n => !n.read).length
})

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

const handleWindowClick = () => {
  showNotificationDropdown.value = false
}

onMounted(() => {
  window.addEventListener('click', handleWindowClick)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
})
</script>

<style scoped>
.global-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-sidebar);
  height: 70px;
  flex-shrink: 0;
  position: relative;
  z-index: 999;
}

.mobile-menu-toggle-btn {
  display: none;
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

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

/* Busca Global / Spotlight Trigger */
.header-search-container {
  position: relative;
  cursor: pointer;
}

.header-search {
  position: relative;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  cursor: pointer;
}

.search-icon {
  position: absolute;
  left: 14px;
  color: var(--text-secondary);
  pointer-events: none;
  transition: color 0.2s ease;
}

.header-search input.header-search-trigger-input {
  background: var(--input-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 9px 38px 9px 40px;
  color: var(--text-primary);
  outline: none;
  width: 290px;
  font-size: 0.85rem;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-search-container:hover .header-search input.header-search-trigger-input {
  border-color: var(--accent);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
  background: var(--input-bg-focus);
}

.header-search-container:hover .search-icon {
  color: var(--accent);
}

.search-shortcut-hint {
  position: absolute;
  right: 10px;
  font-size: 0.68rem;
  font-weight: 700;
  background: var(--kbd-bg);
  color: var(--text-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--border);
  pointer-events: none;
}

/* Notificações */
.notification-container { position: relative; }
.header-icon-btn {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}
.header-icon-btn:hover { background: var(--hover-bg); }
.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: 800;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  width: 320px;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 16px 35px rgba(0,0,0,0.4);
  overflow: hidden;
  z-index: 1050;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.dropdown-header h4 { margin: 0; font-size: 0.9rem; }
.clear-btn { background: none; border: none; color: var(--accent); font-size: 0.8rem; cursor: pointer; }

.dropdown-list { max-height: 300px; overflow-y: auto; }
.notif-item { display: flex; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--border); cursor: pointer; }
.notif-item:hover { background: var(--hover-bg); }
.notif-content h5 { margin: 0 0 4px; font-size: 0.85rem; }
.notif-content p { margin: 0 0 4px; font-size: 0.8rem; color: var(--text-secondary); }
.notif-time { font-size: 0.7rem; color: var(--text-secondary); }
.empty-notif { padding: 20px; text-align: center; color: var(--text-secondary); font-size: 0.85rem; }

@media (max-width: 768px) {
  .mobile-menu-toggle-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
  }
  .header-search input { width: 160px; }
  .header-search.focused input, .header-search input:focus { width: 220px; }
  .global-search-popover { width: 300px; }
}
</style>
