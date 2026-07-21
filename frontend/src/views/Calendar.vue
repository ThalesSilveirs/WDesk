<template>
  <div class="calendar-container">
    <!-- Header Controls -->
    <header class="calendar-header glass-effect">
      <div class="header-left">
        <div class="header-title-box">
          <CalendarIcon :size="24" class="header-icon" />
          <h2>{{ currentPeriodLabel }}</h2>
        </div>
        <div class="nav-btn-group">
          <button @click="navigatePrev" class="icon-btn-glass" title="Anterior">
            <ChevronLeftIcon :size="18" />
          </button>
          <button @click="navigateToday" class="btn-today" title="Ir para hoje">
            Hoje
          </button>
          <button @click="navigateNext" class="icon-btn-glass" title="Próximo">
            <ChevronRightIcon :size="18" />
          </button>
        </div>
      </div>

      <div class="header-center">
        <div class="view-mode-tabs glass-effect">
          <button 
            @click="viewMode = 'month'" 
            class="tab-btn" 
            :class="{ active: viewMode === 'month' }"
          >
            Mês
          </button>
          <button 
            @click="viewMode = 'week'" 
            class="tab-btn" 
            :class="{ active: viewMode === 'week' }"
          >
            Semana
          </button>
          <button 
            @click="viewMode = 'day'" 
            class="tab-btn" 
            :class="{ active: viewMode === 'day' }"
          >
            Dia
          </button>
        </div>
      </div>

      <div class="header-right">
        <button @click="fetchEvents" class="btn-sync" :disabled="loadingEvents">
          <RefreshCwIcon :size="16" :class="{ 'animate-spin': loadingEvents }" />
          <span>{{ loadingEvents ? 'Sincronizando...' : 'Atualizar' }}</span>
        </button>
        <button @click="showFeedsModal = true" class="btn-primary-v2">
          <RssIcon :size="16" />
          <span>Feeds WebCAL</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="calendar-body">
      <!-- 1. MÊS (Month Grid View) -->
      <div v-if="viewMode === 'month'" class="month-grid-wrapper">
        <div class="weekdays-header">
          <div v-for="(dayName, idx) in weekDaysShort" :key="idx" class="weekday-cell">
            {{ dayName }}
          </div>
        </div>

        <div class="month-days-grid">
          <div 
            v-for="(dayObj, idx) in monthDaysGrid" 
            :key="idx" 
            class="day-cell glass-effect"
            :class="{
              'other-month': !dayObj.isCurrentMonth,
              'is-today': dayObj.isToday
            }"
            @click="selectDate(dayObj.date)"
          >
            <div class="day-cell-header">
              <span class="day-number">{{ dayObj.dayNumber }}</span>
              <span v-if="dayObj.events.length > 0" class="event-count-badge">
                {{ dayObj.events.length }}
              </span>
            </div>

            <div class="day-events-list">
              <div 
                v-for="evt in dayObj.events.slice(0, 3)" 
                :key="evt.id || evt.uid" 
                class="event-chip"
                :style="{ backgroundColor: evt.color || '#3b82f6' }"
                @click.stop="openEventDetails(evt)"
              >
                <span class="evt-title">{{ evt.title }}</span>
              </div>
              <div v-if="dayObj.events.length > 3" class="more-events-link">
                +{{ dayObj.events.length - 3 }} mais
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. SEMANA (Week View) -->
      <div v-else-if="viewMode === 'week'" class="week-view-wrapper">
        <div class="week-columns-grid">
          <div 
            v-for="(dayObj, idx) in weekDaysGrid" 
            :key="idx" 
            class="week-column glass-effect"
            :class="{ 'is-today': dayObj.isToday }"
          >
            <div class="week-column-header">
              <span class="week-day-name">{{ dayObj.dayName }}</span>
              <span class="week-day-num">{{ dayObj.dayNumber }}</span>
            </div>

            <div class="week-events-list">
              <div 
                v-for="evt in dayObj.events" 
                :key="evt.id || evt.uid" 
                class="week-event-card"
                :style="{ borderLeftColor: evt.color || '#3b82f6' }"
                @click="openEventDetails(evt)"
              >
                <div class="evt-time" v-if="evt.start">
                  {{ formatEventTime(evt.start) }}
                </div>
                <div class="evt-card-title">{{ evt.title }}</div>
                <div class="evt-card-source" v-if="evt.source">
                  {{ evt.source === 'pendency' ? 'Pendência WDesk' : (evt.feed_name || 'WebCAL') }}
                </div>
              </div>

              <div v-if="dayObj.events.length === 0" class="empty-day-note">
                Nenhum evento
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. DIA (Day View) -->
      <div v-else-if="viewMode === 'day'" class="day-view-wrapper glass-effect">
        <div class="day-view-header">
          <h3>{{ formatFullDate(currentDate) }}</h3>
        </div>

        <div class="day-view-events-list">
          <div 
            v-for="evt in selectedDayEvents" 
            :key="evt.id || evt.uid" 
            class="day-full-event-card glass-effect"
            :style="{ borderLeftColor: evt.color || '#3b82f6' }"
            @click="openEventDetails(evt)"
          >
            <div class="event-time-badge" :style="{ backgroundColor: evt.color || '#3b82f6' }">
              <ClockIcon :size="14" />
              <span>{{ evt.allDay ? 'Dia Inteiro' : formatEventTime(evt.start) }}</span>
            </div>

            <div class="event-info-main">
              <h4>{{ evt.title }}</h4>
              <p v-if="evt.location" class="evt-loc">
                <MapPinIcon :size="14" /> {{ evt.location }}
              </p>
              <p v-if="evt.description" class="evt-desc">
                {{ evt.description }}
              </p>
            </div>
          </div>

          <div v-if="selectedDayEvents.length === 0" class="empty-state-card">
            <CalendarIcon :size="48" class="empty-icon" />
            <p>Nenhum evento registrado para este dia.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal 1: Gerenciar Feeds WebCAL -->
    <Transition name="modal-fade">
      <div v-if="showFeedsModal" class="modal-overlay" @click="showFeedsModal = false">
        <div class="modal-content medium-modal" @click.stop>
          <div class="modal-header">
            <h2>Gerenciar Feeds WebCAL (iCal)</h2>
            <button @click="showFeedsModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <div class="modal-body">
            <!-- Formulário Novo Feed -->
            <form @submit.prevent="saveFeed" class="feed-form glass-effect">
              <h4>Adicionar Novo Feed WebCAL</h4>
              
              <div class="grid-2">
                <div class="form-group">
                  <label>Nome do Calendário / Origem *</label>
                  <input 
                    v-model="feedForm.name" 
                    required 
                    class="input-glass" 
                    placeholder="Ex: Calendário do Google / Outlook" 
                  />
                </div>

                <div class="form-group">
                  <label>Cor do Marcador</label>
                  <div class="color-picker-row">
                    <input 
                      v-model="feedForm.color" 
                      type="color" 
                      class="color-input" 
                    />
                    <div class="color-presets">
                      <span 
                        v-for="c in colorPresets" 
                        :key="c" 
                        class="preset-dot" 
                        :style="{ backgroundColor: c }"
                        @click="feedForm.color = c"
                      ></span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label>URL do WebCAL (.ics ou webcal://) *</label>
                <input 
                  v-model="feedForm.url" 
                  required 
                  class="input-glass" 
                  placeholder="webcal://calendar.google.com/calendar/ical/.../basic.ics" 
                />
              </div>

              <div class="form-actions-right">
                <button type="submit" class="btn-primary-v2" :disabled="savingFeed">
                  {{ savingFeed ? 'Salvando...' : 'Adicionar Feed' }}
                </button>
              </div>
            </form>

            <!-- Lista de Feeds Cadastrados -->
            <div class="feeds-list-section">
              <h4>Feeds Ativos ({{ feedsList.length }})</h4>
              
              <div v-if="loadingFeeds" class="loading-inline">
                <RefreshCwIcon :size="16" class="animate-spin" /> Carregando feeds...
              </div>

              <div v-else-if="feedsList.length === 0" class="no-feeds-note">
                Nenhum feed WebCAL cadastrado ainda. Cole a URL acima para vincular.
              </div>

              <div v-else class="feeds-list">
                <div 
                  v-for="feed in feedsList" 
                  :key="feed.id" 
                  class="feed-item-card glass-effect"
                >
                  <span class="feed-color-dot" :style="{ backgroundColor: feed.color }"></span>
                  <div class="feed-item-info">
                    <strong>{{ feed.name }}</strong>
                    <span class="feed-url-text">{{ feed.url }}</span>
                  </div>
                  <button @click="deleteFeed(feed.id)" class="icon-btn-danger" title="Remover Feed">
                    <TrashIcon :size="16" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal 2: Detalhes do Evento -->
    <Transition name="modal-fade">
      <div v-if="selectedEvent" class="modal-overlay" @click="selectedEvent = null">
        <div class="modal-content small-modal" @click.stop>
          <div class="modal-header" :style="{ borderLeft: `6px solid ${selectedEvent.color || '#3b82f6'}` }">
            <div>
              <h2>{{ selectedEvent.title }}</h2>
              <span class="event-source-badge" :style="{ backgroundColor: selectedEvent.color || '#3b82f6' }">
                {{ selectedEvent.source === 'pendency' ? 'Pendência WDesk' : (selectedEvent.feed_name || 'WebCAL') }}
              </span>
            </div>
            <button @click="selectedEvent = null" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <div class="modal-body event-details-body">
            <div class="detail-row" v-if="selectedEvent.start">
              <ClockIcon :size="18" class="detail-icon" />
              <div>
                <strong>Data e Horário:</strong>
                <p>{{ formatEventDateTime(selectedEvent.start, selectedEvent.end, selectedEvent.allDay) }}</p>
              </div>
            </div>

            <div class="detail-row" v-if="selectedEvent.location">
              <MapPinIcon :size="18" class="detail-icon" />
              <div>
                <strong>Local / Cliente:</strong>
                <p>{{ selectedEvent.location }}</p>
              </div>
            </div>

            <div class="detail-row" v-if="selectedEvent.description">
              <FileTextIcon :size="18" class="detail-icon" />
              <div>
                <strong>Descrição / Detalhes:</strong>
                <p class="description-text">{{ selectedEvent.description }}</p>
              </div>
            </div>

            <div class="modal-actions" style="margin-top: 20px;">
              <button 
                v-if="selectedEvent.source === 'pendency'" 
                @click="goToPendency(selectedEvent.pendency_id)" 
                class="btn-primary-v2"
              >
                Abrir em Pendências
              </button>
              <button @click="selectedEvent = null" class="btn-secondary-v2">
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
  Calendar as CalendarIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  RefreshCw as RefreshCwIcon,
  Rss as RssIcon,
  Clock as ClockIcon,
  MapPin as MapPinIcon,
  FileText as FileTextIcon,
  X as XIcon,
  Trash2 as TrashIcon
} from 'lucide-vue-next'

