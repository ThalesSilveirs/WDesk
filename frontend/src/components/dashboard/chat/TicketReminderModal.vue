<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay animate-fade-in" @click="closeModal">
      <div class="modal-content glass-effect reminder-modal" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <div class="header-icon-wrapper">
          <ClockIcon :size="22" class="header-icon" />
        </div>
        <div class="header-titles">
          <h3>Lembrete de Retorno (Follow-up)</h3>
          <p v-if="ticket">Cliente: <strong>{{ customerName }}</strong> (Ticket #{{ ticket.id }})</p>
        </div>
        <button class="close-btn-round" @click="closeModal" title="Fechar">
          <XIcon :size="18" />
        </button>
      </div>

      <div class="modal-body">
        <!-- Alerta sobre o WhatsApp do atendente -->
        <div v-if="userWhatsApp" class="whatsapp-badge success">
          <SmartphoneIcon :size="16" />
          <span>Notificação via WhatsApp para: <strong>{{ formattedUserWhatsApp }}</strong></span>
        </div>
        <div v-else class="whatsapp-badge warning">
          <AlertCircleIcon :size="16" />
          <span>Você não tem WhatsApp cadastrado no seu perfil. O alerta será emitido na tela, mas cadastre seu número em Perfil para receber no WhatsApp.</span>
        </div>

        <!-- Lembrete Ativo Atual (se houver) -->
        <div v-if="activeReminder" class="active-reminder-box">
          <div class="active-reminder-header">
            <div class="active-tag">
              <span class="pulse-dot"></span>
              Lembrete Agendado Ativo
            </div>
            <button 
              class="cancel-reminder-btn" 
              :disabled="loadingCancel"
              @click="handleCancelReminder"
              title="Excluir este agendamento"
            >
              <Trash2Icon :size="14" />
              <span>{{ loadingCancel ? 'Cancelando...' : 'Remover Lembrete' }}</span>
            </button>
          </div>
          <div class="active-reminder-details">
            <div class="detail-row">
              <CalendarIcon :size="15" />
              <span><strong>Horário:</strong> {{ formatDateTime(activeReminder.scheduled_for) }}</span>
            </div>
            <div v-if="activeReminder.note" class="detail-row">
              <FileTextIcon :size="15" />
              <span><strong>Nota:</strong> {{ activeReminder.note }}</span>
            </div>
          </div>
        </div>

        <div class="section-divider" v-if="activeReminder">
          <span>Reagendar ou Definir Novo Horário</span>
        </div>

        <!-- Presets Rápidos -->
        <div class="form-group">
          <label class="form-label">
            <SparklesIcon :size="14" />
            Sugestões Rápidas de Horário
          </label>
          <div class="presets-grid">
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === '30m' }"
              @click="applyPreset('30m')"
            >
              ⚡ +30 min
            </button>
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === '1h' }"
              @click="applyPreset('1h')"
            >
              ⚡ +1 hora
            </button>
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === '3h' }"
              @click="applyPreset('3h')"
            >
              ⚡ +3 horas
            </button>
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === 'tomorrow_9' }"
              @click="applyPreset('tomorrow_9')"
            >
              📅 Amanhã 09:00
            </button>
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === 'tomorrow_14' }"
              @click="applyPreset('tomorrow_14')"
            >
              📅 Amanhã 14:00
            </button>
            <button 
              type="button"
              class="preset-chip" 
              :class="{ selected: selectedPreset === 'custom' }"
              @click="applyPreset('custom')"
            >
              🗓️ Personalizado
            </button>
          </div>
        </div>

        <!-- Input Data/Hora Personalizada -->
        <div class="form-group">
          <label class="form-label">
            <CalendarIcon :size="14" />
            Data e Hora do Retorno
          </label>
          <input 
            type="datetime-local" 
            v-model="scheduledFor" 
            class="custom-datetime-input"
            :min="minDateTime"
            required
          />
        </div>

        <!-- Observação / Motivo -->
        <div class="form-group">
          <label class="form-label">
            <FileTextIcon :size="14" />
            Anotação / Motivo do Follow-up (opcional)
          </label>
          <textarea 
            v-model="note" 
            placeholder="Ex: Ligar para confirmar se o cliente recebeu a proposta ou se tem dúvidas sobre o plano..." 
            rows="3" 
            class="custom-textarea"
            maxlength="400"
          ></textarea>
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="closeModal" :disabled="loading">
          Cancelar
        </button>
        <button 
          type="button" 
          class="btn-primary" 
          :disabled="loading || !scheduledFor"
          @click="handleSaveReminder"
        >
          <BellIcon :size="16" v-if="!loading" />
          <span>{{ loading ? 'Salvando...' : 'Agendar Lembrete' }}</span>
        </button>
      </div>
    </div>
  </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  Clock as ClockIcon, 
  X as XIcon, 
  Smartphone as SmartphoneIcon, 
  AlertCircle as AlertCircleIcon,
  Sparkles as SparklesIcon,
  Calendar as CalendarIcon,
  FileText as FileTextIcon,
  Trash2 as Trash2Icon,
  Bell as BellIcon
} from 'lucide-vue-next'
import { useChatStore } from '../../../store/chat'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  ticket: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'reminder-saved', 'reminder-cancelled'])
const chatStore = useChatStore()

