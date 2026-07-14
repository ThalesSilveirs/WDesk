<template>
  <div class="settings-page-container animate-fade-in">

    <main class="settings-content">

      <div class="settings-grid">
        <!-- Coluna Esquerda (Configurações) -->
        <div class="settings-col-left">
          <!-- Seção Evolution API -->
          <section class="settings-section glass-effect">
            <div class="section-header">
              <ZapIcon :size="24" class="icon-warning" />
              <h2>Evolution API (Evolution GO)</h2>
            </div>
            <p class="section-desc">Configure os parâmetros de conexão com o gateway do WhatsApp.</p>

            <div class="form-container">
              <div class="form-group">
                <label>URL da API</label>
                <input 
                  v-model="settings.evolution_api_url" 
                  type="text" 
                  placeholder="Ex: http://seu-servidor:8080"
                  class="input-glass premium-input"
                />
                <small>Endereço base onde a Evolution API está rodando.</small>
              </div>

              <div class="form-group">
                <label>Chave de API (Global)</label>
                <div class="input-with-icon">
                  <input 
                    :type="showKey ? 'text' : 'password'" 
                    v-model="settings.evolution_api_key" 
                    placeholder="Sua Global API Key"
                    class="input-glass premium-input"
                  />
                  <button @click="showKey = !showKey" class="icon-toggle">
                    <EyeIcon v-if="!showKey" :size="18" />
                    <EyeOffIcon v-else :size="18" />
                  </button>
                </div>
                <small>Chave mestre para autenticação nas instâncias.</small>
              </div>

              <div class="form-group">
                <label>Webhook Global (Somente Leitura)</label>
                <div class="readonly-box">
                  <code>{{ webhookUrl }}</code>
                  <button @click="copyWebhook" class="copy-btn">
                    <CopyIcon :size="16" />
                  </button>
                </div>
                <small>Configure este endereço na Evolution API para receber eventos em tempo real.</small>
              </div>

              <div class="action-bar">
                <button @click="saveSettings" class="btn-primary" :disabled="saving">
                  <SaveIcon :size="20" />
                  {{ saving ? 'Salvando...' : 'Salvar Configurações' }}
                </button>
                <span v-if="saveSuccess" class="success-msg animate-pop">Configurações salvas com sucesso!</span>
              </div>
            </div>
          </section>

          <!-- Seção Respostas Rápidas -->
          <section class="settings-section glass-effect">
            <div class="section-header" style="justify-content: space-between; display: flex; align-items: center; width: 100%;">
              <div style="display: flex; align-items: center; gap: 15px;">
                <MessageIcon :size="24" style="color: #3b82f6;" />
                <h2>Respostas Rápidas</h2>
              </div>
              <button v-if="!showReplyForm" @click="openNewReplyForm" class="btn-secondary-sm">
                <PlusIcon :size="16" /> Nova Resposta
              </button>
            </div>
            <p class="section-desc">Crie atalhos para responder mensagens comuns rapidamente.</p>

            <!-- Form para Criar/Editar -->
            <div v-if="showReplyForm" class="form-container sub-form glass-effect">
              <h3>{{ editingReplyId ? 'Editar Resposta Rápida' : 'Nova Resposta Rápida' }}</h3>
              <div class="form-group" style="margin-top: 15px;">
                <label>Atalho (Sem a barra "/")</label>
                <input 
                  v-model="replyForm.title" 
                  type="text" 
                  placeholder="Ex: bomdia"
                  class="input-glass premium-input"
                />
                <small>Digite a palavra-chave que acionará esta resposta (ex: /bomdia).</small>
              </div>
              <div class="form-group">
                <label>Conteúdo da Mensagem</label>
                <textarea 
                  v-model="replyForm.body" 
                  rows="4"
                  placeholder="Ex: Olá, tudo bem? Como posso te ajudar hoje?"
                  class="input-glass premium-input"
                />
              </div>
              <div class="action-bar-sm">
                <button @click="saveReply" class="btn-primary-sm" :disabled="savingReply">
                  <CheckIcon :size="16" /> {{ savingReply ? 'Salvando...' : 'Salvar' }}
                </button>
                <button @click="closeReplyForm" class="btn-ghost-sm" :disabled="savingReply">
                  Cancelar
                </button>
              </div>
            </div>

            <!-- Tabela de Respostas Rápidas -->
            <div v-else class="replies-table-container">
              <div v-if="quickReplies.length === 0" class="empty-state">
                Nenhuma resposta rápida cadastrada. Comece adicionando uma!
              </div>
              <table v-else class="premium-table">
                <thead>
                  <tr>
                    <th>Atalho</th>
                    <th>Mensagem</th>
                    <th style="text-align: right;">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="reply in quickReplies" :key="reply.id">
                    <td><span class="shortcut-badge">/{{ reply.title }}</span></td>
                    <td class="reply-text-col" :title="reply.body">{{ reply.body }}</td>
                    <td style="text-align: right;">
                      <div style="display: flex; justify-content: flex-end; gap: 8px;">
                        <button @click="editReply(reply)" class="action-icon-btn edit" title="Editar">
                          <EditIcon :size="16" />
                        </button>
                        <button @click="deleteReply(reply.id)" class="action-icon-btn delete" title="Apagar">
                          <TrashIcon :size="16" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Seção Horário de Ausência -->
          <section class="settings-section glass-effect">
            <div class="section-header">
              <ClockIcon :size="24" style="color: #ef4444;" />
              <h2>Horário de Atendimento & Ausência</h2>
            </div>
            <p class="section-desc">Defina os horários de expediente e a mensagem automática de ausência da sua empresa.</p>

            <div class="form-container">
              <div class="form-group flex-row">
                <label class="switch-container">
                  <input type="checkbox" v-model="absence.enabled" />
                  <span class="switch-slider"></span>
                  <span class="switch-label">Enviar mensagem de ausência fora do expediente</span>
                </label>
              </div>

              <div class="form-group">
                <label>Fuso Horário</label>
                <select v-model="absence.timezone" class="input-glass premium-input">
                  <option value="America/Sao_Paulo">Brasília (America/Sao_Paulo)</option>
                  <option value="America/Manaus">Manaus (America/Manaus)</option>
                  <option value="America/Fortaleza">Fortaleza (America/Fortaleza)</option>
                  <option value="America/New_York">New York (America/New_York)</option>
                  <option value="Europe/London">London (Europe/London)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Mensagem de Ausência</label>
                <textarea 
                  v-model="absence.message" 
                  rows="3"
                  placeholder="Ex: Olá! No momento estamos fora do nosso horário de expediente..."
                  class="input-glass premium-input"
                />
              </div>

              <!-- Grade da Agenda Semanal -->
              <div class="form-group">
                <label>Horário de Expediente por Dia</label>
                <div class="schedule-grid">
                  <div 
                    v-for="(day, index) in weekDays" 
                    :key="index" 
                    class="schedule-day-row"
                    :class="{ inactive: !getDaySchedule(index).active }"
                  >
                    <div class="day-checkbox-label">
                      <input 
                        type="checkbox" 
                        v-model="getDaySchedule(index).active"
                      />
                      <span>{{ day }}</span>
                    </div>
                    
                    <div v-if="getDaySchedule(index).active" class="time-pickers">
                      <input 
                        type="time" 
                        v-model="getDaySchedule(index).start"
                        class="time-input"
                      />
                      <span class="time-separator">até</span>
                      <input 
                        type="time" 
                        v-model="getDaySchedule(index).end"
                        class="time-input"
                      />
                    </div>
                    <div v-else class="day-closed-text">
                      Fechado o dia todo
                    </div>
                  </div>
                </div>
              </div>

              <div class="action-bar">
                <button @click="saveAbsenceSettings" class="btn-primary" :disabled="savingAbsence">
                  <SaveIcon :size="20" />
                  {{ savingAbsence ? 'Salvando...' : 'Salvar Agenda e Mensagem' }}
                </button>
                <span v-if="saveAbsenceSuccess" class="success-msg animate-pop">Configurações salvas com sucesso!</span>
              </div>
            </div>
          </section>

          <!-- Seção Relatório de Pendências -->
          <section class="settings-section glass-effect">
            <div class="section-header">
              <ClipboardIcon :size="24" style="color: var(--accent);" />
              <h2>Relatório Diário de Pendências</h2>
            </div>
            <p class="section-desc">Defina o horário de envio automático e filtros de notificação para o WhatsApp dos atendentes.</p>

            <div class="form-container">
              <div class="form-group">
                <label>Horário de Envio Automático</label>
                <input 
                  v-model="settings.pendency_report_time" 
                  type="time" 
                  class="input-glass premium-input"
                  style="max-width: 150px; font-family: monospace;"
                />
                <small>Horário em que a mensagem de relatório de pendências do dia será disparada automaticamente.</small>
              </div>

              <div class="form-group flex-row">
                <label class="switch-container">
                  <input type="checkbox" v-model="settings.pendency_report_only_support" />
                  <span class="switch-slider"></span>
                  <span class="switch-label">Enviar apenas pendências com tipo de operação "Suporte"</span>
                </label>
              </div>

              <div class="action-bar" style="margin-top: 30px;">
                <button @click="saveSettings" class="btn-primary" :disabled="saving">
                  <SaveIcon :size="20" />
                  {{ saving ? 'Salvando...' : 'Salvar Relatório e Filtros' }}
                </button>
              </div>
            </div>
          </section>

        </div>

        <!-- Coluna Direita (Status / Perigo) -->
        <div class="settings-col-right">
          <!-- Informações Adicionais -->
          <section class="settings-section glass-effect info-card">
            <div class="section-header">
              <InfoIcon :size="24" class="icon-info" />
              <h2>Status do Sistema</h2>
            </div>
            <div class="status-list">
              <div class="status-item">
                <span>Backend</span>
                <span class="status-tag online">Online</span>
              </div>
              <div class="status-item">
                <span>Realtime (Socket)</span>
                <span class="status-tag online">Conectado</span>
              </div>
              <div class="status-item">
                <span>Versão</span>
                <span class="version-label">v1.2.0-stable</span>
              </div>
            </div>
            <div class="help-box">
              <p>Precisa de ajuda com a configuração? Consulte a documentação oficial da Evolution API ou contate o suporte.</p>
            </div>
          </section>

          <!-- Zona de Perigo -->
          <section v-if="chatStore.userRole === 'admin'" class="settings-section glass-effect danger-zone">
            <div class="section-header">
              <AlertIcon :size="24" class="icon-danger" />
              <h2>Zona de Perigo</h2>
            </div>
            <p class="section-desc">Ações irreversíveis que afetam os dados da sua empresa.</p>
            
            <div class="danger-actions">
              <div class="danger-item">
                <div class="danger-text">
                  <h3>Zerar Banco de Conversas</h3>
                  <p>Apaga permanentemente todos os tickets e mensagens de todos os atendentes.</p>
                </div>
                <button @click="triggerResetModal" class="btn-danger" :disabled="reseting">
                  <TrashIcon :size="18" />
                  {{ reseting ? 'Limpando...' : 'Zerar Agora' }}
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>

    <!-- Modal de Confirmação de Reset -->
    <Transition name="modal-fade">
      <div v-if="confirmReset" class="modal-overlay" @click="confirmReset = false">
        <div class="modal-content danger-modal" @click.stop>
          <AlertIcon :size="48" class="icon-danger large" />
          <h2>Tem certeza absoluta?</h2>
          <p>Esta ação apagará **TODAS** as conversas, tickets e históricos de atendimento da sua empresa. Esta ação **não pode ser desfeita**.</p>
          
          <div style="margin-bottom: 20px; text-align: left;">
            <label style="font-size: 0.8rem; font-weight: 700; color: #ef4444; display: block; margin-bottom: 8px; text-transform: uppercase;">
              Digite "Confirmar" para prosseguir:
            </label>
            <input 
              v-model="resetTextConfirm" 
              type="text" 
              placeholder="Digite Confirmar por extenso" 
              class="input-glass premium-input" 
              style="border-color: rgba(239, 68, 68, 0.4); text-align: center;"
            />
          </div>

          <div class="modal-actions-vertical">
            <button 
              @click="handleReset" 
              class="btn-danger block" 
              :disabled="reseting || resetTextConfirm !== 'Confirmar'"
            >
              SIM, APAGAR TUDO
            </button>
            <button @click="confirmReset = false" class="btn-ghost block" :disabled="reseting">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useChatStore } from '../store/chat'