const router = useRouter()

// Estados Reativos
const currentDate = ref(new Date())
const viewMode = ref('month') // 'month' | 'week' | 'day'
const events = ref([])
const feedsList = ref([])
const loadingEvents = ref(false)
const loadingFeeds = ref(false)
const savingFeed = ref(false)

const showFeedsModal = ref(false)
const selectedEvent = ref(null)

const feedForm = ref({
  name: '',
  url: '',
  color: '#3b82f6'
})

const colorPresets = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']
const weekDaysShort = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

// Label do Período Atual
const currentPeriodLabel = computed(() => {
  const d = currentDate.value
  const monthName = d.toLocaleString('pt-BR', { month: 'long' })
  const capitalizedMonth = monthName.charAt(0).toUpperCase() + monthName.slice(1)
  const year = d.getFullYear()
  
  if (viewMode.value === 'month') {
    return `${capitalizedMonth} de ${year}`
  } else if (viewMode.value === 'week') {
    return `Semana de ${capitalizedMonth} ${year}`
  } else {
    return `${d.getDate()} de ${capitalizedMonth} de ${year}`
  }
})

// Navegação de Período
const navigatePrev = () => {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() - 1)
  } else if (viewMode.value === 'week') {
    d.setDate(d.getDate() - 7)
  } else {
    d.setDate(d.getDate() - 1)
  }
  currentDate.value = d
}

