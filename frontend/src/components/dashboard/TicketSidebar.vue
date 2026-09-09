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
        <button 
          class="action-btn" 
          @click="chatStore.toggleLayoutMode" 
          :title="chatStore.layoutMode === 'grid' ? 'Visualização em Lista' : 'Visualização em Grade'"
          :class="{ active: chatStore.layoutMode === 'grid' }"
        >
          <LayoutListIcon v-if="chatStore.layoutMode === 'grid'" :size="18" />
          <LayoutGridIcon v-else :size="18" />
        </button>
        <div class="filter-dropdown-wrapper" ref="filterDropdownRef">
          <button 
            class="action-btn" 
            :class="{ active: hasActiveAdvancedFilters || showFilterPopover }" 
            @click.stop="showFilterPopover = !showFilterPopover" 
            title="Filtros Avançados de Conversas"
          >
            <FilterIcon :size="18" />
            <span v-if="hasActiveAdvancedFilters" class="active-filter-indicator"></span>
          </button>

          <!-- Filter Popover -->
          <Transition name="fade">
            <div v-if="showFilterPopover" class="filter-popover glass-effect" @click.stop>
              <div class="filter-popover-header">
                <h4>Filtros Rápidos</h4>
                <button v-if="hasActiveAdvancedFilters" @click="clearAdvancedFilters" class="clear-filters-btn">Limpar</button>
              </div>

              <div class="filter-options-list">
                <label class="filter-checkbox-row">
                  <input type="checkbox" v-model="advancedFilters.onlyUnread" />
                  <span class="checkbox-label">Apenas Não Lidas</span>
                </label>
                <label class="filter-checkbox-row">
                  <input type="checkbox" v-model="advancedFilters.onlyDrafts" />
                  <span class="checkbox-label">Com Rascunho Salvo</span>
                </label>
                <label class="filter-checkbox-row">
                  <input type="checkbox" v-model="advancedFilters.onlyBlocked" />
                  <span class="checkbox-label">Clientes Bloqueados</span>
                </label>
              </div>

              <div class="filter-priority-section">
                <span class="priority-label-heading">Prioridade:</span>
                <div class="priority-pills-row">
                  <button 
                    type="button"
                    class="priority-pill-btn" 
                    :class="{ active: advancedFilters.priority === 'all' }" 
                    @click="advancedFilters.priority = 'all'"
                  >Todas</button>
                  <button 
                    type="button"
                    class="priority-pill-btn high" 
                    :class="{ active: advancedFilters.priority === 'high' }" 
                    @click="advancedFilters.priority = 'high'"
                  >Alta</button>
                  <button 
                    type="button"
                    class="priority-pill-btn medium" 
                    :class="{ active: advancedFilters.priority === 'medium' }" 
                    @click="advancedFilters.priority = 'medium'"
                  >Média</button>
                  <button 
                    type="button"
                    class="priority-pill-btn low" 
                    :class="{ active: advancedFilters.priority === 'low' }" 
                    @click="advancedFilters.priority = 'low'"
                  >Baixa</button>
                </div>
              </div>
            </div>
          </Transition>
        </div>
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
          placeholder="Filtrar conversas... (Alt+↓/↑ navegar)" 
          class="search-input"
        />
        <span class="shortcut-badge">/</span>
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
        v-if="chatStore.userRole === 'admin'"
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'all' }"
        @click="selectFilter('all')"
      >
        Abertos
      </button>
      <button 
        class="pill-btn" 
        :class="{ active: chatStore.currentFilter === 'closed' }"
        @click="selectFilter('closed')"
      >
        Fechados
      </button>
    </div>

    <!-- Unified Ticket List -->
    <div class="ticket-list" :class="{ 'grid-layout': chatStore.layoutMode === 'grid' }" v-if="chatStore.loading && activeTabTickets.length === 0">
      <div v-for="n in 6" :key="'skel-' + n" class="ticket-skeleton-item" :class="{ 'grid-item': chatStore.layoutMode === 'grid' }">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-details">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line long"></div>
        </div>
      </div>
    </div>

    <div class="ticket-list" :class="{ 'grid-layout': chatStore.layoutMode === 'grid' }" v-else-if="activeTabTickets.length > 0">
      <div 
        v-for="ticket in activeTabTickets" 
        :key="ticket.id"
        class="ticket-item"
        :class="{ 
          active: chatStore.activeTicket?.id === ticket.id,
          'grid-item': chatStore.layoutMode === 'grid',
          'blocked-ticket': ticket.customer_details?.is_blocked || ticket.contact_details?.customer_details?.is_blocked
        }"
        @click="chatStore.selectTicket(ticket)"
        @contextmenu.prevent="handleContextMenu($event, ticket)"
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
            <span class="name">
              {{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}
              <span v-if="ticket.customer_details?.is_blocked || ticket.contact_details?.customer_details?.is_blocked" class="blocked-tag-pill" title="Cliente Bloqueado">
                <LockIcon :size="10" /> Bloqueado
              </span>
            </span>
            <div class="top-row-meta">
              <!-- SLA Waiting Badge -->
              <span 
                v-if="ticket.status !== 'closed' && (ticket.unread_count > 0 || !ticket.user)" 
                class="sla-sidebar-badge"
                :class="getSlaClass(ticket)"
                :title="`Tempo de espera do cliente: ${formatSlaTime(ticket)}`"
              >
                <ClockIcon :size="10" />
                {{ formatSlaTime(ticket) }}
              </span>
              <span class="time">{{ formatDateOrTime(ticket.updated_at) }}</span>
            </div>
          </div>
          
          <div class="bottom-row">
            <p class="last-msg">
              <span v-if="ticket.priority === 'high'" class="priority-dot high"></span>
              <span v-if="ticket.priority === 'medium'" class="priority-dot medium"></span>
              {{ ticket.last_message || 'Nenhuma mensagem' }}
            </p>
            <div class="ticket-badges-group" style="display: flex; align-items: center; gap: 4px; flex-shrink: 0;">
              <span v-if="hasDraft(ticket.id)" class="ticket-draft-badge" title="Rascunho salvo não enviado">
                <PencilIcon :size="10" /> Rascunho
              </span>
              <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
            </div>
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
      <span>{{ chatStore.fetchError || 'Nenhuma conversa encontrada' }}</span>
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

    <!-- Teleported Context Menu (Right-Click on Ticket) -->
    <Teleport to="body">
      <Transition name="fade-fast">
        <div 
          v-if="contextMenu.show" 
          class="ticket-context-menu glass-effect" 
          :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
          @click.stop
        >
          <div class="context-menu-header">
            <span class="ctx-id">#{{ contextMenu.ticket?.id }}</span>
            <strong class="ctx-name">{{ contextMenu.ticket?.contact_details?.name || 'Cliente' }}</strong>
          </div>

          <div class="ctx-divider"></div>

          <!-- Assumir Atendimento -->
          <button 
            v-if="!contextMenu.ticket?.user && contextMenu.ticket?.status !== 'closed'" 
            @click="contextTakeOver" 
            class="ctx-menu-item primary"
          >
            <UserCheckIcon :size="14" />
            <span>Assumir Atendimento</span>
          </button>

          <!-- Abrir Conversa -->
          <button @click="contextOpenTicket" class="ctx-menu-item">
            <MessageSquareIcon :size="14" />
            <span>Abrir Conversa</span>
          </button>

          <div class="ctx-divider"></div>

          <!-- Definir Prioridade -->
          <div class="ctx-submenu">
            <span class="ctx-submenu-title">Definir Prioridade:</span>
            <div class="ctx-priority-btns">
              <button 
                @click="contextSetPriority('high')" 
                class="ctx-priority-btn high" 
                :class="{ selected: contextMenu.ticket?.priority === 'high' }"
              >🔴 Alta</button>
              <button 
                @click="contextSetPriority('medium')" 
                class="ctx-priority-btn medium" 
                :class="{ selected: contextMenu.ticket?.priority === 'medium' }"
              >🟡 Média</button>
              <button 
                @click="contextSetPriority('low')" 
                class="ctx-priority-btn low" 
                :class="{ selected: contextMenu.ticket?.priority === 'low' }"
              >⚪ Baixa</button>
            </div>
          </div>

          <div class="ctx-divider"></div>

          <!-- Copiar Dados -->
          <button @click="contextCopyPhone" class="ctx-menu-item">
            <CopyIcon :size="14" />
            <span>{{ copyPhoneSuccess ? 'Telefone Copiado!' : 'Copiar Telefone' }}</span>
          </button>
          <button @click="contextCopyProtocol" class="ctx-menu-item">
            <HashIcon :size="14" />
            <span>{{ copyProtocolSuccess ? 'Protocolo Copiado!' : 'Copiar Protocolo' }}</span>
          </button>
        </div>
      </Transition>
    </Teleport>
  </aside>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useChatStore } from '../../store/chat'
