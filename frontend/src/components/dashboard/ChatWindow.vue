<template>
  <div class="chat-main-column">
    <header class="chat-header glass-effect">
      <div class="contact-info">
        <button class="mobile-back-btn" @click="goBack" title="Voltar">
          <ChevronLeftIcon :size="24" />
        </button>
        <div class="avatar small">
          <img v-if="chatStore.activeTicket.contact_details?.profile_pic" :src="chatStore.activeTicket.contact_details.profile_pic" class="avatar-img" />
          <span v-else>{{ chatStore.activeTicket.contact_details?.name?.charAt(0) }}</span>
        </div>
        <div class="header-text">
          <div class="name-status">
            <h3>{{ chatStore.activeTicket.contact_details?.name }}</h3>
            <span class="status-tag" :class="chatStore.activeTicket.status">{{ chatStore.activeTicket.status === 'open' ? 'Em aberto' : (chatStore.activeTicket.status === 'pending' ? 'Pendente' : 'Finalizado') }}</span>
          </div>
          <p class="ticket-subject">{{ chatStore.activeTicket.subject || 'Sem assunto definido' }}</p>
        </div>
      </div>
      <div class="header-actions">
        <div v-if="chatStore.activeTicket.status !== 'closed'" class="priority-selector">
          <button @click="emit('openPriorityModal')" class="btn-outline-sm priority-btn" :class="chatStore.activeTicket.priority">
            <span class="dot"></span>
            <span>Prioridade {{ chatStore.activeTicket.priority === 'high' ? 'Alta' : (chatStore.activeTicket.priority === 'medium' ? 'Média' : 'Baixa') }}</span>
          </button>
        </div>
        
        <button @click="emit('update:showCRM', !showCRM)" class="btn-outline-sm" :class="{ active: showCRM }" title="Informações do Cliente">
          <ContactIcon :size="18" />
          <span>Info</span>
        </button>
        
        <template v-if="chatStore.activeTicket.status !== 'closed'">
          <button v-if="!chatStore.activeTicket.user" @click="handleAccept" class="accept-btn">
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

    <div class="messages-wrapper">
      <div class="messages-container" ref="messageRef">
        <div v-for="msg in chatStore.messages" :key="msg.id" class="message" :class="{ 'me': msg.from_me }">
          <div class="message-bubble">
            <!-- Media Display -->
            <div v-if="msg.media_type === 'image'" class="media-image clickable" @click="emit('openImage', msg.media_url || msg.body)">
              <img :src="msg.media_url || msg.body" />
            </div>
            <div v-else-if="msg.media_type === 'audio'" class="media-audio">
              <audio controls>
                <source :src="msg.media_url" type="audio/mpeg">
              </audio>
            </div>
            <div v-else-if="msg.media_type === 'document'" class="media-document clickable" @click="openDocument(msg.media_url)">
              <div class="doc-card">
                <FileIcon :size="32" />
                <div class="doc-info">
                  <span class="doc-name">Ver Documento</span>
                  <span class="doc-ext">PDF / Arquivo</span>
                </div>
              </div>
            </div>
            
            <p v-if="msg.body && msg.media_type !== 'audio' && msg.media_type !== 'document'">
              {{ cleanBody(msg.body, msg.from_me) }}
            </p>
            <span class="msg-time">
              <span v-if="msg.from_me && msg.user_details" class="msg-attendant">{{ msg.user_details.first_name }} {{ msg.user_details.last_name }} • </span>
              {{ new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <footer v-if="chatStore.activeTicket.status !== 'closed'" class="chat-input glass-effect">
      <input 
        type="file" 
        ref="fileInput" 
        style="display: none" 
        @change="handleFileUpload"
        accept="image/*,audio/*,application/pdf"
      />
      <button class="attach-btn" @click="fileInput.click()" title="Enviar Mídia">
        <PlusIcon :size="22" />
      </button>
      <input 
        v-model="newMessage" 
        @keyup.enter="send"
        :placeholder="chatStore.activeTicket.user ? 'Digite uma mensagem...' : 'Aceite o atendimento para responder...'" 
        type="text" 
        :disabled="!chatStore.activeTicket.user"
      />
      <button class="send-btn" @click="send" :disabled="!newMessage.trim() || !chatStore.activeTicket.user">
        <SendIcon :size="20" />
      </button>
    </footer>
    <div v-else class="closed-banner">
      Este atendimento foi finalizado em {{ new Date(chatStore.activeTicket.updated_at).toLocaleString() }}.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../../store/chat'
import { 
  Contact as ContactIcon, 
  CheckCircle as CheckIcon, 
  ArrowRightLeft as TransferIcon, 
  FileText as FileIcon, 
  Plus as PlusIcon, 
  Send as SendIcon 
} from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits([
  'update:showCRM', 
  'openPriorityModal', 
  'openTransferModal', 
  'openCloseModal', 
  'openImage'
])

const chatStore = useChatStore()
const newMessage = ref('')
const messageRef = ref(null)
const fileInput = ref(null)

const handleAccept = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.acceptTicket(chatStore.activeTicket.id)
  emit('openPriorityModal')
}

const cleanBody = (body, fromMe) => {
  if (!fromMe || !body) return body
  const parts = body.split(/:\*\n\n/)
  return parts.length > 1 ? parts.slice(1).join(/:\*\n\n/) : body
}

const openDocument = (url) => { window.open(url, '_blank') }

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    await chatStore.sendMedia(file)
    event.target.value = '' 
  }
}

