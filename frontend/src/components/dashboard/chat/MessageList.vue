<template>
  <div class="messages-wrapper">
    <div class="messages-container" ref="messageRef" @scroll="handleScroll">
      <!-- Loader de mensagens anteriores -->
      <div v-if="chatStore.loadingMore" class="loading-more-spinner">
        <span class="spinner-dot"></span>
        <span>Carregando mensagens anteriores...</span>
      </div>

      <!-- Skeleton de mensagens durante o carregamento inicial da conversa (P0 UI/UX) -->
      <div v-if="chatStore.loadingMessages && messages.length === 0" class="chat-skeleton-container">
        <div class="skeleton-bubble received">
          <div class="skeleton-shimmer skeleton-avatar" style="width: 32px; height: 32px;"></div>
          <div class="skeleton-bubble-content">
            <div class="skeleton-shimmer skeleton-text" style="width: 120px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-text" style="width: 240px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-text" style="width: 180px;"></div>
          </div>
        </div>

        <div class="skeleton-bubble sent">
          <div class="skeleton-bubble-content">
            <div class="skeleton-shimmer skeleton-text" style="width: 200px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-text" style="width: 130px;"></div>
          </div>
        </div>

        <div class="skeleton-bubble received">
          <div class="skeleton-shimmer skeleton-avatar" style="width: 32px; height: 32px;"></div>
          <div class="skeleton-bubble-content">
            <div class="skeleton-shimmer skeleton-text" style="width: 100px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-text" style="width: 280px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-text" style="width: 210px;"></div>
          </div>
        </div>

        <div class="skeleton-bubble sent">
          <div class="skeleton-bubble-content">
            <div class="skeleton-shimmer skeleton-text" style="width: 160px;"></div>
          </div>
        </div>
      </div>

      <!-- Message loop with Daily Date Dividers -->
      <template v-for="(msg, index) in messages" :key="msg.id">
        <!-- Separador de Data Inteligente (Dia Novo) -->
        <div v-if="isNewDay(index)" class="date-divider-center">
          <span class="date-divider-badge">{{ formatDateHeader(msg.created_at) }}</span>
        </div>

        <!-- Mensagem de Evento do Sistema (Centralizada) -->
        <div v-if="isSystemMessage(msg)" class="system-message-center">
          <span class="system-message-badge" v-html="cleanSystemText(msg.body)"></span>
        </div>

        <!-- Mensagem Normal -->
        <MessageBubble
          v-else
          :msg="msg"
          :resolved-url="resolvedUrls[msg.id]"
          :highlighted="Boolean(highlightedMessageId) && (String(msg.id) === String(highlightedMessageId) || String(msg.message_id) === String(highlightedMessageId))"
          :active-reaction-picker-id="activeReactionPickerId"
          :ticket-status="ticketStatus"
          @openImage="emit('openImage', $event)"
          @openVideo="emit('openVideo', $event)"
          @clickQuoted="emit('clickQuoted', $event)"
          @reply="emit('reply', $event)"
          @edit="emit('edit', $event)"
          @react="emit('react', $event)"
          @toggleReactionPicker="emit('toggleReactionPicker', $event)"
        />
      </template>
    </div>

    <!-- Floating Scroll-To-Bottom Button with Unread/New Messages Badge -->
    <Transition name="bounce-scale">
      <button 
        v-if="showScrollBottom" 
        class="floating-scroll-bottom-btn glass-effect" 
        @click="scrollToBottomSmooth"
        title="Rolar para o final da conversa"
      >
        <span v-if="newMessagesBelow > 0" class="new-messages-pill">
          +{{ newMessagesBelow }} nova{{ newMessagesBelow > 1 ? 's' : '' }}
        </span>
        <ChevronDownIcon :size="20" class="scroll-bottom-icon" />
      </button>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../../../store/chat'
import MessageBubble from './MessageBubble.vue'
import { isSystemMessage, cleanSystemText } from '../../../utils/whatsappMarkdown'
import { ChevronDown as ChevronDownIcon } from 'lucide-vue-next'

const props = defineProps({
  messages: {
    type: Array,
    required: true
  },
  resolvedUrls: {
    type: Object,
    default: () => ({})
  },
  highlightedMessageId: {
    type: [String, Number],
    default: null
  },
  activeReactionPickerId: {
    type: [String, Number],
    default: null
  },
  ticketStatus: {
    type: String,
    default: 'open'
  }
})

const emit = defineEmits([
  'openImage',
  'openVideo',
  'clickQuoted',
  'reply',
  'edit',
  'react',
  'toggleReactionPicker'
])

const chatStore = useChatStore()
const messageRef = ref(null)

// Floating scroll bottom & new messages counter
const showScrollBottom = ref(false)
const newMessagesBelow = ref(0)

// Helper: Smart Daily Date Grouping
const isNewDay = (index) => {
  if (index === 0) return true
  const prev = props.messages[index - 1]
  const curr = props.messages[index]
  if (!prev?.created_at || !curr?.created_at) return false

  const prevDate = new Date(prev.created_at).toDateString()
  const currDate = new Date(curr.created_at).toDateString()
  return prevDate !== currDate
}

