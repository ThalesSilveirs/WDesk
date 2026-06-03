<template>
  <header class="chat-header glass-effect">
    <div class="contact-info">
      <button class="mobile-back-btn" @click="goBack" title="Voltar">
        <ChevronLeftIcon :size="24" />
      </button>
      <div class="avatar small">
        <img v-if="activeTicket.contact_details?.profile_pic" :src="activeTicket.contact_details.profile_pic" class="avatar-img" />
        <span v-else>{{ activeTicket.contact_details?.name?.charAt(0) }}</span>
      </div>
      <div class="header-text">
        <div class="name-status">
          <h3>{{ activeTicket.contact_details?.name }}</h3>
          <span class="status-tag" :class="activeTicket.status">
            {{ activeTicket.status === 'open' ? 'Em aberto' : (activeTicket.status === 'pending' ? 'Pendente' : 'Finalizado') }}
          </span>
        </div>
        <p class="ticket-subject">{{ activeTicket.subject || 'Sem assunto definido' }}</p>
      </div>
    </div>
    <div class="header-actions">
      <div v-if="activeTicket.status !== 'closed'" class="priority-selector">
        <button @click="emit('openPriorityModal')" class="btn-outline-sm priority-btn" :class="activeTicket.priority">
          <span class="dot"></span>
          <span>Prioridade {{ activeTicket.priority === 'high' ? 'Alta' : (activeTicket.priority === 'medium' ? 'Média' : 'Baixa') }}</span>
        </button>
      </div>

      <button @click="emit('update:showCRM', !showCRM)" class="btn-outline-sm" :class="{ active: showCRM }" title="Informações do Cliente">
        <ContactIcon :size="18" />
        <span>Info</span>
      </button>

      <button @click="emit('openDeleteModal')" class="btn-danger-sm" title="Excluir Atendimento">
        <TrashIcon :size="18" />
        <span>Excluir</span>
      </button>

      <template v-if="activeTicket.status !== 'closed'">
        <button v-if="!activeTicket.user" @click="handleAccept" class="accept-btn">
          <CheckIcon :size="18" />
          Aceitar Atendimento
        </button>
        <div v-else class="action-group">
          <button @click="emit('openTransferModal')" class="btn-outline-sm" title="Transferir Atendimento">
            <TransferIcon :size="18" />
            <span>Transferir</span>
          </button>
          <button @click="emit('openCloseModal')" class="btn-success-sm">
            <CheckIcon :size="18" />
            <span>Finalizar</span>
          </button>
        </div>
      </template>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../../../store/chat'
import {
  Contact as ContactIcon,
  CheckCircle as CheckIcon,
  ArrowRightLeft as TransferIcon,
  ChevronLeft as ChevronLeftIcon,
  Trash2 as TrashIcon
} from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits([
  'update:showCRM',
  'openPriorityModal',
  'openTransferModal',
  'openCloseModal',
  'openDeleteModal'
])

const chatStore = useChatStore()
const activeTicket = computed(() => chatStore.activeTicket || {})

const goBack = () => {
  chatStore.activeTicket = null
}

const handleAccept = async () => {
  if (!activeTicket.value.id) return
  await chatStore.acceptTicket(activeTicket.value.id)
  emit('openPriorityModal')
}
</script>

<style scoped>
.chat-header {
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
}

.mobile-back-btn {
  display: none;
  background: none;
  border: none;
  color: var(--text-primary);
  margin-right: 15px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .mobile-back-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.contact-info {
  display: flex;
  align-items: center;
}

.avatar {
  width: 50px;
  height: 50px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar.small {
  width: 40px;
  height: 40px;
  font-size: 1rem;
}

.header-text {
  margin-left: 10px;
}

.name-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-tag {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  text-transform: uppercase;
  font-weight: 700;
}

.status-tag.open {
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-tag.pending {
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-tag.closed {
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 768px) {
  .chat-header {
    padding: 10px;
    flex-wrap: wrap;
    gap: 10px;
  }
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  .priority-selector span:last-child {
    display: none;
  }
  .btn-outline-sm span:last-child,
  .btn-success-sm span:last-child {
    display: none;
  }
  .accept-btn span {
    font-size: 0.8rem;
  }
}

.ticket-subject {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 2px;
  text-align: left;
}

.priority-selector {
  display: flex;
  align-items: center;
}

.priority-btn .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

.priority-btn.low .dot {
  background: #94a3b8;
}

.priority-btn.medium .dot {
  background: #f59e0b;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
}

.priority-btn.high .dot {
  background: #ef4444;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.5);
}

.btn-outline-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-outline-sm:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.btn-outline-sm.active {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
  border-color: var(--accent);
}

.action-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-success-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.btn-success-sm:hover {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.btn-danger-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: #f87171;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-danger-sm:hover {
  background: #ef4444;
  color: white;
  border-color: #ef4444;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}

.accept-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 18px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
  display: flex;
  align-items: center;
  gap: 8px;
}

.accept-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}

.accept-btn:active {
  transform: translateY(0) scale(0.98);
}
</style>
