<template>
  <div class="sidebar-container">
    <aside class="sidebar glass-effect">
      <!-- Brand Logo Header -->
      <div class="logo-section">
        <router-link to="/">
          <div class="logo-circle">
            <span class="logo-letter">W</span>
          </div>
        </router-link>
      </div>

      <!-- Navigation Links -->
      <nav class="nav-links">
        <router-link to="/" class="nav-link-item" exact-active-class="active" data-tooltip="Dashboard" @click="closeMobileMenu">
          <LayoutGridIcon :size="20" />
          <span class="nav-label-mobile">Dashboard</span>
        </router-link>

        <router-link to="/conversations" class="nav-link-item" active-class="active" data-tooltip="Conversas" @click="closeMobileMenu">
          <MessageSquareIcon :size="20" />
          <span class="nav-label-mobile">Conversas</span>
        </router-link>

        <router-link to="/pendencies" class="nav-link-item" active-class="active" data-tooltip="Pendências" @click="closeMobileMenu">
          <ClipboardListIcon :size="20" />
          <span class="nav-label-mobile">Pendências</span>
        </router-link>

        <router-link to="/calendar" class="nav-link-item" active-class="active" data-tooltip="Calendário" @click="closeMobileMenu">
          <CalendarIcon :size="20" />
          <span class="nav-label-mobile">Calendário</span>
        </router-link>

        <router-link to="/customers" class="nav-link-item" active-class="active" data-tooltip="Clientes" @click="closeMobileMenu">
          <ContactIcon :size="20" />
          <span class="nav-label-mobile">Clientes</span>
        </router-link>

        <router-link to="/cities" class="nav-link-item" active-class="active" data-tooltip="Cidades" @click="closeMobileMenu">
          <MapPinIcon :size="20" />
          <span class="nav-label-mobile">Cidades</span>
        </router-link>

        <router-link v-if="chatStore.userRole === 'admin'" to="/users" class="nav-link-item" active-class="active" data-tooltip="Equipes" @click="closeMobileMenu">
          <UsersIcon :size="20" />
          <span class="nav-label-mobile">Equipes</span>
        </router-link>

        <router-link to="/analytics" class="nav-link-item" active-class="active" data-tooltip="Métricas" @click="closeMobileMenu">
          <BarChartIcon :size="20" />
          <span class="nav-label-mobile">Métricas</span>
        </router-link>

        <router-link v-if="chatStore.userRole === 'admin'" to="/settings" class="nav-link-item" active-class="active" data-tooltip="Configurações" @click="closeMobileMenu">
          <SettingsIcon :size="20" />
          <span class="nav-label-mobile">Configurações</span>
        </router-link>
      </nav>

      <!-- Bottom Actions -->
      <div class="bottom-section">
        <!-- Search Toggle -->
        <div class="sidebar-popover-container" ref="searchContainerRef">
          <button @click.stop="toggleSearchMenu" class="nav-link-item" :class="{ active: showSearchMenu }" data-tooltip="Buscar">
            <SearchIcon :size="20" />
          </button>
          <Transition name="fade">
            <div v-if="showSearchMenu" class="search-popover glass-effect">
              <div class="popover-header">
                <span class="popover-title">Busca Global</span>
              </div>
              <div class="popover-divider"></div>
              <div class="search-input-wrapper">
                <SearchIcon :size="16" class="search-input-icon" />
                <input 
                  v-model="localSearchQuery" 
                  type="text" 
                  placeholder="Buscar conversas..."
                  class="search-input"
                  ref="searchInputRef"
                />
              </div>
            </div>
          </Transition>
        </div>

        <!-- Notifications Toggle -->
        <div class="sidebar-popover-container" ref="notificationsContainerRef">
          <button @click.stop="toggleNotificationsMenu" class="nav-link-item" :class="{ active: showNotificationsMenu }" data-tooltip="Notificações">
            <BellIcon :size="20" />
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </button>
          <Transition name="fade">
            <div v-if="showNotificationsMenu" class="notifications-popover glass-effect">
              <div class="popover-header">
                <span class="popover-title">Notificações</span>
                <button v-if="chatStore.notifications.length > 0" @click="clearAllNotifications" class="clear-btn">
                  Limpar
                </button>
              </div>
              <div class="popover-divider"></div>
              <div class="notifications-list">
                <div 
                  v-for="notif in chatStore.notifications" 
                  :key="notif.id" 
                  class="notif-item" 
                  :class="{ unread: !notif.read }"
                  @click="handleNotificationClick(notif)"
                >
                  <div class="notif-icon">
                    <MessageSquareIcon :size="14" />
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
          </Transition>
        </div>

        <!-- Theme Toggle -->
        <button @click="chatStore.toggleTheme" class="nav-link-item theme-toggle" :data-tooltip="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
          <SunIcon v-if="chatStore.theme === 'dark'" :size="20" />
          <MoonIcon v-else :size="20" />
        </button>

        <!-- Help -->
        <button @click="showHelpModal = true" class="nav-link-item" data-tooltip="Ajuda">
          <HelpCircleIcon :size="20" />
        </button>

        <!-- User Profile Avatar & Status -->
        <div class="profile-container" ref="profileContainerRef">
          <button @click.stop="toggleProfileMenu" class="avatar-btn" :data-tooltip="userDisplayName">
            <div class="avatar-circle">
              {{ userInitials }}
            </div>
            <span class="status-dot" :class="currentStatus"></span>
          </button>

          <!-- Profile / Status Dropdown Popover -->
          <Transition name="fade">
            <div v-if="showProfileMenu" class="profile-popover glass-effect">
              <div class="popover-header">
                <span class="user-name">{{ userDisplayName }}</span>
                <span class="user-role">{{ chatStore.userRole === 'admin' ? 'Administrador' : 'Atendente' }}</span>
              </div>
              <div class="popover-divider"></div>
              
              <!-- Status Selector Options -->
              <div class="status-option" :class="{ active: currentStatus === 'online' }" @click="changeStatus('online')">
                <span class="status-dot online"></span>
                <span>Online</span>
              </div>
              <div class="status-option" :class="{ active: currentStatus === 'away' }" @click="changeStatus('away')">
                <span class="status-dot away"></span>
                <span>Ausente</span>
              </div>
              <div class="status-option" :class="{ active: currentStatus === 'offline' }" @click="changeStatus('offline')">
                <span class="status-dot offline"></span>
                <span>Offline</span>
              </div>

              <!-- Toggle: Notificações de Todas as Conversas (só admin) -->
              <template v-if="chatStore.userRole === 'admin'">
                <div class="popover-divider"></div>
                <div
                  class="status-option toggle-item"
                  @click.stop="toggleNotifyAll"
                  title="Receber notificações de todas as conversas"
                >
                  <BellIcon :size="14" />
                  <span style="flex: 1; margin-left: 4px; font-size: 0.85rem;">Notificar Todos</span>
                  <div class="toggle-switch" :class="{ active: chatStore.notifyAll }">
                    <div class="toggle-thumb"></div>
                  </div>
                </div>
              </template>

              <div class="popover-divider"></div>
              <button @click="triggerLogout" class="popover-logout-btn">
                <LogOutIcon :size="16" />
                <span>Sair</span>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </aside>

    <!-- Help Modal -->
    <Transition name="modal-fade">
      <div v-if="showHelpModal" class="modal-overlay" @click="showHelpModal = false">
        <div class="modal-content" @click.stop>
          <h2>Central de Ajuda</h2>
          <p style="color: var(--text-secondary); margin-bottom: 20px;">Precisa de auxílio no WDesk?</p>
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

    <!-- Logout Confirmation Modal -->
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
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChatStore } from '../store/chat'
import {
  MessageSquare as MessageSquareIcon,
  LayoutGrid as LayoutGridIcon,
  Users as UsersIcon,
  BarChart3 as BarChartIcon,
  Settings as SettingsIcon,
  HelpCircle as HelpCircleIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
  Contact as ContactIcon,
  MapPin as MapPinIcon,
  ClipboardList as ClipboardListIcon,
  LogOut as LogOutIcon,
  Search as SearchIcon,
  Bell as BellIcon,
  Calendar as CalendarIcon
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()

const closeMobileMenu = () => {
  document.documentElement.classList.remove('mobile-menu-open')
}

const showHelpModal = ref(false)
const showLogoutModal = ref(false)
const showProfileMenu = ref(false)
const showSearchMenu = ref(false)
const showNotificationsMenu = ref(false)
const currentStatus = ref('online')

const profileContainerRef = ref(null)
const searchContainerRef = ref(null)
const notificationsContainerRef = ref(null)
const searchInputRef = ref(null)

const localSearchQuery = ref(chatStore.searchQuery)

let debounceTimeout = null
watch(localSearchQuery, (newVal) => {
  if (debounceTimeout) clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    chatStore.searchQuery = newVal
  }, 250)
})

