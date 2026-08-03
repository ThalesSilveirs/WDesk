import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import App from './App.vue'
import axios from 'axios'
import { useChatStore } from './store/chat'

// Setup global Axios request interceptor for Authorization headers
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Setup global Axios response interceptor for Authorization/Authentication errors (401 Unauthorized)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const chatStore = useChatStore()
      chatStore.logout()
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

// Aplicar Modo de Alto Desempenho se ativado no localStorage
if (localStorage.getItem('performanceMode') === 'true') {
  document.documentElement.classList.add('performance-mode')
}

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Inicializar data-theme a partir do store
const chatStore = useChatStore()
document.documentElement.setAttribute('data-theme', chatStore.theme)

app.mount('#app')
