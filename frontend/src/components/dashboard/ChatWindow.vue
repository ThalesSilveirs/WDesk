<template>
  <div 
    class="chat-main-column" 
    v-if="chatStore.activeTicket"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDropFiles"
  >
    <!-- Header -->
    <ChatHeader
      :showCRM="showCRM"
      :isSearchActive="isSearchActive"
      @update:showCRM="emit('update:showCRM', $event)"
      @openPriorityModal="emit('openPriorityModal')"
      @openTransferModal="emit('openTransferModal')"
      @openCloseModal="emit('openCloseModal')"
      @openDeleteModal="emit('openDeleteModal')"
      @openImage="emit('openImage', $event)"
      @setCRMTab="emit('setCRMTab', $event)"
      @openCreatePendencyModal="emit('openCreatePendencyModal')"
      @toggleSearch="toggleInChatSearch"
      @printConversation="printConversation"
    />

    <!-- In-Chat Search Bar (Slide down) -->
    <Transition name="slide-down">
      <div v-if="isSearchActive" class="chat-search-bar glass-effect">
        <div class="search-input-group">
          <SearchIcon :size="16" class="search-bar-icon" />
          <input 
            ref="inChatSearchInputRef"
            v-model="inChatSearchQuery"
            type="text"
            placeholder="Buscar na conversa... (Enter próximo, Shift+Enter anterior)"
            class="chat-search-input"
            @keydown.enter.exact.prevent="goToNextMatch"
            @keydown.enter.shift.prevent="goToPrevMatch"
            @keydown.esc="closeInChatSearch"
          />
          <span v-if="matchedMessageIds.length > 0" class="search-counter-badge">
            {{ currentMatchIndex + 1 }} de {{ matchedMessageIds.length }}
          </span>
          <span v-else-if="inChatSearchQuery.trim()" class="search-counter-badge no-results">
            0 resultados
          </span>
        </div>

        <div class="search-controls">
          <button 
            class="search-nav-btn" 
            :disabled="matchedMessageIds.length === 0" 
            @click="goToPrevMatch"
            title="Ocorrência anterior (Shift+Enter)"
          >
            <ChevronUpIcon :size="16" />
          </button>
          <button 
            class="search-nav-btn" 
            :disabled="matchedMessageIds.length === 0" 
            @click="goToNextMatch"
            title="Próxima ocorrência (Enter)"
          >
            <ChevronDownIcon :size="16" />
          </button>
          <button 
            class="search-close-btn" 
            @click="closeInChatSearch"
            title="Fechar busca (Esc)"
          >
            <XIcon :size="16" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Message List -->
    <MessageList
      ref="messageListRef"
      :messages="chatStore.messages"
      :resolvedUrls="resolvedUrls"
      :highlightedMessageId="highlightedMessageId || currentSearchMatchId"
      :activeReactionPickerId="activeReactionPickerId"
      :ticketStatus="chatStore.activeTicket.status"
      @openImage="emit('openImage', $event)"
      @openVideo="emit('openVideo', $event)"
      @clickQuoted="scrollToMessage"
      @reply="startReplyingMessage($event, messageInputRef)"
      @edit="startEditingMessage($event, newMessageRef, messageInputRef)"
      @react="handleReaction"
      @toggleReactionPicker="toggleReactionPicker"
      @visible="resolveMessageMedia"
    />

    <!-- Footer / Input -->
    <ChatInput
      ref="chatInputRef"
      v-if="chatStore.activeTicket.status !== 'closed'"
      :ticket="chatStore.activeTicket"
      :editingMessage="editingMessage"
      :replyingMessage="replyingMessage"
      @sendText="handleSendText"
      @sendMedia="handleSendMedia"
      @cancelEdit="cancelEditingMessage(newMessageRef)"
      @cancelReply="cancelReplyingMessage"
    />
    <div v-else class="closed-banner">
      Este atendimento foi finalizado em {{ closedTicketDateFormatted }}.
    </div>

    <!-- Drag & Drop File Dropzone Overlay -->
    <Transition name="fade">
      <div v-if="isDraggingOver" class="chat-dropzone-overlay glass-effect">
        <div class="dropzone-box">
          <UploadCloudIcon :size="54" class="dropzone-icon" />
          <h3>Solte o arquivo para enviar</h3>
          <p>Imagens, documentos, vídeos e áudios</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '../../store/chat'
import { formatFullDateTime } from '../../utils/formatters'
import {
  Search as SearchIcon,
  ChevronUp as ChevronUpIcon,
  ChevronDown as ChevronDownIcon,
  X as XIcon,
  UploadCloud as UploadCloudIcon
} from 'lucide-vue-next'

// Sub-componentes
import ChatHeader from './chat/ChatHeader.vue'
import MessageList from './chat/MessageList.vue'
import ChatInput from './chat/ChatInput.vue'

