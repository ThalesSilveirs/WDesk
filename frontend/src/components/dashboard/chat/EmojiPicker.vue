<template>
  <div class="emoji-picker-container glass-effect" ref="pickerRef">
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
          @click="emit('select', emoji)"
        >
          {{ emoji }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { emojiCategories } from '../../../constants/emojis'

const emit = defineEmits(['select'])

const activeCategoryIndex = ref(0)
const pickerRef = ref(null)

defineExpose({
  pickerRef
})
</script>

<style scoped>
.emoji-picker-container {
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
  box-sizing: border-box;
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
</style>
