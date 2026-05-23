<template>
  <div class="sidebar-container">
    <aside class="sidebar glass-effect">
      <!-- Brand Logo Header -->
      <div class="logo-section">
        <div class="logo-icon">
          <MessageCircleIcon :size="24" />
        </div>
        <div class="logo-text">
          <span class="brand-name">OmniChat</span>
          <span class="brand-sub">Enterprise Support</span>
        </div>
      </div>

      <!-- New Broadcast Action Button -->
      <div class="broadcast-section">
        <button @click="chatStore.showBroadcastModal = true" class="btn-broadcast-main">
          <MegaphoneIcon :size="18" />
          <span>New Broadcast</span>
        </button>
      </div>

      <!-- Navigation Links -->
      <nav class="nav-links">
        <router-link to="/" class="nav-link-item" exact-active-class="active">
          <LayoutGridIcon :size="20" />
          <span class="link-label">Dashboard</span>
        </router-link>

        <router-link to="/conversations" class="nav-link-item" active-class="active">
          <MessageSquareIcon :size="20" />
          <span class="link-label">Conversations</span>
        </router-link>

        <router-link v-if="chatStore.userRole === 'admin'" to="/users" class="nav-link-item" active-class="active">
          <UsersIcon :size="20" />
          <span class="link-label">Teams</span>
        </router-link>

        <router-link to="/analytics" class="nav-link-item" active-class="active">
          <BarChartIcon :size="20" />
          <span class="link-label">Analytics</span>
        </router-link>

        <router-link v-if="chatStore.userRole === 'admin'" to="/settings" class="nav-link-item" active-class="active">
          <SettingsIcon :size="20" />
          <span class="link-label">Settings</span>
        </router-link>
      </nav>

      <!-- Bottom Actions -->
      <div class="bottom-section">
        <button @click="chatStore.toggleTheme" class="nav-link-item theme-toggle" :title="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
          <SunIcon v-if="chatStore.theme === 'dark'" :size="20" />
          <MoonIcon v-else :size="20" />
          <span class="link-label">Tema</span>
        </button>

        <button @click="showHelpModal = true" class="nav-link-item">
          <HelpCircleIcon :size="20" />
          <span class="link-label">Help Center</span>
        </button>

        <button @click="showLogoutModal = true" class="nav-link-item logout-item">
          <LogOutIcon :size="20" />
          <span class="link-label">Logout</span>
        </button>
      </div>
    </aside>

    <!-- Logout Modal -->
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

    <!-- Help Modal -->
    <div v-if="showHelpModal" class="modal-overlay" @click="showHelpModal = false">
      <div class="modal-content glass-effect" @click.stop>
        <h2>Central de Ajuda</h2>
        <p style="color: var(--text-secondary); margin-bottom: 20px;">Precisa de auxílio no OmniChat?</p>
        <div style="display: flex; flex-direction: column; gap: 10px; text-align: left; color: var(--text-secondary);">
          <p>• Para conectar seu WhatsApp, acesse <strong>Conexões</strong> no menu Configurações.</p>
          <p>• Use a aba <strong>Conversas</strong> para responder aos seus clientes em tempo real.</p>
          <p>• Crie campanhas em massa usando o botão <strong>New Broadcast</strong>.</p>
        </div>
        <div class="modal-actions" style="margin-top: 25px;">
          <button @click="showHelpModal = false" class="btn-success-sm">Entendido</button>
        </div>
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
  MessageSquare as MessageSquareIcon,
  LayoutGrid as LayoutGridIcon,
  Megaphone as MegaphoneIcon,
  Users as UsersIcon,
  BarChart3 as BarChartIcon,
  Settings as SettingsIcon,
  HelpCircle as HelpCircleIcon,
  LogOut as LogOutIcon,
  Sun as SunIcon,
  Moon as MoonIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const showLogoutModal = ref(false)
const showHelpModal = ref(false)

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.sidebar-container {
  width: 260px;
  height: 100%;
  flex-shrink: 0;
  z-index: 100;
}

.sidebar {
  width: 100%;
  height: 100%;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 25px 15px;
}

/* Brand Section */
.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 10px;
  margin-bottom: 25px;
}

.logo-icon {
  width: 38px;
  height: 38px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 1.15rem;
  font-weight: 800;
  color: white;
  letter-spacing: -0.5px;
}

.brand-sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

/* Broadcast Button */
.broadcast-section {
  margin-bottom: 25px;
}

.btn-broadcast-main {
  width: 100%;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px;
  font-weight: 700;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
}

.btn-broadcast-main:hover {
  background: #059669;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35);
}

/* Navigation Links */
.nav-links {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.nav-link-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  padding: 12px 15px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-link-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: white;
}

.nav-link-item.active {
  background: #10b981;
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

/* Bottom Section */
.bottom-section {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.logout-item {
  color: #ef4444;
}

.logout-item:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

/* Modal Styling */
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
  z-index: 2000;
}

.modal-content {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  width: 100%;
  max-width: 500px;
  padding: 30px;
  border-radius: 24px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  color: var(--text-primary);
  text-align: center;
}

.small-modal {
  max-width: 400px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 600;
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

.btn-success-sm {
  background: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

/* Responsiveness */
@media (max-width: 768px) {
  .sidebar-container {
    width: 100%;
    height: 60px;
  }

  .sidebar {
    flex-direction: row;
    padding: 0 10px;
    align-items: center;
    justify-content: space-between;
    border-right: none;
    border-top: 1px solid var(--border);
  }

  .logo-section, .broadcast-section, .link-label, .bottom-section {
    display: none !important;
  }

  .nav-links {
    flex-direction: row;
    gap: 10px;
    margin: 0;
    align-items: center;
    width: 100%;
    justify-content: space-around;
  }

  .nav-link-item {
    padding: 10px;
    border-radius: 10px;
  }
}
</style>
