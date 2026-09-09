<template>
  <Teleport to="body">
    <Transition name="palette-fade">
      <div 
        v-if="chatStore.isCommandPaletteOpen" 
        class="command-palette-backdrop"
        @click="closePalette"
      >
        <div 
          class="command-palette-container glass-effect" 
          @click.stop
          role="dialog"
          aria-modal="true"
          aria-label="Barra de Comandos Global"
        >
          <!-- Search Header -->
          <div class="palette-search-bar">
            <SearchIcon :size="20" class="palette-search-icon" />
            <input 
              ref="paletteInputRef"
              v-model="query" 
              type="text" 
              placeholder="Digite um comando ou busque conversas, clientes, pendências..."
              class="palette-input"
              @keydown.down.prevent="navigateResults(1)"
              @keydown.up.prevent="navigateResults(-1)"
              @keydown.enter.prevent="executeSelectedItem"
              @keydown.esc="closePalette"
            />
            <button v-if="query" @click="query = ''" class="palette-clear-btn" title="Limpar busca">
              <XIcon :size="16" />
            </button>
            <span class="palette-esc-badge" @click="closePalette">ESC</span>
          </div>

          <!-- Results & Actions List -->
          <div class="palette-results-list" ref="listContainerRef">
            <!-- Empty State -->
            <div v-if="flatItems.length === 0" class="palette-empty-state">
              <CompassIcon :size="36" class="empty-icon" />
              <p>Nenhum resultado encontrado para "<strong>{{ query }}</strong>"</p>
              <span>Tente buscar por nome de cliente, protocolo, pendência ou navegue pelas rotas.</span>
            </div>

            <!-- Grouped Sections -->
            <template v-else>
              <!-- Ações Rápidas -->
              <div v-if="groupedItems.actions.length > 0" class="palette-group">
                <div class="palette-group-header">
                  <ZapIcon :size="13" />
                  <span>AÇÕES RÁPIDAS</span>
                </div>
                <div 
                  v-for="item in groupedItems.actions" 
                  :key="item.id"
                  :id="'pal-item-' + item.index"
                  class="palette-item"
                  :class="{ selected: selectedIndex === item.index }"
                  @click="selectItem(item)"
                  @mouseenter="selectedIndex = item.index"
                >
                  <div class="item-icon-box action-box">
                    <component :is="item.icon" :size="16" />
                  </div>
                  <div class="item-details">
                    <span class="item-title">{{ item.title }}</span>
                    <span class="item-subtitle">{{ item.subtitle }}</span>
                  </div>
                  <span v-if="item.badge" class="item-badge">{{ item.badge }}</span>
                </div>
              </div>

              <!-- Navegação -->
              <div v-if="groupedItems.navigation.length > 0" class="palette-group">
                <div class="palette-group-header">
                  <NavigationIcon :size="13" />
                  <span>NAVEGAÇÃO RÁPIDA</span>
                </div>
                <div 
                  v-for="item in groupedItems.navigation" 
                  :key="item.id"
                  :id="'pal-item-' + item.index"
                  class="palette-item"
                  :class="{ selected: selectedIndex === item.index }"
                  @click="selectItem(item)"
                  @mouseenter="selectedIndex = item.index"
                >
                  <div class="item-icon-box nav-box">
                    <component :is="item.icon" :size="16" />
                  </div>
                  <div class="item-details">
                    <span class="item-title">{{ item.title }}</span>
                    <span class="item-subtitle">{{ item.subtitle }}</span>
                  </div>
                  <span class="nav-arrow">→</span>
                </div>
              </div>

              <!-- Conversas / Tickets -->
              <div v-if="groupedItems.tickets.length > 0" class="palette-group">
                <div class="palette-group-header">
                  <MessageSquareIcon :size="13" />
                  <span>CONVERSAS ({{ groupedItems.tickets.length }})</span>
                </div>
                <div 
                  v-for="item in groupedItems.tickets" 
                  :key="item.id"
                  :id="'pal-item-' + item.index"
                  class="palette-item"
                  :class="{ selected: selectedIndex === item.index }"
                  @click="selectItem(item)"
                  @mouseenter="selectedIndex = item.index"
                >
                  <div class="item-avatar ticket-avatar">
                    {{ (item.data.customer_name || item.data.contact?.name || '#').charAt(0).toUpperCase() }}
                  </div>
                  <div class="item-details">
                    <div class="item-title-row">
                      <span class="item-title">{{ item.title }}</span>
                      <span class="ticket-id-tag">#{{ item.data.id }}</span>
                      <span class="ticket-status-pill" :class="item.data.status">{{ getStatusLabel(item.data.status) }}</span>
                    </div>
                    <span class="item-subtitle">{{ item.subtitle }}</span>
                  </div>
                </div>
              </div>

              <!-- Clientes -->
              <div v-if="groupedItems.customers.length > 0" class="palette-group">
                <div class="palette-group-header">
                  <UsersIcon :size="13" />
                  <span>CLIENTES ({{ groupedItems.customers.length }})</span>
                </div>
                <div 
                  v-for="item in groupedItems.customers" 
                  :key="item.id"
                  :id="'pal-item-' + item.index"
                  class="palette-item"
                  :class="{ selected: selectedIndex === item.index }"
                  @click="selectItem(item)"
                  @mouseenter="selectedIndex = item.index"
                >
                  <div class="item-avatar customer-avatar">
                    {{ (item.data.name || 'C').charAt(0).toUpperCase() }}
                  </div>
                  <div class="item-details">
                    <div class="item-title-row">
                      <span class="item-title">{{ item.title }}</span>
                      <span v-if="item.data.document" class="doc-badge">{{ item.data.document }}</span>
                    </div>
                    <span class="item-subtitle">{{ item.subtitle }}</span>
                  </div>
                </div>
              </div>

              <!-- Pendências -->
              <div v-if="groupedItems.pendencies.length > 0" class="palette-group">
                <div class="palette-group-header">
                  <CheckSquareIcon :size="13" />
                  <span>PENDÊNCIAS ({{ groupedItems.pendencies.length }})</span>
                </div>
                <div 
                  v-for="item in groupedItems.pendencies" 
                  :key="item.id"
                  :id="'pal-item-' + item.index"
                  class="palette-item"
                  :class="{ selected: selectedIndex === item.index }"
                  @click="selectItem(item)"
                  @mouseenter="selectedIndex = item.index"
                >
                  <div class="item-icon-box pendency-box" :class="item.data.priority">
                    <CheckSquareIcon :size="16" />
                  </div>
                  <div class="item-details">
                    <div class="item-title-row">
                      <span class="item-title">{{ item.title }}</span>
                      <span class="priority-pill" :class="item.data.priority">{{ item.data.priority || 'normal' }}</span>
                    </div>
                    <span class="item-subtitle">{{ item.subtitle }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Footer with keyboard instructions -->
          <div class="palette-footer">
            <div class="footer-keys">
              <span class="key-hint"><kbd>↑</kbd><kbd>↓</kbd> Navegar</span>
              <span class="key-hint"><kbd>↵</kbd> Selecionar</span>
              <span class="key-hint"><kbd>ESC</kbd> Fechar</span>
            </div>
            <div class="footer-brand">
              <span>wDesk Spotlight</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'
import axios from 'axios'
import {
  Search as SearchIcon,
  X as XIcon,
  Compass as CompassIcon,
  Zap as ZapIcon,
  Navigation as NavigationIcon,
  MessageSquare as MessageSquareIcon,
  Users as UsersIcon,
  CheckSquare as CheckSquareIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
  Minimize2 as Minimize2Icon,
  Maximize2 as Maximize2Icon,
  Plus as PlusIcon,
  BarChart2 as BarChart2Icon,
  LayoutDashboard as DashboardIcon,
  UserCheck as UserCheckIcon,
  Settings as SettingsIcon,
  Radio as RadioIcon,
  Layers as LayersIcon,
  Sidebar as SidebarIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()

const query = ref('')
const selectedIndex = ref(0)
const paletteInputRef = ref(null)
const listContainerRef = ref(null)

const customersList = ref([])
const pendenciesList = ref([])
let hasFetchedExternalData = false

// Fetch data when palette opens
const fetchExternalData = async () => {
  if (hasFetchedExternalData) return
  try {
    const [resCust, resPend] = await Promise.all([
      axios.get('/api/v1/customers/'),
      axios.get('/api/v1/pendencies/')
    ])
    customersList.value = resCust.data || []
    pendenciesList.value = resPend.data || []
    hasFetchedExternalData = true
  } catch (err) {
    console.warn('Erro ao pré-carregar dados para o Command Palette:', err)
  }
}

// Available static actions
const staticActions = computed(() => [
  {
    id: 'act-density',
    title: chatStore.densityMode === 'compact' ? 'Modo de Densidade: Alternar para Confortável' : 'Modo de Densidade: Alternar para Compacto',
    subtitle: 'Ajusta espaçamento, tamanhos de fontes e listas de todo o sistema',
    icon: chatStore.densityMode === 'compact' ? Maximize2Icon : Minimize2Icon,
    badge: chatStore.densityMode === 'compact' ? 'Compacto Ativo' : 'Confortável',
    handler: () => chatStore.toggleDensityMode()
  },
  {
    id: 'act-theme',
    title: chatStore.theme === 'dark' ? 'Tema: Alternar para Modo Claro' : 'Tema: Alternar para Modo Escuro',
    subtitle: 'Muda a paleta de cores entre tons escuros e claros',
    icon: chatStore.theme === 'dark' ? SunIcon : MoonIcon,
    badge: chatStore.theme === 'dark' ? 'Dark' : 'Light',
    handler: () => chatStore.toggleTheme()
  },
  {
    id: 'act-crm-mode',
    title: chatStore.crmDrawerMode === 'floating' ? 'Painel CRM: Fixar na Lateral (Docked)' : 'Painel CRM: Tornar Flutuante (Drawer)',
    subtitle: 'Alterna entre painel lateral fixo na tela ou gaveta flutuante sobreposta',
    icon: SidebarIcon,
    badge: chatStore.crmDrawerMode,
    handler: () => chatStore.toggleCrmDrawerMode()
  },
  {
    id: 'act-broadcast',
    title: 'Nova Transmissão em Massa',
    subtitle: 'Disparar mensagem para múltiplos contatos',
    icon: RadioIcon,
    handler: () => {
      chatStore.showBroadcastModal = true
    }
  },
  {
    id: 'act-new-pendency',
    title: 'Nova Pendência / Tarefa',
    subtitle: 'Ir para tela de pendências e criar nova pendência',
    icon: PlusIcon,
    handler: () => {
      router.push({ path: '/pendencies', query: { new: '1' } })
    }
  }
])

// Navigation routes
const navRoutes = [
  { id: 'nav-conversations', title: 'Conversas & Atendimento', subtitle: 'Acessar central de chat e atendimento ao vivo', path: '/conversations', icon: MessageSquareIcon },
  { id: 'nav-customers', title: 'Clientes & Contatos', subtitle: 'Cadastro, histórico e dados de clientes', path: '/customers', icon: UsersIcon },
  { id: 'nav-pendencies', title: 'Gestão de Pendências', subtitle: 'Tarefas pendentes, follow-ups e resoluções', path: '/pendencies', icon: CheckSquareIcon },
  { id: 'nav-dashboard', title: 'Painel do Agente', subtitle: 'Visão geral de métricas e status rápido', path: '/dashboard', icon: DashboardIcon },
  { id: 'nav-analytics', title: 'Relatórios & Métricas', subtitle: 'Estatísticas de desempenho, tempo de espera e TMA', path: '/analytics', icon: BarChart2Icon },
  { id: 'nav-users', title: 'Gerenciamento de Equipe', subtitle: 'Atendentes, permissões e departamentos', path: '/users', icon: UserCheckIcon },
  { id: 'nav-settings', title: 'Configurações do Sistema', subtitle: 'Conexões WhatsApp, integrações e parâmetros', path: '/settings', icon: SettingsIcon }
]

// Grouped items filtered by query
const groupedItems = computed(() => {
  const q = query.value.trim().toLowerCase()
  let counter = 0

  // 1. Actions
  const filteredActions = staticActions.value
    .filter(a => !q || a.title.toLowerCase().includes(q) || a.subtitle.toLowerCase().includes(q))
    .map(a => ({ ...a, type: 'action', index: counter++ }))

  // 2. Navigation
  const filteredNav = navRoutes
    .filter(n => !q || n.title.toLowerCase().includes(q) || n.subtitle.toLowerCase().includes(q))
    .map(n => ({
      ...n,
      type: 'navigation',
      index: counter++,
      handler: () => router.push(n.path)
    }))

  // 3. Tickets
  const allTickets = [...(chatStore.tickets || []), ...(chatStore.myTickets || [])]
  const uniqueTicketsMap = new Map()
  allTickets.forEach(t => uniqueTicketsMap.set(t.id, t))

  const filteredTickets = (!q ? [] : Array.from(uniqueTicketsMap.values()).filter(t => {
    const custName = (t.customer_name || t.contact?.name || t.contact?.push_name || '').toLowerCase()
    const custPhone = (t.contact?.remote_jid || t.contact?.cellphone || '').toLowerCase()
    const ticketId = String(t.id)
    const subject = (t.subject || '').toLowerCase()
    const lastMsg = (t.last_message || '').toLowerCase()
    return custName.includes(q) || custPhone.includes(q) || ticketId.includes(q) || subject.includes(q) || lastMsg.includes(q)
  })).slice(0, 6).map(t => ({
    id: 'ticket-' + t.id,
    type: 'ticket',
    title: t.customer_name || t.contact?.name || 'Cliente Sem Nome',
    subtitle: t.last_message || 'Nenhuma mensagem recente',
    data: t,
    index: counter++,
    handler: async () => {
      chatStore.activeTicket = t
      await chatStore.fetchMessages(t.id)
      router.push('/conversations')
    }
  }))

  // 4. Customers
  const filteredCustomers = (!q ? [] : (customersList.value || []).filter(c => {
    const name = (c.name || '').toLowerCase()
    const doc = (c.document || '').toLowerCase()
    const phone = (c.phone || c.cellphone || '').toLowerCase()
    return name.includes(q) || doc.includes(q) || phone.includes(q)
  })).slice(0, 4).map(c => ({
    id: 'customer-' + c.id,
    type: 'customer',
    title: c.name,
    subtitle: c.phone || c.cellphone || c.email || 'Sem contato adicional',
    data: c,
    index: counter++,
    handler: () => {
      router.push({ path: '/customers', query: { search: c.name } })
    }
  }))

  // 5. Pendencies
  const filteredPendencies = (!q ? [] : (pendenciesList.value || []).filter(p => {
    const title = (p.title || '').toLowerCase()
    const desc = (p.description || '').toLowerCase()
    return title.includes(q) || desc.includes(q)
  })).slice(0, 4).map(p => ({
    id: 'pendency-' + p.id,
    type: 'pendency',
    title: p.title,
    subtitle: p.description || 'Sem descrição cadastrada',
    data: p,
    index: counter++,
    handler: () => {
      router.push({ path: '/pendencies', query: { search: p.title } })
    }
  }))

  return {
    actions: filteredActions,
    navigation: filteredNav,
    tickets: filteredTickets,
    customers: filteredCustomers,
    pendencies: filteredPendencies
  }
})

// Flattened list for linear keyboard navigation
const flatItems = computed(() => {
  const g = groupedItems.value
  return [...g.actions, ...g.navigation, ...g.tickets, ...g.customers, ...g.pendencies]
})

const getStatusLabel = (status) => {
  switch (status) {
    case 'open': return 'Aberto'
    case 'pending': return 'Pendente'
    case 'closed': return 'Fechado'
    default: return status || 'Ativo'
  }
}

const closePalette = () => {
  chatStore.closeCommandPalette()
  query.value = ''
  selectedIndex.value = 0
}

const navigateResults = (direction) => {
  const total = flatItems.value.length
  if (total === 0) return

  let nextIndex = selectedIndex.value + direction
  if (nextIndex < 0) nextIndex = total - 1
  if (nextIndex >= total) nextIndex = 0

  selectedIndex.value = nextIndex

  // Scroll into view
  nextTick(() => {
    const selectedEl = document.getElementById('pal-item-' + nextIndex)
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

const selectItem = (item) => {
  if (item && item.handler) {
    item.handler()
    closePalette()
  }
}

const executeSelectedItem = () => {
  const item = flatItems.value.find(i => i.index === selectedIndex.value)
  if (item) {
    selectItem(item)
  }
}

// Reset selection on query changes
watch(query, () => {
  selectedIndex.value = 0
})

// Focus input when opened
watch(() => chatStore.isCommandPaletteOpen, (isOpen) => {
  if (isOpen) {
    fetchExternalData()
    if (chatStore.tickets.length === 0) chatStore.fetchTickets()
    if (chatStore.myTickets.length === 0) chatStore.fetchMyTickets()
    nextTick(() => {
      paletteInputRef.value?.focus()
    })
  }
})

// Global keyboard shortcut listener
const handleGlobalKey = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    chatStore.toggleCommandPalette()
    return
  }

  if (e.key === 'Escape' && chatStore.isCommandPaletteOpen) {
    e.preventDefault()
    closePalette()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKey)
})
</script>

<style scoped>
.command-palette-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 10vh 16px 24px;
}

.command-palette-container {
  width: 100%;
  max-width: 680px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 75vh;
  animation: modal-pop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-pop {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Search bar */
.palette-search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.02);
}

.palette-search-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.palette-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1.05rem;
  outline: none;
}

