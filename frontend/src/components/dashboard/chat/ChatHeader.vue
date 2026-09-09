<template>
  <header class="chat-header glass-effect">
    <!-- Contact Info (Avatar, Name, Platform, Status) -->
    <div class="contact-info">
      <button class="mobile-back-btn" @click="goBack" title="Voltar">
        <ChevronLeftIcon :size="20" />
      </button>
      
      <!-- Avatar Section with Platform Badge -->
      <div class="avatar-wrapper">
        <div 
          class="avatar clickable" 
          @click="openAvatarImage"
        >
          <img v-if="activeTicket.contact_details?.profile_pic && !imageError" :src="activeTicket.contact_details.profile_pic" class="avatar-img" @error="handleImageError" />
          <span v-else class="avatar-initials">{{ activeTicket.contact_details?.name?.charAt(0) || 'C' }}</span>
        </div>
        <div class="platform-badge" title="WhatsApp">
          <svg viewBox="0 0 24 24" class="platform-badge-svg">
            <path fill="#ffffff" d="M12.012 2c-5.506 0-9.989 4.478-9.99 9.984a9.96 9.96 0 001.37 5.054L2 22l5.177-1.354a9.97 9.97 0 004.822 1.254h.008c5.502 0 9.985-4.477 9.986-9.984A10.002 10.002 0 0012.012 2zm5.835 14.16c-.25.706-1.443 1.293-1.99 1.347-.497.05-1.147.25-3.327-.655-2.79-1.157-4.59-4.004-4.73-4.188-.137-.184-1.116-1.48-1.116-2.825 0-1.344.706-2.003.955-2.27.25-.267.548-.334.73-.334.183 0 .365.003.523.01.162.008.38-.063.593.453.22.53.75 1.83.816 1.964.066.134.11.29.02.47-.09.18-.135.29-.27.447-.135.156-.285.348-.407.467-.136.133-.28.277-.12.553.16.276.71.1.2.98.67 1.05.6 1.486.9 1.286.3-.2.628-.26.928-.1.3.16 1.9.896 2.083.986.183.09.305.134.35.213.046.08.046.463-.204 1.17z"/>
          </svg>
        </div>
      </div>

      <div class="header-text">
        <div class="name-status">
          <h3>{{ activeTicket.contact_details?.name || activeTicket.contact_details?.remote_jid }}</h3>
          <span v-if="activeTicket.customer_details?.fantasy_name || activeTicket.customer_details?.name" class="company-badge" :title="activeTicket.customer_details?.name">
            {{ activeTicket.customer_details?.fantasy_name || activeTicket.customer_details?.name }}
          </span>
          <span v-if="isCustomerBlocked" class="blocked-header-badge" title="Este cliente está bloqueado no cadastro">
            <LockIcon :size="12" /> BLOQUEADO
          </span>
          <span 
            v-if="activeTicket.status !== 'closed' && (activeTicket.unread_count > 0 || !activeTicket.user)"
            class="sla-header-badge"
            :class="getSlaClass(activeTicket)"
            :title="`Tempo de espera do cliente: ${formatSlaTime(activeTicket)}`"
          >
            <ClockIcon :size="11" />
            <span>Espera: {{ formatSlaTime(activeTicket) }}</span>
          </span>
          <span class="status-dot-indicator" :class="activeTicket.status" :title="activeTicket.status === 'open' ? 'Em aberto' : (activeTicket.status === 'pending' ? 'Pendente' : 'Finalizado')"></span>
        </div>
        <p class="ticket-subject">{{ activeTicket.subject || 'Sem assunto definido' }}</p>
      </div>
    </div>

    <!-- Actions (Take Over, Call, Copilot, Options) -->
    <div class="header-actions">
      <!-- Accept/Take Over Button -->
      <button v-if="activeTicket.status !== 'closed' && !activeTicket.user" @click="handleAccept" class="accept-btn">
        <span>Assumir</span>
      </button>

      <!-- Transfer Button -->
      <button 
        v-if="activeTicket.status !== 'closed' && activeTicket.user" 
        @click="triggerAction('openTransferModal')" 
        class="transfer-btn" 
        title="Transferir Atendimento"
      >
        <TransferIcon :size="15" />
        <span class="btn-text">Transferir</span>
      </button>

      <!-- Finalizar Button -->
      <button 
        v-if="activeTicket.status !== 'closed' && activeTicket.user" 
        @click="triggerAction('openCloseModal')" 
        class="close-ticket-btn" 
        title="Finalizar Atendimento"
      >
        <CheckIcon :size="15" />
        <span class="btn-text">Finalizar</span>
      </button>

      <!-- Copilot Sparkle Button -->
      <button 
        class="copilot-btn" 
        :class="{ active: showCRM }" 
        @click="toggleCopilot"
        title="Copilot"
      >
        <SparklesIcon :size="16" />
      </button>

      <!-- Follow-up / Lembrete Button -->
      <button 
        v-if="activeTicket.status !== 'closed'"
        class="reminder-action-btn"
        :class="{ 'has-active-reminder': activeReminder }"
        @click="showReminderModal = true"
        :title="activeReminder ? `Lembrete agendado para ${formatReminderTime(activeReminder.scheduled_for)}` : 'Agendar Lembrete de Retorno / Follow-up'"
      >
        <AlarmClockIcon :size="16" />
        <span class="btn-text" v-if="!activeReminder">Follow-up</span>
        <span v-else class="reminder-time-badge">
          {{ formatShortReminderTime(activeReminder.scheduled_for) }}
        </span>
      </button>

      <!-- In-Chat Search Button -->
      <button 
        class="chat-action-icon-btn" 
        :class="{ active: isSearchActive }" 
        @click="emit('toggleSearch')" 
        title="Buscar na conversa (Ctrl+F)"
      >
        <SearchIcon :size="16" />
      </button>

      <!-- More vertical menu popover container -->
      <div class="dropdown-wrapper" ref="dropdownRef">
        <button @click.stop="toggleMenu" class="more-btn" title="Opções">
          <MoreVerticalIcon :size="18" />
        </button>

        <!-- Dropdown Menu Options -->
        <Transition name="fade">
          <div v-if="showMenu" class="dropdown-menu glass-effect">
            <button @click="emitCRMAction" class="menu-item">
              <ContactIcon :size="15" />
              <span>{{ showCRM ? 'Ocultar Detalhes' : 'Mostrar Detalhes' }}</span>
            </button>
            <button @click="triggerAction('openCreatePendencyModal')" class="menu-item">
              <ClipboardListIcon :size="15" />
              <span>Criar Pendência</span>
            </button>
            <button @click="handlePrintConversation" class="menu-item">
              <PrinterIcon :size="15" />
              <span>Imprimir / Exportar Histórico</span>
            </button>
            <div class="divider" v-if="activeTicket.status !== 'closed'"></div>
            <button v-if="activeTicket.status !== 'closed'" @click="triggerAction('openPriorityModal')" class="menu-item">
              <span class="priority-dot-indicator" :class="activeTicket.priority"></span>
              <span>Prioridade {{ activeTicket.priority === 'high' ? 'Alta' : (activeTicket.priority === 'medium' ? 'Média' : 'Baixa') }}</span>
            </button>
            <button v-if="activeTicket.status !== 'closed'" @click="showReminderModal = true; showMenu = false" class="menu-item">
              <AlarmClockIcon :size="15" />
              <span>{{ activeReminder ? 'Editar Lembrete / Follow-up' : 'Agendar Follow-up' }}</span>
            </button>
            <div class="divider"></div>
            <button @click="triggerAction('openDeleteModal')" class="menu-item danger-item">
              <TrashIcon :size="15" />
              <span>Excluir Atendimento</span>
            </button>
            <button @click="closeActiveChat" class="menu-item">
              <XIcon :size="15" />
              <span>Fechar Janela</span>
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Modal de Lembrete / Follow-up -->
    <TicketReminderModal 
      :show="showReminderModal" 
      :ticket="activeTicket" 
      @close="showReminderModal = false" 
    />
  </header>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '../../../store/chat'
