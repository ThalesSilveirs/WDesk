<template>
  <div class="dashboard-content" :class="{ 'has-active-ticket': !!chatStore.activeTicket, 'has-crm-open': showCRM }">
    <!-- Sidebar -->
    <div class="sidebar-wrapper" :class="{ 'hidden-on-mobile': !!chatStore.activeTicket }">
      <TicketSidebar />
    </div>

    <!-- Chat Area -->
    <main class="chat-area" :class="{ 'with-crm': showCRM }">
      <template v-if="chatStore.activeTicket">
        <ChatWindow 
          :showCRM="showCRM"
          @update:showCRM="showCRM = $event"
          @openPriorityModal="showPriorityModal = true"
          @openTransferModal="openTransfer"
          @openCloseModal="showCloseModal = true"
          @openImage="openImage"
        />

        <CrmPanel 
          :showCRM="showCRM"
          @update:showCRM="showCRM = $event"
        />
      </template>
      
      <div v-else class="empty-state">
        <div class="empty-content">
          <img src="/logo.png" alt="WDesk Watermark" class="watermark-logo" />
          <h1>WDesk</h1>
          <p>Selecione uma conversa para começar a atender.</p>
        </div>
      </div>
    </main>

    <!-- Modal de Finalização -->
    <div v-if="showCloseModal" class="modal-overlay">
      <div class="modal-content glass-effect">
        <h2>Finalizar Atendimento</h2>
        <p style="color: var(--text-secondary); margin-bottom: 15px;">Descreva brevemente como o caso foi resolvido:</p>
        
        <div class="form-group">
          <textarea 
            v-model="resolutionSummary" 
            placeholder="Ex: O cliente foi orientado a reiniciar o roteador e o sinal voltou ao normal."
            rows="5"
            style="width: 100%; background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--border); border-radius: 10px; padding: 10px; outline: none;"
          ></textarea>
        </div>

        <div class="modal-actions" style="margin-top: 20px;">
          <button @click="showCloseModal = false" class="cancel-btn">Cancelar</button>
          <button @click="confirmClose" class="btn-success-sm" :disabled="!resolutionSummary.trim()">Confirmar e Fechar</button>
        </div>
      </div>
    </div>

    <!-- Modal de Transferência -->
    <div v-if="showTransferModal" class="modal-overlay">
      <div class="modal-content glass-effect">
        <h2>Transferir Atendimento</h2>
        <div class="attendants-list">
          <button 
            v-for="user in chatStore.attendants" 
            :key="user.id" 
            @click="confirmTransfer(user.id)"
            class="attendant-option"
          >
            <div class="avatar small">{{ user.username.charAt(0).toUpperCase() }}</div>
            <div>
              <span class="name">{{ user.first_name }} {{ user.last_name }}</span>
              <span class="dept">{{ user.department }}</span>
            </div>
          </button>
        </div>
        <div class="modal-actions"><button @click="showTransferModal = false" class="cancel-btn">Cancelar</button></div>
      </div>
    </div>

    <!-- Modal de Prioridade -->
    <div v-if="showPriorityModal" class="modal-overlay" @click="showPriorityModal = false">
      <div class="modal-content glass-effect small-modal" @click.stop>
        <h2>Definir Prioridade</h2>
        <div class="priority-options">
          <button @click="setPriority('high')" class="priority-option high">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Alta Prioridade</span>
              <span class="desc">Assuntos urgentes / Críticos</span>
            </div>
          </button>
          <button @click="setPriority('medium')" class="priority-option medium">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Média Prioridade</span>
              <span class="desc">Atendimento padrão</span>
            </div>
          </button>
          <button @click="setPriority('low')" class="priority-option low">
            <span class="dot"></span>
            <div class="opt-text">
              <span class="label">Baixa Prioridade</span>
              <span class="desc">Dúvidas gerais / Informativo</span>
            </div>
          </button>
        </div>
        <div class="modal-actions">
          <button @click="showPriorityModal = false" class="cancel-btn block">Cancelar</button>
        </div>
      </div>
    </div>

    <!-- Visualizador de Imagem -->
    <div v-if="selectedImage" class="modal-overlay image-viewer" @click="selectedImage = null">
      <button class="close-viewer"><XIcon :size="32" /></button>
      <img :src="selectedImage" class="full-image" @click.stop />
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '../store/chat'
import { X as XIcon } from 'lucide-vue-next'
import TicketSidebar from '../components/dashboard/TicketSidebar.vue'
import ChatWindow from '../components/dashboard/ChatWindow.vue'
import CrmPanel from '../components/dashboard/CrmPanel.vue'

const chatStore = useChatStore()

