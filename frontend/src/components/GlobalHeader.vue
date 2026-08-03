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
      <!-- Global Advanced Search Suite -->
      <div class="header-search-container" ref="searchContainerRef" @click.stop>
        <div class="header-search" :class="{ focused: isSearchOpen }">
          <SearchIcon :size="18" class="search-icon" />
          <input 
            ref="searchInputRef"
            v-model="localSearchQuery" 
            type="text" 
            placeholder="Buscar clientes, conversas ou pendências..." 
            @focus="isSearchOpen = true"
            @keydown.esc="isSearchOpen = false"
            @keydown.enter="handleSearchEnter"
          />
          <!-- Clear Button -->
          <button v-if="localSearchQuery" @click="clearSearch" class="clear-search-btn" title="Limpar busca">
            <XIcon :size="14" />
          </button>
          <span v-else class="search-shortcut-hint">Ctrl K</span>
        </div>

        <!-- Global Search Autocomplete / Results Popover -->
        <Transition name="fade-fast">
          <div v-if="isSearchOpen && localSearchQuery.trim().length > 0" class="global-search-popover glass-effect">
            <div class="search-popover-header">
              <span>Resultados para "<strong>{{ localSearchQuery }}</strong>"</span>
            </div>

            <div class="search-popover-body">
              <!-- Categoria 1: Conversas / Tickets -->
              <div v-if="searchResults.tickets.length > 0" class="search-category-section">
                <div class="category-header">
                  <MessageSquareIcon :size="14" style="color: var(--accent);" />
                  <span>CONVERSAS ({{ searchResults.tickets.length }})</span>
                </div>
                <div 
                  v-for="ticket in searchResults.tickets" 
                  :key="'t_' + ticket.id" 
                  class="search-result-item"
                  @click="openTicket(ticket)"
                >
                  <div class="item-avatar">
                    {{ (ticket.customer_name || ticket.contact?.name || '#').charAt(0).toUpperCase() }}
                  </div>
                  <div class="item-info">
                    <div class="item-title">
                      <strong>{{ ticket.customer_name || ticket.contact?.name || 'Cliente' }}</strong>
                      <span class="ticket-id-tag">#{{ ticket.id }}</span>
                    </div>
                    <p class="item-sub">{{ ticket.last_message || 'Nenhuma mensagem recente' }}</p>
                  </div>
                </div>
              </div>

              <!-- Categoria 2: Clientes -->
              <div v-if="searchResults.customers.length > 0" class="search-category-section">
                <div class="category-header">
                  <UsersIcon :size="14" style="color: #10b981;" />
                  <span>CLIENTES ({{ searchResults.customers.length }})</span>
                </div>
                <div 
                  v-for="customer in searchResults.customers" 
                  :key="'c_' + customer.id" 
                  class="search-result-item"
                  @click="openCustomer(customer)"
                >
                  <div class="item-avatar customer-bg">
                    {{ customer.name.charAt(0).toUpperCase() }}
                  </div>
                  <div class="item-info">
                    <div class="item-title">
                      <strong>{{ customer.name }}</strong>
                      <span v-if="customer.document" class="doc-tag">{{ customer.document }}</span>
                    </div>
                    <p class="item-sub">{{ customer.phone || customer.email || 'Sem telefone' }}</p>
                  </div>
                </div>
              </div>

              <!-- Categoria 3: Pendências -->
              <div v-if="searchResults.pendencies.length > 0" class="search-category-section">
                <div class="category-header">
                  <CheckSquareIcon :size="14" style="color: #f59e0b;" />
                  <span>PENDÊNCIAS ({{ searchResults.pendencies.length }})</span>
                </div>
                <div 
                  v-for="pendency in searchResults.pendencies" 
                  :key="'p_' + pendency.id" 
                  class="search-result-item"
                  @click="openPendency(pendency)"
                >
                  <div class="item-avatar pendency-bg">
                    📋
                  </div>
                  <div class="item-info">
                    <div class="item-title">
                      <strong>{{ pendency.title }}</strong>
                      <span v-if="pendency.priority" class="priority-tag" :class="pendency.priority">{{ pendency.priority }}</span>
                    </div>
                    <p class="item-sub">{{ pendency.description || 'Sem descrição' }}</p>
                  </div>
                </div>
              </div>

              <!-- Estado Vazio -->
              <div v-if="totalResultsCount === 0" class="search-empty-state">
                <span>Nenhum resultado encontrado para "<strong>{{ localSearchQuery }}</strong>"</span>
              </div>
            </div>

            <!-- Footer: Ver tudo em Conversas -->
            <div class="search-popover-footer" @click="handleSearchEnter">
              <span>Pressione <kbd>Enter</kbd> para filtrar conversas por "{{ localSearchQuery }}"</span>
            </div>
          </div>
        </Transition>
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
  Menu as MenuIcon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const searchInputRef = ref(null)
const searchContainerRef = ref(null)
const isSearchOpen = ref(false)
const localSearchQuery = ref(chatStore.searchQuery || '')
const showNotificationDropdown = ref(false)

const customersList = ref([])
const pendenciesList = ref([])

const fetchSearchData = async () => {
  try {
    const [resCust, resPend] = await Promise.all([
      axios.get('/api/v1/customers/'),
      axios.get('/api/v1/pendencies/')
    ])
    customersList.value = resCust.data || []
    pendenciesList.value = resPend.data || []
  } catch (e) {
    console.error("Erro ao carregar dados da busca global", e)
  }
}

const toggleMobileMenu = () => {
  chatStore.toggleMobileMenu()
}

const clearSearch = () => {
  localSearchQuery.value = ''
  chatStore.searchQuery = ''
  isSearchOpen.value = false
}

