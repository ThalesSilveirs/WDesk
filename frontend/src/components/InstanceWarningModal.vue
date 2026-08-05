<template>
  <Transition name="modal-fade">
    <div v-if="show" class="warning-modal-overlay" @click="closeModal">
      <div class="warning-modal-card glass-effect" @click.stop>
        
        <!-- Glowing Warning Banner Header -->
        <div class="warning-header">
          <div class="warning-icon-badge">
            <WifiOffIcon :size="32" class="wifi-off-icon" />
          </div>
          <button @click="closeModal" class="close-btn" title="Fechar">
            <XIcon :size="20" />
          </button>
        </div>

        <!-- Content -->
        <div class="warning-body">
          <h2>Nenhuma Instância WhatsApp Conectada</h2>
          <p class="description">
            O sistema detectou que não há nenhuma conexão com o WhatsApp ativa no momento. 
            Você não conseguirá enviar ou receber mensagens de clientes até conectar um número.
          </p>

          <div class="warning-status-pill">
            <span class="dot pulse-red"></span>
            <span>Status: <strong>Desconectado</strong></span>
          </div>

          <!-- Actions -->
          <div class="warning-actions">
            <button @click="goToConnections" class="btn-connect-now">
              <QrCodeIcon :size="20" />
              <span>Conectar WhatsApp Agora</span>
              <ArrowRightIcon :size="18" class="arrow" />
            </button>
            
            <button @click="closeModal" class="btn-dismiss">
              <span>Continuar sem Conexão</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { WifiOff as WifiOffIcon, X as XIcon, QrCode as QrCodeIcon, ArrowRight as ArrowRightIcon } from 'lucide-vue-next'
import axios from 'axios'

const router = useRouter()
const show = ref(false)

const checkInstanceConnection = async () => {
  try {
    const response = await axios.get('/api/v1/connections/')
    if (!response.data || response.data.length === 0) {
      show.value = true
      return
    }
    
    // Check if at least one instance is 'connected' or 'CONNECTED'
    const hasConnectedInstance = response.data.some(conn => {
      const status = (conn.status || '').toLowerCase()
      return status === 'connected' || status === 'open'
    })

    if (!hasConnectedInstance) {
      show.value = true
    }
  } catch (e) {
    console.error('Erro ao verificar conexões do WhatsApp:', e)
  }
}

const closeModal = () => {
  show.value = false
}

const goToConnections = () => {
  show.value = false
  router.push('/connections')
}

onMounted(() => {
  checkInstanceConnection()
})
</script>

<style scoped>
.warning-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.warning-modal-card {
  background: rgba(23, 27, 34, 0.95);
  border: 1px solid rgba(239, 68, 68, 0.3);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(239, 68, 68, 0.15);
  border-radius: 24px;
  width: 100%;
  max-width: 480px;
  overflow: hidden;
  position: relative;
  animation: modalScaleUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalScaleUp {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.warning-header {
  padding: 28px 28px 10px 28px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.warning-icon-badge {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.25);
}

.wifi-off-icon {
  animation: pulseWarning 2s infinite ease-in-out;
}

@keyframes pulseWarning {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.08); opacity: 0.8; }
}

.close-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.warning-body {
  padding: 10px 28px 28px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.warning-body h2 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.3px;
  line-height: 1.3;
}

.warning-body .description {
  margin: 0;
  font-size: 0.95rem;
  color: #94a3b8;
  line-height: 1.5;
}

.warning-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 0.85rem;
  color: #f87171;
  width: fit-content;
}

.warning-status-pill .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
}

.warning-status-pill .pulse-red {
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  animation: pulseRedDot 1.8s infinite;
}

@keyframes pulseRedDot {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

.warning-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.btn-connect-now {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  border: none;
  padding: 14px 20px;
  border-radius: 14px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.btn-connect-now:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45);
}

.btn-connect-now .arrow {
  transition: transform 0.2s;
}

.btn-connect-now:hover .arrow {
  transform: translateX(4px);
}

.btn-dismiss {
  background: transparent;
  color: #64748b;
  border: none;
  padding: 10px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s;
}

.btn-dismiss:hover {
  color: #94a3b8;
}

/* Modal Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