import { useUserProfile } from '../../composables/useUserProfile'
import { formatDateOrTime } from '../../utils/formatters'
import {
  Plus as PlusIcon,
  LayoutGrid as LayoutGridIcon,
  LayoutList as LayoutListIcon,
  Filter as FilterIcon,
  Search as SearchIcon,
  MessageSquare as MessageSquareIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
  LogOut as LogOutIcon,
  Lock as LockIcon,
  Pencil as PencilIcon,
  Clock as ClockIcon,
  Copy as CopyIcon,
  Hash as HashIcon,
  UserCheck as UserCheckIcon
} from 'lucide-vue-next'
import { useChatDrafts } from '../../composables/useChatDrafts'

const chatStore = useChatStore()
const { hasDraft } = useChatDrafts()
const localSearchQuery = ref(chatStore.searchQuery)
const searchInputRef = ref(null)

// Advanced Filters State
const showFilterPopover = ref(false)
const filterDropdownRef = ref(null)
const advancedFilters = ref({
  onlyUnread: false,
  onlyDrafts: false,
  onlyBlocked: false,
  priority: 'all' // 'all', 'high', 'medium', 'low'
})

const hasActiveAdvancedFilters = computed(() => {
  return advancedFilters.value.onlyUnread ||
         advancedFilters.value.onlyDrafts ||
         advancedFilters.value.onlyBlocked ||
         advancedFilters.value.priority !== 'all'
})