import { useRouter } from 'vue-router'
import { 
  Settings as SettingsIcon,
  Zap as ZapIcon,
  Eye as EyeIcon,
  EyeOff as EyeOffIcon,
  Save as SaveIcon,
  Copy as CopyIcon,
  Info as InfoIcon,
  Trash2 as TrashIcon,
  AlertTriangle as AlertIcon,
  MessageSquare as MessageIcon,
  Clock as ClockIcon,
  Check as CheckIcon,
  Pencil as EditIcon,
  Plus as PlusIcon,
  ClipboardList as ClipboardIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const saving = ref(false)
const reseting = ref(false)
const saveSuccess = ref(false)
const showKey = ref(false)
const confirmReset = ref(false)
const resetTextConfirm = ref('')

const triggerResetModal = () => {
  resetTextConfirm.value = ''
  confirmReset.value = true
}

const settings = ref({
  evolution_api_url: '',
  evolution_api_key: '',
  pendency_report_time: '08:00',
  pendency_report_only_support: false
})

const webhookUrl = computed(() => {
  return `/api/v1/webhooks/evolution/`
})

// === ESTADOS E MÉTODOS DE RESPOSTAS RÁPIDAS ===
const quickReplies = ref([])
const showReplyForm = ref(false)
const editingReplyId = ref(null)
const savingReply = ref(false)
const replyForm = ref({
  title: '',
  body: ''
})

const fetchQuickReplies = async () => {
  try {
    quickReplies.value = await chatStore.fetchQuickReplies()
  } catch (e) {
    console.error(e)
  }
}

const openNewReplyForm = () => {
  editingReplyId.value = null
  replyForm.value = { title: '', body: '' }
  showReplyForm.value = true
}

const editReply = (reply) => {
  editingReplyId.value = reply.id
  replyForm.value = { title: reply.title, body: reply.body }
  showReplyForm.value = true
}

const closeReplyForm = () => {
  showReplyForm.value = false
}

const saveReply = async () => {
  if (!replyForm.value.title || !replyForm.value.body) {
    alert("Preencha todos os campos da resposta rápida")
    return
  }
  
  savingReply.value = true
  try {
    if (editingReplyId.value) {
      await chatStore.updateQuickReply(editingReplyId.value, replyForm.value)
    } else {
      await chatStore.createQuickReply(replyForm.value)
    }
    await fetchQuickReplies()
    showReplyForm.value = false
  } catch (e) {
    alert("Erro ao salvar resposta rápida")
  } finally {
    savingReply.value = false
  }
}

const deleteReply = async (id) => {
  if (confirm("Tem certeza que deseja excluir esta resposta rápida?")) {
    try {
      await chatStore.deleteQuickReply(id)
      await fetchQuickReplies()
    } catch (e) {
      alert("Erro ao excluir resposta rápida")
    }
  }
}

// === ESTADOS E MÉTODOS DE MENSAGENS DE AUSÊNCIA ===
const weekDays = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
  'Domingo'
]

