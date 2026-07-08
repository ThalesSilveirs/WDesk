<template>
  <aside class="sidebar glass-effect">
    <!-- Header of the conversation list -->
    <div class="sidebar-header">
      <div class="header-left-group">
        <!-- Mobile Profile Dropdown -->
        <div class="mobile-profile-container" ref="profileContainerRef">
          <button @click.stop="toggleProfileMenu" class="mobile-avatar-btn" :title="userDisplayName">
            <div class="avatar-circle">
              {{ userInitials }}
            </div>
            <span class="status-dot-mobile" :class="currentStatus"></span>
          </button>
          
          <Transition name="fade">
            <div v-if="showProfileMenu" class="profile-popover glass-effect">
              <div class="popover-header">
                <span class="user-name">{{ userDisplayName }}</span>
                <span class="user-role">{{ chatStore.userRole === 'admin' ? 'Administrador' : 'Atendente' }}</span>
              </div>
              <div class="popover-divider"></div>
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
              <div class="popover-divider"></div>
              <button @click="triggerLogout" class="popover-logout-btn">
                <LogOutIcon :size="16" />
                <span>Sair</span>
              </button>
            </div>
          </Transition>
        </div>
        <h2>Conversas</h2>
      </div>

      <div class="header-actions">
        <!-- Mobile Theme Toggle -->
        <button @click="chatStore.toggleTheme" class="action-btn mobile-theme-toggle" :title="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
          <SunIcon v-if="chatStore.theme === 'dark'" :size="18" />
          <MoonIcon v-else :size="18" />
        </button>

        <button class="action-btn" @click="chatStore.showBroadcastModal = true" title="Nova Transmissão">
          <PlusIcon :size="18" />
        </button>
        <button class="action-btn" title="Visualização em Grade">
          <LayoutGridIcon :size="18" />
        </button>
        <button class="action-btn" title="Filtrar Conversas">
          <FilterIcon :size="18" />
        </button>
      </div>
    </div>

    <!-- Search Input inside Sidebar with shortcut badge -->
    <div class="search-wrapper">
      <div class="search-input-container">
        <SearchIcon :size="16" class="search-icon" />
        <input 
          ref="searchInputRef"
          type="text" 
          v-model="localSearchQuery" 
          placeholder="Buscar por conversas..." 
          class="search-input"
        />
        <span class="shortcut-badge">{{ isMac ? '⌘K' : 'Ctrl K' }}</span>
      </div>
    </div>

    <!-- Filters Pills row -->
    <div class="filters-pills-row">
      <button 
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'mine' }"
        @click="selectFilter('mine')"
      >
        Meus
        <span class="pill-badge" :class="{ active: chatStore.currentFilter === 'mine' }">
          {{ myTicketsCount }}
        </span>
      </button>
      <button 
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'unassigned' }"
        @click="selectFilter('unassigned')"
      >
        Fila
        <span class="pill-badge" :class="{ active: chatStore.currentFilter === 'unassigned' }">
          {{ unassignedCount }}
        </span>
      </button>
      <button 
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'closed' }"
        @click="selectFilter('closed')"
      >
        Fechados
      </button>
      <button 
        v-if="chatStore.userRole === 'admin'"
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'all' }"
        @click="selectFilter('all')"
      >
        Abertos
      </button>
    </div>

    <!-- Unified Ticket List -->
    <div class="ticket-list" v-if="activeTabTickets.length > 0">
      <div 
        v-for="ticket in activeTabTickets" 
        :key="ticket.id"
        class="ticket-item"
        :class="{ active: chatStore.activeTicket?.id === ticket.id }"
        @click="chatStore.selectTicket(ticket)"
      >
        <!-- Left vertical active bar indicators -->
        <span class="active-indicator"></span>

        <!-- Contact Avatar -->
        <div class="avatar-container">
          <div class="avatar">
            <img 
              v-if="ticket.contact_details?.profile_pic && !ticket.contact_details?.profile_pic_failed" 
              :src="ticket.contact_details.profile_pic" 
              class="avatar-img" 
              @error="ticket.contact_details.profile_pic_failed = true" 
            />
            <span v-else class="avatar-initials">{{ ticket.contact_details?.name?.charAt(0) || 'C' }}</span>
          </div>
          <!-- Platform Icon Badge (WhatsApp Green SVG) -->
          <div class="platform-badge" title="WhatsApp">
            <svg viewBox="0 0 24 24" class="platform-badge-svg">
              <path fill="#ffffff" d="M12.012 2c-5.506 0-9.989 4.478-9.99 9.984a9.96 9.96 0 001.37 5.054L2 22l5.177-1.354a9.97 9.97 0 004.822 1.254h.008c5.502 0 9.985-4.477 9.986-9.984A10.002 10.002 0 0012.012 2zm5.835 14.16c-.25.706-1.443 1.293-1.99 1.347-.497.05-1.147.25-3.327-.655-2.79-1.157-4.59-4.004-4.73-4.188-.137-.184-1.116-1.48-1.116-2.825 0-1.344.706-2.003.955-2.27.25-.267.548-.334.73-.334.183 0 .365.003.523.01.162.008.38-.063.593.453.22.53.75 1.83.816 1.964.066.134.11.29.02.47-.09.18-.135.29-.27.447-.135.156-.285.348-.407.467-.136.133-.28.277-.12.553.16.276.71.1.2.98.67 1.05.6 1.486.9 1.286.3-.2.628-.26.928-.1.3.16 1.9.896 2.083.986.183.09.305.134.35.213.046.08.046.463-.204 1.17z"/>
            </svg>
          </div>
        </div>

        <!-- Ticket text details -->
        <div class="ticket-info">
          <div class="top-row">
            <span class="name">{{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}</span>
            <span class="time">{{ formatTime(ticket.updated_at) }}</span>
          </div>
          
          <div class="bottom-row">
            <p class="last-msg">
              <span v-if="ticket.priority === 'high'" class="priority-dot high"></span>
              <span v-if="ticket.priority === 'medium'" class="priority-dot medium"></span>
              {{ ticket.last_message || 'Nenhuma mensagem' }}
            </p>
            <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
          </div>

          <span v-if="ticket.attendant_details && chatStore.currentFilter !== 'mine'" class="attendant-label">
            {{ ticket.status === 'closed' ? 'Finalizado por' : 'Com' }} {{ ticket.attendant_details.first_name }}
          </span>
        </div>
      </div>
    </div>

    <!-- Empty state for no conversations -->
    <div class="empty-state" v-else>
      <MessageSquareIcon :size="32" class="empty-icon" />
      <span>Nenhuma conversa encontrada</span>
    </div>
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
  </aside>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../../store/chat'
import {
  Plus as PlusIcon,
  LayoutGrid as LayoutGridIcon,
  Filter as FilterIcon,
  Search as SearchIcon,
  MessageSquare as MessageSquareIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
  LogOut as LogOutIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const localSearchQuery = ref(chatStore.searchQuery)
const searchInputRef = ref(null)

const showLogoutModal = ref(false)
const showProfileMenu = ref(false)
const currentStatus = ref('online')
const profileContainerRef = ref(null)

const toggleProfileMenu = () => {
  showProfileMenu.value = !showProfileMenu.value
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
}

const isMac = computed(() => {
  return window.navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

// Debounce local search query back to store
let debounceTimeout = null
watch(localSearchQuery, (newVal) => {
  if (debounceTimeout) clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    chatStore.searchQuery = newVal
  }, 250)
})

watch(() => chatStore.searchQuery, (newVal) => {
  if (newVal !== localSearchQuery.value) {
    localSearchQuery.value = newVal
  }
})

// Handle Global Keyboard Shortcut Ctrl+K / Cmd+K to focus search input
const handleGlobalKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (searchInputRef.value) {
      searchInputRef.value.focus()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('user-status-synced', handleStatusSynced)
  window.addEventListener('click', handleClickOutside)
  if (chatStore.user?.status) {
    currentStatus.value = chatStore.user.status
  }
  // Fetch initial data if lists are empty
  if (chatStore.myTickets.length === 0) {
    chatStore.fetchMyTickets()
  }
  if (chatStore.tickets.length === 0) {
    chatStore.fetchTickets()
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('user-status-synced', handleStatusSynced)
  window.removeEventListener('click', handleClickOutside)
})

const myTicketsCount = computed(() => chatStore.myTickets.length)
const unassignedCount = computed(() => {
  // Let's filter tickets that don't have an attendant
  return chatStore.tickets.filter(t => !t.user && t.status !== 'closed').length
})

const selectFilter = async (filter) => {
  if (filter === 'mine') {
    chatStore.currentFilter = 'mine'
    await chatStore.fetchMyTickets()
  } else {
    await chatStore.fetchTickets(filter)
  }
}

// Unified active list computed based on selection
const activeTabTickets = computed(() => {
  const ticketsList = chatStore.currentFilter === 'mine' ? chatStore.myTickets : chatStore.tickets
  const query = (chatStore.searchQuery || '').toLowerCase().trim()
  if (!query) return ticketsList
  return ticketsList.filter(ticket => {
    const contactName = (ticket.contact_details?.name || '').toLowerCase()
    const remoteJid = (ticket.contact_details?.remote_jid || '').toLowerCase()
    const lastMsg = (ticket.last_message || '').toLowerCase()
    const subject = (ticket.subject || '').toLowerCase()
    
    // Customer details
    const customerName = (ticket.customer_details?.name || '').toLowerCase()
    const customerPhone = (ticket.customer_details?.phone || '').toLowerCase()
    const customerEmail = (ticket.customer_details?.email || '').toLowerCase()
    const customerDoc = (ticket.customer_details?.document || '').toLowerCase()

    return contactName.includes(query) || 
           remoteJid.includes(query) || 
           lastMsg.includes(query) || 
           subject.includes(query) ||
           customerName.includes(query) || 
           customerPhone.includes(query) || 
           customerEmail.includes(query) || 
           customerDoc.includes(query)
  })
})

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { day: '2-digit', month: '2-digit' })
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-ticket-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    border-right: none;
  }
}

