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
        <template v-for="msg in chatStore.messages" :key="msg.id">
          <!-- Mensagem de Evento do Sistema (Centralizada) -->
          <div v-if="isSystemMessage(msg)" class="system-message-center">
            <span class="system-message-badge" v-html="cleanSystemText(msg.body)"></span>
          </div>

          <!-- Mensagem Normal -->
          <div v-else class="message" :class="{ 'me': msg.from_me }">
            <div class="message-bubble">
              <!-- Media Display -->
              <div v-if="msg.media_type === 'image'" class="media-image clickable" @click="emit('openImage', resolvedUrls[msg.id] || msg.media_url || msg.body)">
                <img :src="resolvedUrls[msg.id] || msg.media_url || msg.body" />
              </div>
              <div v-else-if="msg.media_type === 'audio'" class="media-audio">
                <AudioPlayer :src="resolvedUrls[msg.id] || msg.media_url" :from-me="msg.from_me" />
              </div>
              <div v-else-if="msg.media_type === 'video'" class="media-video clickable" @click="emit('openVideo', resolvedUrls[msg.id] || msg.media_url || msg.body)">
                <video :src="resolvedUrls[msg.id] || msg.media_url || msg.body" preload="auto" muted playsinline></video>
                <div class="video-play-overlay">
                  <PlayIcon :size="24" class="play-icon" />
                </div>
              </div>
              <div v-else-if="msg.media_type === 'document'" class="media-document clickable" @click="openDocument(resolvedUrls[msg.id] || msg.media_url || msg.body)">
                <div class="doc-card">
                  <FileIcon :size="32" />
                  <div class="doc-info">
                    <span class="doc-name">Ver Documento</span>
                    <span class="doc-ext">PDF / Arquivo</span>
                  </div>
                </div>
              </div>
              
              <p v-if="msg.body && !isPlaceholder(msg.body) && msg.media_type !== 'audio'">
                {{ cleanBody(msg.body, msg.from_me) }}
              </p>
              <span class="msg-time">
                <span v-if="msg.from_me && msg.user_details" class="msg-attendant">{{ msg.user_details.first_name }} {{ msg.user_details.last_name }} • </span>
                {{ new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
              </span>
            </div>
          </div>
        </template>
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
      
      <!-- ESTADO NORMAL -->
      <template v-if="!isRecording && !hasRecording">
        <button class="attach-btn" @click="fileInput.click()" :disabled="!chatStore.activeTicket.user" title="Enviar Mídia">
          <PlusIcon :size="22" />
        </button>
        <textarea 
          ref="messageInput"
          v-model="newMessage" 
          @keydown="handleKeyDown"
          @paste="handlePaste"
          :placeholder="chatStore.activeTicket.user ? 'Digite uma mensagem...' : 'Aceite o atendimento para responder...'" 
          :disabled="!chatStore.activeTicket.user"
          rows="1"
        />
        <button 
          v-if="newMessage.trim()" 
          class="send-btn" 
          @click="send" 
          :disabled="!chatStore.activeTicket.user"
          title="Enviar Mensagem"
        >
          <SendIcon :size="20" />
        </button>
        <button 
          v-else 
          class="mic-btn" 
          @click="startRecording" 
          :disabled="!chatStore.activeTicket.user"
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
    </footer>
    <div v-else class="closed-banner">
      Este atendimento foi finalizado em {{ new Date(chatStore.activeTicket.updated_at).toLocaleString() }}.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useChatStore } from '../../store/chat'
import AudioPlayer from './AudioPlayer.vue'
import { 
  Contact as ContactIcon, 
  CheckCircle as CheckIcon, 
  ArrowRightLeft as TransferIcon, 
  FileText as FileIcon, 
  Plus as PlusIcon, 
  Send as SendIcon,
  ChevronLeft as ChevronLeftIcon,
  Mic as MicIcon,
  Trash2 as TrashIcon,
  Square as SquareIcon,
  Play as PlayIcon
} from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits([
  'update:showCRM', 
  'openPriorityModal', 
  'openTransferModal', 
  'openCloseModal', 
  'openImage',
  'openVideo'
])

const chatStore = useChatStore()
const newMessage = ref('')
const messageRef = ref(null)
const fileInput = ref(null)
const messageInput = ref(null)

const resolvedUrls = ref({})
const resolvedSources = ref({})

watch(() => chatStore.activeTicket?.id, () => {
  Object.values(resolvedUrls.value).forEach(url => {
    if (url && url.startsWith('blob:')) {
      try {
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error("Erro ao revogar object URL", e)
      }
    }
  })
  resolvedUrls.value = {}
  resolvedSources.value = {}
})

watch(() => chatStore.messages, (newMessages) => {
  if (!newMessages) return
  newMessages.forEach(msg => {
    const url = msg.media_url || msg.body
    if (url && resolvedSources.value[msg.id] !== url) {
      if (resolvedUrls.value[msg.id] && resolvedUrls.value[msg.id].startsWith('blob:')) {
        try {
          URL.revokeObjectURL(resolvedUrls.value[msg.id])
        } catch (e) {}
      }

      if (url.startsWith('data:')) {
        try {
          const parts = url.split(',')
          const contentType = parts[0].split(':')[1].split(';')[0]
          const raw = window.atob(parts[1])
          const rawLength = raw.length
          const uInt8Array = new Uint8Array(rawLength)
          for (let i = 0; i < rawLength; ++i) {
            uInt8Array[i] = raw.charCodeAt(i)
          }
          const blob = new Blob([uInt8Array], { type: contentType })
          resolvedUrls.value[msg.id] = URL.createObjectURL(blob)
          resolvedSources.value[msg.id] = url
        } catch (e) {
          console.error("Erro ao resolver base64 para msg " + msg.id, e)
          resolvedUrls.value[msg.id] = url
          resolvedSources.value[msg.id] = url
        }
      } else {
        resolvedUrls.value[msg.id] = url
        resolvedSources.value[msg.id] = url
      }
    }
  })
}, { immediate: true, deep: true })

onUnmounted(() => {
  Object.values(resolvedUrls.value).forEach(url => {
    if (url && url.startsWith('blob:')) {
      try {
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error("Erro ao revogar object URL", e)
      }
    }
  })
})

const goBack = () => {
  chatStore.activeTicket = null
}

const handleAccept = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.acceptTicket(chatStore.activeTicket.id)
  emit('openPriorityModal')
}

