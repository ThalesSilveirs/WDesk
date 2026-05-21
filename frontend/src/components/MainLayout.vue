<template>
  <div class="app-layout">
    <Sidebar />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useChatStore } from '../store/chat'
import Sidebar from './Sidebar.vue'

const chatStore = useChatStore()

onMounted(() => {
  document.documentElement.setAttribute('data-theme', chatStore.theme)
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
}

@media (max-width: 768px) {
  .app-layout {
    flex-direction: column-reverse;
  }
}
</style>