const scheduledFor = ref('')
const note = ref('')
const selectedPreset = ref('1h')
const loading = ref(false)
const loadingCancel = ref(false)

const customerName = computed(() => {
  if (!props.ticket) return 'Cliente'
  return props.ticket.contact_details?.name || 
         props.ticket.contact?.name || 
         props.ticket.contact_details?.phone || 
         props.ticket.contact?.phone || 
         'Cliente'
})

const userWhatsApp = computed(() => {
  return chatStore.user?.whatsapp || ''
})

const formattedUserWhatsApp = computed(() => {
  const raw = userWhatsApp.value.replace(/\D/g, '')
  if (raw.length === 11) {
    return `(${raw.slice(0, 2)}) ${raw.slice(2, 7)}-${raw.slice(7)}`
  }
  if (raw.length === 10) {
    return `(${raw.slice(0, 2)}) ${raw.slice(2, 6)}-${raw.slice(6)}`
  }
  return userWhatsApp.value
})

const activeReminder = computed(() => {
  return props.ticket?.active_reminder || null
})

const minDateTime = computed(() => {
  const now = new Date()
  return now.toISOString().slice(0, 16)
})

const formatDateTime = (dtStr) => {
  if (!dtStr) return ''
  try {
    const d = new Date(dtStr)
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dtStr
  }
}

// Inicializa com +1 hora por padrão
const applyPreset = (preset) => {
  selectedPreset.value = preset
  const now = new Date()

  if (preset === '30m') {
    now.setMinutes(now.getMinutes() + 30)
    scheduledFor.value = formatToLocalISO(now)
  } else if (preset === '1h') {
    now.setHours(now.getHours() + 1)
    scheduledFor.value = formatToLocalISO(now)
  } else if (preset === '3h') {
    now.setHours(now.getHours() + 3)
    scheduledFor.value = formatToLocalISO(now)
  } else if (preset === 'tomorrow_9') {
    now.setDate(now.getDate() + 1)
    now.setHours(9, 0, 0, 0)
    scheduledFor.value = formatToLocalISO(now)
  } else if (preset === 'tomorrow_14') {
    now.setDate(now.getDate() + 1)
    now.setHours(14, 0, 0, 0)
    scheduledFor.value = formatToLocalISO(now)
  }
}

const formatToLocalISO = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    if (activeReminder.value) {
      // Se já tem lembrete ativo, carrega a data existente
      try {
        const d = new Date(activeReminder.value.scheduled_for)
        scheduledFor.value = formatToLocalISO(d)
      } catch {
        applyPreset('1h')
      }
      note.value = activeReminder.value.note || ''
      selectedPreset.value = 'custom'
    } else {
      note.value = ''
      applyPreset('1h')
    }
  }
})

