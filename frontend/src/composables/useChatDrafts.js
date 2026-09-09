import { reactive } from 'vue'

const DRAFT_PREFIX = 'wdesk_draft_'

// Mapa reativo compartilhado entre componentes (ChatInput e TicketSidebar)
const draftsState = reactive({})

// Inicializa rascunhos salvos previamente no localStorage
function initDrafts() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(DRAFT_PREFIX)) {
        const ticketId = key.substring(DRAFT_PREFIX.length)
        const val = localStorage.getItem(key)
        if (val && val.trim()) {
          draftsState[ticketId] = val
        }
      }
    }
  } catch (e) {
    console.error('Erro ao ler rascunhos do localStorage:', e)
  }
}

initDrafts()

export function useChatDrafts() {
  const getDraft = (ticketId) => {
    if (!ticketId) return ''
    return draftsState[ticketId] || ''
  }

  const setDraft = (ticketId, text) => {
    if (!ticketId) return
    const cleaned = text || ''
    if (!cleaned.trim()) {
      clearDraft(ticketId)
      return
    }
    draftsState[ticketId] = cleaned
    try {
      localStorage.setItem(`${DRAFT_PREFIX}${ticketId}`, cleaned)
    } catch (e) {
      console.warn('Erro ao salvar rascunho no localStorage:', e)
    }
  }

  const clearDraft = (ticketId) => {
    if (!ticketId) return
    delete draftsState[ticketId]
    try {
      localStorage.removeItem(`${DRAFT_PREFIX}${ticketId}`)
    } catch (e) {
      console.warn('Erro ao limpar rascunho do localStorage:', e)
    }
  }

  const hasDraft = (ticketId) => {
    if (!ticketId) return false
    return !!(draftsState[ticketId] && draftsState[ticketId].trim())
  }

  return {
    draftsState,
    getDraft,
    setDraft,
    clearDraft,
    hasDraft
  }
}
