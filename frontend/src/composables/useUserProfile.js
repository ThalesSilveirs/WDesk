import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'

export function useUserProfile() {
  const router = useRouter()
  const chatStore = useChatStore()

  const showProfileMenu = ref(false)
  const showLogoutModal = ref(false)
  const currentStatus = ref('online')
  const profileContainerRef = ref(null)

  const userDisplayName = computed(() => {
    if (!chatStore.user) return 'Carregando...'
    return chatStore.user.first_name 
      ? `${chatStore.user.first_name} ${chatStore.user.last_name || ''}` 
      : chatStore.user.username
  })

  const userInitials = computed(() => {
    if (!chatStore.user) return '?'
    const name = chatStore.user.first_name || chatStore.user.username
    return name.charAt(0).toUpperCase()
  })

  const toggleProfileMenu = () => {
    showProfileMenu.value = !showProfileMenu.value
  }

  const changeStatus = (status) => {
    currentStatus.value = status
    showProfileMenu.value = false
    chatStore.changeUserStatus(status)
  }

  const triggerLogout = () => {
    showProfileMenu.value = false
    showLogoutModal.value = true
  }

  const logout = () => {
    chatStore.logout()
    router.push('/login')
  }

  const handleStatusSynced = (e) => {
    currentStatus.value = e.detail.status
  }

  const handleClickOutside = (event) => {
    if (profileContainerRef.value && !profileContainerRef.value.contains(event.target)) {
      showProfileMenu.value = false
    }
  }

  onMounted(() => {
    window.addEventListener('user-status-synced', handleStatusSynced)
    window.addEventListener('click', handleClickOutside)
    if (chatStore.user?.status) {
      currentStatus.value = chatStore.user.status
    }
  })

  onUnmounted(() => {
    window.removeEventListener('user-status-synced', handleStatusSynced)
    window.removeEventListener('click', handleClickOutside)
  })

  return {
    showProfileMenu,
    showLogoutModal,
    currentStatus,
    profileContainerRef,
    userDisplayName,
    userInitials,
    toggleProfileMenu,
    changeStatus,
    triggerLogout,
    logout
  }
}
