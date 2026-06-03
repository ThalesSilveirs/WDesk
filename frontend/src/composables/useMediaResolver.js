import { shallowRef, watch, onUnmounted } from 'vue'
import { base64ToBlobUrl } from '../utils/whatsappMarkdown'

export function useMediaResolver(messagesRef, activeTicketIdRef) {
  const resolvedUrls = shallowRef({})
  const resolvedSources = {}

  const cleanupResolvedUrls = () => {
    Object.values(resolvedUrls.value).forEach(url => {
      if (url && url.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(url)
        } catch (e) {
          console.error("Erro ao revogar object URL", e)
        }
      }
    })
    resolvedUrls.value = {}
    // Limpar o objeto normal de fontes
    for (const key in resolvedSources) {
      delete resolvedSources[key]
    }
  }

  const resolveMessageMedia = (msg) => {
    if (!msg) return
    const url = msg.media_url || msg.body
    if (!url) return
    if (resolvedSources[msg.id] === url) return

    // Se já tinha um blob associado a esse id, revoga antes
    if (resolvedUrls.value[msg.id] && resolvedUrls.value[msg.id].startsWith('blob:')) {
      try {
        URL.revokeObjectURL(resolvedUrls.value[msg.id])
      } catch (e) {}
    }

    let resolvedUrl = url
    if (url.startsWith('data:')) {
      resolvedUrl = base64ToBlobUrl(url)
    }

    resolvedUrls.value = {
      ...resolvedUrls.value,
      [msg.id]: resolvedUrl
    }
    resolvedSources[msg.id] = url
  }

  // Monitorar mudança do ticket para limpar mídias antigas
  watch(activeTicketIdRef, () => {
    cleanupResolvedUrls()
  })

  // Monitorar novas mensagens
  watch(messagesRef, (newMessages) => {
    if (!newMessages) return
    newMessages.forEach(resolveMessageMedia)
  }, { immediate: true })

  watch(() => messagesRef.value?.length, (newLength, oldLength) => {
    const msgs = messagesRef.value
    if (!msgs || newLength === 0) return
    const startIndex = oldLength && oldLength < newLength ? oldLength : 0
    for (let i = startIndex; i < newLength; i++) {
      resolveMessageMedia(msgs[i])
    }
  })

  onUnmounted(() => {
    cleanupResolvedUrls()
  })

  return {
    resolvedUrls
  }
}