/* Sidebar header style */
.sidebar-header {
  padding: 24px 20px 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
}

.header-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

/* Search bar styling */
.search-wrapper {
  padding: 8px 20px 16px 20px;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-secondary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 38px;
  padding: 0 60px 0 36px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.88rem;
  transition: all 0.2s ease;
}

.search-input:focus {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
}

.shortcut-badge {
  position: absolute;
  right: 12px;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 6px;
  user-select: none;
  pointer-events: none;
}

/* Filters Pills Row */
.filters-pills-row {
  display: flex;
  gap: 8px;
  padding: 0 20px 16px 20px;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  scrollbar-width: none; /* Firefox */
}

.filters-pills-row::-webkit-scrollbar {
  display: none; /* Safari and Chrome */
}

.pill-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pill-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}

.pill-btn.active {
  background: var(--text-primary);
  color: var(--bg-ticket-sidebar);
  border-color: var(--text-primary);
}

.pill-badge {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 0.72rem;
}

.pill-badge.active {
  background: rgba(0, 0, 0, 0.15);
  color: var(--bg-ticket-sidebar);
}

/* Ticket List styling */
.ticket-list {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  padding: 16px 20px;
  display: flex;
  gap: 14px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.ticket-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.ticket-item.active {
  background: rgba(255, 255, 255, 0.03);
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.ticket-item.active .active-indicator {
  opacity: 1;
}

/* Avatar container with badge */
.avatar-container {
  position: relative;
  flex-shrink: 0;
}

.avatar {
  width: 46px;
  height: 46px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.platform-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #25d366;
  border: 2px solid var(--bg-ticket-sidebar);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
}

.platform-badge-svg {
  width: 100%;
  height: 100%;
}

/* Ticket information fields */
.ticket-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.name {
  font-weight: 600;
  font-size: 0.94rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.time {
  font-size: 0.76rem;
  color: var(--text-secondary);
  margin-left: 8px;
}

.bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-msg {
  font-size: 0.84rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.priority-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.priority-dot.high {
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
}

.priority-dot.medium {
  background: #f59e0b;
}

.unread-badge {
  background: #ef4444; /* Vermelho como mockup */
  color: white;
  font-size: 0.72rem;
  font-weight: 800;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
  flex-shrink: 0;
}

.attendant-label {
  display: block;
  font-size: 0.75rem;
  color: var(--accent);
  margin-top: 4px;
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  gap: 12px;
  padding: 20px;
}

.empty-icon {
  opacity: 0.4;
}

/* Mobile Profile and Header Styling */
.header-left-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mobile-profile-container {
  position: relative;
  display: none;
}

.mobile-avatar-btn {
  background: none;
  border: none;
  padding: 0;
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--brand-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(34, 181, 95, 0.25);
}

.status-dot-mobile {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-sidebar);
}

.status-dot-mobile.online { background: #10b981; }
.status-dot-mobile.away { background: #f59e0b; }
.status-dot-mobile.offline { background: #94a3b8; }

.profile-popover {
  position: absolute;
  top: 40px;
  left: 0;
  width: 220px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  z-index: 100;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.popover-header {
  display: flex;
  flex-direction: column;
  padding: 4px 8px 8px 8px;
  text-align: left;
}

.popover-header .user-name {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.popover-header .user-role {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.popover-divider {
  height: 1px;
  background: var(--border);
  margin: 6px 0;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  transition: background 0.2s ease;
  text-align: left;
}

.status-option:hover {
  background: rgba(255, 255, 255, 0.05);
}

.status-option.active {
  background: rgba(34, 181, 95, 0.1);
  color: #60a5fa;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online { background: #10b981; }
.status-dot.away { background: #f59e0b; }
.status-dot.offline { background: #94a3b8; }

.popover-logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ef4444;
  width: 100%;
  cursor: pointer;
  transition: background 0.2s ease;
  text-align: left;
}

.popover-logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

.mobile-theme-toggle {
  display: none;
}

/* Modals */
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
  padding: 24px;
  width: 90%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.modal-content h2 {
  font-size: 1.3rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-danger-sm {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 768px) {
  .mobile-profile-container {
    display: block;
  }
  .mobile-theme-toggle {
    display: flex !important;
  }
}
</style>