// Result computation
const searchResults = computed(() => {
  const q = (localSearchQuery.value || '').trim().toLowerCase()
  if (!q) return { tickets: [], customers: [], pendencies: [] }

  // 1. Tickets
  const allTickets = [...(chatStore.tickets || []), ...(chatStore.myTickets || [])]
  const uniqueTicketsMap = new Map()
  allTickets.forEach(t => uniqueTicketsMap.set(t.id, t))
  
  const matchedTickets = Array.from(uniqueTicketsMap.values()).filter(t => {
    const custName = (t.customer_name || t.contact?.name || t.contact?.push_name || '').toLowerCase()
    const custPhone = (t.contact?.remote_jid || t.contact?.cellphone || '').toLowerCase()
    const ticketId = String(t.id)
    const subject = (t.subject || '').toLowerCase()
    const lastMsg = (t.last_message || '').toLowerCase()
    return custName.includes(q) || custPhone.includes(q) || ticketId.includes(q) || subject.includes(q) || lastMsg.includes(q)
  }).slice(0, 5)

  // 2. Customers
  const matchedCustomers = (customersList.value || []).filter(c => {
    const name = (c.name || '').toLowerCase()
    const doc = (c.document || '').toLowerCase()
    const phone = (c.phone || c.cellphone || '').toLowerCase()
    return name.includes(q) || doc.includes(q) || phone.includes(q)
  }).slice(0, 4)

  // 3. Pendencies
  const matchedPendencies = (pendenciesList.value || []).filter(p => {
    const title = (p.title || '').toLowerCase()
    const desc = (p.description || '').toLowerCase()
    return title.includes(q) || desc.includes(q)
  }).slice(0, 4)

  return {
    tickets: matchedTickets,
    customers: matchedCustomers,
    pendencies: matchedPendencies
  }
})

const totalResultsCount = computed(() => {
  const r = searchResults.value
  return r.tickets.length + r.customers.length + r.pendencies.length
})

const openTicket = async (ticket) => {
  chatStore.activeTicket = ticket
  await chatStore.fetchMessages(ticket.id)
  isSearchOpen.value = false
  if (route.path !== '/conversations') {
    router.push('/conversations')
  }
}

const openCustomer = (customer) => {
  isSearchOpen.value = false
  router.push({ path: '/customers', query: { search: customer.name } })
}

const openPendency = (pendency) => {
  isSearchOpen.value = false
  router.push({ path: '/pendencies', query: { search: pendency.title } })
}

const handleSearchEnter = () => {
  if (localSearchQuery.value) {
    chatStore.searchQuery = localSearchQuery.value
    isSearchOpen.value = false
    if (route.path !== '/conversations') {
      router.push('/conversations')
    }
  }
}

// Sync store searchQuery
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
})

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

const handleGlobalKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    searchInputRef.value?.focus()
    isSearchOpen.value = true
  } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault()
    searchInputRef.value?.focus()
    isSearchOpen.value = true
  } else if (e.key === 'Escape') {
    isSearchOpen.value = false
  }
}

const handleWindowClick = (e) => {
  showNotificationDropdown.value = false
  if (searchContainerRef.value && !searchContainerRef.value.contains(e.target)) {
    isSearchOpen.value = false
  }
}

onMounted(() => {
  fetchSearchData()
  window.addEventListener('click', handleWindowClick)
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
  window.removeEventListener('keydown', handleGlobalKeydown)
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

/* Busca Global */
.header-search-container {
  position: relative;
}

.header-search {
  position: relative;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.search-icon {
  position: absolute;
  left: 14px;
  color: var(--text-secondary);
  pointer-events: none;
}

.header-search input {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 9px 38px 9px 40px;
  color: var(--text-primary);
  outline: none;
  width: 320px;
  font-size: 0.85rem;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-search.focused input,
.header-search input:focus {
  border-color: var(--accent);
  width: 400px;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
  background: rgba(0, 0, 0, 0.35);
}

.search-shortcut-hint {
  position: absolute;
  right: 12px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  pointer-events: none;
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 50%;
}

.clear-search-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

/* Popover de Resultados da Busca Global */
.global-search-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 10px;
  width: 420px;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 16px 35px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  z-index: 1050;
}

.search-popover-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.1);
}

.search-popover-body {
  max-height: 380px;
  overflow-y: auto;
  padding: 8px 0;
}

.search-category-section {
  margin-bottom: 8px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.item-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.customer-bg { background: #10b981; }
.pendency-bg { background: #f59e0b; }

.item-info {
  flex: 1;
  overflow: hidden;
}

.item-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.88rem;
  color: var(--text-primary);
}

.ticket-id-tag {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
}

.doc-tag {
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-family: monospace;
}

.priority-tag {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 4px;
}

.priority-tag.high { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.priority-tag.medium { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.priority-tag.low { background: rgba(16, 185, 129, 0.2); color: #10b981; }

.item-sub {
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 2px 0 0;
}

.search-empty-state {
  padding: 30px 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.search-popover-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.15);
  font-size: 0.78rem;
  color: var(--text-secondary);
  text-align: center;
  cursor: pointer;
}

.search-popover-footer:hover {
  color: var(--accent);
}

.search-popover-footer kbd {
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 5px;
  border-radius: 4px;
  font-family: monospace;
}

/* Notificações */
.notification-container { position: relative; }
.header-icon-btn {
  background: rgba(255, 255, 255, 0.05);
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
.header-icon-btn:hover { background: rgba(255, 255, 255, 0.1); }
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
.notif-item:hover { background: rgba(255, 255, 255, 0.05); }
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
