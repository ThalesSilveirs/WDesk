<template>
  <div
    :id="'msg-' + msg.message_id"
    ref="bubbleRef"
    class="message"
    :class="{ 'me': msg.from_me, 'highlight-msg': highlighted }"
    v-memo="[msg.body, msg.reactions?.length, msg.is_edited, highlighted, activeReactionPickerId === msg.id, resolvedUrl]"
  >
    <div class="message-bubble-wrapper">
      <div class="message-bubble">
        <!-- Quoted Message Display -->
        <div
          v-if="msg.quoted_message_body"
          class="quoted-message-bubble-container"
          @click.stop="emit('clickQuoted', msg.quoted_message_id)"
        >
          <span class="quoted-message-sender">{{ msg.quoted_message_sender || 'Contato' }}</span>
          <p class="quoted-message-text">{{ cleanBody(msg.quoted_message_body, msg.quoted_message_sender === 'Você') }}</p>
        </div>

        <!-- Media Display -->
        <div v-if="msg.media_type === 'image'" class="media-image clickable" @click="emit('openImage', resolvedUrl || msg.media_url || msg.body)">
          <img :src="resolvedUrl || msg.media_url || msg.body" loading="lazy" />
        </div>
        <div v-else-if="msg.media_type === 'audio'" class="media-audio">
          <AudioPlayer :src="resolvedUrl || msg.media_url" :from-me="msg.from_me" />
        </div>
        <div v-else-if="msg.media_type === 'video'" class="media-video clickable" @click="emit('openVideo', resolvedUrl || msg.media_url || msg.body)">
          <video :src="resolvedUrl || msg.media_url || msg.body" preload="metadata" muted playsinline></video>
          <div class="video-play-overlay">
            <PlayIcon :size="24" class="play-icon" />
          </div>
        </div>
        <div v-else-if="msg.media_type === 'document'" class="media-document clickable" @click="openDocument(resolvedUrl || msg.media_url || msg.body)">
          <div class="doc-card">
            <FileIcon :size="32" />
            <div class="doc-info">
              <span class="doc-name">Ver Documento</span>
              <span class="doc-ext">PDF / Arquivo</span>
            </div>
          </div>
        </div>

        <!-- Text Display -->
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
            @click.stop="emit('react', { msg, emoji: react.emoji })"
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

      <!-- Action Menu for Reactions / Reply / Edit (when not closed) -->
      <MessageActionBar
        v-if="ticketStatus !== 'closed'"
        :msg="msg"
        :active-reaction-picker-id="activeReactionPickerId"
        @reply="emit('reply', $event)"
        @edit="emit('edit', $event)"
        @react="emit('react', $event)"
        @toggle-picker="emit('toggleReactionPicker', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AudioPlayer from '../AudioPlayer.vue'
import MessageActionBar from './MessageActionBar.vue'
import {
  cleanBody,
  isPlaceholder,
  parseWhatsAppMarkdown,
  openDocument
} from '../../../utils/whatsappMarkdown'
import {
  FileText as FileIcon,
  Play as PlayIcon
} from 'lucide-vue-next'

const props = defineProps({
  msg: {
    type: Object,
    required: true
  },
  resolvedUrl: {
    type: String,
    default: ''
  },
  highlighted: {
    type: Boolean,
    default: false
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
  'toggleReactionPicker',
  'visible'
])

const bubbleRef = ref(null)
let observer = null

onMounted(() => {
  if (props.msg.media_type) {
    observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        emit('visible', props.msg)
        if (observer) {
          observer.disconnect()
          observer = null
        }
      }
    }, { rootMargin: '100px' })
    if (bubbleRef.value) {
      observer.observe(bubbleRef.value)
    }
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})

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
</script>

<style scoped>
.message {
  display: flex;
  width: 100%;
  position: relative;
  z-index: 1;
}

.message.me {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 100%;
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
  text-align: left;
}

.message-bubble p {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  text-align: left;
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
  text-align: left;
}

.doc-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.doc-ext {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

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

.message-bubble-wrapper :deep(.message-actions-trigger) {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.message-bubble-wrapper:hover :deep(.message-actions-trigger) {
  opacity: 1;
  pointer-events: auto;
}

.msg-edited-badge {
  font-style: italic;
  font-weight: 500;
  opacity: 0.8;
}

.message.me .msg-edited-badge {
  color: rgba(255, 255, 255, 0.7);
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

@media (max-width: 768px) {
  .message-bubble {
    max-width: 100%;
  }

  .message-bubble-wrapper {
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
}
</style>
