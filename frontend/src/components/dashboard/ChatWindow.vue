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

        <button @click="emit('openDeleteModal')" class="btn-danger-sm" title="Excluir Atendimento">
          <TrashIcon :size="18" />
          <span>Excluir</span>
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
          <div v-else :id="'msg-' + msg.message_id" class="message" :class="{ 'me': msg.from_me, 'highlight-msg': highlightedMessageId === msg.message_id }">
            <div class="message-bubble-wrapper">
              <div class="message-bubble">
                <!-- Quoted Message Display -->
                <div 
                  v-if="msg.quoted_message_body" 
                  class="quoted-message-bubble-container"
                  @click.stop="scrollToMessage(msg.quoted_message_id)"
                >
                  <span class="quoted-message-sender">{{ msg.quoted_message_sender || 'Contato' }}</span>
                  <p class="quoted-message-text">{{ cleanBody(msg.quoted_message_body, msg.quoted_message_sender === 'Você') }}</p>
                </div>
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
                
                <p 
                  v-if="msg.body && !isPlaceholder(msg.body) && msg.media_type !== 'audio'"
                  v-html="parseWhatsAppMarkdown(msg.body, msg.from_me)"
                ></p>
                
                <!-- Reaction Badges -->
                <div v-if="msg.reactions && msg.reactions.length > 0" class="message-reactions">
                  <span 
                    v-for="react in getGroupedReactions(msg.reactions)" 
                    :key="react.emoji" 
                    class="reaction-badge"
                    :class="{ 'reacted-by-me': react.reactedByMe }"
                    :title="react.users.join(', ')"
                    @click.stop="toggleReaction(msg, react.emoji)"
                  >
                    {{ react.emoji }} <span v-if="react.count > 1" class="reaction-count">{{ react.count }}</span>
                  </span>
                </div>

                <span class="msg-time">
                  <span v-if="msg.from_me && msg.user_details" class="msg-attendant">{{ msg.user_details.first_name }} {{ msg.user_details.last_name }} • </span>
                  <span v-if="msg.is_edited" class="msg-edited-badge" title="Mensagem editada">(editada) • </span>
                  {{ new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                </span>
              </div>

              <!-- Action Menu for Reactions -->
              <div class="message-actions-trigger" v-if="chatStore.activeTicket.status !== 'closed'">
                <button class="reaction-trigger-btn" @click.stop="toggleReactionPicker(msg.id)" title="Reagir">
                  <SmileIcon :size="16" />
                </button>
                <button 
                  class="reply-trigger-btn" 
                  @click.stop="startReplyingMessage(msg)" 
                  title="Responder"
                >
                  <ReplyIcon :size="16" />
                </button>
                <button 
                  v-if="msg.from_me && (!msg.media_type || msg.media_type === 'text' || msg.media_type === '')" 
                  class="edit-trigger-btn" 
                  @click.stop="startEditingMessage(msg)" 
                  title="Editar Mensagem"
                >
                  <EditIcon :size="16" />
                </button>
                
                <Transition name="pop">
                  <div v-if="activeReactionPickerId === msg.id" class="reactions-picker glass-effect">
                    <span 
                      v-for="emoji in ['👍', '❤️', '😂', '😮', '😢', '🙏']" 
                      :key="emoji" 
                      class="reaction-picker-emoji"
                      :class="{ 'active': hasAttendantReactedWith(msg.reactions, emoji) }"
                      @click.stop="toggleReaction(msg, emoji)"
                    >
                      {{ emoji }}
                    </span>
                  </div>
                </Transition>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <footer v-if="chatStore.activeTicket.status !== 'closed'" class="chat-input glass-effect">
      <!-- EMOJI PICKER POPUP -->
      <Transition name="fade">
        <div v-if="showEmojiPicker" class="emoji-picker-container glass-effect">
          <div class="emoji-picker-header">
            <button 
              v-for="(cat, idx) in emojiCategories" 
              :key="idx"
              class="emoji-category-tab"
              :class="{ active: activeCategoryIndex === idx }"
              @click="activeCategoryIndex = idx"
              :title="cat.name"
            >
              {{ cat.icon }}
            </button>
          </div>
          <div class="emoji-picker-body">
            <div class="emoji-grid">
              <span 
                v-for="emoji in emojiCategories[activeCategoryIndex].emojis" 
                :key="emoji"
                class="emoji-item"
                @click="insertEmoji(emoji)"
              >
                {{ emoji }}
              </span>
            </div>
          </div>
        </div>
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
        <button class="cancel-edit-btn" @click="cancelEditingMessage" title="Cancelar edição">
          <XIcon :size="16" />
        </button>
      </div>

      <!-- REPLY MESSAGE BANNER -->
      <div v-if="replyingMessage" class="edit-message-banner reply-message-banner">
        <div class="edit-message-info">
          <ReplyIcon :size="14" class="edit-icon-label" style="transform: scaleX(-1);" />
          <div class="edit-message-text">
            <span class="edit-label">Respondendo a <strong>{{ replyingMessage.from_me ? 'Você' : (chatStore.activeTicket.contact_details?.name || 'Cliente') }}</strong></span>
            <p class="edit-preview">{{ cleanBody(replyingMessage.body, replyingMessage.from_me) || (replyingMessage.media_type ? '📷 Mídia' : '') }}</p>
          </div>
        </div>
        <button class="cancel-edit-btn" @click="cancelReplyingMessage" title="Cancelar resposta">
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
          <button class="attach-btn" @click="fileInput.click()" :disabled="!chatStore.activeTicket.user" title="Enviar Mídia">
            <PlusIcon :size="22" />
          </button>
          <button class="emoji-btn" @click="toggleEmojiPicker" :disabled="!chatStore.activeTicket.user" title="Inserir Emoji">
            <SmileIcon :size="22" />
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
      </div>
    </footer>
    <div v-else class="closed-banner">
      Este atendimento foi finalizado em {{ new Date(chatStore.activeTicket.updated_at).toLocaleString() }}.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
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
  Play as PlayIcon,
  Smile as SmileIcon,
  Pencil as EditIcon,
  Reply as ReplyIcon,
  X as XIcon
} from 'lucide-vue-next'

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
  'openVideo'
])