.palette-input::placeholder {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.palette-clear-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.palette-clear-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
}

.palette-esc-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 7px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  cursor: pointer;
}

/* Results list */
.palette-results-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  max-height: 50vh;
}

.palette-group {
  margin-bottom: 8px;
}

.palette-group:last-child {
  margin-bottom: 0;
}

.palette-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.palette-item.selected {
  background: rgba(16, 185, 129, 0.1);
  border-left-color: var(--accent);
}

.item-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-icon-box.action-box {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
}

.item-icon-box.nav-box {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.item-icon-box.pendency-box {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.item-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.item-avatar.ticket-avatar {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.item-avatar.customer-avatar {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
}

.item-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.item-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.item-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-subtitle {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-id-tag {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent);
  background: rgba(16, 185, 129, 0.12);
  padding: 1px 6px;
  border-radius: 4px;
}

.ticket-status-pill {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.ticket-status-pill.open {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.ticket-status-pill.pending {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.ticket-status-pill.closed {
  background: rgba(107, 114, 128, 0.2);
  color: var(--text-secondary);
}

.doc-badge {
  font-size: 0.7rem;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  padding: 1px 5px;
  border-radius: 4px;
}

.priority-pill {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: capitalize;
}

.priority-pill.high, .priority-pill.urgent {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.priority-pill.normal {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.priority-pill.low {
  background: rgba(107, 114, 128, 0.15);
  color: var(--text-secondary);
}

.item-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 8px;
  border-radius: 6px;
}

.nav-arrow {
  color: var(--text-secondary);
  opacity: 0.5;
  font-size: 1rem;
}

/* Empty State */
.palette-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  gap: 8px;
}

.empty-icon {
  color: var(--text-secondary);
  opacity: 0.4;
  margin-bottom: 4px;
}

.palette-empty-state p {
  font-size: 0.95rem;
  color: var(--text-primary);
  margin: 0;
}

.palette-empty-state span {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* Footer */
.palette-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.15);
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.footer-keys {
  display: flex;
  align-items: center;
  gap: 14px;
}

.key-hint {
  display: flex;
  align-items: center;
  gap: 4px;
}

.key-hint kbd {
  font-family: inherit;
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 5px;
  color: var(--text-primary);
}

.footer-brand {
  font-weight: 600;
  opacity: 0.6;
}

/* Transitions */
.palette-fade-enter-active,
.palette-fade-leave-active {
  transition: opacity 0.18s ease;
}

.palette-fade-enter-from,
.palette-fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .command-palette-backdrop {
    padding: 0;
    align-items: stretch;
  }
  
  .command-palette-container {
    max-height: 100dvh;
    height: 100dvh;
    border-radius: 0;
    border: none;
  }

  .palette-results-list {
    max-height: none;
  }

  .footer-brand {
    display: none;
  }
}
</style>