watch(() => chatStore.searchQuery, (newQuery) => {
  if (newQuery !== localSearchQuery.value) {
    localSearchQuery.value = newQuery
  }
  if (newQuery && route.path !== '/conversations') {
    router.push('/conversations')
  }
})

const unreadCount = computed(() => {
  return chatStore.notifications.filter(n => !n.read).length
})

const clearAllNotifications = () => {
  chatStore.clearNotifications()
}

const handleNotificationClick = async (notif) => {
  notif.read = true
  showNotificationsMenu.value = false
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

const toggleNotifyAll = () => {
  chatStore.toggleNotifyAll()
}

const toggleProfileMenu = () => {
  showProfileMenu.value = !showProfileMenu.value
  showSearchMenu.value = false
  showNotificationsMenu.value = false
}

const toggleSearchMenu = () => {
  showSearchMenu.value = !showSearchMenu.value
  showNotificationsMenu.value = false
  showProfileMenu.value = false
  if (showSearchMenu.value) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
}

const toggleNotificationsMenu = () => {
  showNotificationsMenu.value = !showNotificationsMenu.value
  showSearchMenu.value = false
  showProfileMenu.value = false
  if (showNotificationsMenu.value) {
    chatStore.markAllNotificationsAsRead()
  }
}

const changeStatus = (status) => {
  currentStatus.value = status
  showProfileMenu.value = false
  chatStore.changeUserStatus(status)
}

const triggerLogout = () => {
  showProfileMenu.value = false
  showLogoutModal.value = true
}

const logout = () => {
  chatStore.logout()
  router.push('/login')
}

const handleStatusSynced = (e) => {
  currentStatus.value = e.detail.status
}

const userDisplayName = computed(() => {
  if (!chatStore.user) return 'Carregando...'
  return chatStore.user.first_name 
    ? `${chatStore.user.first_name} ${chatStore.user.last_name || ''}` 
    : chatStore.user.username
})

const userInitials = computed(() => {
  if (!chatStore.user) return '?'
  const name = chatStore.user.first_name || chatStore.user.username
  return name.charAt(0).toUpperCase()
})

const handleClickOutside = (event) => {
  if (profileContainerRef.value && !profileContainerRef.value.contains(event.target)) {
    showProfileMenu.value = false
  }
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target)) {
    showSearchMenu.value = false
  }
  if (notificationsContainerRef.value && !notificationsContainerRef.value.contains(event.target)) {
    showNotificationsMenu.value = false
  }
}