// Composables
import { useMediaResolver } from '../../composables/useMediaResolver'
import { useMessageActions } from '../../composables/useMessageActions'
import { useReactions } from '../../composables/useReactions'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits([
  'update:showCRM',
  'openPriorityModal',
  'openTransferModal',
  'openCloseModal',
  'openDeleteModal',
  'openImage',
  'openVideo',
  'setCRMTab',
  'openCreatePendencyModal'
])

const chatStore = useChatStore()

// Refs para os componentes filhos
const messageListRef = ref(null)
const chatInputRef = ref(null)

// In-Chat Search State
const isSearchActive = ref(false)
const inChatSearchQuery = ref('')
const currentMatchIndex = ref(0)
const inChatSearchInputRef = ref(null)

// Drag & Drop State
const isDraggingOver = ref(false)
let dragCounter = 0

// Computed wrappers para passar referências internas do ChatInput para os composables
const messageInputRef = computed(() => chatInputRef.value?.messageInput)
const newMessageRef = computed({
  get: () => chatInputRef.value?.newMessage || '',
  set: (val) => {
    if (chatInputRef.value) {
      chatInputRef.value.newMessage = val
    }
  }
})

// 1. Resolução e limpeza de Blob URLs
const activeTicketId = computed(() => chatStore.activeTicket?.id)
const closedTicketDateFormatted = computed(() => {
  return formatFullDateTime(chatStore.activeTicket?.updated_at)
})
const { resolvedUrls, resolveMessageMedia } = useMediaResolver(activeTicketId)

// 2. Ações de mensagem (editar, responder, scroll)
const {
  editingMessage,
  replyingMessage,
  highlightedMessageId,
  startEditingMessage,
  cancelEditingMessage,
  startReplyingMessage,
  cancelReplyingMessage,
  scrollToMessage
} = useMessageActions()

// 3. Reações (emoji picker rápido, group & toggle)
const {
  activeReactionPickerId,
  toggleReactionPicker,
  toggleReaction
} = useReactions(async (msgId, newEmoji) => {
  if (chatStore.activeTicket?.id) {
    await chatStore.reactToMessage(chatStore.activeTicket.id, msgId, newEmoji)
  }
})

// In-Chat Search Logic
const matchedMessageIds = computed(() => {
  const q = inChatSearchQuery.value.trim().toLowerCase()
  if (!q) return []
  return (chatStore.messages || [])
    .filter(m => (m.body || '').toLowerCase().includes(q))
    .map(m => m.id)
})

const currentSearchMatchId = computed(() => {
  if (matchedMessageIds.value.length === 0) return null
  return matchedMessageIds.value[currentMatchIndex.value] || null
})

const toggleInChatSearch = () => {
  isSearchActive.value = !isSearchActive.value
  if (isSearchActive.value) {
    nextTick(() => {
      inChatSearchInputRef.value?.focus()
    })
  } else {
    inChatSearchQuery.value = ''
    currentMatchIndex.value = 0
  }
}

const closeInChatSearch = () => {
  isSearchActive.value = false
  inChatSearchQuery.value = ''
  currentMatchIndex.value = 0
}

const scrollToCurrentSearchMatch = () => {
  const matchId = currentSearchMatchId.value
  if (matchId) {
    scrollToMessage(matchId)
  }
}

const goToNextMatch = () => {
  const total = matchedMessageIds.value.length
  if (total === 0) return
  currentMatchIndex.value = (currentMatchIndex.value + 1) % total
  scrollToCurrentSearchMatch()
}

const goToPrevMatch = () => {
  const total = matchedMessageIds.value.length
  if (total === 0) return
  currentMatchIndex.value = (currentMatchIndex.value - 1 + total) % total
  scrollToCurrentSearchMatch()
}

watch(inChatSearchQuery, () => {
  currentMatchIndex.value = 0
  if (matchedMessageIds.value.length > 0) {
    nextTick(scrollToCurrentSearchMatch)
  }
})

// Drag and Drop File Handlers
const onDragEnter = (e) => {
  dragCounter++
  if (e.dataTransfer?.items?.length > 0) {
    isDraggingOver.value = true
  }
}

const onDragOver = (e) => {
  e.dataTransfer.dropEffect = 'copy'
}

const onDragLeave = () => {
  dragCounter--
  if (dragCounter <= 0) {
    isDraggingOver.value = false
    dragCounter = 0
  }
}

const onDropFiles = (e) => {
  dragCounter = 0
  isDraggingOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && chatInputRef.value?.openMediaPreview) {
    chatInputRef.value.openMediaPreview(file)
  }
}

