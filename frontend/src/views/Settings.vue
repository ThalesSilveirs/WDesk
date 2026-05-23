<template>
  <div class="settings-page-container animate-fade-in">

    <main class="settings-content">
      <header class="settings-header glass-effect">
        <div class="header-title">
          <SettingsIcon :size="32" class="icon-accent" />
          <div>
            <h1>Configurações do Sistema</h1>
            <p>Gerencie as integrações e parâmetros da plataforma</p>
          </div>
        </div>
      </header>

      <div class="settings-grid">
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
                class="premium-input"
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
                  class="premium-input"
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
    </main>

    <!-- Modal de Confirmação de Reset -->
    <div v-if="confirmReset" class="modal-overlay">
      <div class="modal-content glass-effect danger-modal">
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
            class="premium-input" 
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
  AlertTriangle as AlertIcon
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
  evolution_api_key: ''
})

const webhookUrl = computed(() => {
  return `/api/v1/webhooks/evolution/`
})

const fetchSettings = async () => {
  try {
    const data = await chatStore.fetchCompanySettings()
    settings.value.evolution_api_url = data.evolution_api_url || ''
    settings.value.evolution_api_key = data.evolution_api_key || ''
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
    await chatStore.resetConversations()
    confirmReset.value = false
    alert("Todas as conversas foram apagadas com sucesso.")
  } catch (e) {
    console.error("Erro no reset:", e)
    const errorMsg = e.response?.data?.error || e.response?.data?.detail || e.message
    alert("Erro ao zerar conversas: " + errorMsg)
  } finally {
    reseting.value = false
  }
}



onMounted(fetchSettings)
</script>

<style scoped>
.settings-page-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
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
  color: #94a3b8;
  margin-bottom: 10px;
}

.premium-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 12px 16px;
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 1rem;
  outline: none;
  transition: all 0.2s;
}

.premium-input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
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
  color: #64748b;
}

.readonly-box {
  background: rgba(0, 0, 0, 0.2);
  padding: 12px 16px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
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