const formatDateHeader = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Hoje'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Ontem'
  } else {
    const formatted = date.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long' })
    if (date.getFullYear() !== today.getFullYear()) {
      return `${formatted} de ${date.getFullYear()}`
    }
    return formatted
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageRef.value) {
      messageRef.value.scrollTop = messageRef.value.scrollHeight
      showScrollBottom.value = false
      newMessagesBelow.value = 0
    }
  })
}

const scrollToBottomSmooth = () => {
  if (messageRef.value) {
    messageRef.value.scrollTo({
      top: messageRef.value.scrollHeight,
      behavior: 'smooth'
    })
    showScrollBottom.value = false
    newMessagesBelow.value = 0
  }
}

const handleScroll = async (e) => {
  const container = e.target
  if (!container) return

  // Detect scroll offset from bottom
  const distFromBottom = container.scrollHeight - container.clientHeight - container.scrollTop
  showScrollBottom.value = distFromBottom > 160
  if (!showScrollBottom.value) {
    newMessagesBelow.value = 0
  }

  // Infinite scroll upwards for older messages
  if (container.scrollTop === 0 && chatStore.hasMoreMessages && !chatStore.loadingMore) {
    const prevScrollHeight = container.scrollHeight
    await chatStore.loadMoreMessages()
    nextTick(() => {
      container.scrollTop = container.scrollHeight - prevScrollHeight
    })
  }
}

// Watch incoming messages: if user is scrolled up, count new messages; otherwise auto-scroll
watch(
  () => props.messages.length,
  (newLen, oldLen) => {
    if (oldLen === undefined || oldLen === 0) {
      scrollToBottom()
      return
    }

    if (newLen > oldLen) {
      if (showScrollBottom.value) {
        newMessagesBelow.value += (newLen - oldLen)
      } else {
        scrollToBottom()
      }
    }
  }
)

defineExpose({
  scrollToBottom,
  scrollToBottomSmooth
})
</script>

<style scoped>
.messages-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  background: var(--chat-bg);
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

/* Smart Daily Date Dividers */
.date-divider-center {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 16px 0 10px;
  width: 100%;
  position: relative;
  z-index: 2;
}

.date-divider-badge {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  text-transform: capitalize;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.system-message-center {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 12px 0;
  width: 100%;
}

.system-message-badge {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: 12px;
  font-size: 0.85rem;
  max-width: 80%;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: inline-block;
}

.system-message-badge :deep(strong) {
  color: var(--text-primary);
  font-weight: 600;
}

.loading-more-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 0.85rem;
  color: var(--accent);
}

.spinner-dot {
  width: 12px;
  height: 12px;
  border: 2px solid var(--accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Floating Scroll-to-Bottom Button */
.floating-scroll-bottom-btn {
  position: absolute;
  right: 24px;
  bottom: 20px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
  transition: transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.floating-scroll-bottom-btn:hover {
  transform: translateY(-2px);
  background: var(--surface-tinted-hover);
  border-color: var(--accent);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
}

.floating-scroll-bottom-btn:active {
  transform: translateY(0);
}

.scroll-bottom-icon {
  color: var(--text-primary);
  transition: transform 0.2s ease;
}

.floating-scroll-bottom-btn:hover .scroll-bottom-icon {
  color: var(--accent);
}

.new-messages-pill {
  position: absolute;
  top: -12px;
  background: var(--accent);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.4);
  animation: pulse-badge 1.8s infinite;
}

@keyframes pulse-badge {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
}

/* Transitions */
.bounce-scale-enter-active {
  animation: bounce-in 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.bounce-scale-leave-active {
  animation: bounce-out 0.2s cubic-bezier(0.6, -0.28, 0.735, 0.045);
}

@keyframes bounce-in {
  from {
    opacity: 0;
    transform: scale(0.6) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes bounce-out {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.6) translateY(10px);
  }
}

@media (max-width: 768px) {
  .messages-container {
    padding: 15px;
  }
  .floating-scroll-bottom-btn {
    right: 16px;
    bottom: 14px;
    width: 40px;
    height: 40px;
  }
}

/* Chat Skeleton Bubbles (P0 UI/UX) */
.chat-skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 14px 20px;
  width: 100%;
}

.skeleton-bubble {
  display: flex;
  gap: 10px;
  max-width: 70%;
  align-items: flex-start;
}

.skeleton-bubble.received {
  align-self: flex-start;
}

.skeleton-bubble.sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.skeleton-bubble-content {
  background: var(--surface-tinted);
  border: 1px solid var(--border);
  padding: 12px 16px;
  border-radius: 14px;
  min-width: 160px;
  display: flex;
  flex-direction: column;
}

.skeleton-bubble.received .skeleton-bubble-content {
  border-bottom-left-radius: 2px;
}

.skeleton-bubble.sent .skeleton-bubble-content {
  border-bottom-right-radius: 2px;
  background: rgba(34, 181, 95, 0.08);
  border-color: rgba(34, 181, 95, 0.2);
}
</style>