onMounted(() => {
  window.addEventListener('user-status-synced', handleStatusSynced)
  window.addEventListener('click', handleClickOutside)
  if (chatStore.user?.status) {
    currentStatus.value = chatStore.user.status
  }
})

onUnmounted(() => {
  window.removeEventListener('user-status-synced', handleStatusSynced)
  window.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.sidebar-container {
  width: 70px;
  height: 100%;
  flex-shrink: 0;
  z-index: 100;
  position: relative;
}

.sidebar {
  width: 100%;
  height: 100%;
  background: var(--bg-nav-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  position: relative;
}

/* Brand Logo Circle */
.logo-section {
  margin-bottom: 25px;
}

.logo-circle {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(34, 181, 95, 0.35);
  transition: transform 0.3s ease;
}

.logo-circle:hover {
  transform: scale(1.05) rotate(5deg);
}

.logo-letter {
  color: white;
  font-size: 1.5rem;
  font-weight: 900;
  font-family: 'Outfit', 'Inter', sans-serif;
  user-select: none;
}

/* Navigation Links */
.nav-links {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex: 1;
  width: 100%;
}

.nav-link-item {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: none;
  border: none;
  position: relative;
  text-decoration: none;
}

.nav-link-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.nav-link-item.active {
  background: var(--border);
  color: var(--accent);
  box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.15);
}

/* Tooltip implementation */
@media (min-width: 769px) {
  .nav-link-item[data-tooltip]::after,
  .avatar-btn[data-tooltip]::after {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 12px);
    top: 50%;
    transform: translateY(-50%) translateX(-8px);
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1), transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    z-index: 9999;
  }

  .nav-link-item[data-tooltip]:hover::after,
  .avatar-btn[data-tooltip]:hover::after {
    opacity: 1;
    visibility: visible;
    transform: translateY(-50%) translateX(0);
  }
}

/* Bottom Section */
.bottom-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

/* Profile container & popover */
.profile-container,
.sidebar-popover-container {
  position: relative;
}

.avatar-btn {
  background: none;
  border: none;
  position: relative;
  cursor: pointer;
  padding: 0;
  outline: none;
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #db2777; /* Rosa chamativo como mockup */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
  box-shadow: 0 2px 8px rgba(219, 39, 119, 0.3);
  transition: transform 0.2s ease;
}

