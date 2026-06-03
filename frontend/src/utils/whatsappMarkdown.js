// WhatsApp Markdown and Text Utilities

export const escapeHtml = (text) => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export const applyInlineFormatting = (line) => {
  // Bold (*bold*)
  line = line.replace(/\*([^*]+?)\*/g, '<strong>$1</strong>')
  // Italic (_italic_)
  line = line.replace(/_([^_]+?)_/g, '<em>$1</em>')
  // Strikethrough (~strike~)
  line = line.replace(/~([^~]+?)~/g, '<del>$1</del>')
  return line
}

export const cleanBody = (body, fromMe) => {
  if (!body) return ''
  if (!fromMe) return body
  const parts = body.split(/:\*\n\n/)
  return parts.length > 1 ? parts.slice(1).join(/:\*\n\n/) : body
}

export const parseWhatsAppMarkdown = (body, fromMe) => {
  let text = cleanBody(body, fromMe)
  if (!text) return ''
  text = escapeHtml(text)
  
  // 1. Monospace blocks (```code```)
  text = text.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>')
  
  // 2. Inline code (`code`)
  text = text.replace(/`([^`\n]+?)`/g, '<code>$1</code>')
  
  // Split into lines for blockquotes and lists
  const lines = text.split('\n')
  const processedLines = []
  
  for (let line of lines) {
    // Blockquote
    if (line.startsWith('&gt;')) {
      let content = line.substring(4)
      content = applyInlineFormatting(content)
      processedLines.push(`<blockquote>${content}</blockquote>`)
      continue
    }
    
    // Bullet list (* or -)
    const bulletMatch = line.match(/^(\*|-)\s+(.*)/)
    if (bulletMatch) {
      let content = applyInlineFormatting(bulletMatch[2])
      processedLines.push(`<ul><li>${content}</li></ul>`)
      continue
    }
    
    // Numbered list (1. 2. etc.)
    const numMatch = line.match(/^(\d+)\.\s+(.*)/)
    if (numMatch) {
      let content = applyInlineFormatting(numMatch[2])
      processedLines.push(`<ol start="${numMatch[1]}"><li>${content}</li></ol>`)
      continue
    }
    
    processedLines.push(applyInlineFormatting(line))
  }
  
  text = processedLines.join('\n')
  
  // Merge consecutive list items
  text = text.replace(/<\/ul>\n<ul>/g, '')
  text = text.replace(/<\/ol>\n<ol[^>]*>/g, '')
  
  // Convert newlines (outside of pre/list blocks) to <br>
  text = text.split('\n').map((line) => {
    if (
      line.endsWith('</li>') || 
      line.endsWith('</ul>') || 
      line.endsWith('</ol>') || 
      line.endsWith('</blockquote>') || 
      line.startsWith('<pre>') || 
      line.startsWith('</pre>') || 
      line.startsWith('<code>') || 
      line.startsWith('</code>')
    ) {
      return line
    }
    return line + '<br>'
  }).join('\n')
  
  text = text.replace(/<br>\n*(<\/ul>|<\/ol>|<blockquote>|<\/blockquote>|<pre>|<\/pre>)/g, '$1')
  
  return text
}

export const isPlaceholder = (body) => {
  if (!body) return false
  const content = body.includes(':*\n\n') ? body.split(/:\*\n\n/).slice(1).join(':*\n\n') : body
  return ['Enviou um image', 'Enviou um video', 'Enviou um document', 'Enviou um audio', 'Enviou um sticker'].some(
    phrase => content.trim() === phrase
  )
}

export const isSystemMessage = (msg) => {
  if (!msg.from_me || msg.user) return false
  const cleanText = msg.body?.replace(/^[\s_]+|[\s_]+$/g, '') || ''
  return (
    cleanText.startsWith('Seu atendimento foi') || 
    cleanText.startsWith('Seu atendimento iniciado') ||
    cleanText.includes('atendimento foi transferido')
  )
}

export const cleanSystemText = (body) => {
  if (!body) return ''
  let text = body
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
  text = text.replace(/\*(.*?)\*/g, '<strong>$1</strong>')
  text = text.replace(/_(.*?)_/g, '<em>$1</em>')
  return text
}

export const base64ToBlobUrl = (dataUrl) => {
  try {
    const parts = dataUrl.split(',')
    const contentType = parts[0].split(':')[1].split(';')[0]
    const raw = window.atob(parts[1])
    const rawLength = raw.length
    const uInt8Array = new Uint8Array(rawLength)
    for (let i = 0; i < rawLength; ++i) {
      uInt8Array[i] = raw.charCodeAt(i)
    }
    const blob = new Blob([uInt8Array], { type: contentType })
    return URL.createObjectURL(blob)
  } catch (e) {
    console.error("Erro ao converter base64 para blob", e)
    return dataUrl
  }
}

export const openDocument = (url) => {
  if (!url) return
  if (url.startsWith('data:')) {
    const blobUrl = base64ToBlobUrl(url)
    window.open(blobUrl, '_blank')
  } else {
    window.open(url, '_blank')
  }
}