const clearAdvancedFilters = () => {
  advancedFilters.value.onlyUnread = false
  advancedFilters.value.onlyDrafts = false
  advancedFilters.value.onlyBlocked = false
  advancedFilters.value.priority = 'all'
}

// Right-Click Context Menu State
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  ticket: null
})
const copyPhoneSuccess = ref(false)
const copyProtocolSuccess = ref(false)

const handleContextMenu = (e, ticket) => {
  const menuWidth = 230
  const menuHeight = 270
  let x = e.clientX
  let y = e.clientY

  if (x + menuWidth > window.innerWidth) {
    x = window.innerWidth - menuWidth - 12
  }
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 12
  }

  contextMenu.value = {
    show: true,
    x,
    y,
    ticket
  }
  copyPhoneSuccess.value = false
  copyProtocolSuccess.value = false
}

const closeContextMenu = () => {
  contextMenu.value.show = false
}

const contextOpenTicket = () => {
  if (contextMenu.value.ticket) {
    chatStore.selectTicket(contextMenu.value.ticket)
  }
  closeContextMenu()
}

const contextTakeOver = async () => {
  if (contextMenu.value.ticket) {
    await chatStore.acceptTicket(contextMenu.value.ticket.id)
    chatStore.selectTicket(contextMenu.value.ticket)
  }
  closeContextMenu()
}

const contextSetPriority = async (priorityLevel) => {
  if (contextMenu.value.ticket) {
    contextMenu.value.ticket.priority = priorityLevel
    await chatStore.updateTicket(contextMenu.value.ticket.id, { priority: priorityLevel })
  }
  closeContextMenu()
}

const contextCopyPhone = () => {
  const phone = contextMenu.value.ticket?.contact_details?.remote_jid || contextMenu.value.ticket?.contact_details?.cellphone || ''
  const clean = phone.replace(/[^0-9]/g, '')
  navigator.clipboard.writeText(clean || phone)
  copyPhoneSuccess.value = true
  setTimeout(closeContextMenu, 800)
}

const contextCopyProtocol = () => {
  const protocol = String(contextMenu.value.ticket?.id || '')
  navigator.clipboard.writeText(protocol)
  copyProtocolSuccess.value = true
  setTimeout(closeContextMenu, 800)
}

// SLA Calculation
const getWaitingMinutes = (ticket) => {
  if (!ticket || ticket.status === 'closed') return 0
  const lastDate = new Date(ticket.updated_at || ticket.created_at)
  const diffMs = Date.now() - lastDate.getTime()
  return Math.max(0, Math.floor(diffMs / 60000))
}

const getSlaClass = (ticket) => {
  const mins = getWaitingMinutes(ticket)
  if (mins >= 15) return 'sla-critical'
  if (mins >= 5) return 'sla-warning'
  return 'sla-ok'
}

const formatSlaTime = (ticket) => {
  const mins = getWaitingMinutes(ticket)
  if (mins < 60) return `${mins}m`
  const hours = Math.floor(mins / 60)
  const rem = mins % 60
  return `${hours}h ${rem}m`
}

