import { ref } from 'vue'

export function useReactions(reactToMessageCallback) {
  const activeReactionPickerId = ref(null)

  const toggleReactionPicker = (msgId) => {
    if (activeReactionPickerId.value === msgId) {
      activeReactionPickerId.value = null
    } else {
      activeReactionPickerId.value = msgId
    }
  }

  const closeReactionPicker = () => {
    activeReactionPickerId.value = null
  }

  const getGroupedReactions = (reactions) => {
    if (!reactions || !reactions.length) return []
    const groups = {}
    reactions.forEach(r => {
      if (!groups[r.emoji]) {
        groups[r.emoji] = { emoji: r.emoji, count: 0, users: [], reactedByMe: false }
      }
      groups[r.emoji].count++
      groups[r.emoji].users.push(r.from_me ? 'Você' : 'Cliente')
      if (r.from_me) {
        groups[r.emoji].reactedByMe = true
      }
    })
    return Object.values(groups)
  }

  const hasAttendantReactedWith = (reactions, emoji) => {
    if (!reactions) return false
    return reactions.some(r => r.emoji === emoji && r.from_me)
  }

  const toggleReaction = async (msg, emoji) => {
    activeReactionPickerId.value = null
    const alreadyReacted = hasAttendantReactedWith(msg.reactions, emoji)
    const newEmoji = alreadyReacted ? '' : emoji
    if (reactToMessageCallback) {
      await reactToMessageCallback(msg.id, newEmoji)
    }
  }

  return {
    activeReactionPickerId,
    toggleReactionPicker,
    closeReactionPicker,
    getGroupedReactions,
    hasAttendantReactedWith,
    toggleReaction
  }
}