const absence = ref({
  enabled: false,
  message: '',
  timezone: 'America/Sao_Paulo',
  schedule: [
    { day: 0, start: '08:00', end: '18:00', active: false },
    { day: 1, start: '08:00', end: '18:00', active: false },
    { day: 2, start: '08:00', end: '18:00', active: false },
    { day: 3, start: '08:00', end: '18:00', active: false },
    { day: 4, start: '08:00', end: '18:00', active: false },
    { day: 5, start: '08:00', end: '18:00', active: false },
    { day: 6, start: '08:00', end: '18:00', active: false }
  ]
})

const getDaySchedule = (dayIdx) => {
  const item = absence.value.schedule.find(s => parseInt(s.day) === dayIdx)
  return item || { day: dayIdx, start: '08:00', end: '18:00', active: false }
}

const savingAbsence = ref(false)
const saveAbsenceSuccess = ref(false)

const fetchAbsenceSettings = async () => {
  try {
    const data = await chatStore.fetchAbsenceSchedule()
    if (data) {
      absence.value.enabled = data.enabled
      absence.value.message = data.message
      absence.value.timezone = data.timezone
      if (data.schedule && data.schedule.length > 0) {
        data.schedule.forEach(item => {
          const idx = absence.value.schedule.findIndex(s => parseInt(s.day) === parseInt(item.day))
          if (idx !== -1) {
            absence.value.schedule[idx] = { ...absence.value.schedule[idx], ...item }
          }
        })
      }
    }
  } catch (e) {
    console.error("Erro ao buscar horários de ausência", e)
  }
}