const {
  showProfileMenu,
  showLogoutModal,
  currentStatus,
  profileContainerRef,
  userDisplayName,
  userInitials,
  toggleProfileMenu,
  changeStatus,
  triggerLogout,
  logout
} = useUserProfile()

const isMac = computed(() => {
  return /mac/i.test(navigator.userAgent)
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

// Handle Keyboard Shortcuts (/ para busca local, Alt+↓ / Alt+↑ para navegação entre conversas)
const handleGlobalKeydown = (e) => {
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault()
    if (searchInputRef.value) {
      searchInputRef.value.focus()
    }
    return
  }

  // Alt + ArrowDown / Alt + ArrowUp para alternar tickets rapidamente
  if (e.altKey && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
    const list = activeTabTickets.value
    if (!list || list.length === 0) return

    e.preventDefault()
    const currentIndex = list.findIndex(t => t.id === chatStore.activeTicket?.id)

    if (e.key === 'ArrowDown') {
      if (currentIndex === -1 || currentIndex >= list.length - 1) {
        chatStore.selectTicket(list[0])
      } else {
        chatStore.selectTicket(list[currentIndex + 1])
      }
    } else if (e.key === 'ArrowUp') {
      if (currentIndex <= 0) {
        chatStore.selectTicket(list[list.length - 1])
      } else {
        chatStore.selectTicket(list[currentIndex - 1])
      }
    }
  }

  if (e.key === 'Escape') {
    if (showFilterPopover.value) showFilterPopover.value = false
    if (contextMenu.value.show) closeContextMenu()
  }
}

const handleGlobalClick = (e) => {
  if (showFilterPopover.value && filterDropdownRef.value && !filterDropdownRef.value.contains(e.target)) {
    showFilterPopover.value = false
  }
  if (contextMenu.value.show) {
    closeContextMenu()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('click', handleGlobalClick)
  window.addEventListener('scroll', closeContextMenu, true)

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
  window.removeEventListener('click', handleGlobalClick)
  window.removeEventListener('scroll', closeContextMenu, true)
})

const myTicketsCount = computed(() => chatStore.myTickets.length)
const unassignedCount = computed(() => {
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

// 1. Base list memoized by current filter selection
const baseTicketsList = computed(() => {
  return chatStore.currentFilter === 'mine' ? chatStore.myTickets : chatStore.tickets
})

// 2. Active list computed based on query filter and advanced filters
const activeTabTickets = computed(() => {
  let list = baseTicketsList.value

  // Search Query filter
  const query = (chatStore.searchQuery || '').toLowerCase().trim()
  if (query) {
    list = list.filter(ticket => {
      const contactName = (ticket.contact_details?.name || '').toLowerCase()
      const remoteJid = (ticket.contact_details?.remote_jid || '').toLowerCase()
      const lastMsg = (ticket.last_message || '').toLowerCase()
      const subject = (ticket.subject || '').toLowerCase()
      
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
  }

  // Advanced Filters
  if (advancedFilters.value.onlyUnread) {
    list = list.filter(t => (t.unread_count || 0) > 0)
  }
  if (advancedFilters.value.onlyDrafts) {
    list = list.filter(t => hasDraft(t.id))
  }
  if (advancedFilters.value.onlyBlocked) {
    list = list.filter(t => t.customer_details?.is_blocked || t.contact_details?.customer_details?.is_blocked)
  }
  if (advancedFilters.value.priority !== 'all') {
    list = list.filter(t => t.priority === advancedFilters.value.priority)
  }

  return list
})
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
  gap: 5px;
  padding: 0 14px 14px 14px;
  border-bottom: 1px solid var(--border);
}

.pill-btn {
  flex: 1;
  min-width: 0;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 4px;
  border-radius: 12px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
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
  padding: 1px 5px;
  border-radius: 10px;
  font-size: 0.7rem;
  flex-shrink: 0;
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

.ticket-item {
  content-visibility: auto;
  contain-intrinsic-size: 72px;
}

/* Skeleton Loading Animation */
.ticket-skeleton-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  opacity: 0.6;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--border);
  flex-shrink: 0;
}

.skeleton-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  height: 12px;
  border-radius: 4px;
  background: var(--border);
}

.skeleton-line.short { width: 40%; }
.skeleton-line.long { width: 80%; }

@keyframes skeleton-pulse {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

/* Grid Layout Styles */
.ticket-list.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
  padding: 12px;
  align-content: start;
}

.ticket-item.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid rgba(255, 255, 255, 0.04);
  gap: 8px;
  position: relative;
  transition: all 0.2s ease;
  border-bottom: none;
  contain-intrinsic-size: 140px;
}

.ticket-item.grid-item:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.ticket-item.grid-item.active {
  background: rgba(34, 181, 95, 0.08);
  border-color: var(--accent);
}

.ticket-item.grid-item.active .active-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: auto;
  width: 100%;
  height: 3px;
  opacity: 1;
  border-radius: 3px 3px 0 0;
}

