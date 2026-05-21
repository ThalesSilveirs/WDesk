<template>
  <aside v-if="showCRM" class="crm-sidebar glass-effect animate-slide-in">
    <div class="crm-header">
      <h3>Dados do Ticket</h3>
      <button @click="emit('update:showCRM', false)" class="close-btn"><XIcon :size="20" /></button>
    </div>
    
    <div class="crm-content">
       <!-- Seção de Dados do Ticket -->
       <div class="ticket-meta-form">
         <div class="form-group-sm">
           <label>Assunto do Atendimento</label>
           <input 
            v-model="chatStore.activeTicket.subject" 
            @blur="updateTicketSubject"
            placeholder="Ex: Suporte Financeiro" 
            :disabled="chatStore.activeTicket.status === 'closed'"
           />
         </div>
       </div>

       <hr class="crm-divider" />

      <template v-if="chatStore.activeTicket.customer_details">
        <div class="crm-avatar">
          <img v-if="chatStore.activeTicket.customer_details.profile_pic" :src="chatStore.activeTicket.customer_details.profile_pic" class="avatar-img" />
          <span v-else>{{ chatStore.activeTicket.customer_details.name.charAt(0) }}</span>
        </div>
        <h2 class="crm-name">{{ chatStore.activeTicket.customer_details.name }}</h2>
        
        <div class="crm-info-list">
          <div class="crm-info-item">
            <label>Falar com:</label>
            <p style="color: #10b981; font-weight: 700;">{{ chatStore.activeTicket.contact_details.name }}</p>
          </div>
          <div class="crm-info-item">
            <label>Telefone Principal</label>
            <p>{{ chatStore.activeTicket.customer_details.phone }}</p>
          </div>
          <div v-if="chatStore.activeTicket.customer_details.email" class="crm-info-item">
            <label>E-mail</label>
            <p>{{ chatStore.activeTicket.customer_details.email }}</p>
          </div>
          <div v-if="chatStore.activeTicket.customer_details.document" class="crm-info-item">
            <label>CPF/CNPJ</label>
            <p>{{ chatStore.activeTicket.customer_details.document }}</p>
          </div>
        </div>

        <button @click="router.push('/customers')" class="btn-block-outline">Ver Histórico Completo</button>
      </template>

      <div v-else class="crm-quick-create">
        <div class="empty-icon">
          <UserXIcon :size="48" />
        </div>
        <p>Contato não vinculado.</p>
        
        <div class="quick-form glass-effect">
          <h4>Cadastro Rápido</h4>
          <div class="form-group-sm">
            <label>Nome / Empresa</label>
            <input v-model="quickForm.name" placeholder="Ex: João da Silva" />
          </div>
          <div class="form-group-sm">
            <label>CPF/CNPJ</label>
            <input v-model="quickForm.document" placeholder="000.000.000-00" />
          </div>
          <button @click="handleQuickCreate" class="btn-primary-sm block pulse-effect" :disabled="loadingCRM">
            {{ loadingCRM ? 'Salvando...' : 'Criar e Vincular' }}
          </button>
        </div>
      </div>

      <div v-if="chatStore.activeTicket.resolution" class="resolution-view">
        <hr class="crm-divider" />
        <label>Resolução Final:</label>
        <p>{{ chatStore.activeTicket.resolution }}</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../../store/chat'
import { X as XIcon, UserX as UserXIcon } from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits(['update:showCRM'])

const router = useRouter()
const chatStore = useChatStore()
const loadingCRM = ref(false)
const quickForm = ref({
  name: '',
  document: ''
})

watch(() => chatStore.activeTicket?.id, (newId) => {
  if (newId) {
    quickForm.value = {
      name: chatStore.activeTicket.contact_details?.name || '',
      document: ''
    }
  }
})

const updateTicketSubject = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    subject: chatStore.activeTicket.subject
  })
}

const handleQuickCreate = async () => {
  if (!quickForm.value.name) return
  loadingCRM.value = true
  try {
    const customer = await chatStore.createCustomer({
      name: quickForm.value.name,
      document: quickForm.value.document,
      phone: chatStore.activeTicket.contact_details.remote_jid.split('@')[0]
    })
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: customer.id
    })
    await chatStore.selectTicket(chatStore.activeTicket)
  } catch (e) {
    alert("Erro ao criar cliente rápido")
  } finally {
    loadingCRM.value = false
  }
}
</script>

<style scoped>
.crm-sidebar {
  width: 320px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
}

.crm-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.close-btn:hover { color: white; }

.crm-content {
  padding: 20px;
  overflow-y: auto;
}

.ticket-meta-form { margin-bottom: 20px; }
.crm-divider { border: 0; border-top: 1px solid var(--border); margin: 20px 0; }

.crm-avatar { width: 60px; height: 60px; background: var(--accent); border-radius: 20px; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; border-radius: 20px; }

.crm-name { font-size: 1.2rem; text-align: center; margin-bottom: 20px; color: var(--text-primary); }
.crm-info-item { margin-bottom: 15px; }
.crm-info-item label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; }
.crm-info-item p { font-size: 0.9rem; margin-bottom: 12px; color: var(--text-primary); }

.crm-quick-create {
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 15px;
  opacity: 0.5;
}

.quick-form {
  padding: 15px;
  border-radius: 12px;
  margin-top: 15px;
  border: 1px solid var(--border);
  text-align: left;
}

.quick-form h4 {
  margin-bottom: 15px;
  color: var(--text-primary);
}

.form-group-sm { margin-bottom: 15px; }
.form-group-sm label { 
  font-size: 0.75rem; 
  color: #94a3b8; 
  margin-bottom: 6px; 
  display: block; 
  font-weight: 600; 
  text-transform: uppercase; 
  letter-spacing: 0.5px; 
}
.form-group-sm input { 
  width: 100%; 
  background: rgba(255, 255, 255, 0.03); 
  border: 1px solid var(--border); 
  border-radius: 10px; 
  padding: 10px 12px; 
  color: white; 
  outline: none; 
  transition: all 0.3s ease;
}
.form-group-sm input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.btn-primary-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary-sm:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-primary-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary-sm.block { width: 100%; }

.btn-block-outline {
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-block-outline:hover {
  background: var(--glass);
}

.resolution-view label { font-size: 0.75rem; color: var(--accent); text-transform: uppercase; font-weight: 700; }
.resolution-view p { font-size: 0.9rem; color: #94a3b8; margin-top: 5px; font-style: italic; }
</style>