const saveAbsenceSettings = async () => {
  savingAbsence.value = true
  saveAbsenceSuccess.value = false
  try {
    absence.value.schedule.sort((a, b) => parseInt(a.day) - parseInt(b.day))
    await chatStore.updateAbsenceSchedule(absence.value)
    saveAbsenceSuccess.value = true
    setTimeout(() => { saveAbsenceSuccess.value = false }, 3000)
  } catch (e) {
    alert("Erro ao salvar horários de ausência")
  } finally {
    savingAbsence.value = false
  }
}

const fetchSettings = async () => {
  try {
    const data = await chatStore.fetchCompanySettings()
    settings.value.evolution_api_url = data.evolution_api_url || ''
    settings.value.evolution_api_key = data.evolution_api_key || ''
    let repTime = data.pendency_report_time || '08:00'
    if (repTime.length > 5) {
      repTime = repTime.slice(0, 5)
    }
    settings.value.pendency_report_time = repTime
    settings.value.pendency_report_only_support = data.pendency_report_only_support || false
  } catch (e) {
    console.error("Erro ao buscar configurações", e)
  }
}

const saveSettings = async () => {
  saving.value = true
  saveSuccess.value = false
  try {
    await chatStore.updateCompanySettings(settings.value)
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e) {
    alert("Erro ao salvar configurações")
  } finally {
    saving.value = false
  }
}

