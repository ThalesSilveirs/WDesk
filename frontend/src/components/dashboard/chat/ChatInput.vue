<template>
  <footer class="chat-input-container">
    <!-- EMOJI PICKER POPUP (Carregamento assíncrono) -->
    <Transition name="fade">
      <EmojiPicker
        v-if="showEmojiPicker"
        class="emoji-picker-position"
        ref="pickerContainerRef"
        @select="insertEmoji"
      />
    </Transition>

    <!-- QUICK REPLIES FLOATING POPUP -->
    <Transition name="fade">
      <QuickRepliesModal
        v-if="showQuickReplies"
        class="quick-replies-position"
        ref="quickRepliesContainerRef"
        :filter-query="quickReplyFilter"
        @select="selectQuickReply"
        @close="closeQuickReplies"
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

    <!-- MEDIA PREVIEW MODAL (Colar / Upload de Imagem ou Arquivo) -->
    <Transition name="modal-fade">
      <div v-if="showMediaPreview" class="media-preview-overlay" @click.self="closeMediaPreview">
        <div class="media-preview-modal glass-modal">
          <div class="media-preview-header">
            <div class="header-file-info">
              <ImageIcon v-if="isImage" :size="18" class="header-icon" />
              <FileTextIcon v-else :size="18" class="header-icon" />
              <div class="file-name-size">
                <span class="file-name" :title="pendingMediaFile?.name">{{ pendingMediaFile?.name || 'Arquivo' }}</span>
                <span class="file-size">{{ formatFileSize(pendingMediaFile?.size) }}</span>
              </div>
            </div>
            <button class="close-preview-btn" @click="closeMediaPreview" :disabled="isSendingMedia" title="Fechar (Esc)">
              <XIcon :size="18" />
            </button>
          </div>

          <div class="media-preview-body">
            <!-- Image Preview -->
            <div v-if="isImage" class="preview-container image-mode">
              <img :src="pendingMediaPreviewUrl" alt="Pré-visualização" class="preview-image" />
            </div>

            <!-- Video Preview -->
            <div v-else-if="isVideo" class="preview-container video-mode">
              <video :src="pendingMediaPreviewUrl" controls class="preview-video"></video>
            </div>

            <!-- Audio Preview -->
            <div v-else-if="isAudio" class="preview-container audio-mode">
              <audio :src="pendingMediaPreviewUrl" controls class="preview-audio"></audio>
            </div>

            <!-- Document / Generic File Preview -->
            <div v-else class="preview-container doc-mode">
              <div class="doc-preview-card">
                <FileTextIcon :size="48" class="doc-large-icon" />
                <span class="doc-name">{{ pendingMediaFile?.name }}</span>
                <span class="doc-size">{{ formatFileSize(pendingMediaFile?.size) }}</span>
              </div>
            </div>
          </div>

          <!-- Caption & Actions -->
          <div class="media-preview-footer">
            <div class="caption-input-box">
              <input
                ref="captionInputRef"
                v-model="pendingMediaCaption"
                @keydown.enter.prevent="sendPendingMedia"
                placeholder="Adicionar legenda... (pressione Enter para enviar)"
                :disabled="isSendingMedia"
                class="caption-input"
              />
            </div>
            <div class="preview-actions">
              <button 
                class="btn-preview-cancel" 
                @click="closeMediaPreview" 
                :disabled="isSendingMedia"
              >
                Cancelar
              </button>
              <button 
                class="btn-preview-send" 
                @click="sendPendingMedia" 
                :disabled="isSendingMedia"
              >
                <LoaderIcon v-if="isSendingMedia" class="spin-icon" :size="16" />
                <SendIcon v-else :size="16" />
                <span>{{ isSendingMedia ? 'Enviando...' : 'Enviar' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Main input editor card wrapper -->
    <div class="chat-input-card">
      <input
        type="file"
        ref="fileInput"
        style="display: none"
        @change="handleFileUpload"
        accept="*/*"
      />

      <!-- Textarea input area (Upper Section) -->
      <div class="textarea-section" v-if="!isRecording && !hasRecording">
        <textarea
          ref="messageInput"
          v-model="newMessage"
          @keydown="handleKeyDown"
          @paste="handlePaste"
          :placeholder="ticket.user ? 'Digite uma mensagem ou / para ver comandos...' : 'Aceite o atendimento para responder...'"
          :disabled="!ticket.user"
          rows="1"
        />
      </div>

      <!-- Recording Audio active state -->
      <div class="recording-section" v-else-if="isRecording">
        <div class="recording-indicator">
          <span class="recording-dot"></span>
          <span class="recording-text">Gravando ({{ formatTime(recordingTime) }})</span>
          <canvas ref="canvasRef" width="100" height="30" class="recording-canvas"></canvas>
        </div>
        <div class="recording-actions">
          <button class="rec-btn-action cancel" @click="cancelRecording" title="Cancelar Gravação">
            <TrashIcon :size="16" />
          </button>
          <button class="rec-btn-action stop" @click="stopRecording" title="Parar Gravação">
            <SquareIcon :size="16" />
          </button>
        </div>
      </div>

      <!-- Audio Preview state -->
      <div class="recording-section" v-else-if="hasRecording">
        <div class="audio-preview-container">
          <audio :src="recordedAudioUrl" controls class="audio-preview-player"></audio>
        </div>
        <div class="recording-actions">
          <button class="rec-btn-action cancel" @click="cancelRecording" :disabled="isSending" title="Descartar Áudio">
            <TrashIcon :size="16" />
          </button>
          <button class="rec-btn-action send" @click="sendRecording" :disabled="isSending" title="Enviar Áudio">
            <ArrowUpIcon :size="16" />
          </button>
        </div>
      </div>

      <!-- Rich Toolbar (Lower Section) -->
      <div class="toolbar-section" v-if="!isRecording && !hasRecording">
        <div class="toolbar-left">
          <button class="toolbar-btn text-mode-btn" :disabled="!ticket.user">
            <span>Responder</span>
            <ChevronDownIcon :size="12" />
          </button>
          <div class="style-divider"></div>
          <button class="toolbar-btn style-btn" @click="applyFormatting('*')" :disabled="!ticket.user" title="Negrito">
            <BoldIcon :size="14" />
          </button>
          <button class="toolbar-btn style-btn" @click="applyFormatting('_')" :disabled="!ticket.user" title="Itálico">
            <ItalicIcon :size="14" />
          </button>
          <button class="toolbar-btn style-btn" @click="applyFormatting('~')" :disabled="!ticket.user" title="Tachado">
            <StrikethroughIcon :size="14" />
          </button>
          <button class="toolbar-btn style-btn" @click.stop="toggleQuickReplies" :disabled="!ticket.user" title="Respostas Rápidas (/)">
            <ZapIcon :size="14" />
          </button>
        </div>

        <div class="toolbar-right">
          <button class="toolbar-btn attach-btn" @click="fileInput.click()" :disabled="!ticket.user" title="Enviar Mídia">
            <PaperclipIcon :size="16" />
          </button>
          <button class="toolbar-btn" @click="startRecording" :disabled="!ticket.user" title="Gravar Áudio">
            <MicIcon :size="16" />
          </button>
          <button class="toolbar-btn emoji-btn" @click.stop="toggleEmojiPicker" :disabled="!ticket.user" title="Inserir Emoji">
            <SmileIcon :size="16" />
          </button>
          <button 
            class="send-circle-btn" 
            @click="send" 
            :disabled="!ticket.user || !newMessage.trim()"
            title="Enviar Mensagem"
          >
            <ArrowUpIcon :size="18" />
          </button>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import { useAudioRecorder } from '../../../composables/useAudioRecorder'
import { cleanBody } from '../../../utils/whatsappMarkdown'
import {
  Mic as MicIcon,
  Trash2 as TrashIcon,
  Square as SquareIcon,
  Smile as SmileIcon,
  Pencil as EditIcon,
  Reply as ReplyIcon,
  X as XIcon,
  Zap as ZapIcon,
  Bold as BoldIcon,
  Italic as ItalicIcon,
  Strikethrough as StrikethroughIcon,
  ChevronDown as ChevronDownIcon,
  Paperclip as PaperclipIcon,
  ArrowUp as ArrowUpIcon,
  Image as ImageIcon,
  FileText as FileTextIcon,
  Loader2 as LoaderIcon,
  Send as SendIcon
} from 'lucide-vue-next'

// Lazy Load do EmojiPicker
const EmojiPicker = defineAsyncComponent(() => import('./EmojiPicker.vue'))
const QuickRepliesModal = defineAsyncComponent(() => import('./QuickRepliesModal.vue'))

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

const showQuickReplies = ref(false)
const quickReplyFilter = ref('')
const quickRepliesContainerRef = ref(null)

watch(newMessage, (val) => {
  if (val.startsWith('/')) {
    showQuickReplies.value = true
    quickReplyFilter.value = val.substring(1)
  } else {
    if (showQuickReplies.value) {
      showQuickReplies.value = false
    }
  }
})

const selectQuickReply = (body) => {
  newMessage.value = body
  showQuickReplies.value = false
  focusInput()
}

const toggleQuickReplies = () => {
  showQuickReplies.value = !showQuickReplies.value
  if (showQuickReplies.value) {
    quickReplyFilter.value = ''
  }
}

const closeQuickReplies = () => {
  showQuickReplies.value = false
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
  if (showQuickReplies.value) {
    const menu = quickRepliesContainerRef.value?.$el || document.querySelector('.quick-replies-position')
    const btn = document.querySelector('.quick-reply-btn')
    if (menu && !menu.contains(e.target) && btn && !btn.contains(e.target)) {
      showQuickReplies.value = false
    }
  }
}

// Estado do Modal de Pré-visualização de Mídia
const showMediaPreview = ref(false)
const pendingMediaFile = ref(null)
const pendingMediaPreviewUrl = ref(null)
const pendingMediaCaption = ref('')
const isSendingMedia = ref(false)
const captionInputRef = ref(null)

const isImage = computed(() => {
  if (!pendingMediaFile.value) return false
  return pendingMediaFile.value.type.startsWith('image/')
})

const isVideo = computed(() => {
  if (!pendingMediaFile.value) return false
  return pendingMediaFile.value.type.startsWith('video/')
})

const isAudio = computed(() => {
  if (!pendingMediaFile.value) return false
  return pendingMediaFile.value.type.startsWith('audio/')
})

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const openMediaPreview = (file) => {
  if (!file) return
  pendingMediaFile.value = file
  pendingMediaCaption.value = ''
  if (pendingMediaPreviewUrl.value) {
    URL.revokeObjectURL(pendingMediaPreviewUrl.value)
  }
  pendingMediaPreviewUrl.value = URL.createObjectURL(file)
  showMediaPreview.value = true
  nextTick(() => {
    if (captionInputRef.value) {
      captionInputRef.value.focus()
    }
  })
}

const closeMediaPreview = () => {
  if (isSendingMedia.value) return
  showMediaPreview.value = false
  if (pendingMediaPreviewUrl.value) {
    URL.revokeObjectURL(pendingMediaPreviewUrl.value)
  }
  pendingMediaPreviewUrl.value = null
  pendingMediaFile.value = null
  pendingMediaCaption.value = ''
  focusInput()
}

const sendPendingMedia = async () => {
  if (!pendingMediaFile.value || isSendingMedia.value) return
  isSendingMedia.value = true
  try {
    await emit('sendMedia', {
      file: pendingMediaFile.value,
      caption: pendingMediaCaption.value
    })
    closeMediaPreview()
  } catch (err) {
    console.error("Erro ao enviar mídia:", err)
    alert("Não foi possível enviar o arquivo: " + (err.response?.data?.error || err.message || "Erro desconhecido"))
  } finally {
    isSendingMedia.value = false
  }
}

const handleGlobalKeyDown = (e) => {
  if (e.key === 'Escape' && showMediaPreview.value && !isSendingMedia.value) {
    closeMediaPreview()
  }
}

onMounted(() => {
  window.addEventListener('click', handleWindowClick)
  window.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
  window.removeEventListener('keydown', handleGlobalKeyDown)
  if (pendingMediaPreviewUrl.value) {
    URL.revokeObjectURL(pendingMediaPreviewUrl.value)
  }
})

// Auto resize textarea
const autoResize = () => {
  nextTick(() => {
    if (!messageInput.value) return
    messageInput.value.style.height = 'auto'
    const targetHeight = Math.min(Math.max(messageInput.value.scrollHeight, 24), 140)
    messageInput.value.style.height = `${targetHeight}px`
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
  if (items && items.length > 0) {
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.kind === 'file' || item.type.indexOf('image') !== -1) {
        const file = item.getAsFile()
        if (file) {
          event.preventDefault()
          openMediaPreview(file)
          return
        }
      }
    }
  }

  // Fallback para clipboardData.files
  if (clipboardData.files && clipboardData.files.length > 0) {
    event.preventDefault()
    openMediaPreview(clipboardData.files[0])
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    openMediaPreview(file)
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

const applyFormatting = (prefix, suffix = prefix) => {
  const textarea = messageInput.value
  if (!textarea) return

  const startPos = textarea.selectionStart
  const endPos = textarea.selectionEnd
  const text = newMessage.value

  const selectedText = text.substring(startPos, endPos)
  const replacement = prefix + selectedText + suffix

  newMessage.value = text.substring(0, startPos) + replacement + text.substring(endPos)

  setTimeout(() => {
    textarea.focus()
    const newCursorPos = startPos + prefix.length + selectedText.length + suffix.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  }, 10)
}

defineExpose({
  newMessage,
  messageInput
})
</script>

<style scoped>
.chat-input-container {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  padding: 16px 24px 24px 24px;
  background: var(--chat-bg);
}

.chat-input-card {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

/* Upper Section: Textarea */
.textarea-section {
  display: flex;
  padding: 14px 18px 4px 18px;
}

.textarea-section textarea {
  flex: 1;
  background: transparent;
  border: none;
  padding: 0;
  color: var(--text-primary);
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 0.94rem;
  line-height: 1.4;
  height: 24px;
  max-height: 150px;
  overflow-y: auto;
}

.textarea-section textarea::placeholder {
  color: var(--text-secondary);
}

.textarea-section textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Recording State active UI */
.recording-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  height: 48px;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
}

.recording-dot {
  width: 8px;
  height: 8px;
  background-color: #ef4444;
  border-radius: 50%;
  animation: pulse-red 1.2s infinite;
}

.recording-text {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-primary);
}

.recording-canvas {
  margin-left: 10px;
  background: transparent;
  opacity: 0.8;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.recording-actions {
  display: flex;
  gap: 6px;
}

.rec-btn-action {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  background: none;
  border: none;
  transition: all 0.2s ease;
}

.rec-btn-action.cancel {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.rec-btn-action.cancel:hover {
  background: #ef4444;
  color: white;
}

.rec-btn-action.stop {
  background: var(--border);
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.rec-btn-action.stop:hover {
  background: rgba(255, 255, 255, 0.08);
}

.rec-btn-action.send {
  background: var(--accent);
  color: white;
  border: none;
}

.rec-btn-action.send:hover {
  background: var(--accent-hover);
}

.audio-preview-container {
  flex: 1;
  display: flex;
  align-items: center;
  margin-right: 12px;
}

.audio-preview-player {
  width: 100%;
  height: 32px;
}

/* Lower Section: Toolbar */
.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 10px 12px;
  background: rgba(0, 0, 0, 0.08);
  border-top: 1px solid var(--border);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  height: 32px;
  padding: 0 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.text-mode-btn {
  font-size: 0.8rem;
  font-weight: 700;
  gap: 6px;
  padding: 0 10px;
}

.style-divider {
  width: 1px;
  height: 16px;
  background: var(--border);
  margin: 0 6px;
}

.style-btn {
  width: 32px;
}

.send-circle-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--text-primary);
  color: var(--chat-bg);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-left: 6px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.send-circle-btn:hover:not(:disabled) {
  transform: scale(1.08);
}

.send-circle-btn:disabled {
  background: var(--border);
  color: var(--text-secondary);
  cursor: not-allowed;
}

.emoji-picker-position {
  position: absolute;
  bottom: 80px;
  right: 24px;
}

.quick-replies-position {
  position: absolute;
  bottom: 80px;
  left: 24px;
}

/* Edit/Reply message banners */
.edit-message-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 8px;
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
  color: var(--accent);
  flex-shrink: 0;
}

.edit-message-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  text-align: left;
}

.edit-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.edit-preview {
  font-size: 0.8rem;
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
  transition: all 0.2s ease;
  flex-shrink: 0;
  margin-left: 8px;
}

.cancel-edit-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.reply-message-banner {
  border-left: 4px solid var(--accent) !important;
}

@media (max-width: 768px) {
  .chat-input-container {
    padding: 10px;
  }
  
  .chat-input-card {
    border-radius: 12px;
  }

  .recording-canvas {
    display: none;
  }
}

@media (max-width: 560px) {
  .style-btn,
  .style-divider {
    display: none !important;
  }
}

/* ==========================================================================
   MEDIA PREVIEW MODAL STYLES (Paste / File Upload)
   ========================================================================== */
.media-preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.78);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.media-preview-modal {
  background: rgba(18, 22, 28, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.7);
  animation: scaleUp 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.media-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.header-file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.header-icon {
  color: var(--accent, #10b981);
  flex-shrink: 0;
}

.file-name-size {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  text-align: left;
}

.file-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: #f3f4f6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 380px;
}

.file-size {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 1px;
}

.close-preview-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-preview-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.media-preview-body {
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  min-height: 200px;
  max-height: 400px;
  overflow: hidden;
}

.preview-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.preview-video {
  max-width: 100%;
  max-height: 340px;
  border-radius: 8px;
}

.preview-audio {
  width: 100%;
  max-width: 400px;
}

.doc-preview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  width: 100%;
  box-sizing: border-box;
}

.doc-large-icon {
  color: var(--accent, #10b981);
}

.doc-name {
  font-size: 0.92rem;
  font-weight: 600;
  color: #f3f4f6;
  text-align: center;
  word-break: break-all;
  max-width: 90%;
}

.doc-size {
  font-size: 0.8rem;
  color: #9ca3af;
}

.media-preview-footer {
  padding: 16px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(18, 22, 28, 0.98);
}

.caption-input-box {
  width: 100%;
}

.caption-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 0.88rem;
  color: #f3f4f6;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.caption-input:focus {
  border-color: var(--accent, #10b981);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.preview-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.btn-preview-cancel {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #d1d5db;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 0.86rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-preview-cancel:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.btn-preview-send {
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  color: #fff;
  padding: 8px 20px;
  border-radius: 10px;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-preview-send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.btn-preview-send:disabled,
.btn-preview-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