import TicketReminderModal from './TicketReminderModal.vue'
import {
  ChevronLeft as ChevronLeftIcon,
  Sparkles as SparklesIcon,
  MoreVertical as MoreVerticalIcon,
  Contact as ContactIcon,
  ArrowRightLeft as TransferIcon,
  CheckCircle2 as CheckIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  ClipboardList as ClipboardListIcon,
  Lock as LockIcon,
  Search as SearchIcon,
  Printer as PrinterIcon,
  Clock as ClockIcon,
  AlarmClock as AlarmClockIcon
} from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean,
  isSearchActive: Boolean
})

const emit = defineEmits([
  'update:showCRM',
  'openPriorityModal',
  'openTransferModal',
  'openCloseModal',
  'openDeleteModal',
  'openImage',
  'setCRMTab',
  'openCreatePendencyModal',
  'toggleSearch',
  'printConversation'
])

const chatStore = useChatStore()
const activeTicket = computed(() => chatStore.activeTicket || {})
const showReminderModal = ref(false)

const activeReminder = computed(() => {
  return activeTicket.value?.active_reminder || null
})

const formatReminderTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

const formatShortReminderTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const today = new Date()
    const isToday = d.toDateString() === today.toDateString()
    const hours = String(d.getHours()).padStart(2, '0')
    const mins = String(d.getMinutes()).padStart(2, '0')
    if (isToday) return `${hours}:${mins}`
    return `${d.getDate()}/${d.getMonth() + 1} ${hours}:${mins}`
  } catch {
    return ''
  }
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

