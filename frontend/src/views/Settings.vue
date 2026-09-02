<template>
  <div class="settings-page-container animate-fade-in">
    <!-- Cabeçalho Principal -->
    <header class="settings-header glass-effect">
      <div class="header-info">
        <h1>Configurações do Sistema</h1>
        <p>Gerencie integrações, atalhos, horários de ausência e preferências de desempenho</p>
      </div>

      <!-- Barra de Abas de Navegação -->
      <nav class="settings-tabs">
        <button 
          @click="activeSettingsTab = 'general'" 
          :class="{ active: activeSettingsTab === 'general' }" 
          class="tab-btn"
        >
          <ZapIcon :size="18" />
          <span>Geral & Desempenho</span>
        </button>

        <button 
          @click="activeSettingsTab = 'gateway'" 
          :class="{ active: activeSettingsTab === 'gateway' }" 
          class="tab-btn"
        >
          <ServerIcon :size="18" />
          <span>Gateway WhatsApp</span>
        </button>

        <button 
          @click="activeSettingsTab = 'replies'" 
          :class="{ active: activeSettingsTab === 'replies' }" 
          class="tab-btn"
        >
          <MessageIcon :size="18" />
          <span>Respostas Rápidas</span>
        </button>

        <button 
          @click="activeSettingsTab = 'schedule'" 
          :class="{ active: activeSettingsTab === 'schedule' }" 
          class="tab-btn"
        >
          <ClockIcon :size="18" />
          <span>Horário de Atendimento</span>
        </button>

        <button 
          @click="activeSettingsTab = 'webcal'" 
          :class="{ active: activeSettingsTab === 'webcal' }" 
          class="tab-btn"
        >
          <CalendarIcon :size="18" />
          <span>Calendários iCal</span>
        </button>

        <button 
          @click="activeSettingsTab = 'notifications'" 
          :class="{ active: activeSettingsTab === 'notifications' }" 
          class="tab-btn"
        >
          <BellIcon :size="18" />
          <span>Minhas Notificações</span>
        </button>

        <button 
          v-if="chatStore.userRole === 'admin'" 
          @click="activeSettingsTab = 'danger'" 
          :class="{ active: activeSettingsTab === 'danger' }" 
          class="tab-btn danger-tab"
        >
          <AlertIcon :size="18" />
          <span>Avançado & Sistema</span>
        </button>
      </nav>
    </header>

    <main class="settings-content">
      <!-- ABA 1: GERAL & DESEMPENHO -->
      <div v-if="activeSettingsTab === 'general'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header">
            <ZapIcon :size="24" style="color: #f59e0b;" />
            <div>
              <h2>Desempenho da Interface</h2>
              <p class="section-desc">Otimizações visuais recomendadas para máquinas antigas ou celulares.</p>
            </div>
          </div>

          <div class="form-container">
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">⚡ Modo de Alto Desempenho (Leve / PCs Antigos)</label>
                <span class="setting-desc">Desativa efeitos visuais pesados (glassmorphism/blur e animações) deixando a navegação instantânea em processadores Core i5 de 1ª Ger ou RAM limitada.</span>
              </div>
              <label class="switch-container">
                <input type="checkbox" v-model="performanceMode" @change="togglePerformanceMode" />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- SEÇÃO: MONITOR DE RECURSOS DO SERVIDOR AO VIVO -->
        <section class="settings-section glass-effect" style="margin-top: 25px;">
          <div class="section-header" style="justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 15px;">
              <ActivityIcon :size="24" style="color: #10b981;" />
              <div>
                <h2>Monitor de Recursos do Servidor (Ao Vivo)</h2>
                <p class="section-desc">Uso de CPU, Memória RAM e SWAP em tempo real no servidor.</p>
              </div>
            </div>
            <div class="live-indicator">
              <span class="pulse-dot"></span>
              <span>AO VIVO</span>
            </div>
          </div>

          <!-- Cards de Métricas e Gráficos -->
          <div class="metrics-grid">
            <!-- CPU Card -->
            <div class="metric-card glass-effect">
              <div class="metric-header">
                <div class="metric-title-wrap">
                  <CpuIcon :size="18" style="color: #3b82f6;" />
                  <span class="metric-name">Processador (CPU)</span>
                </div>
                <span class="metric-value" :class="getCpuColorClass(currentMetrics.cpu_percent)">
                  {{ currentMetrics.cpu_percent }}%
                </span>
              </div>
              <div class="chart-container">
                <svg class="live-svg-chart" viewBox="0 0 300 80" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.4"/>
                      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0"/>
                    </linearGradient>
                  </defs>
                  <polygon :points="getCpuFillPoints" fill="url(#cpuGrad)" />
                  <polyline :points="getCpuStrokePoints" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>
            </div>

            <!-- RAM Card -->
            <div class="metric-card glass-effect">
              <div class="metric-header">
                <div class="metric-title-wrap">
                  <RamIcon :size="18" style="color: #10b981;" />
                  <span class="metric-name">Memória RAM</span>
                </div>
                <div class="metric-value-wrap">
                  <span class="metric-value" :class="getRamColorClass(currentMetrics.memory_percent)">
                    {{ currentMetrics.memory_percent }}%
                  </span>
                  <small class="metric-sub">{{ currentMetrics.memory_used_mb }} MB / {{ currentMetrics.memory_total_mb }} MB</small>
                </div>
              </div>
              <div class="chart-container">
                <svg class="live-svg-chart" viewBox="0 0 300 80" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#10b981" stop-opacity="0.4"/>
                      <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
                    </linearGradient>
                  </defs>
                  <polygon :points="getRamFillPoints" fill="url(#ramGrad)" />
                  <polyline :points="getRamStrokePoints" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>
            </div>

            <!-- SWAP Card (se houver SWAP no sistema) -->
            <div v-if="currentMetrics.swap_total_mb > 0" class="metric-card glass-effect">
              <div class="metric-header">
                <div class="metric-title-wrap">
                  <HardDriveIcon :size="18" style="color: #f59e0b;" />
                  <span class="metric-name">Memória SWAP</span>
                </div>
                <div class="metric-value-wrap">
                  <span class="metric-value" :class="getRamColorClass(currentMetrics.swap_percent)">
                    {{ currentMetrics.swap_percent }}%
                  </span>
                  <small class="metric-sub">{{ currentMetrics.swap_used_mb }} MB / {{ currentMetrics.swap_total_mb }} MB</small>
                </div>
              </div>
              <div class="swap-progress-bg">
                <div class="swap-progress-fill" :style="{ width: currentMetrics.swap_percent + '%' }"></div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- ABA 2: GATEWAY WHATSAPP -->
      <div v-if="activeSettingsTab === 'gateway'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header">
            <ServerIcon :size="24" style="color: #10b981;" />
            <div>
              <h2>Evolution API (Evolution GO)</h2>
              <p class="section-desc">Parâmetros globais de conexão com o servidor da Evolution API.</p>
            </div>
          </div>

          <div class="form-container">
            <div class="grid-2">
              <div class="form-group">
                <label>URL Base da API *</label>
                <input 
                  v-model="settings.evolution_api_url" 
                  type="text" 
                  placeholder="Ex: http://evolution-go:8080"
                  class="input-glass premium-input"
                />
                <small>Endereço do container/servidor onde a Evolution API está operando.</small>
              </div>

              <div class="form-group">
                <label>Chave Global de API (API Key) *</label>
                <div class="input-with-icon">
                  <input 
                    :type="showKey ? 'text' : 'password'" 
                    v-model="settings.evolution_api_key" 
                    placeholder="Sua Global API Key"
                    class="input-glass premium-input"
                  />
                  <button type="button" @click="showKey = !showKey" class="icon-toggle">
                    <EyeIcon v-if="!showKey" :size="18" />
                    <EyeOffIcon v-else :size="18" />
                  </button>
                </div>
                <small>Chave mestre global informada no docker-compose.</small>
              </div>
            </div>

            <div class="form-group" style="margin-top: 15px;">
              <label>Webhook Global de Eventos</label>
              <div class="readonly-box">
                <code>{{ webhookUrl }}</code>
                <button type="button" @click="copyWebhook" class="copy-btn" title="Copiar URL do Webhook">
                  <CopyIcon :size="16" />
                </button>
              </div>
              <small>Cadastre este endereço na Evolution API para receber mensagens em tempo real.</small>
            </div>

            <div class="action-bar" style="margin-top: 25px;">
              <button @click="saveSettings" class="btn-primary" :disabled="saving">
                <SaveIcon :size="20" />
                {{ saving ? 'Salvando...' : 'Salvar Alterações' }}
              </button>
              <span v-if="saveSuccess" class="success-msg animate-pop">Configurações salvas com sucesso!</span>
            </div>
          </div>
        </section>
      </div>

      <!-- ABA 3: RESPOSTAS RÁPIDAS -->
      <div v-if="activeSettingsTab === 'replies'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header" style="justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 15px;">
              <MessageIcon :size="24" style="color: #3b82f6;" />
              <div>
                <h2>Respostas Rápidas</h2>
                <p class="section-desc">Crie atalhos `/` para enviar textos pré-formatados durante o atendimento.</p>
              </div>
            </div>
            <button v-if="!showReplyForm" @click="openNewReplyForm" class="btn-primary">
              <PlusIcon :size="18" /> Nova Resposta
            </button>
          </div>

          <!-- Formulário Criar/Editar -->
          <div v-if="showReplyForm" class="form-container sub-form glass-effect" style="margin-top: 20px;">
            <h3>{{ editingReplyId ? 'Editar Resposta Rápida' : 'Nova Resposta Rápida' }}</h3>
            <div class="grid-2" style="margin-top: 15px;">
              <div class="form-group">
                <label>Atalho (Sem a barra "/") *</label>
                <input 
                  v-model="replyForm.title" 
                  type="text" 
                  placeholder="Ex: bomdia"
                  class="input-glass premium-input"
                />
                <small>Acionador no chat (Exemplo: /bomdia).</small>
              </div>
              <div class="form-group">
                <label>Conteúdo da Mensagem *</label>
                <textarea 
                  v-model="replyForm.body" 
                  rows="3"
                  placeholder="Ex: Olá! Como posso te ajudar hoje?"
                  class="input-glass premium-input"
                />
              </div>
            </div>
            <div class="action-bar-sm" style="margin-top: 15px; display: flex; gap: 10px;">
              <button @click="saveReply" class="btn-primary" :disabled="savingReply">
                <CheckIcon :size="18" /> {{ savingReply ? 'Salvando...' : 'Salvar Atalho' }}
              </button>
              <button @click="closeReplyForm" class="btn-secondary" :disabled="savingReply">
                Cancelar
              </button>
            </div>
          </div>

          <!-- Tabela de Respostas -->
          <div v-else class="replies-table-container" style="margin-top: 20px;">
            <div v-if="quickReplies.length === 0" class="empty-state glass-effect">
              Nenhuma resposta rápida cadastrada. Clique em "+ Nova Resposta" para criar.
            </div>
            <table v-else class="premium-table">
              <thead>
                <tr>
                  <th>Atalho</th>
                  <th>Conteúdo da Mensagem</th>
                  <th style="text-align: right;">Ações</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="reply in quickReplies" :key="reply.id">
                  <td><span class="shortcut-badge">/{{ reply.title }}</span></td>
                  <td class="reply-text-col" :title="reply.body">{{ reply.body }}</td>
                  <td style="text-align: right;">
                    <div style="display: flex; justify-content: flex-end; gap: 8px;">
                      <button @click="editReply(reply)" class="action-icon-btn edit" title="Editar">
                        <EditIcon :size="16" />
                      </button>
                      <button @click="deleteReply(reply.id)" class="action-icon-btn delete" title="Apagar">
                        <TrashIcon :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <!-- ABA 4: HORÁRIO DE ATENDIMENTO -->
      <div v-if="activeSettingsTab === 'schedule'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header">
            <ClockIcon :size="24" style="color: #ef4444;" />
            <div>
              <h2>Horário de Atendimento & Ausência</h2>
              <p class="section-desc">Defina o expediente da equipe e ative a resposta automática fora do horário.</p>
            </div>
          </div>

          <div class="form-container">
            <div class="setting-row-card glass-effect" style="margin-bottom: 20px;">
              <div class="setting-info">
                <label class="setting-title">Enviar Mensagem de Ausência Fora do Expediente</label>
                <span class="setting-desc">Dispara uma mensagem automática quando um cliente entra em contato fora dos horários configurados abaixo.</span>
              </div>
              <label class="switch-container">
                <input type="checkbox" v-model="absence.enabled" />
                <span class="switch-slider"></span>
              </label>
            </div>

            <div class="grid-2">
              <div class="form-group">
                <label>Fuso Horário *</label>
                <select v-model="absence.timezone" class="select-glass">
                  <option value="America/Sao_Paulo">Brasília (America/Sao_Paulo)</option>
                  <option value="America/Manaus">Manaus (America/Manaus)</option>
                  <option value="America/Fortaleza">Fortaleza (America/Fortaleza)</option>
                  <option value="America/New_York">New York (America/New_York)</option>
                </select>
              </div>

              <div class="form-group">
                <label>Mensagem de Ausência</label>
                <textarea 
                  v-model="absence.message" 
                  rows="3"
                  placeholder="Ex: Olá! No momento estamos fora do nosso horário de atendimento..."
                  class="input-glass premium-input"
                />
              </div>
            </div>

            <!-- Grade Semanal -->
            <div class="form-group" style="margin-top: 20px;">
              <label style="font-weight: 700; margin-bottom: 12px; display: block;">Horário de Expediente por Dia da Semana</label>
              <div class="schedule-grid">
                <div 
                  v-for="(day, index) in weekDays" 
                  :key="index" 
                  class="schedule-day-row glass-effect"
                  :class="{ inactive: !getDaySchedule(index).active }"
                >
                  <div class="day-checkbox-label">
                    <input 
                      type="checkbox" 
                      v-model="getDaySchedule(index).active"
                      style="width: 18px; height: 18px; accent-color: var(--accent);"
                    />
                    <span style="font-weight: 600;">{{ day }}</span>
                  </div>
                  
                  <div v-if="getDaySchedule(index).active" class="time-pickers">
                    <input 
                      type="time" 
                      v-model="getDaySchedule(index).start"
                      class="time-input input-glass"
                    />
                    <span class="time-separator">até</span>
                    <input 
                      type="time" 
                      v-model="getDaySchedule(index).end"
                      class="time-input input-glass"
                    />
                  </div>
                  <div v-else class="day-closed-text">
                    Fechado o dia todo
                  </div>
                </div>
              </div>
            </div>

            <div class="action-bar" style="margin-top: 25px;">
              <button @click="saveAbsenceSettings" class="btn-primary" :disabled="savingAbsence">
                <SaveIcon :size="20" />
                {{ savingAbsence ? 'Salvando...' : 'Salvar Agenda e Ausência' }}
              </button>
              <span v-if="saveAbsenceSuccess" class="success-msg animate-pop">Agenda atualizada com sucesso!</span>
            </div>
          </div>
        </section>
      </div>

      <!-- ABA 5: CALENDÁRIOS iCAL -->
      <div v-if="activeSettingsTab === 'webcal'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header" style="justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 15px;">
              <CalendarIcon :size="24" style="color: #8b5cf6;" />
              <div>
                <h2>Feeds de Calendários (Webcal / iCal)</h2>
                <p class="section-desc">Sincronize agendas do Google Calendar, Outlook ou Apple Calendar.</p>
              </div>
            </div>
            <button v-if="!showFeedForm" @click="openNewFeedForm" class="btn-primary">
              <PlusIcon :size="18" /> Novo Calendário
            </button>
          </div>

          <div v-if="showFeedForm" class="form-container sub-form glass-effect" style="margin-top: 20px;">
            <h3>{{ editingFeedId ? 'Editar Calendário' : 'Novo Calendário Webcal' }}</h3>
            <div class="grid-2" style="margin-top: 15px;">
              <div class="form-group">
                <label>Nome do Calendário *</label>
                <input v-model="feedForm.name" type="text" placeholder="Ex: Agenda de Reuniões" class="input-glass" />
              </div>
              <div class="form-group">
                <label>URL do Feed (webcal:// ou https://...ics) *</label>
                <input v-model="feedForm.url" type="text" placeholder="https://calendar.google.com/.../basic.ics" class="input-glass" />
              </div>
            </div>
            <div class="action-bar-sm" style="margin-top: 15px; display: flex; gap: 10px;">
              <button @click="saveFeed" class="btn-primary" :disabled="savingFeed">
                <CheckIcon :size="18" /> {{ savingFeed ? 'Salvando...' : 'Salvar Feed' }}
              </button>
              <button @click="closeFeedForm" class="btn-secondary">Cancelar</button>
            </div>
          </div>

          <div v-else class="feeds-list" style="margin-top: 20px;">
            <div v-if="webcalFeeds.length === 0" class="empty-state glass-effect">
              Nenhum feed de calendário adicionado.
            </div>
            <div v-else class="feeds-grid">
              <div v-for="feed in webcalFeeds" :key="feed.id" class="feed-card glass-effect">
                <div class="feed-info">
                  <span class="feed-color-dot" :style="{ background: feed.color || '#3b82f6' }"></span>
                  <strong>{{ feed.name }}</strong>
                </div>
                <div class="feed-actions">
                  <button @click="editFeed(feed)" class="action-icon-btn edit"><EditIcon :size="16" /></button>
                  <button @click="deleteFeed(feed.id)" class="action-icon-btn delete"><TrashIcon :size="16" /></button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- ABA 6: AVANÇADO & SISTEMA -->
      <div v-if="activeSettingsTab === 'danger' && chatStore.userRole === 'admin'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header">
            <ServerIcon :size="24" style="color: #3b82f6;" />
            <div>
              <h2>Status e Diagnóstico do Sistema</h2>
              <p class="section-desc">Conexão interna com microsserviços.</p>
            </div>
          </div>
          <div class="status-grid-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            <div class="status-card glass-effect">
              <span>Backend Django</span>
              <strong class="status-tag online">ONLINE</strong>
            </div>
            <div class="status-card glass-effect">
              <span>Servidor Realtime (Redis)</span>
              <strong class="status-tag online">CONECTADO</strong>
            </div>
            <div class="status-card glass-effect">
              <span>Versão do Sistema</span>
              <strong>v1.2.0-stable</strong>
            </div>
          </div>
        </section>

        <!-- Zona de Perigo -->
        <section class="settings-section glass-effect danger-zone" style="margin-top: 25px;">
          <div class="section-header">
            <AlertIcon :size="24" class="icon-danger" />
            <div>
              <h2>Zona de Perigo</h2>
              <p class="section-desc">Ações de limpeza permanentes. Proceda com cautela.</p>
            </div>
          </div>

          <div class="danger-actions" style="margin-top: 15px;">
            <div class="danger-item glass-effect">
              <div class="danger-text">
                <h3>Zerar Histórico de Conversas</h3>
                <p>Apaga permanentemente todos os tickets e mensagens enviadas de todos os atendentes.</p>
              </div>
              <button @click="triggerResetModal" class="btn-danger" :disabled="reseting">
                <TrashIcon :size="18" />
                {{ reseting ? 'Limpando...' : 'Zerar Banco de Conversas' }}
              </button>
            </div>
          </div>
        </section>
      </div>

      <!-- ABA: MINHAS NOTIFICAÇÕES WHATSAPP -->
      <div v-if="activeSettingsTab === 'notifications'" class="tab-pane animate-fade-in">
        <section class="settings-section glass-effect">
          <div class="section-header">
            <BellIcon :size="24" style="color: #10b981;" />
            <div>
              <h2>Preferências de Notificações Diárias</h2>
              <p class="section-desc">Personalize o horário e quais relatórios você deseja receber no seu WhatsApp.</p>
            </div>
          </div>

          <div class="form-container" style="margin-top: 20px;">
            <!-- Número de WhatsApp do Usuário -->
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">📱 Seu Número de WhatsApp</label>
                <span class="setting-desc">Número utilizado para receber os relatórios diários e alertas de conversas/pendências.</span>
              </div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <input 
                  v-model="userProfile.whatsapp" 
                  type="text" 
                  placeholder="Ex: 5511999999999" 
                  class="input-glass premium-input"
                  style="width: 220px;"
                />
              </div>
            </div>

            <!-- Horário de Envio -->
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">⏰ Horário de Envio dos Relatórios</label>
                <span class="setting-desc">Horário em que o WDesk enviará automaticamente o resumo diário para o seu WhatsApp.</span>
              </div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <input 
                  v-model="userProfile.notification_time" 
                  type="time" 
                  class="input-glass premium-input"
                  style="width: 140px; text-align: center;"
                />
              </div>
            </div>

            <!-- Relatório de Pendências -->
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">📋 Relatório Diário de Pendências</label>
                <span class="setting-desc">Receba diariamente o resumo das suas pendências atrasadas, previstas para hoje e ativas.</span>
              </div>
              <label class="switch-container">
                <input type="checkbox" v-model="userProfile.notify_daily_pendencies" />
                <span class="switch-slider"></span>
              </label>
            </div>

            <!-- Relatório de Conversas Abertas / Pendentes -->
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">💬 Relatório Diário de Conversas Abertas</label>
                <span class="setting-desc">Receba diariamente o resumo dos atendimentos em andamento e aguardando retorno sob sua responsabilidade.</span>
              </div>
              <label class="switch-container">
                <input type="checkbox" v-model="userProfile.notify_daily_open_tickets" />
                <span class="switch-slider"></span>
              </label>
            </div>

            <!-- Alerta de Fila sem Atendimento -->
            <div class="setting-row-card glass-effect">
              <div class="setting-info">
                <label class="setting-title">⏳ Alerta de Fila sem Atendimento</label>
                <span class="setting-desc">Seja alertado no WhatsApp se um cliente ficar aguardando atendimento na Fila por mais tempo que o tolerado.</span>
                <div v-if="userProfile.notify_queue_delay" style="margin-top: 8px; display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 0.85rem; color: var(--text-secondary);">Tempo de tolerância na fila:</span>
                  <select v-model="userProfile.queue_delay_minutes" class="select-glass" style="width: auto; padding: 4px 10px; font-size: 0.85rem;">
                    <option :value="3">3 minutos</option>
                    <option :value="5">5 minutos (Padrão)</option>
                    <option :value="10">10 minutos</option>
                    <option :value="15">15 minutos</option>
                    <option :value="30">30 minutos</option>
                  </select>
                </div>
              </div>
              <label class="switch-container">
                <input type="checkbox" v-model="userProfile.notify_queue_delay" />
                <span class="switch-slider"></span>
              </label>
            </div>

            <!-- Ações de Salvar e Testar -->
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 25px; flex-wrap: wrap; gap: 15px;">
              <button 
                @click="testUserNotifications" 
                class="btn-secondary" 
                :disabled="testingNotif || !userProfile.whatsapp"
                title="Dispara um envio de teste imediatamente para o seu WhatsApp"
              >
                <SendIcon :size="16" />
                <span>{{ testingNotif ? 'Enviando Teste...' : 'Testar Envio no Meu WhatsApp' }}</span>
              </button>

              <button 
                @click="saveUserProfile" 
                class="btn-primary" 
                :disabled="savingProfile"
              >
                <SaveIcon :size="16" />
                <span>{{ savingProfile ? 'Salvando...' : 'Salvar Preferências' }}</span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- Modal de Confirmação de Reset -->
    <Transition name="modal-fade">
      <div v-if="confirmReset" class="modal-overlay" @click="confirmReset = false">
        <div class="modal-content danger-modal" @click.stop>
          <AlertIcon :size="48" class="icon-danger large" />
          <h2>Tem certeza absoluta?</h2>
          <p>Esta ação apagará **TODAS** as conversas, tickets e históricos de atendimento da sua empresa. Esta ação **não pode ser desfeita**.</p>
          
          <div style="margin-bottom: 20px; text-align: left;">
            <label style="font-size: 0.8rem; font-weight: 700; color: #ef4444; display: block; margin-bottom: 8px; text-transform: uppercase;">
              Digite "Confirmar" para prosseguir:
            </label>
            <input 
              v-model="resetTextConfirm" 
              type="text" 
              placeholder="Digite Confirmar por extenso" 
              class="input-glass premium-input" 
              style="border-color: rgba(239, 68, 68, 0.4); text-align: center;"
            />
          </div>

          <div class="modal-actions-vertical">
            <button 
              @click="handleReset" 
              class="btn-danger block" 
              :disabled="reseting || resetTextConfirm !== 'Confirmar'"
            >
              SIM, APAGAR TUDO
            </button>
            <button @click="confirmReset = false" class="btn-ghost block" :disabled="reseting">
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { useChatStore } from '../store/chat'
import { useRouter } from 'vue-router'
import { 
  Settings as SettingsIcon,
  Zap as ZapIcon,
  Eye as EyeIcon,
  EyeOff as EyeOffIcon,
  Save as SaveIcon,
  Copy as CopyIcon,
  Info as InfoIcon,
  Trash2 as TrashIcon,
  AlertTriangle as AlertIcon,
  MessageSquare as MessageIcon,
  Clock as ClockIcon,
  Check as CheckIcon,
  Pencil as EditIcon,
  Plus as PlusIcon,
  ClipboardList as ClipboardIcon,
  Server as ServerIcon,
  Calendar as CalendarIcon,
  Activity as ActivityIcon,
  Cpu as CpuIcon,
  HardDrive as HardDriveIcon,
  Database as RamIcon,
  Bell as BellIcon,
  Send as SendIcon
} from 'lucide-vue-next'

const router = useRouter()
const chatStore = useChatStore()
const activeSettingsTab = ref('general')
const saving = ref(false)
const reseting = ref(false)
const saveSuccess = ref(false)
const showKey = ref(false)

const performanceMode = ref(localStorage.getItem('performanceMode') === 'true')

// === ESTADOS E MÉTODOS DE MONITORAMENTO DO SERVIDOR ===
const currentMetrics = ref({
  cpu_percent: 0,
  memory_percent: 0,
  memory_used_mb: 0,
  memory_total_mb: 0,
  swap_percent: 0,
  swap_used_mb: 0,
  swap_total_mb: 0
})

const cpuHistory = ref(Array(20).fill(0))
const ramHistory = ref(Array(20).fill(0))
let metricsInterval = null

const fetchMetrics = async () => {
  const data = await chatStore.fetchSystemMetrics()
  if (data) {
    currentMetrics.value = data
    cpuHistory.value.push(data.cpu_percent)
    if (cpuHistory.value.length > 20) cpuHistory.value.shift()

    ramHistory.value.push(data.memory_percent)
    if (ramHistory.value.length > 20) ramHistory.value.shift()
  }
}

const startMetricsPolling = () => {
  if (metricsInterval) clearInterval(metricsInterval)
  fetchMetrics()
  metricsInterval = setInterval(fetchMetrics, 3000)
}

const stopMetricsPolling = () => {
  if (metricsInterval) {
    clearInterval(metricsInterval)
    metricsInterval = null
  }
}

watch(activeSettingsTab, (newTab) => {
  if (newTab === 'general') {
    startMetricsPolling()
  } else {
    stopMetricsPolling()
  }
}, { immediate: true })

onUnmounted(() => {
  stopMetricsPolling()
})

const getCpuColorClass = (val) => {
  if (val > 85) return 'danger-text'
  if (val > 60) return 'warning-text'
  return 'success-text'
}

const getRamColorClass = (val) => {
  if (val > 85) return 'danger-text'
  if (val > 70) return 'warning-text'
  return 'success-text'
}

const getCpuStrokePoints = computed(() => {
  const width = 300
  const height = 80
  const step = width / (cpuHistory.value.length - 1 || 1)
  return cpuHistory.value.map((val, idx) => {
    const x = idx * step
    const y = height - (val / 100) * (height - 10) - 5
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})

const getCpuFillPoints = computed(() => {
  const stroke = getCpuStrokePoints.value
  return `0,80 ${stroke} 300,80`
})

const getRamStrokePoints = computed(() => {
  const width = 300
  const height = 80
  const step = width / (ramHistory.value.length - 1 || 1)
  return ramHistory.value.map((val, idx) => {
    const x = idx * step
    const y = height - (val / 100) * (height - 10) - 5
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})

const getRamFillPoints = computed(() => {
  const stroke = getRamStrokePoints.value
  return `0,80 ${stroke} 300,80`
})


const togglePerformanceMode = () => {
  localStorage.setItem('performanceMode', performanceMode.value ? 'true' : 'false')
  if (performanceMode.value) {
    document.documentElement.classList.add('performance-mode')
  } else {
    document.documentElement.classList.remove('performance-mode')
  }
}

const triggerResetModal = () => {
  resetTextConfirm.value = ''
  confirmReset.value = true
}

const settings = ref({
  evolution_api_url: '',
  evolution_api_key: '',
  pendency_report_time: '08:00',
  pendency_report_only_support: false
})

const webhookUrl = computed(() => {
  return `/api/v1/webhooks/evolution/`
})

// === ESTADOS E MÉTODOS DE RESPOSTAS RÁPIDAS ===
const quickReplies = ref([])
const showReplyForm = ref(false)
const editingReplyId = ref(null)
const savingReply = ref(false)
const replyForm = ref({
  title: '',
  body: ''
})

const fetchQuickReplies = async () => {
  try {
    quickReplies.value = await chatStore.fetchQuickReplies()
  } catch (e) {
    console.error(e)
  }
}

const openNewReplyForm = () => {
  editingReplyId.value = null
  replyForm.value = { title: '', body: '' }
  showReplyForm.value = true
}

const editReply = (reply) => {
  editingReplyId.value = reply.id
  replyForm.value = { title: reply.title, body: reply.body }
  showReplyForm.value = true
}

const closeReplyForm = () => {
  showReplyForm.value = false
}

const saveReply = async () => {
  if (!replyForm.value.title || !replyForm.value.body) {
    alert("Preencha todos os campos da resposta rápida")
    return
  }
  
  savingReply.value = true
  try {
    if (editingReplyId.value) {
      await chatStore.updateQuickReply(editingReplyId.value, replyForm.value)
    } else {
      await chatStore.createQuickReply(replyForm.value)
    }
    await fetchQuickReplies()
    showReplyForm.value = false
  } catch (e) {
    alert("Erro ao salvar resposta rápida")
  } finally {
    savingReply.value = false
  }
}

const deleteReply = async (id) => {
  if (confirm("Tem certeza que deseja excluir esta resposta rápida?")) {
    try {
      await chatStore.deleteQuickReply(id)
      await fetchQuickReplies()
    } catch (e) {
      alert("Erro ao excluir resposta rápida")
    }
  }
}

// === ESTADOS E MÉTODOS DE MENSAGENS DE AUSÊNCIA ===
const weekDays = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
  'Domingo'
]

const absence = ref({
  enabled: false,
  message: '',
  timezone: 'America/Sao_Paulo',
  schedule: [
    { day: 0, start: '08:00', end: '18:00', active: false },
    { day: 1, start: '08:00', end: '18:00', active: false },
    { day: 2, start: '08:00', end: '18:00', active: false },
    { day: 3, start: '08:00', end: '18:00', active: false },
    { day: 4, start: '08:00', end: '18:00', active: false },
    { day: 5, start: '08:00', end: '18:00', active: false },
    { day: 6, start: '08:00', end: '18:00', active: false }
  ]
})

const getDaySchedule = (dayIdx) => {
  const item = absence.value.schedule.find(s => parseInt(s.day) === dayIdx)
  return item || { day: dayIdx, start: '08:00', end: '18:00', active: false }
}

const savingAbsence = ref(false)
const saveAbsenceSuccess = ref(false)

const fetchAbsenceSettings = async () => {
  try {
    const data = await chatStore.fetchAbsenceSchedule()
    if (data) {
      absence.value.enabled = data.enabled
      absence.value.message = data.message
      absence.value.timezone = data.timezone
      if (data.schedule && data.schedule.length > 0) {
        data.schedule.forEach(item => {
          const idx = absence.value.schedule.findIndex(s => parseInt(s.day) === parseInt(item.day))
          if (idx !== -1) {
            absence.value.schedule[idx] = { ...absence.value.schedule[idx], ...item }
          }
        })
      }
    }
  } catch (e) {
    console.error("Erro ao buscar horários de ausência", e)
  }
}

const saveAbsenceSettings = async () => {
  savingAbsence.value = true
  saveAbsenceSuccess.value = false
  try {
    absence.value.schedule.sort((a, b) => parseInt(a.day) - parseInt(b.day))
    await chatStore.updateAbsenceSchedule(absence.value)
    saveAbsenceSuccess.value = true
    setTimeout(() => { saveAbsenceSuccess.value = false }, 3000)
  } catch (e) {
    alert("Erro ao salvar horários de ausência")
  } finally {
    savingAbsence.value = false
  }
}

const fetchSettings = async () => {
  try {
    const data = await chatStore.fetchCompanySettings()
    settings.value.evolution_api_url = data.evolution_api_url || ''
    settings.value.evolution_api_key = data.evolution_api_key || ''
    let repTime = data.pendency_report_time || '08:00'
    if (repTime.length > 5) {
      repTime = repTime.slice(0, 5)
    }
    settings.value.pendency_report_time = repTime
    settings.value.pendency_report_only_support = data.pendency_report_only_support || false
  } catch (e) {
    console.error("Erro ao buscar configurações", e)
  }
}

const saveSettings = async () => {
  saving.value = true
  saveSuccess.value = false
  try {
    await chatStore.updateCompanySettings(settings.value)
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e) {
    alert("Erro ao salvar configurações")
  } finally {
    saving.value = false
  }
}

const copyWebhook = () => {
  navigator.clipboard.writeText(webhookUrl.value)
  alert("URL copiada para a área de transferência!")
}

const handleReset = async () => {
  reseting.value = true
  try {
    const res = await chatStore.resetConversations()
    confirmReset.value = false
    alert(res?.message || "O processo de limpeza foi iniciado com sucesso.")
  } catch (e) {
    console.error("Erro no reset:", e)
    const errorMsg = e.response?.data?.error || e.response?.data?.detail || e.message
    alert("Erro ao zerar conversas: " + errorMsg)
  } finally {
    reseting.value = false
  }
}

// === ESTADOS E MÉTODOS DE CALENDÁRIOS WEBCAL ===
const webcalFeeds = ref([])
const showFeedForm = ref(false)
const editingFeedId = ref(null)
const savingFeed = ref(false)
const feedForm = ref({
  name: '',
  url: '',
  color: '#3b82f6'
})

const fetchWebcalFeeds = async () => {
  try {
    webcalFeeds.value = await chatStore.fetchWebcalFeeds()
  } catch (e) {
    console.error("Erro ao buscar calendários iCal", e)
  }
}

const openNewFeedForm = () => {
  editingFeedId.value = null
  feedForm.value = { name: '', url: '', color: '#3b82f6' }
  showFeedForm.value = true
}

const editFeed = (feed) => {
  editingFeedId.value = feed.id
  feedForm.value = { name: feed.name, url: feed.url, color: feed.color || '#3b82f6' }
  showFeedForm.value = true
}

const closeFeedForm = () => {
  showFeedForm.value = false
}

const saveFeed = async () => {
  if (!feedForm.value.name || !feedForm.value.url) {
    alert("Preencha o nome e a URL do feed de calendário")
    return
  }

  savingFeed.value = true
  try {
    if (editingFeedId.value) {
      await chatStore.updateWebcalFeed(editingFeedId.value, feedForm.value)
    } else {
      await chatStore.createWebcalFeed(feedForm.value)
    }
    await fetchWebcalFeeds()
    showFeedForm.value = false
  } catch (e) {
    alert("Erro ao salvar calendário. Verifique se a URL está correta.")
  } finally {
    savingFeed.value = false
  }
}

const deleteFeed = async (id) => {
  if (confirm("Tem certeza que deseja remover este calendário?")) {
    try {
      await chatStore.deleteWebcalFeed(id)
      await fetchWebcalFeeds()
    } catch (e) {
      alert("Erro ao excluir calendário")
    }
  }
}

// === ESTADOS DE PREFERÊNCIAS DE NOTIFICAÇÃO DO USUÁRIO ===
const userProfile = ref({
  whatsapp: '',
  notification_time: '08:00',
  notify_daily_pendencies: true,
  notify_daily_open_tickets: true,
  notify_queue_delay: false,
  queue_delay_minutes: 5
})
const savingProfile = ref(false)
const testingNotif = ref(false)
const confirmReset = ref(false)
const resetTextConfirm = ref('')

// === MÉTODOS DE NOTIFICAÇÕES DO USUÁRIO ===
const fetchUserProfile = async () => {
  try {
    const res = await axios.get('/api/v1/users/me/')
    const data = res.data
    userProfile.value = {
      whatsapp: data.whatsapp || '',
      notification_time: data.notification_time ? data.notification_time.substring(0, 5) : '08:00',
      notify_daily_pendencies: data.notify_daily_pendencies ?? true,
      notify_daily_open_tickets: data.notify_daily_open_tickets ?? true,
      notify_queue_delay: data.notify_queue_delay ?? false,
      queue_delay_minutes: data.queue_delay_minutes ?? 5
    }
  } catch (e) {
    console.error("Erro ao buscar perfil do usuário", e)
  }
}

const saveUserProfile = async () => {
  savingProfile.value = true
  try {
    await axios.patch('/api/v1/users/me/', {
      whatsapp: userProfile.value.whatsapp,
      notification_time: userProfile.value.notification_time,
      notify_daily_pendencies: userProfile.value.notify_daily_pendencies,
      notify_daily_open_tickets: userProfile.value.notify_daily_open_tickets,
      notify_queue_delay: userProfile.value.notify_queue_delay,
      queue_delay_minutes: userProfile.value.queue_delay_minutes
    })
    alert("Preferências de notificação salvas com sucesso!")
  } catch (e) {
    alert("Erro ao salvar preferências de notificação: " + (e.response?.data?.detail || e.message))
  } finally {
    savingProfile.value = false
  }
}

const testUserNotifications = async () => {
  testingNotif.value = true
  try {
    const res = await axios.post('/api/v1/users/test-notifications/', { type: 'all' })
    alert(res.data.message || "Disparo de teste executado!")
  } catch (e) {
    alert("Erro no teste de notificação: " + (e.response?.data?.error || e.message))
  } finally {
    testingNotif.value = false
  }
}

onMounted(() => {
  fetchSettings()
  fetchQuickReplies()
  fetchAbsenceSettings()
  fetchWebcalFeeds()
  fetchUserProfile()
})

</script>

<style scoped>
.settings-page-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 30px;
}

.settings-header {
  padding: 24px 30px;
  border-radius: 20px;
  margin-bottom: 25px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border: 1px solid var(--border);
}

.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title h1 { font-size: 1.8rem; font-weight: 800; margin: 0; }
.header-title p { color: var(--text-secondary); margin: 5px 0 0; }

.icon-accent { color: var(--accent); }

.settings-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
}

.settings-section {
  padding: 30px;
  border-radius: 20px;
  border: 1px solid var(--border);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.section-header h2 { font-size: 1.3rem; margin: 0; }
.section-desc { color: var(--text-secondary); margin-bottom: 30px; font-size: 0.95rem; }

.icon-warning { color: #f59e0b; }
.icon-info { color: var(--accent); }

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.icon-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 5px;
}

.form-group small {
  display: block;
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.readonly-box {
  background: var(--glass);
  padding: 12px 16px;
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--border);
}

.readonly-box code {
  font-family: 'Fira Code', monospace;
  font-size: 0.9rem;
  color: #10b981;
}

.copy-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-btn:hover { background: rgba(255, 255, 255, 0.2); }

.action-bar {
  margin-top: 40px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 14px 28px;
  border-radius: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2);
}

.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.success-msg { color: #10b981; font-weight: 600; font-size: 0.9rem; }

/* Sidebar Info Card */
.status-list { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
.status-item { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }
.status-tag { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.status-tag.online { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.version-label { color: var(--text-secondary); font-family: monospace; }

.help-box {
  margin-top: 30px;
  padding: 20px;
  background: rgba(245, 158, 11, 0.05);
  border-left: 4px solid #f59e0b;
  border-radius: 8px;
}
.help-box p { font-size: 0.85rem; color: #d97706; margin: 0; line-height: 1.5; }

/* Danger Zone */
.danger-zone {
  border: 1px solid rgba(239, 68, 68, 0.2) !important;
  background: rgba(239, 68, 68, 0.02) !important;
}

.icon-danger { color: #ef4444; }
.icon-danger.large { margin: 0 auto 20px; display: block; }

.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.danger-text h3 { font-size: 1rem; margin-bottom: 5px; color: #ef4444; }
.danger-text p { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

.btn-danger.block { width: 100%; justify-content: center; padding: 16px; }

/* Modal de Perigo */
.danger-modal {
  max-width: 440px;
  text-align: center;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.danger-modal h2 { margin-bottom: 15px; font-size: 1.4rem; color: #ef4444; }
.danger-modal p { color: var(--text-secondary); margin-bottom: 25px; line-height: 1.6; font-size: 0.9rem; }

.modal-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Sub Form */
.sub-form {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid var(--border);
  padding: 20px;
  border-radius: 12px;
  margin-top: 15px;
}

.action-bar-sm {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.btn-primary-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary-sm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.btn-secondary-sm {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn-secondary-sm:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-ghost-sm {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-ghost-sm:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}

/* Premium Table */
.replies-table-container {
  margin-top: 15px;
  overflow-x: auto;
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.premium-table th {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.premium-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 0.9rem;
  vertical-align: middle;
}

.shortcut-badge {
  font-size: 0.8rem;
  font-weight: 700;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  font-family: monospace;
}

.reply-text-col {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}

.action-icon-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-icon-btn:hover.edit {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.action-icon-btn:hover.delete {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
}

.empty-state {
  padding: 30px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
  border: 1px dashed var(--border);
  border-radius: 12px;
  margin-top: 15px;
}

/* Switch styling */
.flex-row {
  display: flex;
  align-items: center;
}

.switch-container {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  gap: 12px;
}

.switch-container input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.switch-slider {
  width: 48px;
  height: 24px;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border);
  border-radius: 20px;
  position: relative;
  transition: .3s;
}

.switch-slider:before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: .3s;
}

.switch-container input:checked + .switch-slider {
  background-color: var(--accent);
  border-color: rgba(16, 185, 129, 0.5);
}

.switch-container input:checked + .switch-slider:before {
  transform: translateX(24px);
}

.switch-label {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* Schedule Grid */
.schedule-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(0, 0, 0, 0.15);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  margin-top: 10px;
}

.schedule-day-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.schedule-day-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.schedule-day-row.inactive {
  opacity: 0.5;
}

.day-checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.day-checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  accent-color: var(--accent);
}

.time-pickers {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-input {
  background: var(--glass);
  border: 1px solid var(--border);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  outline: none;
  font-family: monospace;
}

.time-input:focus {
  border-color: var(--accent);
}

.time-separator {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.day-closed-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
}

/* Animations */
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
.animate-pop { animation: pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pop { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }

@media (max-width: 768px) {
  .settings-content {
    padding: 20px;
  }
  .settings-header {
    padding: 20px;
    margin-bottom: 20px;
  }
  .header-title h1 {
    font-size: 1.4rem;
  }
  .settings-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .settings-section {
    padding: 20px;
  }
  .readonly-box {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .readonly-box code {
    word-break: break-all;
    text-align: center;
  }
  .copy-btn {
    align-self: center;
    width: 100%;
    display: flex;
    justify-content: center;
  }
  .action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  .btn-primary {
    justify-content: center;
  }
  .danger-item {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  .btn-danger {
    width: 100%;
    justify-content: center;
  }
}

/* Estilos das Abas e Cards da UI de Configurações */
.settings-header {
  padding: 24px 30px;
  border-radius: 16px;
  margin-bottom: 25px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.settings-header p {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.settings-tabs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 5px;
  scrollbar-width: thin;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.tab-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.tab-btn.danger-tab.active {
  background: #ef4444;
  border-color: #ef4444;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.setting-row-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid var(--border);
}

.setting-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
  display: block;
}

.setting-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 4px;
  display: block;
  line-height: 1.4;
}

.status-card {
  padding: 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border: 1px solid var(--border);
}

.status-card span {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.status-card strong {
  font-size: 1rem;
  color: var(--text-primary);
}

/* Estilos das Métricas do Servidor Ao Vivo */
.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #10b981;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.95); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
  100% { transform: scale(0.95); opacity: 1; }
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.metric-card {
  padding: 20px;
  border-radius: 16px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.metric-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.metric-value {
  font-size: 1.4rem;
  font-weight: 800;
  font-family: monospace;
}

.metric-sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.danger-text { color: #ef4444; }
.warning-text { color: #f59e0b; }
.success-text { color: #10b981; }

.chart-container {
  width: 100%;
  height: 70px;
  overflow: hidden;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px;
}

.live-svg-chart {
  width: 100%;
  height: 100%;
  display: block;
}

.swap-progress-bg {
  width: 100%;
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  overflow: hidden;
}

.swap-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #ef4444);
  transition: width 0.5s ease;
}
</style>