const closeModal = () => {
  emit('close')
}

const handleSaveReminder = async () => {
  if (!scheduledFor.value || !props.ticket) return
  loading.value = true
  try {
    const isoString = new Date(scheduledFor.value).toISOString()
    const res = await chatStore.createTicketReminder(props.ticket.id, {
      scheduled_for: isoString,
      note: note.value.trim()
    })
    emit('reminder-saved', res)
    closeModal()
  } catch (e) {
    console.error("Erro ao salvar lembrete:", e)
    const err = e.response?.data?.error || "Erro ao agendar lembrete"
    alert(err)
  } finally {
    loading.value = false
  }
}

const handleCancelReminder = async () => {
  if (!props.ticket) return
  if (!confirm("Deseja realmente remover o lembrete deste atendimento?")) return
  loadingCancel.value = true
  try {
    await chatStore.cancelTicketReminder(props.ticket.id)
    emit('reminder-cancelled')
    closeModal()
  } catch (e) {
    console.error("Erro ao cancelar lembrete:", e)
    alert("Erro ao cancelar lembrete.")
  } finally {
    loadingCancel.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  padding: 16px;
  box-sizing: border-box;
}

.reminder-modal {
  width: 100%;
  max-width: 500px;
  background: var(--bg-card, #1e293b);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUpModal 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUpModal {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  background: rgba(255, 255, 255, 0.02);
}

.header-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(234, 88, 12, 0.25));
  color: #f59e0b;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.header-titles {
  flex: 1;
}

.header-titles h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-main, #f8fafc);
}

.header-titles p {
  font-size: 0.8rem;
  margin: 2px 0 0;
  color: var(--text-muted, #94a3b8);
}

.close-btn-round {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn-round:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-height: 75vh;
  overflow-y: auto;
}

.whatsapp-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 0.82rem;
  line-height: 1.35;
}

.whatsapp-badge.success {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: #4ade80;
}

.whatsapp-badge.warning {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.25);
  color: #fbbf24;
}

.active-reminder-box {
  background: rgba(245, 158, 11, 0.07);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 12px;
  padding: 14px;
}

.active-reminder-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.active-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #f59e0b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
  animation: pulseDot 1.5s infinite;
}

@keyframes pulseDot {
  0% { transform: scale(0.95); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.7; }
}

.cancel-reminder-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-reminder-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  color: #fca5a5;
}

.active-reminder-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.83rem;
  color: var(--text-main, #e2e8f0);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: var(--text-muted, #94a3b8);
  font-size: 0.75rem;
  margin: 4px 0;
}

.section-divider::before,
.section-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
}

.section-divider span {
  padding: 0 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-main, #cbd5e1);
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

@media (max-width: 450px) {
  .presets-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.preset-chip {
  padding: 9px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 9px;
  color: var(--text-main, #e2e8f0);
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preset-chip:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.preset-chip.selected {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(234, 88, 12, 0.3));
  border-color: #f59e0b;
  color: #fbbf24;
  font-weight: 600;
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.25);
}

.custom-datetime-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  border-radius: 10px;
  color: var(--text-main, #f8fafc);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.2s;
}

.custom-datetime-input:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
}

.custom-textarea {
  width: 100%;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  border-radius: 10px;
  color: var(--text-main, #f8fafc);
  font-size: 0.85rem;
  line-height: 1.4;
  outline: none;
  resize: vertical;
  transition: border-color 0.2s;
}

.custom-textarea:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  background: rgba(0, 0, 0, 0.15);
}

.btn-secondary {
  padding: 9px 16px;
  border-radius: 9px;
  background: transparent;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  color: var(--text-main, #e2e8f0);
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.06);
}

.btn-primary {
  padding: 9px 18px;
  border-radius: 9px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border: none;
  color: #fff;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