const send = async () => {
  if (!newMessage.value.trim()) return
  const text = newMessage.value
  newMessage.value = ''
  await chatStore.sendMessage(text)
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => { 
    if (messageRef.value) {
      messageRef.value.scrollTop = messageRef.value.scrollHeight 
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)
</script>

<style scoped>
.chat-main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

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

.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.avatar.small { width: 40px; height: 40px; font-size: 1rem; }

.header-text { margin-left: 10px; }
.name-status { display: flex; align-items: center; gap: 10px; }
.status-tag {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  text-transform: uppercase;
  font-weight: 700;
}
.status-tag.open { color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.status-tag.pending { color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
.status-tag.closed { color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

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
  .btn-outline-sm span:last-child, .btn-success-sm span:last-child {
    display: none;
  }
  .accept-btn span {
    font-size: 0.8rem;
  }
}

.ticket-subject { font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; }

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

.priority-btn.low .dot { background: #94a3b8; }
.priority-btn.medium .dot { background: #f59e0b; box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }
.priority-btn.high .dot { background: #ef4444; box-shadow: 0 0 12px rgba(239, 68, 68, 0.5); }


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

.action-group { display: flex; align-items: center; gap: 10px; }

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

.messages-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1;
}

.messages-wrapper::before {
  content: "";
  position: absolute;
  top: -50%; left: -50%; width: 200%; height: 200%;
  background-image: url('/favicon.png');
  background-repeat: repeat;
  background-size: 80px;
  opacity: var(--pattern-opacity);
  filter: var(--pattern-filter);
  transform: rotate(-15deg);
  pointer-events: none;
  z-index: 0;
}

.message { display: flex; width: 100%; position: relative; z-index: 1; }
.message.me { justify-content: flex-end; }
.message-bubble {
  max-width: 65%;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.message.me .message-bubble { background: var(--accent); }

.media-image {
  margin: 8px 0 !important;
  max-width: 250px !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 2px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
  transition: transform 0.2s !important;
  cursor: pointer !important;
}

.media-image:hover {
  transform: scale(1.03) !important;
}

.media-image img {
  width: 100% !important;
  height: auto !important;
  display: block !important;
  object-fit: cover !important;
  max-height: 300px !important;
}

.doc-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
}
.doc-info {
  display: flex;
  flex-direction: column;
}
.doc-name { font-weight: 600; font-size: 0.9rem; }
.doc-ext { font-size: 0.75rem; color: var(--text-secondary); }

.msg-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  display: block;
  text-align: right;
  margin-top: 4px;
}
.msg-attendant {
  color: rgba(255, 255, 255, 0.7);
}

.chat-input {
  padding: 15px 25px;
  display: flex;
  gap: 15px;
  align-items: center;
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border);
}

.chat-input input[type="text"] {
  flex: 1;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 12px;
  border-radius: 12px;
  color: var(--text-primary);
  outline: none;
}

.chat-input input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: rgba(0, 0, 0, 0.1);
}

.attach-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.attach-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.05) rotate(90deg);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.send-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  border: none;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05) translateX(2px);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  background: #64748b;
  cursor: not-allowed;
  box-shadow: none;
}

.closed-banner {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>