const chatStore = useChatStore()
const newMessage = ref('')
const messageRef = ref(null)
const fileInput = ref(null)
const messageInput = ref(null)

const resolvedUrls = ref({})
const resolvedSources = ref({})

const activeReactionPickerId = ref(null)
const editingMessage = ref(null)
const replyingMessage = ref(null)
const highlightedMessageId = ref(null)

const startEditingMessage = (msg) => {
  cancelReplyingMessage()
  editingMessage.value = msg
  newMessage.value = msg.body
  setTimeout(() => {
    if (messageInput.value) {
      messageInput.value.focus()
    }
  }, 50)
}

const cancelEditingMessage = () => {
  editingMessage.value = null
  newMessage.value = ''
}

const startReplyingMessage = (msg) => {
  cancelEditingMessage()
  replyingMessage.value = msg
  setTimeout(() => {
    if (messageInput.value) {
      messageInput.value.focus()
    }
  }, 50)
}

const cancelReplyingMessage = () => {
  replyingMessage.value = null
}

const scrollToMessage = (quotedMsgId) => {
  if (!quotedMsgId) return
  const element = document.getElementById('msg-' + quotedMsgId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    highlightedMessageId.value = quotedMsgId
    setTimeout(() => {
      if (highlightedMessageId.value === quotedMsgId) {
        highlightedMessageId.value = null
      }
    }, 2000)
  }
}

const toggleReactionPicker = (msgId) => {
  if (activeReactionPickerId.value === msgId) {
    activeReactionPickerId.value = null
  } else {
    activeReactionPickerId.value = msgId
  }
}

const closeReactionPicker = () => {
  activeReactionPickerId.value = null
}

const getGroupedReactions = (reactions) => {
  if (!reactions || !reactions.length) return []
  const groups = {}
  reactions.forEach(r => {
    if (!groups[r.emoji]) {
      groups[r.emoji] = { emoji: r.emoji, count: 0, users: [], reactedByMe: false }
    }
    groups[r.emoji].count++
    groups[r.emoji].users.push(r.from_me ? 'Você' : 'Cliente')
    if (r.from_me) {
      groups[r.emoji].reactedByMe = true
    }
  })
  return Object.values(groups)
}

const hasAttendantReactedWith = (reactions, emoji) => {
  if (!reactions) return false
  return reactions.some(r => r.emoji === emoji && r.from_me)
}