const handlePrintConversation = () => {
  showMenu.value = false
  emit('printConversation')
}
const isCustomerBlocked = computed(() => {
  return !!(
    activeTicket.value?.customer_details?.is_blocked ||
    activeTicket.value?.contact_details?.customer_details?.is_blocked
  )
})
const imageError = ref(false)
const showMenu = ref(false)
const dropdownRef = ref(null)

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const toggleCopilot = () => {
  // If CRM details panel is already open, and active tab is Copilot, toggle CRM off.
  // Otherwise, open CRM and set active tab to Copilot
  emit('setCRMTab', 'copilot')
}

const emitCRMAction = () => {
  showMenu.value = false
  emit('update:showCRM', !props.showCRM)
}

const triggerAction = (actionName) => {
  showMenu.value = false
  emit(actionName)
}

const openAvatarImage = () => {
  if (activeTicket.value?.contact_details?.profile_pic && !imageError.value) {
    emit('openImage', activeTicket.value.contact_details.profile_pic)
  }
}

watch(() => activeTicket.value?.id, (newId) => {
  imageError.value = false
  if (activeTicket.value?.contact_details?.id && !activeTicket.value.contact_details.profile_pic) {
    chatStore.fetchContactAvatar(activeTicket.value.contact_details.id)
  }
}, { immediate: true })

watch(() => activeTicket.value?.contact_details?.profile_pic, () => {
  imageError.value = false
})

const handleImageError = () => {
  imageError.value = true
  if (activeTicket.value?.contact_details?.id) {
    chatStore.fetchContactAvatar(activeTicket.value.contact_details.id, true)
  }
}

const goBack = () => {
  chatStore.activeTicket = null
}

const closeActiveChat = () => {
  showMenu.value = false
  chatStore.activeTicket = null
}

const handleAccept = async () => {
  if (!activeTicket.value.id) return
  await chatStore.acceptTicket(activeTicket.value.id)
  emit('openPriorityModal')
}

const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    showMenu.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.chat-header {
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  height: 70px;
}

.mobile-back-btn {
  display: none;
  background: none;
  border: none;
  color: var(--text-primary);
  margin-right: 12px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .mobile-back-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-text {
    display: none;
  }

  .transfer-btn,
  .close-ticket-btn {
    width: 38px;
    height: 38px;
    padding: 0;
    justify-content: center;
    gap: 0;
  }

  .chat-header {
    padding: 10px 16px;
  }
}

