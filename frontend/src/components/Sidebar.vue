<template>
  <aside class="mini-sidebar glass-effect">
    <div class="logo-wrapper">
      <img src="/favicon.png" alt="WDesk Favicon" class="app-logo" />
    </div>
    <router-link to="/" class="nav-item" exact-active-class="active" title="Atendimentos">
      <MessageCircleIcon :size="24" />
    </router-link>
    <router-link to="/customers" class="nav-item" active-class="active" title="Clientes">
      <ContactIcon :size="24" />
    </router-link>
    <router-link v-if="chatStore.userRole === 'admin'" to="/users" class="nav-item" active-class="active" title="Equipe">
      <UsersIcon :size="24" />
    </router-link>
    <router-link v-if="chatStore.userRole === 'admin'" to="/connections" class="nav-item" active-class="active" title="Conexões">
      <WifiIcon :size="24" />
    </router-link>
    <router-link v-if="chatStore.userRole === 'admin'" to="/settings" class="nav-item" active-class="active" title="Configurações">
      <SettingsIcon :size="24" />
    </router-link>
    <div class="bottom-actions">
      <button @click="chatStore.toggleTheme" class="nav-item theme-toggle" :title="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
        <SunIcon v-if="chatStore.theme === 'dark'" :size="24" />
        <MoonIcon v-else :size="24" />
      </button>
      <button @click="showLogoutModal = true" class="nav-item logout" title="Sair">
        <LogOutIcon :size="24" />
      </button>
    </div>
  </aside>

  <!-- Modal de Logout -->
  <div v-if="showLogoutModal" class="modal-overlay" @click="showLogoutModal = false">
    <div class="modal-content glass-effect small-modal" @click.stop>
      <h2>Sair do Sistema</h2>
      <p style="color: var(--text-secondary); margin-bottom: 20px;">Tem certeza que deseja encerrar sua sessão?</p>
      <div class="modal-actions">
        <button @click="showLogoutModal = false" class="cancel-btn">Cancelar</button>
        <button @click="logout" class="btn-danger-sm">Confirmar Sair</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../store/chat'
import {
  MessageCircle as MessageCircleIcon,
  Users as UsersIcon,
  LogOut as LogOutIcon,
  Contact as ContactIcon,
  Settings as SettingsIcon,
  Wifi as WifiIcon,
  Sun as SunIcon,
  Moon as MoonIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const showLogoutModal = ref(false)

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.mini-sidebar {
  width: 70px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  gap: 20px;
  flex-shrink: 0;
  height: 100%;
}

.logo-wrapper {
  padding: 10px;
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.app-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.3));
}

.nav-item {
  color: var(--text-secondary);
  padding: 12px;
  border-radius: 12px;
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.nav-item:hover,
.nav-item.active {
  background: var(--accent);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.logout {
  color: #ef4444;
  border: none;
  background: none;
}
.logout:hover {
  background: #ef4444;
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.theme-toggle {
  border: none;
  background: none;
  color: var(--text-secondary);
}
.theme-toggle:hover {
  color: var(--accent);
  background: transparent;
  box-shadow: none;
}

.bottom-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .mini-sidebar {
    width: 100%;
    height: 60px;
    flex-direction: row;
    border-right: none;
    border-top: 1px solid var(--border);
    padding: 0 10px;
    justify-content: space-between;
    gap: 5px;
    z-index: 50;
  }
  .logo-wrapper {
    display: none;
  }
  .bottom-actions {
    flex-direction: row;
    margin-top: 0;
    gap: 5px;
  }
  .nav-item {
    padding: 8px;
  }
}

/* Modais */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  width: 100%;
  max-width: 550px;
  padding: 35px;
  border-radius: 30px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  color: var(--text-primary);
}

.small-modal {
  max-width: 400px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 15px;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-danger-sm {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger-sm:hover {
  background: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}
</style>
