// Utilitário de formatação de datas e horários de alto desempenho
const timeFormatter = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
const dateFormatter = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' })
const fullDateTimeFormatter = new Intl.DateTimeFormat('pt-BR', { 
  day: '2-digit', 
  month: '2-digit', 
  year: 'numeric',
  hour: '2-digit', 
  minute: '2-digit' 
})

export const formatTime = (dateInput) => {
  if (!dateInput) return ''
  const d = dateInput instanceof Date ? dateInput : new Date(dateInput)
  if (isNaN(d.getTime())) return ''
  return timeFormatter.format(d)
}

export const formatDateOrTime = (dateInput) => {
  if (!dateInput) return ''
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput)
  if (isNaN(date.getTime())) return ''
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return timeFormatter.format(date)
  }
  return dateFormatter.format(date)
}

export const formatFullDateTime = (dateInput) => {
  if (!dateInput) return ''
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput)
  if (isNaN(date.getTime())) return ''
  return fullDateTimeFormatter.format(date)
}
