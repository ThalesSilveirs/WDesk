<template>
  <footer class="chat-input glass-effect">
    <!-- EMOJI PICKER POPUP (Carregamento assíncrono) -->
    <Transition name="fade">
      <EmojiPicker
        v-if="showEmojiPicker"
        class="emoji-picker-position"
        ref="pickerContainerRef"
        @select="insertEmoji"
      />
    </Transition>

    <!-- EDIT MESSAGE BANNER -->
    <div v-if="editingMessage" class="edit-message-banner">
      <div class="edit-message-info">
        <EditIcon :size="14" class="edit-icon-label" />
        <div class="edit-message-text">
          <span class="edit-label">Editando mensagem</span>
          <p class="edit-preview">{{ editingMessage.body }}</p>
        </div>
      </div>
      <button class="cancel-edit-btn" @click="emit('cancelEdit')" title="Cancelar edição">
        <XIcon :size="16" />
      </button>
    </div>

    <!-- REPLY MESSAGE BANNER -->
    <div v-if="replyingMessage" class="edit-message-banner reply-message-banner">
      <div class="edit-message-info">
        <ReplyIcon :size="14" class="edit-icon-label" style="transform: scaleX(-1);" />
        <div class="edit-message-text">
          <span class="edit-label">Respondendo a <strong>{{ replyingMessage.from_me ? 'Você' : (ticket.contact_details?.name || 'Cliente') }}</strong></span>
          <p class="edit-preview">{{ cleanBody(replyingMessage.body, replyingMessage.from_me) || (replyingMessage.media_type ? '📷 Mídia' : '') }}</p>
        </div>
      </div>
      <button class="cancel-edit-btn" @click="emit('cancelReply')" title="Cancelar resposta">
        <XIcon :size="16" />
      </button>
    </div>

    <div class="chat-input-row">
      <input
        type="file"
        ref="fileInput"
        style="display: none"
        @change="handleFileUpload"
        accept="image/*,audio/*,application/pdf"
      />

      <!-- ESTADO NORMAL -->
      <template v-if="!isRecording && !hasRecording">
        <button class="attach-btn" @click="fileInput.click()" :disabled="!ticket.user" title="Enviar Mídia">
          <PlusIcon :size="22" />
        </button>
        <button class="emoji-btn" @click.stop="toggleEmojiPicker" :disabled="!ticket.user" title="Inserir Emoji">
          <SmileIcon :size="22" />
        </button>
        <textarea
          ref="messageInput"
          v-model="newMessage"
          @keydown="handleKeyDown"
          @paste="handlePaste"
          :placeholder="ticket.user ? 'Digite uma mensagem...' : 'Aceite o atendimento para responder...'"
          :disabled="!ticket.user"
          rows="1"
        />
        <button
          v-if="newMessage.trim()"
          class="send-btn"
          @click="send"
          :disabled="!ticket.user"
          title="Enviar Mensagem"
        >
          <SendIcon :size="20" />
        </button>
        <button
          v-else
          class="mic-btn"
          @click="startRecording"
          :disabled="!ticket.user"
          title="Gravar Áudio"
        >
          <MicIcon :size="20" />
        </button>
      </template>

      <!-- ESTADO GRAVANDO -->
      <template v-else-if="isRecording">
        <div class="recording-indicator">
          <span class="recording-dot"></span>
          <span class="recording-text">Gravando ({{ formatTime(recordingTime) }})</span>
          <canvas ref="canvasRef" width="100" height="30" class="recording-canvas"></canvas>
        </div>
        <div class="recording-actions">
          <button class="cancel-rec-btn" @click="cancelRecording" title="Cancelar Gravação">
            <TrashIcon :size="20" />
          </button>
          <button class="stop-rec-btn" @click="stopRecording" title="Parar Gravação">
            <SquareIcon :size="20" />
          </button>
        </div>
      </template>

      <!-- ESTADO PRÉVIA DE ÁUDIO -->
      <template v-else-if="hasRecording">
        <div class="audio-preview-container">
          <audio :src="recordedAudioUrl" controls class="audio-preview-player"></audio>
        </div>
        <div class="recording-actions">
          <button class="cancel-rec-btn" @click="cancelRecording" :disabled="isSending" title="Descartar Áudio">
            <TrashIcon :size="20" />
          </button>
          <button class="send-rec-btn" @click="sendRecording" :disabled="isSending" title="Enviar Áudio">
            <SendIcon :size="20" />
          </button>
        </div>
      </template>
    </div>
  </footer>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import { useAudioRecorder } from '../../../composables/useAudioRecorder'