const toggleReaction = async (msg, emoji) => {
  activeReactionPickerId.value = null
  const alreadyReacted = hasAttendantReactedWith(msg.reactions, emoji)
  const newEmoji = alreadyReacted ? '' : emoji
  await chatStore.reactToMessage(chatStore.activeTicket.id, msg.id, newEmoji)
}

// --- EMOJI PICKER & WHATSAPP MARKDOWN ---
const showEmojiPicker = ref(false)
const activeCategoryIndex = ref(0)

const emojiCategories = [
  {
    name: 'Carinhas',
    icon: '😊',
    emojis: ['😀','😃','😄','😁','😆','😅','😂','🤣','😊','😇','🙂','🙃','😉','😌','😍','🥰','😘','😗','😙','😚','😋','😛','😝','😜','🤪','🤨','🧐','🤓','😎','🥸','🤩','🥳','😏','😒','😞','😔','😟','😕','🙁','☹️','😣','😖','😫','😩','🥺','😢','😭','😤','😠','😡','🤬','🤯','😳','🥵','🥶','😱','😨','😰','😥','😓','🤗','🤔','🫣','🤭','🤫','🫡','✍️','👏','🙌','👐','🤲','🤝','🙏','👍','👎','👊','✊','🤛','🤜','🤞','🤟','🤘','👌','🤌','🤏','✌️','🤞','🤙','👈','👉','👆','🖕','👇','☝️']
  },
  {
    name: 'Animais & Natureza',
    icon: '🐱',
    emojis: ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐻‍❄️','🐨','🐯','🦁','🐮','🐷','🐽','🐸','🐵','🙈','🙉','🙊','🐒','🐔','🐧','🐦','🐤','🐣','🐥','🦆','🦅','🦉','🦇','🐺','🐗','🐴','🦄','🐝','🪱','🐛','🦋','🐌','🐞','🐜','🪰','🪲','🪳','🦟','🦗','🕷️','🕸️','🦂','🐢','🐍','🦎','🦖','🦕','🐙','🦑','🦞','🦀','🐡','🐠','🐟','🐬','🐳','🐋','🦈','🐊','🐅','🐆','🦓','🦍','🦧','🦣','🐘','🦛','🦏','🐪','🐫','🦒','🦘','🦬','🐃','🐂','🐄','🐎','🐖','🐏','🐑','🦙','🐐','🦌','🐕','🐩','🐈','🐈‍⬛','🐓','🦃','🦚','🦜','\uD83E\uDDF0','🦩','🕊️','🐇','\uD83E\uDD9D','🦨','🦡','🦫','🦦','🦥','🐁','🐀','🐿️','🦔','🐾','🐉','🐲','🌵','🎄','🌲','🌳','🌴','🪵','🌱','🌿','☘️','🍀','🎍','🪴','🍃','🍂','🍁','🍄','🐚','🪨','🌾','💐','🌷','🌹','🥀','🌺','🌸','🌼','🌻','🌞','🌝','🌛','🌜','🌚','🌕','\uD83C\uDF16','🌗','🌘','🌑','🌒','🌓','🌔','🌙','🌎','🌍','🌏','🪐','💫','⭐️','🌟','✨','⚡️','☄️','💥','🔥','🌪️','🌈','☀️','🌤️','\uD83C\uDF24','🌥️','☁️','🌦️','🌧️','⛈️','🌩️','🌨️','❄️','☃️','⛄️','💨','💧','💦','🌪️','🌫️']
  },
  {
    name: 'Comida & Bebida',
    icon: '🍏',
    emojis: ['🍏','🍎','🍐','🍊','🍋','🍌','🍉','🍇','🍓','🫐','🍈','🍒','🍑','🥭','🍍','🥥','🥝','🍅','🍆','🥑',' broccoli','🥬','🥒','🌶️','🫑','🧅','🧄','🥔','🥕','🌽','🍠','🥐','🥯','🍞','🥖','🥨','🧀','🥚','🍳','🧈','🥞','🧇','🥓','🥩','🍗','🍖','🌭','🍔','🍟','🍕','🫓','🥪','🥙','🧆','🌮','🌯','🥘','🍲','🫕','🥣','🥗','🍿','🧂','🥫','🍱','🍘','🍙','🍚','🍛','🍜','🍝','🍠','🍢','🍣','🍤','🍥','🥮','🍡','🥟','🥠','🥡','🦀','🦞','🦐','🦑','🦪','🍦','🍧','🍨','🍩','🍪','🎂','🍰','🧁','🥧','🍫','🍬','🍭','🍮','🍯','🍼','🥛','☕️','🫖','🍵','🍶','🍾','🍷','🍸','🍹','🍺','🍻','🥂','🥃','🥤','🧋','🧃','🧉','🧊']
  },
  {
    name: 'Atividades & Esportes',
    icon: '⚽',
    emojis: ['⚽','🏀','🏈','⚾','🥎','🎾','🏐','🏉','🥏','🎱','🪀','🏓','🏸','🏒','🏑','🥍','🏏','🪃','🥅','⛳️','🪁','🏹','\uD83C\uDFA3','🤿','🥊','🥋','🎽','🛹','🛼','🛷','⛸️','🥌','🎿','\uD83C\uDFC2','🏂','🪂','🏋️‍♀️','🏋️‍♂️','🏋️','🤼‍♀️','🤼‍♂️','🤼','🤸‍♀️','🤸‍♂️','🤸','⛹️‍♀️','⛹️‍♂️','⛹️','🤾‍♀️','🤾‍♂️','🤾','🏌️‍♀️','🏌️‍♂️','🏌️','🏄‍♀️','🏄‍♂️','🏄','🏊‍♀️','🏊‍♂️','🏊','\uD83E\uDD3D','🚣‍♀️','🚣‍♂️','🚣','🧗‍♀️','🧗‍♂️','🧗','🚴‍♀️','🚴‍♂️','🚴','🚵‍♀️','🚵‍♂️','🚵','🏆','\uD83E\uDD47','🥈','🥉','🏅','🎖️','🎫','🎟️','🎭','🎨','🎬','🎤','🎧','🎼','🎹','🥁','🪗','🎸','🪕','🎻','🎲','🧩','🎳','🎯','🎮','🎰']
  },
  {
    name: 'Objetos & Símbolos',
    icon: '💡',
    emojis: ['⌚️','📱','📲','💻','⌨️','🖥️','🖨️','🖱️','🖲️','🕹️','🗜️','💽','💾','💿','📀','📼','📷','📸','📹','🎥','📽️','🎞️','📞','☎️','📟','📠','📺','📻','🎙️','🎚️','🎛️','🧭','⏱️','⏲️','⏰','🕰️','\uD83E\uDDF3','⏳','📡','🔋','🔌','💡',' flashlight','🕯️','🪔','🧯','🛢️','💸','💵','\uD83D\uDCB4','💶','💷','🪙','💰','💳','💎','⚖️','\uD83E\uDE9C','🔧','🔨','⚒️','🛠️','⛏️','🪛','🔩','⚙️','🧱','⛓️','🧲','🔫','💣','🧨','🪓','🔪','🗡️','⚔️','🛡️','🚬','⚰️','🪦','⚱️','🏺','🔮','📿','🧿','💈','🧫','🧪','🌡️','🧬','🔬','🔭','📡','🛰️','💉','🩸','💊','🩹','🩺','🚪','🛗','🪞','🪟','🛏️','🛋️','🪑','🚽','🪠','🚿','🛁','🪒','🧴','🧷','🧹','🧺','🧻','🧼','🧽','🪣','🔑','🗝️']
  }
]