const copyWebhook = () => {
  navigator.clipboard.writeText(webhookUrl.value)
  alert("URL copiada para a área de transferência!")
}

const handleReset = async () => {
  reseting.value = true
  try {
    const res = await chatStore.resetConversations()
    confirmReset.value = false
    alert(res?.message || "O processo de limpeza foi iniciado com sucesso.")
  } catch (e) {
    console.error("Erro no reset:", e)
    const errorMsg = e.response?.data?.error || e.response?.data?.detail || e.message
    alert("Erro ao zerar conversas: " + errorMsg)
  } finally {
    reseting.value = false
  }
}

onMounted(() => {
  fetchSettings()
  fetchQuickReplies()
  fetchAbsenceSettings()
})
</script>

<style scoped>
.settings-page-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
}

.danger-modal {
  border-color: rgba(239, 68, 68, 0.3);
  text-align: center;
}

.danger-modal h2 {
  font-size: 1.4rem;
  color: #ef4444;
  margin-top: 15px;
  margin-bottom: 10px;
}

.danger-modal p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 25px;
}

.modal-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 40px;
}

.settings-header {
  padding: 30px;
  border-radius: 20px;
  margin-bottom: 30px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title h1 { font-size: 1.8rem; font-weight: 800; margin: 0; }
.header-title p { color: var(--text-secondary); margin: 5px 0 0; }

.icon-accent { color: var(--accent); }

.settings-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
}

.settings-section {
  padding: 30px;
  border-radius: 20px;
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.section-header h2 { font-size: 1.3rem; margin: 0; }
.section-desc { color: var(--text-secondary); margin-bottom: 30px; font-size: 0.95rem; }

.icon-warning { color: #f59e0b; }
.icon-info { color: var(--accent); }

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.icon-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 5px;
}

.form-group small {
  display: block;
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.readonly-box {
  background: var(--glass);
  padding: 12px 16px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--border);
}

.readonly-box code {
  font-family: 'Fira Code', monospace;
  font-size: 0.9rem;
  color: #10b981;
}

.copy-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-btn:hover { background: rgba(255, 255, 255, 0.2); }

.action-bar {
  margin-top: 40px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 14px 28px;
  border-radius: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2);
}

