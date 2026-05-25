<template>
  <aside class="sidebar glass-effect">
    <div class="ticket-list-wrapper top">
      <div class="list-header">
        <h3>Meus Atendimentos</h3>
        <span class="badge green">{{ filteredMyTickets.length }}</span>
      </div>
      <div class="ticket-list">
        <div 
          v-for="ticket in filteredMyTickets" 
          :key="ticket.id"
          class="ticket-item"
          :class="{ active: chatStore.activeTicket?.id === ticket.id }"
          @click="chatStore.selectTicket(ticket)"
        >
          <div class="avatar">
            <img v-if="ticket.contact_details?.profile_pic" :src="ticket.contact_details.profile_pic" class="avatar-img" />
            <span v-else>{{ ticket.contact_details?.name?.charAt(0) || 'C' }}</span>
          </div>
          <div class="ticket-info">
            <div class="top">
              <span class="name">{{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}</span>
              <div class="time-unread">
                <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
                <span class="time">{{ formatTime(ticket.updated_at) }}</span>
              </div>
            </div>
            <p class="last-msg">
              <span v-if="ticket.priority === 'high'" class="priority-dot high"></span>
              <span v-if="ticket.priority === 'medium'" class="priority-dot medium"></span>
              {{ ticket.last_message || 'Nenhuma mensagem' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="ticket-list-wrapper bottom">
      <div class="list-header">
        <div class="header-main">
          <h3>{{ chatStore.currentFilter === 'closed' ? 'Histórico' : (chatStore.currentFilter === 'all' ? 'Todos' : 'Fila') }}</h3>
          <span class="badge">{{ filteredTickets.length }}</span>
        </div>
        <div class="tabs-top-inline">
          <button 
            class="tab-btn-mini" 
            :class="{ active: chatStore.currentFilter === 'unassigned' }"
            @click="chatStore.fetchTickets('unassigned')"
          >
            Fila
          </button>
          <button 
            class="tab-btn-mini" 
            :class="{ active: chatStore.currentFilter === 'closed' }"
            @click="chatStore.fetchTickets('closed')"
          >
            Fechados
          </button>
          <button 
            v-if="chatStore.userRole === 'admin'"
            class="tab-btn-mini" 
            :class="{ active: chatStore.currentFilter === 'all' }"
            @click="chatStore.fetchTickets('all')"
          >
            Todos
          </button>
        </div>
      </div>
      <div class="ticket-list">
        <div 
          v-for="ticket in filteredTickets" 
          :key="ticket.id"
          class="ticket-item"
          :class="{ active: chatStore.activeTicket?.id === ticket.id }"
          @click="chatStore.selectTicket(ticket)"
        >
          <div class="avatar">
            <img v-if="ticket.contact_details?.profile_pic" :src="ticket.contact_details.profile_pic" class="avatar-img" />
            <span v-else>{{ ticket.contact_details?.name?.charAt(0) || 'C' }}</span>
          </div>
          <div class="ticket-info">
            <div class="top">
              <span class="name">{{ ticket.contact_details?.name || ticket.contact_details?.remote_jid }}</span>
              <div class="time-unread">
                <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
                <span class="time">{{ formatTime(ticket.updated_at) }}</span>
              </div>
            </div>
            <p class="last-msg">{{ ticket.last_message || 'Nenhuma mensagem' }}</p>
            <span v-if="ticket.attendant_details" class="attendant-label">
              {{ ticket.status === 'closed' ? 'Atendido por' : 'Com' }} {{ ticket.attendant_details.first_name }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../../store/chat'

const chatStore = useChatStore()

const filteredMyTickets = computed(() => {
  const query = (chatStore.searchQuery || '').toLowerCase().trim()
  if (!query) return chatStore.myTickets
  return chatStore.myTickets.filter(ticket => {
    const contactName = (ticket.contact_details?.name || '').toLowerCase()
    const remoteJid = (ticket.contact_details?.remote_jid || '').toLowerCase()
    const lastMsg = (ticket.last_message || '').toLowerCase()
    return contactName.includes(query) || remoteJid.includes(query) || lastMsg.includes(query)
  })
})

const filteredTickets = computed(() => {
  const query = (chatStore.searchQuery || '').toLowerCase().trim()
  if (!query) return chatStore.tickets
  return chatStore.tickets.filter(ticket => {
    const contactName = (ticket.contact_details?.name || '').toLowerCase()
    const remoteJid = (ticket.contact_details?.remote_jid || '').toLowerCase()
    const lastMsg = (ticket.last_message || '').toLowerCase()
    return contactName.includes(query) || remoteJid.includes(query) || lastMsg.includes(query)
  })
})

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { day: '2-digit', month: '2-digit' })
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    border-right: none;
  }
}

.ticket-list {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  padding: 15px 20px;
  display: flex;
  gap: 15px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--border);
}

.ticket-item:hover { background: var(--glass); }

.ticket-item.active {
  background: rgba(16, 185, 129, 0.1);
  border-left: 3px solid var(--accent);
}

.avatar {
  width: 50px;
  height: 50px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  overflow: hidden;
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.avatar.small { width: 40px; height: 40px; font-size: 1rem; }

.ticket-info { flex: 1; overflow: hidden; }
.ticket-info .top { display: flex; justify-content: space-between; margin-bottom: 5px; }
.name { font-weight: 600; color: var(--text-primary); }
.time { font-size: 0.8rem; color: var(--text-secondary); }
.last-msg {
  font-size: 0.9rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 5px;
}

.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.priority-dot.high { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.priority-dot.medium { background: #f59e0b; }

.time-unread {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.unread-badge {
  background: var(--accent);
  color: white;
  font-size: 0.7rem;
  font-weight: 800;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
  animation: badge-pulse 2s infinite;
}

@keyframes badge-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
}
.badge.green { background: var(--accent); }

.ticket-list-wrapper { display: flex; flex-direction: column; overflow: hidden; }
.ticket-list-wrapper.top { flex: 1; }
.ticket-list-wrapper.bottom { height: 45%; border-top: 1px solid var(--border); background: rgba(0, 0, 0, 0.1); }
.list-header { 
  padding: 12px 20px; 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  background: var(--glass);
}

.list-header h3 { 
  font-size: 0.85rem; 
  font-weight: 700; 
  text-transform: uppercase; 
  color: var(--text-secondary); 
}

.header-main { display: flex; align-items: center; gap: 8px; }

.tabs-top-inline { 
  display: flex; 
  background: var(--bg-dark); 
  padding: 3px; 
  border-radius: 8px; 
  margin-left: auto; 
  border: 1px solid var(--border);
}
.tab-btn-mini { 
  padding: 6px 10px; 
  border: none; 
  background: none; 
  color: var(--text-secondary); 
  font-size: 0.75rem; 
  font-weight: 600; 
  cursor: pointer; 
  border-radius: 6px; 
  transition: all 0.2s;
}

.tab-btn-mini.active { 
  background: var(--accent); 
  color: white; 
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.2);
}

.attendant-label {
  display: block;
  font-size: 0.75rem;
  color: var(--accent);
  margin-top: 4px;
}
</style>