.avatar-btn:hover .avatar-circle {
  transform: scale(1.05);
}

.status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--bg-nav-sidebar);
  background: #10b981; /* Default online green */
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  transition: background 0.3s ease;
}

.status-dot.online {
  background: #10b981;
}

.status-dot.away {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
}

.status-dot.offline {
  background: #71717a;
  box-shadow: none;
}

/* Profile Popover Menu */
.profile-popover {
  position: absolute;
  bottom: 0;
  left: 55px;
  width: 200px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
}

.popover-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.user-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.popover-divider {
  height: 1px;
  background: var(--border);
  margin: 6px 0;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.2s ease;
}

.status-option:hover {
  background: rgba(255, 255, 255, 0.05);
}

.status-option.active {
  background: rgba(16, 185, 129, 0.1);
  color: var(--accent);
}

.status-option .status-dot {
  position: static;
  border: none;
  width: 8px;
  height: 8px;
}

.popover-logout-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  padding: 8px;
  border-radius: 8px;
  color: #ef4444;
  font-weight: 600;
  font-size: 0.9rem;
  width: 100%;
  cursor: pointer;
  transition: background 0.2s ease;
}

.popover-logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Help Modal overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 30px;
  width: 90%;
  max-width: 500px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.modal-content h2 {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-danger-sm {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-danger-sm:hover {
  background: #dc2626;
}

.btn-success-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-success-sm:hover {
  background: var(--accent-hover);
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Search Popover */
.search-popover {
  position: absolute;
  bottom: 0;
  left: 55px;
  width: 250px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.search-input-icon {
  position: absolute;
  left: 10px;
  color: var(--text-secondary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px 8px 32px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.85rem;
}

.search-input:focus {
  border-color: var(--accent);
}

/* Notifications Popover */
.notifications-popover {
  position: absolute;
  bottom: 0;
  left: 55px;
  width: 300px;
  max-height: 350px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.notifications-list {
  max-height: 250px;
  overflow-y: auto;
  padding: 4px;
}

.notif-item {
  display: flex;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.notif-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notif-item.unread {
  background: rgba(34, 181, 95, 0.05);
}

.notif-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(34, 181, 95, 0.1);
  color: var(--accent);
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
  margin: 0 0 2px 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.notif-content p {
  margin: 0 0 4px 0;
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

.notif-time {
  font-size: 0.65rem;
  color: var(--text-secondary);
  opacity: 0.7;
}

.empty-notif {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.8rem;
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

.nav-link-item .badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  font-weight: bold;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* iOS-style toggle switch */
.toggle-item {
  justify-content: space-between !important;
  cursor: pointer;
  user-select: none;
}

.toggle-switch {
  width: 30px;
  height: 16px;
  border-radius: 8px;
  background: var(--border);
  position: relative;
  transition: background 0.25s;
  flex-shrink: 0;
  pointer-events: none;
}

.toggle-switch.active {
  background: var(--accent);
  box-shadow: 0 0 8px rgba(34, 181, 95, 0.4);
}

.toggle-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.25s;
}

.toggle-switch.active .toggle-thumb {
  transform: translateX(14px);
}

/* Responsiveness */
.nav-label-mobile {
  display: none;
  font-size: 0.95rem;
  font-weight: 600;
  margin-left: 12px;
}

/* Responsiveness: Sidebar Lateral Retrátil no Mobile */
@media (max-width: 768px) {
  .sidebar-container {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 260px;
    height: 100dvh;
    z-index: 2000;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 10px 0 30px rgba(0,0,0,0.5);
  }

  html.mobile-menu-open .sidebar-container {
    transform: translateX(0);
  }

  .sidebar {
    height: 100%;
    flex-direction: column;
    padding: 20px 15px;
    align-items: flex-start;
    justify-content: flex-start;
    border-right: 1px solid var(--border);
    border-top: none;
    background: var(--bg-sidebar);
  }

  .logo-section,
  .bottom-section,
  .profile-container,
  .sidebar-popover-container {
    display: flex !important;
  }

  .logo-section {
    margin-bottom: 20px;
    width: 100%;
  }

  .nav-links {
    flex-direction: column;
    gap: 8px;
    width: 100%;
    align-items: stretch;
    overflow-y: auto;
  }

  .nav-link-item {
    width: 100%;
    height: 48px;
    padding: 0 16px;
    justify-content: flex-start;
    border-radius: 10px;
  }

  .nav-label-mobile {
    display: inline-block;
  }

  .bottom-section {
    width: 100%;
    margin-top: auto;
  }
}
</style>
