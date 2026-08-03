<template>
  <div class="chat-main-column" v-if="chatStore.activeTicket">
    <!-- Header -->
    <ChatHeader
      :showCRM="showCRM"
      @update:showCRM="emit('update:showCRM', $event)"
      @openPriorityModal="emit('openPriorityModal')"
      @openTransferModal="emit('openTransferModal')"
      @openCloseModal="emit('openCloseModal')"
      @openDeleteModal="emit('openDeleteModal')"
      @openImage="emit('openImage', $event)"
      @setCRMTab="emit('setCRMTab', $event)"
      @openCreatePendencyModal="emit('openCreatePendencyModal')"
    />

    <!-- Message List -->
    <MessageList
      ref="messageListRef"
      :messages="chatStore.messages"
      :resolvedUrls="resolvedUrls"
      :highlightedMessageId="highlightedMessageId"
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
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '../../store/chat'
import { formatFullDateTime } from '../../utils/formatters'

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

const handleSendMedia = async (file) => {
  await chatStore.sendMedia(file)
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
}

.closed-banner {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>