const isPlaceholder = (body) => {
  if (!body) return false
  const content = body.includes(':*\n\n') ? body.split(/:\*\n\n/).slice(1).join(':*\n\n') : body
  return ['Enviou um image', 'Enviou um video', 'Enviou um document', 'Enviou um audio', 'Enviou um sticker'].some(phrase => content.trim() === phrase)
}

const cleanBody = (body, fromMe) => {
  if (!body) return ''
  if (!fromMe) return body
  const parts = body.split(/:\*\n\n/)
  return parts.length > 1 ? parts.slice(1).join(/:\*\n\n/) : body
}

const openDocument = (url) => {
  if (!url) return
  if (url.startsWith('data:')) {
    try {
      const parts = url.split(',')
      const contentType = parts[0].split(':')[1].split(';')[0]
      const raw = window.atob(parts[1])
      const rawLength = raw.length
      const uInt8Array = new Uint8Array(rawLength)
      for (let i = 0; i < rawLength; ++i) {
        uInt8Array[i] = raw.charCodeAt(i)
      }
      const blob = new Blob([uInt8Array], { type: contentType })
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank')
    } catch (e) {
      console.error("Erro ao converter base64 para blob", e)
      window.open(url, '_blank')
    }
  } else {
    window.open(url, '_blank')
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    await chatStore.sendMedia(file)
    event.target.value = '' 
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
        await chatStore.sendMedia(file)
      }
    }
  }
}