const navigateNext = () => {
  const d = new Date(currentDate.value)
  if (viewMode.value === 'month') {
    d.setMonth(d.getMonth() + 1)
  } else if (viewMode.value === 'week') {
    d.setDate(d.getDate() + 7)
  } else {
    d.setDate(d.getDate() + 1)
  }
  currentDate.value = d
}

const navigateToday = () => {
  currentDate.value = new Date()
}

const selectDate = (date) => {
  currentDate.value = new Date(date)
}

// 1. MÊS (Month Grid Builder)
const monthDaysGrid = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  const firstDayOfMonth = new Date(year, month, 1)
  const lastDayOfMonth = new Date(year, month + 1, 0)

  const startingDayOfWeek = firstDayOfMonth.getDay() // 0 = Domingo
  const daysInMonth = lastDayOfMonth.getDate()

  const grid = []
  const todayStr = new Date().toISOString().split('T')[0]

  // Dias do mês anterior
  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    const prevDate = new Date(year, month - 1, prevMonthLastDay - i)
    const dateStr = prevDate.toISOString().split('T')[0]
    grid.push({
      date: prevDate,
      dateStr,
      dayNumber: prevMonthLastDay - i,
      isCurrentMonth: false,
      isToday: dateStr === todayStr,
      events: getEventsForDate(dateStr)
    })
  }

  // Dias do mês atual
  for (let day = 1; day <= daysInMonth; day++) {
    const currDate = new Date(year, month, day)
    const dateStr = currDate.toISOString().split('T')[0]
    grid.push({
      date: currDate,
      dateStr,
      dayNumber: day,
      isCurrentMonth: true,
      isToday: dateStr === todayStr,
      events: getEventsForDate(dateStr)
    })
  }

  // Completa as semanas (até 35 ou 42 células)
  const remainingCells = (7 - (grid.length % 7)) % 7
  for (let day = 1; day <= remainingCells; day++) {
    const nextDate = new Date(year, month + 1, day)
    const dateStr = nextDate.toISOString().split('T')[0]
    grid.push({
      date: nextDate,
      dateStr,
      dayNumber: day,
      isCurrentMonth: false,
      isToday: dateStr === todayStr,
      events: getEventsForDate(dateStr)
    })
  }

  return grid
})

