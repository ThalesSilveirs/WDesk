<template>
  <div class="login-container">
    <div class="login-card glass-effect">
      <div class="brand-logo">
        <h1 class="brand">WDesk</h1>
        <p>SaaS WhatsApp CRM</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <label>Usuário</label>
          <input v-model="username" type="text" class="input-glass" placeholder="Seu usuário" required />
        </div>
        
        <div class="input-group">
          <label>Senha</label>
          <input v-model="password" type="password" class="input-glass" placeholder="Sua senha" required />
        </div>
        
        <div v-if="errorMessage" class="error-banner">
          {{ errorMessage }}
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()
const chatStore = useChatStore()

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await chatStore.login(username.value, password.value)
    router.push('/')
  } catch (err) {
    errorMessage.value = 'Erro ao entrar. Verifique suas credenciais.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top right, var(--bg-card), var(--bg-dark));
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  border-radius: 24px;
  text-align: center;
}

.brand-logo h1 {
  font-size: 3rem;
  color: var(--accent);
  margin-bottom: 0;
}

.brand-logo p {
  color: var(--text-secondary);
  margin-bottom: 30px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: left;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.error-banner {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  text-align: center;
}

button {
  margin-top: 10px;
  height: 48px;
}

@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
    width: 95%;
    border-radius: 16px;
  }
  
  .brand-logo h1 {
    font-size: 2.2rem;
  }
}
</style>