const isSystemMessage = (msg) => {
  if (!msg.from_me || msg.user) return false
  const cleanText = msg.body?.replace(/^[\s_]+|[\s_]+$/g, '') || ''
  return (
    cleanText.startsWith('Seu atendimento foi') || 
    cleanText.startsWith('Seu atendimento iniciado') ||
    cleanText.includes('atendimento foi transferido')
  )
}

const cleanSystemText = (body) => {
  if (!body) return ''
  let text = body
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
  text = text.replace(/\*(.*?)\*/g, '<strong>$1</strong>')
  text = text.replace(/_(.*?)_/g, '<em>$1</em>')
  return text
}

const send = async () => {
  if (!newMessage.value.trim()) return
  const text = newMessage.value
  newMessage.value = ''
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
  }
  await chatStore.sendMessage(text)
  scrollToBottom()
}

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
    e.preventDefault()
    send()
  }
}

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

const scrollToBottom = () => {
  nextTick(() => { 
    if (messageRef.value) {
      messageRef.value.scrollTop = messageRef.value.scrollHeight 
    }
  })
}

// Controle de Gravação de Áudio
const isRecording = ref(false)
const hasRecording = ref(false)
const isSending = ref(false)
const recordedAudioUrl = ref(null)
const recordedFile = ref(null)

const recordingTime = ref(0)
const recordingTimer = ref(null)
const canvasRef = ref(null)

let mediaRecorder = null
let audioChunks = []
let audioCtx = null
let analyser = null
let source = null
let animationFrameId = null

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    
    let options = { mimeType: 'audio/webm' }
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options = { mimeType: 'audio/ogg' }
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options = { mimeType: 'audio/mp4' }
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options = {}
        }
      }
    }
    
    mediaRecorder = new MediaRecorder(stream, options)
    
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      analyser = audioCtx.createAnalyser()
      source = audioCtx.createMediaStreamSource(stream)
      source.connect(analyser)
    } catch (e) {
      console.warn("AudioContext não suportado ou falhou:", e)
    }
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }
    
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(track => track.stop())
      
      if (animationFrameId) cancelAnimationFrame(animationFrameId)
      if (audioCtx) {
        audioCtx.close().catch(() => {})
        audioCtx = null
      }
      analyser = null
      
      if (audioChunks.length === 0) return
      
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' })
      const extension = (mediaRecorder.mimeType || '').includes('ogg') ? 'ogg' : 
                        (mediaRecorder.mimeType || '').includes('mp4') ? 'mp4' : 'webm'
      
      if (recordedAudioUrl.value) {
        URL.revokeObjectURL(recordedAudioUrl.value)
      }
      
      recordedAudioUrl.value = URL.createObjectURL(audioBlob)
      recordedFile.value = new File([audioBlob], `audio_record.${extension}`, { type: audioBlob.type })
      
      hasRecording.value = true
    }
    
    isRecording.value = true
    hasRecording.value = false
    recordedAudioUrl.value = null
    recordedFile.value = null
    recordingTime.value = 0
    
    mediaRecorder.start()
    
    recordingTimer.value = setInterval(() => {
      recordingTime.value++
    }, 1000)
    
    nextTick(() => {
      drawWaveform()
    })
    
  } catch (err) {
    console.error("Erro ao iniciar gravação de áudio:", err)
    alert("Não foi possível acessar o microfone. Verifique as permissões do seu navegador.")
  }
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
  clearInterval(recordingTimer.value)
  recordingTime.value = 0
}

const cancelRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.onstop = () => {
      const stream = mediaRecorder.stream
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
    mediaRecorder.stop()
  }
  
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (audioCtx) {
    audioCtx.close().catch(() => {})
    audioCtx = null
  }
  analyser = null
  
  if (recordedAudioUrl.value) {
    URL.revokeObjectURL(recordedAudioUrl.value)
  }
  
  isRecording.value = false
  hasRecording.value = false
  recordedAudioUrl.value = null
  recordedFile.value = null
  clearInterval(recordingTimer.value)
  recordingTime.value = 0
  audioChunks = []
}

