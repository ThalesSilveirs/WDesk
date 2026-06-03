import { ref } from 'vue'

export function useMessageActions() {
  const editingMessage = ref(null)
  const replyingMessage = ref(null)
  const highlightedMessageId = ref(null)

  const startEditingMessage = (msg, textRef, inputRef) => {
    cancelReplyingMessage()
    editingMessage.value = msg
    if (textRef) {
      textRef.value = msg.body
    }
    setTimeout(() => {
      if (inputRef && inputRef.value) {
        inputRef.value.focus()
      }
    }, 50)
  }

  const cancelEditingMessage = (textRef) => {
    editingMessage.value = null
    if (textRef) {
      textRef.value = ''
    }
  }

  const startReplyingMessage = (msg, inputRef) => {
    cancelEditingMessage()
    replyingMessage.value = msg
    setTimeout(() => {
      if (inputRef && inputRef.value) {
        inputRef.value.focus()
      }
    }, 50)
  }

  const cancelReplyingMessage = () => {
    replyingMessage.value = null
  }

  const scrollToMessage = (quotedMsgId) => {
    if (!quotedMsgId) return
    const element = document.getElementById('msg-' + quotedMsgId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      highlightedMessageId.value = quotedMsgId
      setTimeout(() => {
        if (highlightedMessageId.value === quotedMsgId) {
          highlightedMessageId.value = null
        }
      }, 2000)
    }
  }

  return {
    editingMessage,
    replyingMessage,
    highlightedMessageId,
    startEditingMessage,
    cancelEditingMessage,
    startReplyingMessage,
    cancelReplyingMessage,
    scrollToMessage
  }
}