// 2. SEMANA (Week Grid Builder)
const weekDaysGrid = computed(() => {
  const curr = new Date(currentDate.value)
  const dayOfWeek = curr.getDay()
  const firstDayOfWeek = new Date(curr)
  firstDayOfWeek.setDate(curr.getDate() - dayOfWeek)

  const todayStr = new Date().toISOString().split('T')[0]
  const weekDays = []

  for (let i = 0; i < 7; i++) {
    const d = new Date(firstDayOfWeek)
    d.setDate(firstDayOfWeek.getDate() + i)
    const dateStr = d.toISOString().split('T')[0]
    weekDays.push({
      date: d,
      dateStr,
      dayNumber: d.getDate(),
      dayName: weekDaysShort[i],
      isToday: dateStr === todayStr,
      events: getEventsForDate(dateStr)
    })
  }

  return weekDays
})

// 3. DIA (Day View Events)
const selectedDayEvents = computed(() => {
  const dateStr = currentDate.value.toISOString().split('T')[0]
  return getEventsForDate(dateStr)
})

// Utilitário para buscar eventos de uma data YYYY-MM-DD
const getEventsForDate = (dateStr) => {
  return events.value.filter(evt => {
    if (!evt.start) return false
    const evtDateStr = evt.start.split('T')[0]
    return evtDateStr === dateStr
  })
}

// Formatadores
const formatEventTime = (isoStart) => {
  if (!isoStart || !isoStart.includes('T')) return ''
  const parts = isoStart.split('T')[1].split(':')
  return `${parts[0]}:${parts[1]}`
}

const formatFullDate = (date) => {
  return date.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

const formatEventDateTime = (start, end, allDay) => {
  if (allDay) return 'Dia Inteiro'
  if (!start) return ''
  const s = new Date(start).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  if (!end) return s
  const e = new Date(end).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  return `${s} até ${e}`
}

// Requisições HTTP (API Backend)
const fetchEvents = async () => {
  loadingEvents.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/v1/webcal-feeds/events/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    events.value = res.data
  } catch (err) {
    console.error('Erro ao buscar eventos do calendário:', err)
  } finally {
    loadingEvents.value = false
  }
}

const fetchFeeds = async () => {
  loadingFeeds.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/v1/webcal-feeds/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    feedsList.value = res.data
  } catch (err) {
    console.error('Erro ao carregar feeds:', err)
  } finally {
    loadingFeeds.value = false
  }
}

const saveFeed = async () => {
  if (!feedForm.value.name || !feedForm.value.url) return
  savingFeed.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('/api/v1/webcal-feeds/', feedForm.value, {
      headers: { Authorization: `Bearer ${token}` }
    })
    feedForm.value = { name: '', url: '', color: '#3b82f6' }
    await fetchFeeds()
    await fetchEvents()
  } catch (err) {
    console.error('Erro ao salvar feed:', err)
    alert('Erro ao salvar feed WebCAL.')
  } finally {
    savingFeed.value = false
  }
}

