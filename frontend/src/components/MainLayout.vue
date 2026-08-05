<template>
  <div class="app-layout">
    <Sidebar />
    
    <div class="main-content-wrapper">
      <GlobalHeader />
      
      <!-- Main Router View with Page Transitions -->
      <div class="page-content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    
    <BroadcastModal />
    <InstanceWarningModal />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../store/chat'
import Sidebar from './Sidebar.vue'
import GlobalHeader from './GlobalHeader.vue'
import BroadcastModal from './dashboard/BroadcastModal.vue'
import InstanceWarningModal from './InstanceWarningModal.vue'

const chatStore = useChatStore()
const route = useRoute()

onMounted(() => {
  document.documentElement.setAttribute('data-theme', chatStore.theme)
  chatStore.fetchCurrentUser()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  height: 100dvh;
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

.page-content-wrapper {
  flex: 1;
  overflow: hidden;
  height: 100%;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }
  .main-content-wrapper {
    height: 100dvh;
  }
}
</style>