import { cleanBody } from '../../../utils/whatsappMarkdown'
import {
  Plus as PlusIcon,
  Send as SendIcon,
  Mic as MicIcon,
  Trash2 as TrashIcon,
  Square as SquareIcon,
  Smile as SmileIcon,
  Pencil as EditIcon,
  Reply as ReplyIcon,
  X as XIcon
} from 'lucide-vue-next'

// Lazy Load do EmojiPicker
const EmojiPicker = defineAsyncComponent(() => import('./EmojiPicker.vue'))

const props = defineProps({
  ticket: {
    type: Object,
    required: true
  },
  editingMessage: {
    type: Object,
    default: null
  },
  replyingMessage: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['sendText', 'sendMedia', 'cancelEdit', 'cancelReply'])

const newMessage = ref('')
const messageInput = ref(null)
const fileInput = ref(null)
const showEmojiPicker = ref(false)
const pickerContainerRef = ref(null)
const isSending = ref(false)

// Hook de áudio
const {
  isRecording,
  hasRecording,
  recordedAudioUrl,
  recordedFile,
  recordingTime,
  canvasRef,
  startRecording,
  stopRecording,
  cancelRecording,
  clearRecording,
  formatTime
} = useAudioRecorder()

// Watch para focar o input ao mudar de edição/resposta
watch(() => props.editingMessage, (newVal) => {
  if (newVal) {
    newMessage.value = newVal.body
    focusInput()
  } else if (!props.replyingMessage) {
    newMessage.value = ''
  }
})

watch(() => props.replyingMessage, (newVal) => {
  if (newVal) {
    focusInput()
  }
})

const focusInput = () => {
  nextTick(() => {
    if (messageInput.value) {
      messageInput.value.focus()
    }
  })
}

// Inserir emoji no cursor
const insertEmoji = (emoji) => {
  const textarea = messageInput.value
  if (!textarea) {
    newMessage.value += emoji
    return
  }

  const startPos = textarea.selectionStart
  const endPos = textarea.selectionEnd
  const text = newMessage.value

  newMessage.value = text.substring(0, startPos) + emoji + text.substring(endPos)

  setTimeout(() => {
    textarea.focus()
    const newCursorPos = startPos + emoji.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  }, 10)
}

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const handleWindowClick = (e) => {
  if (showEmojiPicker.value) {
    const picker = pickerContainerRef.value?.$el || document.querySelector('.emoji-picker-container')
    const btn = document.querySelector('.emoji-btn')
    if (picker && !picker.contains(e.target) && btn && !btn.contains(e.target)) {
      showEmojiPicker.value = false
    }
  }
}

onMounted(() => {
  window.addEventListener('click', handleWindowClick)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
})

// Auto resize textarea
const autoResize = () => {
  nextTick(() => {
    if (!messageInput.value) return
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = `${messageInput.value.scrollHeight}px`
  })
}

watch(newMessage, () => {
  autoResize()
})

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
    e.preventDefault()
    send()
  }
}

const handlePaste = async (event) => {
  const clipboardData = event.clipboardData || window.clipboardData
  if (!clipboardData) return

  const items = clipboardData.items
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      const file = item.getAsFile()
      if (file) {
        event.preventDefault()
        emit('sendMedia', file)
      }
    }
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    emit('sendMedia', file)
    event.target.value = ''
  }
}