const toggleEmojiPicker = (e) => {
  e.stopPropagation()
  showEmojiPicker.value = !showEmojiPicker.value
}

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

const handleWindowClick = (e) => {
  if (showEmojiPicker.value) {
    const picker = document.querySelector('.emoji-picker-container')
    const btn = document.querySelector('.emoji-btn')
    if (picker && !picker.contains(e.target) && btn && !btn.contains(e.target)) {
      showEmojiPicker.value = false
    }
  }
  
  if (activeReactionPickerId.value !== null) {
    const picker = document.querySelector('.reactions-picker')
    const trigger = e.target.closest('.reaction-trigger-btn')
    if (picker && !picker.contains(e.target) && !trigger) {
      activeReactionPickerId.value = null
    }
  }
}

onMounted(() => {
  window.addEventListener('click', handleWindowClick)
})

onUnmounted(() => {
  window.removeEventListener('click', handleWindowClick)
})

// WhatsApp Markdown Parser
const escapeHtml = (text) => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const applyInlineFormatting = (line) => {
  // Bold (*bold*)
  line = line.replace(/\*([^*]+?)\*/g, '<strong>$1</strong>')
  // Italic (_italic_)
  line = line.replace(/_([^_]+?)_/g, '<em>$1</em>')
  // Strikethrough (~strike~)
  line = line.replace(/~([^~]+?)~/g, '<del>$1</del>')
  return line
}