const showTransferModal = ref(false)
const showPriorityModal = ref(false)
const showCloseModal = ref(false)
const selectedImage = ref(null)
const showCRM = ref(false)
const resolutionSummary = ref('')

const openTransfer = () => {
  chatStore.fetchAttendants()
  showTransferModal.value = true
}

const confirmTransfer = async (userId) => {
  await chatStore.transferTicket(chatStore.activeTicket.id, userId)
  showTransferModal.value = false
}

const confirmClose = async () => {
  if (!resolutionSummary.value.trim()) return
  await chatStore.closeTicket(chatStore.activeTicket.id, resolutionSummary.value)
  showCloseModal.value = false
  resolutionSummary.value = ''
}

const updateTicketPriority = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    priority: chatStore.activeTicket.priority
  })
}

const setPriority = async (level) => {
  if (!chatStore.activeTicket) return
  chatStore.activeTicket.priority = level
  await updateTicketPriority()
  showPriorityModal.value = false
}

const openImage = (url) => { selectedImage.value = url }

onMounted(() => {
  chatStore.fetchTickets()
  chatStore.fetchMyTickets()
  chatStore.initSocket()
})
</script>

<style scoped>
.dashboard-content {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  display: flex;
  background: var(--bg-dark);
  position: relative;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at center, var(--empty-bg-inner) 0%, var(--empty-bg-outer) 100%);
}

.empty-content {
  text-align: center;
  opacity: 0.5;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.watermark-logo {
  width: 280px;
  height: 280px;
  object-fit: contain;
  margin-bottom: 30px;
  filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.15));
  opacity: 0.7;
  transition: all 0.5s ease;
}

.empty-content:hover .watermark-logo {
  transform: scale(1.05);
  opacity: 0.9;
}

.empty-content h1 {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(to bottom, #ffffff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-content { 
  background: var(--bg-sidebar); 
  padding: 30px; 
  border-radius: 24px; 
  width: 450px; 
  border: 1px solid var(--border);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  color: var(--text-primary);
}

.attendants-list {
  max-height: 300px;
  overflow-y: auto;
}

.attendant-option { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
  padding: 12px; 
  width: 100%; 
  background: rgba(255, 255, 255, 0.03); 
  border: 1px solid var(--border); 
  color: white; 
  border-radius: 12px; 
  cursor: pointer; 
  margin-bottom: 10px; 
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.attendant-option:hover {
  background: rgba(16, 185, 129, 0.1);
  border-color: var(--accent);
  transform: translateX(8px);
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

.avatar.small { width: 40px; height: 40px; font-size: 1rem; }

.attendant-option .name { font-weight: 600; display: block; text-align: left; }
.attendant-option .dept { font-size: 0.75rem; color: var(--text-secondary); display: block; text-align: left; }

.cancel-btn { 
  background: none; 
  border: 1px solid var(--border); 
  color: var(--text-primary); 
  padding: 8px 16px; 
  border-radius: 8px; 
  cursor: pointer; 
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: var(--glass);
  border-color: var(--text-secondary);
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

.btn-success-sm:hover:not(:disabled) { 
  background: #059669; 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.btn-success-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.priority-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 15px;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease;
  text-align: left;
}

.priority-option:hover {
  background: rgba(255, 255, 255, 0.07);
  transform: scale(1.02);
}

.priority-option .dot { width: 12px; height: 12px; border-radius: 50%; }
.priority-option.high { border-left: 4px solid #ef4444; }
.priority-option.high .dot { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
.priority-option.medium { border-left: 4px solid #f59e0b; }
.priority-option.medium .dot { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
.priority-option.low { border-left: 4px solid #94a3b8; }
.priority-option.low .dot { background: #94a3b8; }

.priority-option .opt-text { display: flex; flex-direction: column; }
.priority-option .label { font-weight: 700; font-size: 1rem; }
.priority-option .desc { font-size: 0.8rem; color: var(--text-secondary); }

.small-modal { width: 400px !important; }
.cancel-btn.block { width: 100%; margin-top: 10px; }

.image-viewer {
  display: flex;
  flex-direction: column;
}
.full-image {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  border-radius: 12px;
}
.close-viewer {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
}
.close-viewer:hover {
  opacity: 1;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .sidebar-wrapper {
    width: 100%;
    display: flex;
  }
  .sidebar-wrapper.hidden-on-mobile {
    display: none !important;
  }

  .dashboard-content:not(.has-active-ticket) .chat-area {
    display: none;
  }

  .dashboard-content.has-active-ticket .chat-area {
    display: flex;
    width: 100%;
  }

  .dashboard-content.has-crm-open :deep(.crm-sidebar) {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 100;
  }
}
</style>