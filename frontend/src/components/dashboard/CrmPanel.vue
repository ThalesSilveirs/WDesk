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

       <!-- Dados do Contato (Sempre visíveis) -->
       <div class="crm-contact-section">
         <div class="crm-info-item">
           <label>Falar com (Nome do Contato)</label>
           <div class="edit-field-wrapper">
             <input 
               v-if="editingName" 
               v-model="contactName" 
               @blur="saveContactName" 
               @keyup.enter="saveContactName"
               class="input-inline"
               ref="nameInputRef"
             />
             <div v-else @click="startEditingName" class="text-inline clickable">
               <span class="contact-name-highlight">{{ contactName || chatStore.activeTicket.contact_details?.name || 'Contato Sem Nome' }}</span>
               <EditIcon :size="14" class="edit-icon" />
             </div>
           </div>
         </div>

         <div class="crm-info-item">
           <label>Cargo / Observação Curta</label>
           <div class="edit-field-wrapper">
             <input 
               v-if="editingNote" 
               v-model="contactNote" 
               @blur="saveContactNote" 
               @keyup.enter="saveContactNote"
               class="input-inline"
               placeholder="Ex: Gerente de TI, Compras..."
               ref="noteInputRef"
               maxlength="150"
             />
             <div v-else @click="startEditingNote" class="text-inline clickable">
               <span v-if="contactNote" class="note-badge">🏷️ {{ contactNote }}</span>
               <span v-else class="placeholder-text">Adicionar observação (ex: cargo, setor)...</span>
               <EditIcon :size="14" class="edit-icon" />
             </div>
           </div>
         </div>
       </div>

       <hr class="crm-divider" />

       <!-- Dados do Cliente Vinculado -->
       <template v-if="chatStore.activeTicket.customer_details">
         <div class="crm-avatar">
           <img v-if="chatStore.activeTicket.customer_details.profile_pic && !chatStore.activeTicket.customer_details.profile_pic_failed" :src="chatStore.activeTicket.customer_details.profile_pic" class="avatar-img" @error="chatStore.activeTicket.customer_details.profile_pic_failed = true" />
           <span v-else>{{ chatStore.activeTicket.customer_details.name.charAt(0) }}</span>
         </div>
         <h2 class="crm-name">{{ chatStore.activeTicket.customer_details.name }}</h2>
         
         <div class="crm-info-list">
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

         <div class="crm-actions">
           <button @click="router.push('/customers')" class="btn-block-outline">Ver Histórico Completo</button>
           <button @click="unlinkCustomer" class="btn-danger-outline" :disabled="loadingCRM">
             <UserMinusIcon :size="16" /> Desvincular Cliente
           </button>
         </div>
       </template>

       <!-- Fluxo de Vincular a Cliente Existente -->
       <div v-else class="crm-link-customer">
         <div class="empty-icon">
           <UserXIcon :size="48" />
         </div>
         <p>Nenhum cliente cadastrado vinculado.</p>
         
         <div class="link-search-box glass-effect">
           <h4>Vincular Cliente</h4>
           <div class="search-input-wrapper">
             <input 
               v-model="customerSearchQuery" 
               @input="handleSearchInput" 
               placeholder="Buscar por nome ou telefone..."
               class="search-input"
             />
             <SearchIcon :size="16" class="search-box-icon" />
           </div>
           
           <!-- Dropdown de Resultados -->
           <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown">
             <div 
               v-for="cust in searchResults" 
               :key="cust.id" 
               @click="selectCustomerToLink(cust)"
               class="dropdown-item"
             >
               <span class="cust-name">{{ cust.name }}</span>
               <span class="cust-detail">{{ cust.phone }} <span v-if="cust.document">| {{ cust.document }}</span></span>
             </div>
           </div>
           <div v-else-if="customerSearchQuery.trim().length >= 2 && !searching && searchResults.length === 0" class="no-results">
             Nenhum cliente encontrado.
           </div>
           <div v-else-if="searching" class="searching-text">
             Buscando...
           </div>
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
import { X as XIcon, UserX as UserXIcon, Edit as EditIcon, Search as SearchIcon, UserMinus as UserMinusIcon } from 'lucide-vue-next'

const props = defineProps({
  showCRM: Boolean
})

const emit = defineEmits(['update:showCRM'])

const router = useRouter()
const chatStore = useChatStore()
const loadingCRM = ref(false)

// Estados de Edição do Contato
const contactName = ref('')
const contactNote = ref('')
const editingName = ref(false)
const editingNote = ref(false)
const nameInputRef = ref(null)
const noteInputRef = ref(null)

// Estados de Busca e Vínculo de Clientes
const customerSearchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const showDropdown = ref(false)

watch(() => chatStore.activeTicket?.id, (newId) => {
  if (newId) {
    contactName.value = chatStore.activeTicket.contact_details?.name || ''
    contactNote.value = chatStore.activeTicket.contact_details?.note || ''
    editingName.value = false
    editingNote.value = false
    customerSearchQuery.value = ''
    searchResults.value = []
    showDropdown.value = false
  }
}, { immediate: true })

// Quando a propriedade do contact_details for alterada em background (via WebSocket), sincroniza o formulário
watch(() => chatStore.activeTicket?.contact_details, (newDetails) => {
  if (newDetails && !editingName.value && !editingNote.value) {
    contactName.value = newDetails.name || ''
    contactNote.value = newDetails.note || ''
  }
}, { deep: true })