const deleteFeed = async (feedId) => {
  if (!confirm('Deseja excluir este feed WebCAL?')) return
  try {
    const token = localStorage.getItem('token')
    await axios.delete(`/api/v1/webcal-feeds/${feedId}/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    await fetchFeeds()
    await fetchEvents()
  } catch (err) {
    console.error('Erro ao excluir feed:', err)
  }
}

const openEventDetails = (evt) => {
  selectedEvent.value = evt
}

const goToPendency = (pendencyId) => {
  selectedEvent.value = null
  router.push('/pendencies')
}

onMounted(() => {
  fetchEvents()
  fetchFeeds()
})
</script>

<style scoped>
.calendar-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: hidden;
  padding: 20px;
  gap: 16px;
  background: var(--bg-dark);
  color: var(--text-primary);
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-sidebar);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-title-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  color: var(--accent);
}

.header-title-box h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}

.nav-btn-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn-glass {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  width: 34px;
  height: 34px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn-glass:hover {
  background: var(--border);
  transform: translateY(-1px);
}

.btn-today {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

.btn-today:hover {
  background: var(--border);
}

.view-mode-tabs {
  display: flex;
  padding: 4px;
  border-radius: 12px;
  background: var(--glass);
  border: 1px solid var(--border);
}

.tab-btn {
  padding: 6px 18px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--accent);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(34, 181, 95, 0.3);
}

.btn-sync {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

.btn-sync:hover {
  background: var(--border);
}

.btn-primary-v2 {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  border: none;
  color: #ffffff;
  padding: 8px 18px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary-v2:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(34, 181, 95, 0.3);
}

.btn-secondary-v2 {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 8px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary-v2:hover {
  background: var(--border);
}

/* Body Area */
.calendar-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 1. Month Grid */
.month-grid-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 8px;
}

.weekdays-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  text-align: center;
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.month-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(5, 1fr);
  gap: 8px;
  flex: 1;
}

.day-cell {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.day-cell:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.day-cell.other-month {
  opacity: 0.35;
}

.day-cell.is-today {
  border: 2px solid var(--accent);
  background: rgba(34, 181, 95, 0.08);
}

.day-cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.day-number {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.event-count-badge {
  font-size: 0.7rem;
  font-weight: 700;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 10px;
  color: var(--text-secondary);
}

.day-events-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.event-chip {
  padding: 3px 8px;
  border-radius: 6px;
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-events-link {
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: 600;
  margin-top: 2px;
}

/* 2. Week View */
.week-view-wrapper {
  flex: 1;
  display: flex;
}

.week-columns-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  flex: 1;
}

.week-column {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
}

.week-column.is-today {
  border-color: var(--accent);
  background: rgba(34, 181, 95, 0.08);
}

.week-column-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
  margin-bottom: 12px;
}

.week-day-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.week-day-num {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
}

.week-events-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.week-event-card {
  background: var(--glass);
  border: 1px solid var(--border);
  border-left-width: 4px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.week-event-card:hover {
  background: var(--border);
}

.evt-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.evt-card-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 2px;
}

.evt-card-source {
  font-size: 0.7rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

.empty-day-note {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 20px;
  opacity: 0.5;
}

/* 3. Day View */
.day-view-wrapper {
  flex: 1;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
}

.day-view-header h3 {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}

.day-view-events-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.day-full-event-card {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-left-width: 6px;
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
}

.event-time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  color: #ffffff;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.event-info-main h4 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.evt-loc, .evt-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 2px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.empty-state-card {
  text-align: center;
  padding: 50px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.4;
}

/* Modais */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.medium-modal {
  width: 550px;
  max-width: 92%;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  color: var(--text-primary);
}

.small-modal {
  width: 450px;
  max-width: 90%;
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  color: var(--text-primary);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h2 {
  color: var(--text-primary);
}

.close-btn-round {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn-round:hover {
  background: var(--border);
}

.feed-form {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--glass);
  margin-bottom: 20px;
}

.feed-form h4 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 14px 0;
}

.form-group label {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 6px;
  display: block;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-group {
  margin-bottom: 12px;
}

.color-picker-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-input {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  background: transparent;
}

.color-presets {
  display: flex;
  gap: 6px;
}

.preset-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
}

.preset-dot:hover {
  transform: scale(1.2);
}

.feeds-list-section h4 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  margin-bottom: 10px;
}

.feeds-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
}

.feed-item-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--glass);
  border: 1px solid var(--border);
}

.feed-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.feed-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.feed-item-info strong {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.feed-url-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.icon-btn-danger {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
}

.icon-btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
}

/* Details Modal */
.event-source-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #ffffff;
  padding: 3px 8px;
  border-radius: 6px;
  display: inline-block;
  margin-top: 6px;
}

.event-details-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: var(--text-primary);
}

.detail-icon {
  color: var(--accent);
  margin-top: 2px;
}

.detail-row strong {
  font-size: 0.85rem;
  color: var(--text-secondary);
  display: block;
}

.detail-row p {
  font-size: 0.95rem;
  color: var(--text-primary);
  margin: 2px 0 0 0;
}

.description-text {
  white-space: pre-wrap;
  background: var(--glass);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  max-height: 150px;
  overflow-y: auto;
  color: var(--text-primary);
}
</style>

