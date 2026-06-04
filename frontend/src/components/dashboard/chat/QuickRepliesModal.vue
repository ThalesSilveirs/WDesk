<template>
  <div class="quick-replies-modal glass-effect">
    <div class="quick-replies-header">
      <ZapIcon :size="16" class="lightning-icon" />
      <h3>Respostas Rápidas</h3>
    </div>
    <div v-if="filteredReplies.length === 0" class="no-replies">
      Nenhuma resposta rápida encontrada.
    </div>
    <div v-else class="replies-list" ref="listRef">
      <button
        v-for="(reply, idx) in filteredReplies"
        :key="reply.id"
        class="reply-item"
        :class="{ active: idx === activeIdx }"
        @click="selectReply(reply)"
        @mouseenter="activeIdx = idx"
      >
        <div class="reply-shortcut">/{{ reply.title }}</div>
        <div class="reply-body">{{ reply.body }}</div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Zap as ZapIcon } from 'lucide-vue-next'
import { useChatStore } from '../../../store/chat'

const props = defineProps({
  filterQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select', 'close'])
const chatStore = useChatStore()
const listRef = ref(null)
const activeIdx = ref(0)

onMounted(async () => {
  await chatStore.fetchQuickReplies()
  window.addEventListener('keydown', handleKeyDown, true)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown, true)
})

const filteredReplies = computed(() => {
  const query = props.filterQuery.toLowerCase().trim()
  if (!query) return chatStore.quickReplies

  return chatStore.quickReplies.filter(
    (reply) =>
      reply.title.toLowerCase().includes(query) ||
      reply.body.toLowerCase().includes(query)
  )
})

watch(filteredReplies, () => {
  activeIdx.value = 0
}, { deep: true })

const selectReply = (reply) => {
  emit('select', reply.body)
}

const handleKeyDown = (e) => {
  if (filteredReplies.value.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value + 1) % filteredReplies.value.length
    scrollToActive()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value - 1 + filteredReplies.value.length) % filteredReplies.value.length
    scrollToActive()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    e.stopPropagation()
    selectReply(filteredReplies.value[activeIdx.value])
  } else if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

const scrollToActive = () => {
  const container = listRef.value
  if (!container) return
  const activeEl = container.querySelector('.reply-item.active')
  if (!activeEl) return

  const containerHeight = container.clientHeight
  const elemTop = activeEl.offsetTop
  const elemHeight = activeEl.offsetHeight

  if (elemTop < container.scrollTop) {
    container.scrollTop = elemTop
  } else if (elemTop + elemHeight > container.scrollTop + containerHeight) {
    container.scrollTop = elemTop + elemHeight - containerHeight
  }
}
</script>

<style scoped>
.quick-replies-modal {
  position: absolute;
  bottom: calc(100% + 12px);
  left: 16px;
  width: 320px;
  max-height: 280px;
  border-radius: 12px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  overflow: hidden;
  backdrop-filter: blur(16px);
  background: var(--bg-surface-glass, rgba(22, 28, 36, 0.9));
}

.quick-replies-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  background: rgba(255, 255, 255, 0.02);
}

.lightning-icon {
  color: #ffb700;
}

.quick-replies-header h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary, #ffffff);
}

.replies-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.reply-item {
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s ease;
}

.reply-item.active,
.reply-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.reply-shortcut {
  font-size: 11px;
  font-weight: 700;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  width: fit-content;
}

.reply-body {
  font-size: 13px;
  color: var(--text-secondary, #b0b3b8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-replies {
  padding: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted, #74767b);
}
</style>