// Print / Export Conversation Document
const printConversation = () => {
  const ticket = chatStore.activeTicket
  if (!ticket) return

  const customerName = ticket.customer_name || ticket.contact_details?.name || 'Cliente'
  const protocol = ticket.id
  const attendant = ticket.user?.username || 'Atendente'
  const dateStr = new Date().toLocaleString('pt-BR')

  const messagesHtml = (chatStore.messages || []).map(m => {
    const sender = m.from_me ? 'Atendente' : customerName
    const time = m.created_at ? new Date(m.created_at).toLocaleString('pt-BR') : ''
    const body = m.body || (m.media_type ? `[Arquivo: ${m.file_name || m.media_type}]` : '')
    return `
      <div class="msg-row ${m.from_me ? 'msg-out' : 'msg-in'}">
        <div class="msg-meta"><strong>${sender}</strong> <span>${time}</span></div>
        <div class="msg-body">${body}</div>
      </div>
    `
  }).join('')

  const printWindow = window.open('', '_blank')
  if (!printWindow) return

  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <title>Atendimento #${protocol} - ${customerName}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 30px; color: #1f2937; max-width: 820px; margin: auto; }
          .header { border-bottom: 2px solid #10b981; padding-bottom: 14px; margin-bottom: 24px; }
          .header h1 { margin: 0 0 8px; font-size: 22px; color: #111827; }
          .header p { margin: 3px 0; font-size: 13px; color: #4b5563; }
          .msg-row { margin-bottom: 12px; padding: 12px 16px; border-radius: 8px; font-size: 13.5px; page-break-inside: avoid; }
          .msg-in { background: #f3f4f6; border-left: 4px solid #6b7280; }
          .msg-out { background: #ecfdf5; border-left: 4px solid #10b981; }
          .msg-meta { font-size: 11px; color: #6b7280; margin-bottom: 6px; display: flex; justify-content: space-between; }
          .msg-body { white-space: pre-wrap; word-break: break-word; line-height: 1.45; }
          @media print { body { padding: 0; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>wDesk - Histórico de Atendimento #${protocol}</h1>
          <p><strong>Cliente:</strong> ${customerName} | <strong>Protocolo:</strong> #${protocol}</p>
          <p><strong>Atendente:</strong> ${attendant} | <strong>Emitido em:</strong> ${dateStr}</p>
        </div>
        <div class="messages">
          ${messagesHtml || '<p style="color: #9ca3af;">Nenhuma mensagem registrada.</p>'}
        </div>
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.print()
  }, 350)
}

// Global Keydown Handler (Ctrl+F for in-chat search)
const handleGlobalKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
    e.preventDefault()
    toggleInChatSearch()
  } else if (e.key === 'Escape' && isSearchActive.value) {
    closeInChatSearch()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

// Controladores locais de scroll e envios
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollToBottom()
    }
  })
}

const handleSendText = async (text) => {
  if (!chatStore.activeTicket) return

  if (editingMessage.value) {
    const msgToEdit = editingMessage.value
    cancelEditingMessage(newMessageRef)
    await chatStore.editMessage(chatStore.activeTicket.id, msgToEdit.id, text)
  } else if (replyingMessage.value) {
    const msgToReply = replyingMessage.value
    cancelReplyingMessage()
    await chatStore.sendMessage(text, msgToReply.id)
  } else {
    await chatStore.sendMessage(text)
  }
  scrollToBottom()
}

const handleSendMedia = async (payload) => {
  if (payload instanceof File || payload instanceof Blob) {
    await chatStore.sendMedia(payload)
  } else if (payload && payload.file) {
    await chatStore.sendMedia(payload.file, payload.caption || '')
  }
  scrollToBottom()
}

const handleReaction = async ({ msg, emoji }) => {
  await toggleReaction(msg, emoji)
}

watch(() => chatStore.messages.length, scrollToBottom)
</script>

<style scoped>
.chat-main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  position: relative;
}

/* In-Chat Search Bar */
.chat-search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  gap: 12px;
  z-index: 15;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-input-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--input-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 6px 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-input-group:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
}

.search-bar-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.chat-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.85rem;
}

.chat-search-input::placeholder {
  color: var(--text-secondary);
  font-size: 0.82rem;
}

.search-counter-badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent);
  background: rgba(16, 185, 129, 0.12);
  padding: 2px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.search-counter-badge.no-results {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.search-nav-btn,
.search-close-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.search-nav-btn:hover:not(:disabled),
.search-close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  border-color: var(--accent);
}

.search-nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Drag & Drop File Dropzone Overlay */
.chat-dropzone-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px;
  pointer-events: none;
}

.dropzone-box {
  width: 100%;
  max-width: 440px;
  border: 2px dashed var(--accent);
  border-radius: 20px;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: rgba(16, 185, 129, 0.05);
  animation: dropzone-pulse 2s infinite ease-in-out;
}

.dropzone-icon {
  color: var(--accent);
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 10px rgba(16, 185, 129, 0.4));
}

.dropzone-box h3 {
  margin: 0 0 6px;
  font-size: 1.15rem;
  color: var(--text-primary);
  font-weight: 700;
}

.dropzone-box p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

@keyframes dropzone-pulse {
  0%, 100% {
    transform: scale(1);
    border-color: var(--accent);
  }
  50% {
    transform: scale(1.02);
    border-color: #34d399;
  }
}

.closed-banner {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* Transitions */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>