.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.success-msg { color: #10b981; font-weight: 600; font-size: 0.9rem; }

/* Sidebar Info Card */
.status-list { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
.status-item { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }
.status-tag { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.status-tag.online { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.version-label { color: var(--text-secondary); font-family: monospace; }

.help-box {
  margin-top: 30px;
  padding: 20px;
  background: rgba(245, 158, 11, 0.05);
  border-left: 4px solid #f59e0b;
  border-radius: 8px;
}
.help-box p { font-size: 0.85rem; color: #d97706; margin: 0; line-height: 1.5; }

/* Danger Zone */
.danger-zone {
  border: 1px solid rgba(239, 68, 68, 0.2) !important;
  background: rgba(239, 68, 68, 0.02) !important;
}

.icon-danger { color: #ef4444; }
.icon-danger.large { margin: 0 auto 20px; display: block; }

.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.danger-text h3 { font-size: 1rem; margin-bottom: 5px; color: #ef4444; }
.danger-text p { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

.btn-danger.block { width: 100%; justify-content: center; padding: 16px; }

.danger-modal {
  max-width: 400px;
  text-align: center;
}

.danger-modal h2 { margin-bottom: 15px; }
.danger-modal p { color: var(--text-secondary); margin-bottom: 30px; line-height: 1.6; }

.modal-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-ghost {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-ghost:hover { background: rgba(255, 255, 255, 0.05); }

.btn-ghost:hover { background: rgba(255, 255, 255, 0.05); }

.settings-col-left {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.settings-col-right {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* Sub Form */
.sub-form {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid var(--border);
  padding: 20px;
  border-radius: 12px;
  margin-top: 15px;
}

.action-bar-sm {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.btn-primary-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary-sm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.btn-secondary-sm {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn-secondary-sm:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-ghost-sm {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-ghost-sm:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}

/* Premium Table */
.replies-table-container {
  margin-top: 15px;
  overflow-x: auto;
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.premium-table th {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.premium-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 0.9rem;
  vertical-align: middle;
}

.shortcut-badge {
  font-size: 0.8rem;
  font-weight: 700;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  font-family: monospace;
}

.reply-text-col {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}

.action-icon-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-icon-btn:hover.edit {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.action-icon-btn:hover.delete {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
}

.empty-state {
  padding: 30px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
  border: 1px dashed var(--border);
  border-radius: 12px;
  margin-top: 15px;
}

/* Switch styling */
.flex-row {
  display: flex;
  align-items: center;
}

.switch-container {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  gap: 12px;
}

.switch-container input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.switch-slider {
  width: 48px;
  height: 24px;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border);
  border-radius: 20px;
  position: relative;
  transition: .3s;
}

.switch-slider:before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: .3s;
}

.switch-container input:checked + .switch-slider {
  background-color: var(--accent);
  border-color: rgba(16, 185, 129, 0.5);
}

.switch-container input:checked + .switch-slider:before {
  transform: translateX(24px);
}

.switch-label {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* Schedule Grid */
.schedule-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(0, 0, 0, 0.15);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  margin-top: 10px;
}

.schedule-day-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.schedule-day-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.schedule-day-row.inactive {
  opacity: 0.5;
}

.day-checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.day-checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  accent-color: var(--accent);
}

.time-pickers {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-input {
  background: var(--glass);
  border: 1px solid var(--border);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  outline: none;
  font-family: monospace;
}

.time-input:focus {
  border-color: var(--accent);
}

.time-separator {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.day-closed-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
}

/* Animations */
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
.animate-pop { animation: pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pop { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }

@media (max-width: 768px) {
  .settings-content {
    padding: 20px;
  }
  .settings-header {
    padding: 20px;
    margin-bottom: 20px;
  }
  .header-title h1 {
    font-size: 1.4rem;
  }
  .settings-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .settings-section {
    padding: 20px;
  }
  .readonly-box {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .readonly-box code {
    word-break: break-all;
    text-align: center;
  }
  .copy-btn {
    align-self: center;
    width: 100%;
    display: flex;
    justify-content: center;
  }
  .action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  .btn-primary {
    justify-content: center;
  }
  .danger-item {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  .btn-danger {
    width: 100%;
    justify-content: center;
  }
}
</style>