.contact-info {
  display: flex;
  align-items: center;
  min-width: 0;
}

/* Avatar wrapper for platform badge overlap */
.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
  margin-right: 12px;
}

.avatar {
  width: 42px;
  height: 42px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.2s ease;
}

.avatar.clickable {
  cursor: pointer;
}

.avatar.clickable:hover {
  transform: scale(1.05);
  border-color: var(--accent);
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
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #25d366;
  border: 2px solid var(--bg-sidebar);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
}

.platform-badge-svg {
  width: 100%;
  height: 100%;
}

.header-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.name-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-status h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.company-badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent);
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 2px 8px;
  border-radius: 6px;
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  vertical-align: middle;
}

.status-dot-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot-indicator.open {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

.status-dot-indicator.pending {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
}

.status-dot-indicator.closed {
  background: #71717a;
}

.ticket-subject {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin: 2px 0 0 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
}

/* Header Actions row */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.accept-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.accept-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.copilot-btn,
.chat-action-icon-btn,
.more-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chat-action-icon-btn:hover,
.more-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.chat-action-icon-btn.active {
  background: rgba(16, 185, 129, 0.15);
  border-color: var(--accent);
  color: var(--accent);
}

.transfer-btn,
.close-ticket-btn {
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.transfer-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.transfer-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.close-ticket-btn {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: var(--accent);
}

.close-ticket-btn:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: var(--accent);
  transform: translateY(-1px);
}

.copilot-btn:hover {
  background: rgba(34, 181, 95, 0.1);
  color: #60a5fa;
  border-color: rgba(34, 181, 95, 0.2);
  transform: translateY(-1px);
}

.copilot-btn.active {
  background: var(--brand-gradient);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(34, 181, 95, 0.3);
}

/* Dropdown styling */
.dropdown-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 45px;
  right: 0;
  width: 210px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.88rem;
  font-weight: 600;
  width: 100%;
  cursor: pointer;
  transition: background 0.2s ease;
  text-align: left;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.menu-item.success-item {
  color: var(--accent);
}

.menu-item.success-item:hover {
  background: rgba(16, 185, 129, 0.1);
}

.menu-item.danger-item {
  color: #f87171;
}

.menu-item.danger-item:hover {
  background: rgba(239, 68, 68, 0.1);
}

.divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.priority-dot-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.priority-dot-indicator.low {
  background: #71717a;
}

.priority-dot-indicator.medium {
  background: #f59e0b;
}

.priority-dot-indicator.high {
  background: #ef4444;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.blocked-header-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}

.sla-header-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.sla-header-badge.sla-ok {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.sla-header-badge.sla-warning {
  background: rgba(245, 158, 11, 0.18);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.sla-header-badge.sla-critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
  animation: pulse-sla 1.8s infinite ease-in-out;
}

@keyframes pulse-sla {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.03); }
}

.reminder-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 11px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  border-radius: 8px;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.78rem;
  font-weight: 500;
  height: 34px;
}

.reminder-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-main, #f8fafc);
  transform: translateY(-1px);
}

.reminder-action-btn.has-active-reminder {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.4);
  color: #fbbf24;
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.25);
  animation: reminderPulse 2s infinite ease-in-out;
}

.reminder-action-btn.has-active-reminder:hover {
  background: rgba(245, 158, 11, 0.25);
  border-color: #f59e0b;
}

.reminder-time-badge {
  font-size: 0.74rem;
  font-weight: 600;
  color: #fbbf24;
  letter-spacing: 0.3px;
}

@keyframes reminderPulse {
  0%, 100% { box-shadow: 0 0 8px rgba(245, 158, 11, 0.2); }
  50% { box-shadow: 0 0 16px rgba(245, 158, 11, 0.45); }
}

@media (max-width: 768px) {
  .reminder-action-btn .btn-text {
    display: none;
  }
}
</style>

