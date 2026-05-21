<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-content-wrapper">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
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

.main-content-wrapper {
  flex: 1;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .app-layout {
    flex-direction: column-reverse;
  }
  .main-content-wrapper {
    height: calc(100vh - 60px);
  }
}
</style>
