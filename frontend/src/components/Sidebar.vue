<template>
  <div class="sidebar-container" :class="{ 'collapsed': isCollapsed }">
    <aside class="sidebar glass-effect">
      <!-- Collapse Toggle Button (Desktop Only) -->
      <button class="collapse-toggle-btn" @click="toggleCollapse" :title="isCollapsed ? 'Expandir Menu' : 'Recolher Menu'">
        <ChevronRightIcon v-if="isCollapsed" :size="16" />
        <ChevronLeftIcon v-else :size="16" />
      </button>

      <!-- Brand Logo Header -->
      <div class="logo-section">
        <img src="/logo.png" alt="wDesk Logo" class="brand-logo-img full-logo" />
        <img src="/favicon.png" alt="wDesk Logo" class="brand-logo-img mini-logo" />
      </div>

      <!-- Navigation Links -->
      <nav class="nav-links">
        <router-link to="/" class="nav-link-item" exact-active-class="active" data-tooltip="Dashboard">
          <LayoutGridIcon :size="20" />
          <span class="link-label">Dashboard</span>
        </router-link>

        <router-link to="/conversations" class="nav-link-item" active-class="active" data-tooltip="Conversas">
          <MessageSquareIcon :size="20" />
          <span class="link-label">Conversas</span>
        </router-link>

        <router-link to="/customers" class="nav-link-item" active-class="active" data-tooltip="Clientes">
          <ContactIcon :size="20" />
          <span class="link-label">Clientes</span>
        </router-link>

        <router-link v-if="chatStore.userRole === 'admin'" to="/users" class="nav-link-item" active-class="active" data-tooltip="Equipes">
          <UsersIcon :size="20" />
          <span class="link-label">Equipes</span>
        </router-link>

        <router-link to="/analytics" class="nav-link-item" active-class="active" data-tooltip="Métricas">
          <BarChartIcon :size="20" />
          <span class="link-label">Métricas</span>
        </router-link>

        <!-- Nova Transmissão -->
        <button @click="chatStore.showBroadcastModal = true" class="nav-link-item broadcast-link" data-tooltip="Nova Transmissão">
          <MegaphoneIcon :size="20" />
          <span class="link-label">Nova Transmissão</span>
        </button>

        <router-link v-if="chatStore.userRole === 'admin'" to="/settings" class="nav-link-item mobile-only" active-class="active" data-tooltip="Configurações">
          <SettingsIcon :size="20" />
          <span class="link-label">Configurações</span>
        </router-link>
      </nav>

      <!-- Bottom Actions -->
      <div class="bottom-section" :class="{ 'collapsed-bottom': isCollapsed }">
        <button @click="chatStore.toggleTheme" class="nav-link-item theme-toggle" :data-tooltip="chatStore.theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'">
          <SunIcon v-if="chatStore.theme === 'dark'" :size="20" />
          <MoonIcon v-else :size="20" />
          <span class="link-label">Tema</span>
        </button>

        <button @click="showHelpModal = true" class="nav-link-item" data-tooltip="Ajuda">
          <HelpCircleIcon :size="20" />
          <span class="link-label">Ajuda</span>
        </button>

        <router-link v-if="chatStore.userRole === 'admin'" to="/settings" class="nav-link-item" active-class="active" data-tooltip="Configurações">
          <SettingsIcon :size="20" />
          <span class="link-label">Configurações</span>
        </router-link>
      </div>
    </aside>

    <!-- Help Modal -->
    <Transition name="modal-fade">
      <div v-if="showHelpModal" class="modal-overlay" @click="showHelpModal = false">
        <div class="modal-content" @click.stop>
          <h2>Central de Ajuda</h2>
          <p style="color: var(--text-secondary); margin-bottom: 20px;">Precisa de auxílio no OmniChat?</p>
          <div style="display: flex; flex-direction: column; gap: 10px; text-align: left; color: var(--text-secondary);">
            <p>• Para conectar seu WhatsApp, acesse <strong>Conexões</strong> no menu Configurações.</p>
            <p>• Use a aba <strong>Conversas</strong> para responder aos seus clientes em tempo real.</p>
            <p>• Crie campanhas em massa usando o botão <strong>Nova Transmissão</strong>.</p>
          </div>
          <div class="modal-actions" style="margin-top: 25px;">
            <button @click="showHelpModal = false" class="btn-success-sm">Entendido</button>
          </div>
        </div>
      </div>
    </Transition>
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
  Sun as SunIcon,
  Moon as MoonIcon,
  Contact as ContactIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const showHelpModal = ref(false)

const isCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', isCollapsed.value ? 'true' : 'false')
}
</script>

<style scoped>
.sidebar-container {
  width: 260px;
  height: 100%;
  flex-shrink: 0;
  z-index: 100;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  will-change: width;
}

.sidebar-container.collapsed {
  width: 80px;
}

.sidebar {
  width: 100%;
  height: 100%;
  background: var(--bg-nav-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 25px 15px;
  position: relative;
}

/* Collapse Toggle Button (Desktop Only) */
.collapse-toggle-btn {
  position: absolute;
  top: 32px;
  right: -12px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 110;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.collapse-toggle-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--border);
  transform: scale(1.1);
}

/* Brand Section */
.logo-section {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  margin-bottom: 30px;
  width: 100%;
}

.brand-logo-img {
  object-fit: contain;
  filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.25));
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.full-logo {
  width: 100%;
  max-height: fit-content;
  display: block;
  transform: scale(1.2);
  opacity: 1;
}

.sidebar-container.collapsed .full-logo {
  opacity: 0;
  transform: scale(0.8);
  pointer-events: none;
}

.mini-logo {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0.8);
  width: 32px;
  height: 32px;
  opacity: 0;
  pointer-events: none;
}

.sidebar-container.collapsed .mini-logo {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1.15);
  pointer-events: auto;
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
  color: var(--text-secondary);
  padding: 12px 15px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  font-family: inherit;
  box-sizing: border-box;
  overflow: hidden;
  white-space: nowrap;
}

.nav-link-item:hover {
  background: var(--border);
  color: var(--text-primary);
}

.nav-link-item.active {
  background: #10b981;
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.link-label {
  margin-left: 12px;
  opacity: 1;
  max-width: 150px;
  display: inline-block;
  vertical-align: middle;
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1), max-width 0.25s cubic-bezier(0.4, 0, 0.2, 1), margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-container.collapsed .link-label {
  opacity: 0;
  max-width: 0;
  margin-left: 0;
}

/* Custom Tooltips for Collapsed State */
@media (min-width: 769px) {
  .sidebar-container.collapsed .nav-link-item {
    position: relative;
  }

  .sidebar-container.collapsed .nav-link-item::after {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 12px);
    top: 50%;
    transform: translateY(-50%) translateX(-8px);
    background: var(--bg-nav-sidebar);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1), transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(8px);
    z-index: 120;
  }

  .sidebar-container.collapsed .nav-link-item:hover::after {
    opacity: 1;
    visibility: visible;
    transform: translateY(-50%) translateX(0);
  }
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
.small-modal {
  max-width: 400px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
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
    width: 100% !important;
    height: 60px;
  }

  .collapse-toggle-btn {
    display: none !important;
  }

  .sidebar {
    flex-direction: row;
    padding: 0 10px;
    align-items: center;
    justify-content: space-between;
    border-right: none;
    border-top: 1px solid var(--border);
  }

  .logo-section, .broadcast-section, .link-label, .bottom-section, .broadcast-link {
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

  .mobile-only {
    display: flex !important;
  }
}

.mobile-only {
  display: none !important;
}
</style>