const updateTicketSubject = async () => {
  if (!chatStore.activeTicket) return
  await chatStore.updateTicket(chatStore.activeTicket.id, {
    subject: chatStore.activeTicket.subject
  })
}

// Ações de edição do Contato
const startEditingName = () => {
  editingName.value = true
  setTimeout(() => {
    nameInputRef.value?.focus()
  }, 50)
}

const startEditingNote = () => {
  editingNote.value = true
  setTimeout(() => {
    noteInputRef.value?.focus()
  }, 50)
}

const saveContactName = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  editingName.value = false
  try {
    const updatedContact = await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      name: contactName.value
    })
    chatStore.activeTicket.contact_details.name = updatedContact.name
  } catch (err) {
    alert('Erro ao atualizar nome do contato')
  }
}

const saveContactNote = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  editingNote.value = false
  try {
    const updatedContact = await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      note: contactNote.value
    })
    chatStore.activeTicket.contact_details.note = updatedContact.note
  } catch (err) {
    alert('Erro ao atualizar observação do contato')
  }
}

// Busca Incremental
const handleSearchInput = async () => {
  const query = customerSearchQuery.value.trim()
  if (query.length < 2) {
    searchResults.value = []
    showDropdown.value = false
    return
  }
  searching.value = true
  try {
    const res = await chatStore.searchCustomers(query)
    searchResults.value = res
    showDropdown.value = res.length > 0
  } catch (err) {
    console.error(err)
  } finally {
    searching.value = false
  }
}

// Vincular Cliente
const selectCustomerToLink = async (customer) => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  loadingCRM.value = true
  try {
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: customer.id
    })
    // Atualiza activeTicket localmente
    chatStore.activeTicket.customer_details = customer
    chatStore.activeTicket.contact_details.customer = customer.id
    
    // Reseta estados de busca
    customerSearchQuery.value = ''
    searchResults.value = []
    showDropdown.value = false
  } catch (e) {
    alert('Erro ao vincular cliente')
  } finally {
    loadingCRM.value = false
  }
}

// Desvincular Cliente
const unlinkCustomer = async () => {
  if (!chatStore.activeTicket?.contact_details?.id) return
  if (!confirm('Deseja realmente desvincular este cliente do contato?')) return
  loadingCRM.value = true
  try {
    await chatStore.updateContact(chatStore.activeTicket.contact_details.id, {
      customer: null
    })
    chatStore.activeTicket.customer_details = null
    chatStore.activeTicket.contact_details.customer = null
  } catch (e) {
    alert('Erro ao desvincular cliente')
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

.close-btn:hover { color: var(--text-primary); }

.crm-content {
  padding: 20px;
  overflow-y: auto;
}

.ticket-meta-form { margin-bottom: 20px; }
.crm-divider { border: 0; border-top: 1px solid var(--border); margin: 20px 0; }

.crm-contact-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
  background: rgba(255, 255, 255, 0.02);
  padding: 15px;
  border-radius: 12px;
  border: 1px solid var(--border);
}

.edit-field-wrapper {
  display: flex;
  align-items: center;
  margin-top: 5px;
  width: 100%;
}

.input-inline {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 6px 10px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.9rem;
}

.text-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 6px 0;
  border-bottom: 1px dashed transparent;
  transition: all 0.2s;
}

.text-inline.clickable {
  cursor: pointer;
}

.text-inline.clickable:hover {
  border-bottom-color: var(--accent);
}

.contact-name-highlight {
  color: var(--accent);
  font-weight: 700;
  font-size: 1rem;
}

.edit-icon {
  opacity: 0.3;
  color: var(--text-secondary);
  transition: opacity 0.2s;
}

.text-inline:hover .edit-icon {
  opacity: 1;
}

.note-badge {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 4px 8px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.placeholder-text {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-style: italic;
}

.crm-avatar { width: 60px; height: 60px; background: var(--accent); border-radius: 20px; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; border-radius: 20px; }

.crm-name { font-size: 1.2rem; text-align: center; margin-bottom: 20px; color: var(--text-primary); }
.crm-info-item { margin-bottom: 15px; }
.crm-info-item label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
.crm-info-item p { font-size: 0.9rem; margin-bottom: 12px; color: var(--text-primary); }

.crm-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 15px;
}

.btn-danger-outline {
  width: 100%;
  padding: 10px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-danger-outline:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
}

.crm-link-customer {
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 15px;
  opacity: 0.5;
}

.link-search-box {
  padding: 15px;
  border-radius: 12px;
  margin-top: 15px;
  border: 1px solid var(--border);
  text-align: left;
  position: relative;
}

.link-search-box h4 {
  margin-bottom: 12px;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px 10px 35px;
  color: var(--text-primary);
  outline: none;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.search-input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.07);
}

.search-box-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-top: 5px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.dropdown-item {
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: rgba(16, 185, 129, 0.1);
}

.cust-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.85rem;
}

.cust-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.no-results, .searching-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 8px;
  text-align: center;
  font-style: italic;
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
  color: var(--text-primary);
  outline: none;
  transition: all 0.3s ease;
}
.form-group-sm input:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

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