const sendRecording = async () => {
  if (recordedFile.value && !isSending.value) {
    isSending.value = true
    try {
      await chatStore.sendMedia(recordedFile.value)
      
      if (recordedAudioUrl.value) {
        URL.revokeObjectURL(recordedAudioUrl.value)
      }
      
      isRecording.value = false
      hasRecording.value = false
      recordedAudioUrl.value = null
      recordedFile.value = null
      scrollToBottom()
    } catch (err) {
      console.error("Erro ao enviar áudio gravado:", err)
      const errorMsg = err.response?.data?.error || err.message || "Erro desconhecido"
      alert("Não foi possível enviar o áudio: " + errorMsg)
    } finally {
      isSending.value = false
    }
  }
}

const drawWaveform = () => {
  if (!canvasRef.value || !analyser) return
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  analyser.fftSize = 32
  const bufferLength = analyser.frequencyBinCount
  const dataArray = new Uint8Array(bufferLength)
  
  const draw = () => {
    if (!isRecording.value) return
    animationFrameId = requestAnimationFrame(draw)
    analyser.getByteFrequencyData(dataArray)
    
    ctx.clearRect(0, 0, width, height)
    
    const barWidth = width / bufferLength
    let barHeight
    let x = 0
    
    for (let i = 0; i < bufferLength; i++) {
      barHeight = (dataArray[i] / 255) * height * 0.8
      if (barHeight < 2) barHeight = 2
      
      ctx.fillStyle = '#ef4444'
      const y = (height - barHeight) / 2
      
      ctx.fillRect(x, y, barWidth - 2, barHeight)
      x += barWidth
    }
  }
  
  draw()
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0')
  const secs = (seconds % 60).toString().padStart(2, '0')
  return `${mins}:${secs}`
}

onUnmounted(() => {
  if (recordingTimer.value) clearInterval(recordingTimer.value)
  if (recordedAudioUrl.value) {
    URL.revokeObjectURL(recordedAudioUrl.value)
  }
})

watch(() => chatStore.messages.length, scrollToBottom)
</script>

<style scoped>
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

.system-message-badge strong {
  color: var(--text-primary);
  font-weight: 600;
}

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

.message-bubble p {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

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

.media-video {
  margin: 8px 0 !important;
  max-width: 250px !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  border: 2px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
  position: relative !important;
  cursor: pointer !important;
  transition: transform 0.2s !important;
}

.media-video:hover {
  transform: scale(1.03) !important;
}

.media-video video {
  width: 100% !important;
  height: auto !important;
  display: block !important;
  object-fit: cover !important;
  max-height: 200px !important;
  background: #000 !important;
}

.video-play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.media-video:hover .video-play-overlay {
  background: rgba(0, 0, 0, 0.2);
}

.video-play-overlay .play-icon {
  color: white;
  background: rgba(16, 185, 129, 0.9);
  padding: 10px;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.media-video:hover .play-icon {
  transform: scale(1.1);
  background: var(--accent);
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
  align-items: flex-end;
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border);
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

.closed-banner {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  color: var(--text-secondary);
  font-size: 0.9rem;
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

.send-rec-btn:disabled, .cancel-rec-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

@media (max-width: 768px) {
  .messages-container {
    padding: 15px;
  }

  .message-bubble {
    max-width: 85%;
  }

  .media-image {
    max-width: 180px !important;
    margin: 4px 0 !important;
  }

  .media-image img {
    max-height: 180px !important;
  }

  .media-video {
    max-width: 220px !important;
    margin: 4px 0 !important;
  }

  .media-video video {
    max-height: 180px !important;
  }

  .media-audio {
    width: 100%;
    min-width: 200px;
  }

  .media-audio audio {
    width: 100%;
    display: block;
  }

  .chat-input {
    padding: 10px 15px;
    gap: 8px;
  }

  .chat-input textarea {
    padding: 10px;
    font-size: 0.9rem;
  }

  .attach-btn, .send-btn, .rec-btn, .cancel-rec-btn, .stop-rec-btn, .send-rec-btn {
    width: 36px;
    height: 36px;
    border-radius: 8px;
  }

  .recording-canvas {
    display: none;
  }
}
</style>