<template>
  <div class="messages-wrapper">
    <div class="messages-container" ref="messageRef" @scroll="handleScroll">
      <!-- Loader de mensagens anteriores -->
      <div v-if="chatStore.loadingMore" class="loading-more-spinner">
        <span class="spinner-dot"></span>
        <span>Carregando mensagens anteriores...</span>
      </div>

      <!-- Loader de troca de conversa -->
      <div v-if="chatStore.loadingMessages && messages.length === 0" class="loading-more-spinner">
        <span class="spinner-dot"></span>
        <span>Carregando conversa...</span>
      </div>

      <template v-for="msg in messages" :key="msg.id">
        <!-- Mensagem de Evento do Sistema (Centralizada) -->
        <div v-if="isSystemMessage(msg)" class="system-message-center">
          <span class="system-message-badge" v-html="cleanSystemText(msg.body)"></span>
        </div>

        <!-- Mensagem Normal -->
        <MessageBubble
          v-else
          :msg="msg"
          :resolved-url="resolvedUrls[msg.id]"
          :highlighted="highlightedMessageId === msg.quoted_message_id || highlightedMessageId === msg.message_id"
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
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useChatStore } from '../../../store/chat'
import MessageBubble from './MessageBubble.vue'
import { isSystemMessage, cleanSystemText } from '../../../utils/whatsappMarkdown'

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

const scrollToBottom = () => {
  nextTick(() => {
    if (messageRef.value) {
      messageRef.value.scrollTop = messageRef.value.scrollHeight
    }
  })
}

const handleScroll = async (e) => {
  const container = e.target
  if (container.scrollTop === 0 && chatStore.hasMoreMessages && !chatStore.loadingMore) {
    const prevScrollHeight = container.scrollHeight
    
    await chatStore.loadMoreMessages()
    
    nextTick(() => {
      container.scrollTop = container.scrollHeight - prevScrollHeight
    })
  }
}

defineExpose({
  scrollToBottom
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

.messages-wrapper::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background-image: url('/favicon.png');
  background-repeat: repeat;
  background-size: 80px;
  opacity: var(--pattern-opacity);
  filter: var(--pattern-filter);
  transform: rotate(-15deg);
  pointer-events: none;
  z-index: 0;
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

@media (max-width: 768px) {
  .messages-container {
    padding: 15px;
  }
}
</style>