.ticket-item.grid-item .ticket-info {
  align-items: center;
  width: 100%;
  text-align: center;
}

.ticket-item.grid-item .top-row {
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-bottom: 2px;
  gap: 2px;
}

.ticket-item.grid-item .top-row .time {
  font-size: 0.72rem;
  opacity: 0.6;
}

.ticket-item.grid-item .bottom-row {
  justify-content: center;
  width: 100%;
  margin-top: 2px;
}

.ticket-item.grid-item .last-msg {
  text-align: center;
  font-size: 0.78rem;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-item.grid-item .unread-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  margin: 0;
}

.ticket-item.grid-item .attendant-label {
  font-size: 0.7rem;
  margin-top: 4px;
  opacity: 0.7;
}

.ticket-skeleton-item.grid-item {
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border-bottom: none;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
}

.ticket-skeleton-item.grid-item .skeleton-details {
  align-items: center;
  width: 100%;
}

.blocked-tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  margin-left: 5px;
  vertical-align: middle;
  text-transform: uppercase;
}

.ticket-item.blocked-ticket {
  border-left: 3px solid #ef4444;
  background: rgba(239, 68, 68, 0.03);
}

@media (max-width: 768px) {
  .mobile-profile-container {
    display: block;
  }
  .mobile-theme-toggle {
    display: flex !important;
  }
}

/* Filter Dropdown Popover */
.filter-dropdown-wrapper {
  position: relative;
}

.active-filter-indicator {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
}

.filter-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  width: 250px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 16px 35px rgba(0, 0, 0, 0.45);
  z-index: 1000;
}

.filter-popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.filter-popover-header h4 {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.clear-filters-btn {
  background: transparent;
  border: none;
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}

.clear-filters-btn:hover {
  background: rgba(16, 185, 129, 0.1);
}

.filter-options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.filter-checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-primary);
  cursor: pointer;
}

.filter-checkbox-row input {
  accent-color: var(--accent);
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.filter-priority-section {
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

.priority-label-heading {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.priority-pills-row {
  display: flex;
  gap: 4px;
}

.priority-pill-btn {
  flex: 1;
  padding: 4px 6px;
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

.priority-pill-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.priority-pill-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.priority-pill-btn.high.active {
  background: #ef4444;
  border-color: #ef4444;
}

.priority-pill-btn.medium.active {
  background: #f59e0b;
  border-color: #f59e0b;
}

.priority-pill-btn.low.active {
  background: #71717a;
  border-color: #71717a;
}

/* SLA Waiting Time Badge */
.sla-sidebar-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
}

.sla-sidebar-badge.sla-ok {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.sla-sidebar-badge.sla-warning {
  background: rgba(245, 158, 11, 0.18);
  color: #f59e0b;
}

.sla-sidebar-badge.sla-critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  animation: pulse-sla 1.8s infinite ease-in-out;
}

/* Ticket Context Menu */
.ticket-context-menu {
  position: fixed;
  width: 220px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
  padding: 6px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  animation: ctx-pop 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes ctx-pop {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.context-menu-header {
  padding: 6px 10px 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

.ctx-id {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent);
}

.ctx-name {
  font-size: 0.8rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ctx-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.ctx-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
  text-align: left;
}

.ctx-menu-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.ctx-menu-item.primary {
  color: var(--accent);
}

.ctx-menu-item.primary:hover {
  background: rgba(16, 185, 129, 0.12);
}

.ctx-submenu {
  padding: 4px 8px;
}

.ctx-submenu-title {
  display: block;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.ctx-priority-btns {
  display: flex;
  gap: 4px;
}

.ctx-priority-btn {
  flex: 1;
  padding: 3px 4px;
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s ease;
}

.ctx-priority-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.ctx-priority-btn.selected {
  border-color: var(--accent);
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
}

.fade-fast-enter-active,
.fade-fast-leave-active {
  transition: opacity 0.15s ease;
}

.fade-fast-enter-from,
.fade-fast-leave-to {
  opacity: 0;
}
</style>