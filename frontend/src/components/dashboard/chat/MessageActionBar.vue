<template>
  <div class="message-actions-trigger">
    <button class="reaction-trigger-btn" @click.stop="emit('toggle-picker', msg.id)" title="Reagir">
      <SmileIcon :size="16" />
    </button>
    <button class="reply-trigger-btn" @click.stop="emit('reply', msg)" title="Responder">
      <ReplyIcon :size="16" />
    </button>
    <button
      v-if="msg.from_me && (!msg.media_type || msg.media_type === 'text' || msg.media_type === '')"
      class="edit-trigger-btn"
      @click.stop="emit('edit', msg)"
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
          @click.stop="emit('react', { msg, emoji })"
        >
          {{ emoji }}
        </span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import {
  Smile as SmileIcon,
  Reply as ReplyIcon,
  Pencil as EditIcon
} from 'lucide-vue-next'

const props = defineProps({
  msg: {
    type: Object,
    required: true
  },
  activeReactionPickerId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['reply', 'edit', 'react', 'toggle-picker'])

const hasAttendantReactedWith = (reactions, emoji) => {
  if (!reactions) return false
  return reactions.some(r => r.emoji === emoji && r.from_me)
}
</script>

<style scoped>
.message-actions-trigger {
  display: flex;
  align-items: center;
  position: relative;
}

.reaction-trigger-btn,
.edit-trigger-btn,
.reply-trigger-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reaction-trigger-btn:hover,
.edit-trigger-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.reply-trigger-btn {
  border-radius: 8px;
}

.reply-trigger-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: scale(1.05);
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
</style>