const send = () => {
  if (!newMessage.value.trim()) return
  const text = newMessage.value
  newMessage.value = ''
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
  }
  emit('sendText', text)
}

const sendRecording = async () => {
  if (recordedFile.value && !isSending.value) {
    isSending.value = true
    try {
      emit('sendMedia', recordedFile.value)
      clearRecording()
    } catch (err) {
      console.error("Erro ao enviar áudio gravado:", err)
      const errorMsg = err.response?.data?.error || err.message || "Erro desconhecido"
      alert("Não foi possível enviar o áudio: " + errorMsg)
    } finally {
      isSending.value = false
    }
  }
}

defineExpose({
  newMessage,
  messageInput
})
</script>

<style scoped>
.chat-input {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border);
}

.chat-input-row {
  padding: 15px 25px;
  display: flex;
  gap: 15px;
  align-items: flex-end;
  width: 100%;
  box-sizing: border-box;
}

.chat-input textarea {
  flex: 1;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 12px;
  border-radius: 12px;
  color: var(--text-primary);
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.4;
  height: 44px;
  max-height: 150px;
  overflow-y: auto;
}

.chat-input textarea:disabled {
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

.mic-btn {
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

.mic-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05);
  box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
}

.mic-btn:disabled {
  opacity: 0.5;
  background: #64748b;
  cursor: not-allowed;
  box-shadow: none;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  color: #ef4444;
  font-weight: 500;
}

.recording-dot {
  width: 10px;
  height: 10px;
  background-color: #ef4444;
  border-radius: 50%;
  animation: pulse-red 1.2s infinite;
}

.recording-text {
  font-size: 0.95rem;
  color: var(--text-primary);
}

@keyframes pulse-red {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

.recording-actions {
  display: flex;
  gap: 10px;
}

.cancel-rec-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-rec-btn:hover {
  background: #ef4444;
  color: white;
}

.stop-rec-btn {
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
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.stop-rec-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.05);
}

.audio-preview-container {
  flex: 1;
  display: flex;
  align-items: center;
}

.audio-preview-player {
  width: 100%;
  height: 36px;
  border-radius: 8px;
  background: transparent;
}

.recording-canvas {
  margin-left: 10px;
  background: transparent;
  border-radius: 4px;
}

.send-rec-btn {
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
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.send-rec-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.05);
}

.send-rec-btn:disabled,
.cancel-rec-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.emoji-btn {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.emoji-btn:hover {
  color: var(--accent);
  background: var(--border);
  transform: scale(1.05);
}

.emoji-picker-position {
  position: absolute;
  bottom: 75px;
  left: 20px;
}

.edit-message-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--bg-hover);
  border-bottom: 1px solid var(--border);
  width: 100%;
  box-sizing: border-box;
}

.edit-message-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  flex: 1;
}

.edit-icon-label {
  color: var(--primary-color);
  flex-shrink: 0;
}

.edit-message-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  text-align: left;
}

.edit-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--primary-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.edit-preview {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  margin: 0;
}

.cancel-edit-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease;
  flex-shrink: 0;
  margin-left: 8px;
}

.cancel-edit-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.reply-message-banner {
  border-left: 4px solid var(--accent) !important;
}

@media (max-width: 768px) {
  .chat-input {
    padding: 0;
    gap: 0;
  }

  .chat-input-row {
    padding: 10px 15px;
    gap: 8px;
  }

  .chat-input textarea {
    padding: 10px;
    font-size: 0.9rem;
  }

  .attach-btn,
  .send-btn,
  .mic-btn,
  .cancel-rec-btn,
  .stop-rec-btn,
  .send-rec-btn,
  .emoji-btn {
    width: 36px;
    height: 36px;
    border-radius: 8px;
  }

  .recording-canvas {
    display: none;
  }
}
</style>