const parseWhatsAppMarkdown = (body, fromMe) => {
  let text = cleanBody(body, fromMe)
  if (!text) return ''
  text = escapeHtml(text)
  
  // 1. Monospace blocks (```code```)
  text = text.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>')
  
  // 2. Inline code (`code`)
  text = text.replace(/`([^`\n]+?)`/g, '<code>$1</code>')
  
  // Split into lines for blockquotes and lists
  const lines = text.split('\n')
  const processedLines = []
  
  for (let line of lines) {
    // Blockquote
    if (line.startsWith('&gt;')) {
      let content = line.substring(4)
      content = applyInlineFormatting(content)
      processedLines.push(`<blockquote>${content}</blockquote>`)
      continue
    }
    
    // Bullet list (* or -)
    const bulletMatch = line.match(/^(\*|-)\s+(.*)/)
    if (bulletMatch) {
      let content = applyInlineFormatting(bulletMatch[2])
      processedLines.push(`<ul><li>${content}</li></ul>`)
      continue
    }
    
    // Numbered list (1. 2. etc.)
    const numMatch = line.match(/^(\d+)\.\s+(.*)/)
    if (numMatch) {
      let content = applyInlineFormatting(numMatch[2])
      processedLines.push(`<ol start="${numMatch[1]}"><li>${content}</li></ol>`)
      continue
    }
    
    processedLines.push(applyInlineFormatting(line))
  }
  
  text = processedLines.join('\n')
  
  // Merge consecutive list items
  text = text.replace(/<\/ul>\n<ul>/g, '')
  text = text.replace(/<\/ol>\n<ol[^>]*>/g, '')
  
  // Convert newlines (outside of pre/list blocks) to <br>
  text = text.split('\n').map((line) => {
    if (line.endsWith('</li>') || line.endsWith('</ul>') || line.endsWith('</ol>') || line.endsWith('</blockquote>') || line.startsWith('<pre>') || line.startsWith('</pre>') || line.startsWith('<code>') || line.startsWith('</code>')) {
      return line
    }
    return line + '<br>'
  }).join('\n')
  
  text = text.replace(/<br>\n*(<\/ul>|<\/ol>|<blockquote>|<\/blockquote>|<pre>|<\/pre>)/g, '$1')
  
  return text
}

watch(() => chatStore.activeTicket?.id, () => {
  editingMessage.value = null
  replyingMessage.value = null
  highlightedMessageId.value = null
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
  if (editingMessage.value) {
    const msgToEdit = editingMessage.value
    editingMessage.value = null
    await chatStore.editMessage(chatStore.activeTicket.id, msgToEdit.id, text)
  } else if (replyingMessage.value) {
    const msgToReply = replyingMessage.value
    replyingMessage.value = null
    await chatStore.sendMessage(text, msgToReply.id)
  } else {
    await chatStore.sendMessage(text)
  }
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

.btn-danger-sm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: #f87171;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-danger-sm:hover {
  background: #ef4444;
  color: white;
  border-color: #ef4444;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
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
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.message.me .message-bubble { 
  background: var(--accent); 
  color: #ffffff;
  border-color: rgba(16, 185, 129, 0.2);
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
}

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

  .attach-btn, .send-btn, .rec-btn, .cancel-rec-btn, .stop-rec-btn, .send-rec-btn, .emoji-btn {
    width: 36px;
    height: 36px;
    border-radius: 8px;
  }

  .recording-canvas {
    display: none;
  }
}

/* --- Emoji Picker Style --- */
.emoji-picker-container {
  position: absolute;
  bottom: 75px;
  left: 20px;
  width: 320px;
  height: 350px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  z-index: 100;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
  padding: 10px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

[data-theme='light'] .emoji-picker-container {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
}

.emoji-picker-header {
  display: flex;
  justify-content: space-around;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin-bottom: 8px;
}

.emoji-category-tab {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.emoji-category-tab:hover {
  background: var(--glass);
}

.emoji-category-tab.active {
  background: rgba(16, 185, 129, 0.15);
  border-bottom: 2px solid var(--accent);
  border-radius: 8px 8px 0 0;
}

.emoji-picker-body {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.emoji-item {
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: transform 0.1s, background 0.1s;
  user-select: none;
}

.emoji-item:hover {
  background: var(--glass);
  transform: scale(1.15);
}

.emoji-item:active {
  transform: scale(0.95);
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

/* --- WhatsApp Formatting Styles --- */
.message-bubble blockquote {
  border-left: 3px solid var(--accent);
  margin: 5px 0;
  padding: 2px 10px;
  color: var(--text-secondary);
  font-style: italic;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 0 4px 4px 0;
}

.message-bubble pre {
  background: rgba(0, 0, 0, 0.15);
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
}

.message-bubble code {
  font-family: 'Courier New', Courier, monospace;
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message.me .message-bubble code {
  background: rgba(255, 255, 255, 0.2);
}

.message.me .message-bubble blockquote {
  border-left-color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.message-bubble pre code {
  background: none;
  padding: 0;
}

.message-bubble ul, .message-bubble ol {
  margin: 6px 0;
  padding-left: 20px;
}

.message-bubble li {
  margin: 3px 0;
}

/* Msg Edited Badge */
.msg-edited-badge {
  font-style: italic;
  font-weight: 500;
  opacity: 0.8;
}
.message.me .msg-edited-badge {
  color: rgba(255, 255, 255, 0.7);
}

/* Reaction Badges Container */
.message-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  position: relative;
  z-index: 2;
}

.reaction-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.reaction-badge:hover {
  background: var(--border);
  transform: scale(1.05);
}

.reaction-badge.reacted-by-me {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.reaction-count {
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.reaction-badge.reacted-by-me .reaction-count {
  color: var(--accent);
}

/* Hover trigger for reactions */
.message-bubble-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 65%;
  position: relative;
}

.message.me .message-bubble-wrapper {
  flex-direction: row-reverse;
}

.message-bubble-wrapper .message-bubble {
  max-width: 100%;
}

.message-actions-trigger {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  position: relative;
  display: flex;
  align-items: center;
}

.message-bubble-wrapper:hover .message-actions-trigger {
  opacity: 1;
  pointer-events: auto;
}

.reaction-trigger-btn, .edit-trigger-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: background 0.2s ease, color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reaction-trigger-btn:hover, .edit-trigger-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Reactions Emoji Picker Dropdown */
.reactions-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  display: flex;
  gap: 6px;
  padding: 6px;
  border-radius: 30px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 50;
  backdrop-filter: blur(10px);
}

.message.me .reactions-picker {
  left: auto;
  right: 0;
}

.reaction-picker-emoji {
  cursor: pointer;
  font-size: 1.25rem;
  padding: 4px;
  border-radius: 50%;
  transition: transform 0.2s ease, background 0.2s ease;
  user-select: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
}

.reaction-picker-emoji:hover {
  transform: scale(1.25);
  background: var(--bg-hover);
}

.reaction-picker-emoji.active {
  background: rgba(16, 185, 129, 0.15);
}

/* Transition pop */
.pop-enter-active,
.pop-leave-active {
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.2s ease;
}

.pop-enter-from,
.pop-leave-to {
  transform: scale(0.8) translateY(10px);
  opacity: 0;
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

.quoted-message-bubble-container {
  background: rgba(148, 163, 184, 0.08);
  border-left: 4px solid var(--accent);
  padding: 8px 10px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  max-width: 100%;
  display: block;
  text-align: left;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
  transition: background-color 0.2s ease;
}
.quoted-message-bubble-container:hover {
  background: rgba(148, 163, 184, 0.15);
}
.message.me .quoted-message-bubble-container {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: #ffffff;
}
.message.me .quoted-message-bubble-container:hover {
  background: rgba(255, 255, 255, 0.22);
}
.quoted-message-sender {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  display: block;
  margin-bottom: 3px;
}
.message.me .quoted-message-sender {
  color: #a7f3d0;
}
.quoted-message-text {
  font-size: 0.8rem;
  margin: 0;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.message.me .quoted-message-text {
  color: rgba(255, 255, 255, 0.85);
}

.message.highlight-msg .message-bubble {
  box-shadow: 0 0 18px var(--accent);
  border-color: var(--accent);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.reply-trigger-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.reply-trigger-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: scale(1.05);
}

.reply-message-banner {
  border-left: 4px solid var(--accent) !important;
}
</style>