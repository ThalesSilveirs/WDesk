<template>
  <div class="pendencies-page-container">
    <main ref="mainContentEl" class="main-content">
      <!-- Cabeçalho da Página -->
      <header class="page-header glass-effect animate-in">
        <div class="header-info">
          <h1>Tickets e Pendências</h1>
          <p>Gerencie, priorize e acompanhe as atividades da sua equipe</p>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <SearchIcon :size="20" />
            <input v-model="search" placeholder="Buscar por título ou descrição..." type="text" />
          </div>
          <button @click="showFilters = !showFilters" :class="{ 'btn-filter-active': showFilters || activeFiltersCount > 0 }" class="btn-filter-toggle" title="Filtrar Pendências">
            <FilterIcon :size="18" />
            <span>Filtros</span>
            <span v-if="activeFiltersCount > 0" class="filter-count-badge">{{ activeFiltersCount }}</span>
          </button>
          <div class="view-switcher-toggle">
            <button @click="viewMode = 'grid'" :class="{ active: viewMode === 'grid' }" class="toggle-btn" title="Visualização em Grade">
              <LayoutGridIcon :size="18" />
            </button>
            <button @click="viewMode = 'list'" :class="{ active: viewMode === 'list' }" class="toggle-btn" title="Visualização em Tabela">
              <ListIcon :size="18" />
            </button>
          </div>
          <button v-if="chatStore.userRole === 'admin'" @click="sendDailyReports" class="btn-secondary" :disabled="sendingReports" title="Enviar Relatório Diário por WhatsApp para toda a equipe">
            <SendIcon :size="18" />
            <span>{{ sendingReports ? 'Enviando...' : 'Relatórios WhatsApp' }}</span>
          </button>
          <button @click="openCreateModal" class="btn-primary">
            <PlusIcon :size="20" /> Nova Pendência
          </button>
        </div>
      </header>

      <div class="content-wrapper">
        <!-- Barra de Filtros Expansível -->
        <Transition name="slide-fade">
          <div class="filters-container glass-effect" v-if="showFilters">
            <div class="filter-grid">
              <div class="filter-group">
                <label>Cliente</label>
                <select v-model="filterCustomer" class="select-glass">
                  <option value="all">Todos os Clientes</option>
                  <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Responsável</label>
                <select v-model="filterUser" class="select-glass">
                  <option value="all">Todos os Usuários</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">
                    {{ u.first_name ? `${u.first_name} ${u.last_name || ''}` : u.username }}
                  </option>
                </select>
              </div>

              <div class="filter-group">
                <label>Tipo de Operação</label>
                <select v-model="filterOperation" class="select-glass">
                  <option value="all">Todos os Tipos</option>
                  <option v-for="(label, key) in operationTypes" :key="key" :value="key">{{ label }}</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Status</label>
                <select v-model="filterStatus" class="select-glass">
                  <option value="all">Todos os Status</option>
                  <option value="open">Aberta</option>
                  <option value="closed">Finalizada</option>
                </select>
              </div>

              <div class="filter-group">
                <label>Abertura Início</label>
                <input v-model="filterStartDate" type="date" class="input-glass" />
              </div>

              <div class="filter-group">
                <label>Abertura Fim</label>
                <input v-model="filterEndDate" type="date" class="input-glass" />
              </div>

              <div class="filter-group">
                <label>Previsão Início</label>
                <input v-model="filterForecastStartDate" type="date" class="input-glass" />
              </div>

              <div class="filter-group">
                <label>Previsão Fim</label>
                <input v-model="filterForecastEndDate" type="date" class="input-glass" />
              </div>
            </div>

            <div class="filter-actions-row">
              <button v-if="hasActiveFilters" @click="clearFilters" class="btn-clear-filters">
                Limpar Filtros
              </button>
            </div>
          </div>
        </Transition>

        <!-- Loading State -->
        <div v-if="loadingList" class="loading-state glass-effect animate-in">
          <div class="spinner"></div>
          <p>Carregando pendências...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredPendencies.length === 0" class="empty-state glass-effect animate-in">
          <div class="empty-icon">
            <SearchIcon v-if="hasActiveFilters || search.trim()" :size="40" />
            <ClipboardListIcon v-else :size="40" />
          </div>
          <template v-if="hasActiveFilters || search.trim()">
            <h2>Nenhum resultado encontrado</h2>
            <p>Nenhuma pendência corresponde aos filtros ou termos de busca aplicados. Tente ajustar ou limpar os critérios de busca.</p>
            <div class="empty-actions">
              <button @click="clearFiltersAndSearch" class="btn-primary">
                Limpar Filtros e Busca
              </button>
            </div>
          </template>
          <template v-else>
            <h2>Tudo em dia!</h2>
            <p>Você não possui pendências registradas no momento. Que tal começar criando uma nova agora?</p>
            <div class="empty-actions">
              <button @click="openCreateModal" class="btn-primary">
                <PlusIcon :size="18" /> Nova Pendência
              </button>
            </div>
          </template>
        </div>

        <!-- Grade de Cards (Grid Mode) -->
        <div v-else-if="viewMode === 'grid'" class="pendencies-grid">
          <div v-for="item in displayedPendencies" :key="item.id" class="pendency-card glass-effect animate-in" :class="item.priority">
            <!-- Header do Card -->
            <div class="card-header-new">
              <div class="card-top-row">
                <div class="card-actions-new">
                  <button v-if="item.status !== 'closed'" @click="openFinishModal(item)" class="icon-btn finish" title="Finalizar"><CheckCircleIcon :size="16" /></button>
                  <button @click="editPendency(item)" class="icon-btn" title="Editar"><EditIcon :size="16" /></button>
                  <button @click="confirmDelete(item)" class="icon-btn delete" title="Excluir"><TrashIcon :size="16" /></button>
                </div>
              </div>
              <div v-if="item.customer_details" class="card-customer-header-new">
                <ContactIcon :size="18" />
                <span class="customer-name-large" :title="item.customer_details.name">{{ item.customer_details.name }}</span>
              </div>
              <div v-else class="card-customer-header-new empty">
                <ContactIcon :size="18" />
                <span class="customer-name-large">Sem Cliente</span>
              </div>
            </div>

            <!-- Corpo do Card -->
            <div class="card-body">
              <h3 class="card-title">{{ item.title }}</h3>
              <p class="card-desc">{{ item.description || 'Sem descrição.' }}</p>

              <div class="card-details">
                <div v-if="item.contact_details" class="detail-row">
                  <PhoneIcon :size="14" />
                  <span><strong>Contato:</strong> {{ item.contact_details.name || item.contact_details.remote_jid }}</span>
                </div>
                <div v-if="item.user_details" class="detail-row">
                  <UserIcon :size="14" />
                  <span><strong>Responsável:</strong> {{ item.user_details.first_name ? `${item.user_details.first_name} ${item.user_details.last_name || ''}` : item.user_details.username }}</span>
                </div>
                <div class="detail-row">
                  <CalendarIcon :size="14" />
                  <span><strong>Abertura:</strong> {{ formatDateTime(item.opening_date) }}</span>
                </div>
                <div class="detail-row" :class="{ 'overdue': isOverdue(item) }">
                  <ClockIcon :size="14" />
                  <span><strong>Previsão:</strong> {{ item.forecast_date ? formatDateTime(item.forecast_date) : 'Não informada' }}</span>
                </div>
                <div class="detail-row">
                  <TagIcon :size="14" />
                  <span><strong>Tipo:</strong> {{ operationTypes[item.operation_type] }}</span>
                </div>
                <div class="detail-row">
                  <AlertTriangleIcon :size="14" />
                  <span><strong>Prioridade:</strong> <span class="priority-text" :class="item.priority">{{ priorityLabels[item.priority] }}</span></span>
                </div>
                <div class="detail-row">
                  <ActivityIcon :size="14" />
                  <span><strong>Status:</strong> <span class="status-indicator-inline" :class="item.status">{{ statusLabels[item.status] }}</span></span>
                </div>
                <!-- Botões de Movimentações e Anexos abaixo do Status -->
                <div class="card-movements-btn-row">
                  <button @click="openMovementsModal(item)" class="btn-movements-inline">
                    <HistoryIcon :size="14" />
                    <span>Movimentações</span>
                    <span v-if="item.movements?.length > 0" class="movement-badge-inline">{{ item.movements.length }}</span>
                  </button>
                  <button @click="openAttachmentsModal(item)" class="btn-attachments-inline" title="Ver e Gerenciar Anexos">
                    <PaperclipIcon :size="14" />
                    <span>Anexos</span>
                    <span v-if="item.images?.length > 0" class="attachment-badge-inline">{{ item.images.length }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Footer do Card -->
            <div class="card-footer">
              <span class="created-at">Atualizado por <strong>{{ getLastUpdater(item) }}</strong> em {{ formatDateTime(item.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Tabela (List Mode) -->
        <div v-else class="pendencies-table-view glass-effect animate-in">
          <table class="pendencies-table">
            <thead>
              <tr>
                <th>Título / Operação</th>
                <th>Cliente</th>
                <th>Responsável</th>
                <th>Abertura</th>
                <th>Previsão</th>
                <th>Prioridade</th>
                <th>Status</th>
                <th>Anexos</th>
                <th class="actions-col">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in displayedPendencies" :key="item.id" :class="item.priority">
                <td>
                  <div class="title-cell">
                    <span class="tbl-title">{{ item.title }}</span>
                    <span class="tbl-operation">{{ operationTypes[item.operation_type] }}</span>
                  </div>
                </td>
                <td>
                  <div v-if="item.customer_details" class="client-cell">
                    <span>{{ item.customer_details.name }}</span>
                    <span v-if="item.contact_details" class="subtext">{{ item.contact_details.name || item.contact_details.remote_jid }}</span>
                  </div>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="item.user_details">
                    {{ item.user_details.first_name ? `${item.user_details.first_name} ${item.user_details.last_name || ''}` : item.user_details.username }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>{{ formatDateTime(item.opening_date) }}</td>
                <td :class="{ 'overdue-text': isOverdue(item) }">
                  {{ item.forecast_date ? formatDateTime(item.forecast_date) : '-' }}
                </td>
                <td>
                  <span class="priority-badge" :class="item.priority">{{ priorityLabels[item.priority] }}</span>
                </td>
                <td>
                  <span class="status-indicator" :class="item.status">{{ statusLabels[item.status] }}</span>
                </td>
                <td>
                  <button @click="openAttachmentsModal(item)" class="btn-table-attachments" title="Ver Anexos">
                    <PaperclipIcon :size="14" />
                    <span>Anexos</span>
                    <span v-if="item.images?.length > 0" class="attachment-count-badge">{{ item.images.length }}</span>
                  </button>
                </td>
                <td class="actions-col">
                  <div class="table-actions">
                    <button v-if="item.status !== 'closed'" @click="openFinishModal(item)" class="table-action-btn finish" title="Finalizar"><CheckCircleIcon :size="16" /></button>
                    <button @click="openMovementsModal(item)" class="table-action-btn" title="Movimentações">
                      <HistoryIcon :size="16" />
                      <span v-if="item.movements?.length > 0" class="movement-count-badge">{{ item.movements.length }}</span>
                    </button>
                    <button @click="editPendency(item)" class="table-action-btn" title="Editar"><EditIcon :size="16" /></button>
                    <button @click="confirmDelete(item)" class="table-action-btn delete" title="Excluir"><TrashIcon :size="16" /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Lazy Loading Footer -->
        <div v-if="visibleItemsLimit < filteredPendencies.length" class="load-more-container glass-effect">
          <p class="load-more-text">Exibindo {{ displayedPendencies.length }} de {{ filteredPendencies.length }} pendências</p>
          <button @click="visibleItemsLimit += 50" class="btn-primary btn-load-more">
            Carregar Mais
          </button>
        </div>
      </div>
    </main>

    <!-- Modal de Criação / Edição de Pendência Repaginado -->
    <Transition name="modal-fade">
      <div v-if="showModal" class="modal-overlay" @click="showModal = false" @paste="handleModalPaste">
        <div class="modal-content large-modal pendency-edit-modal" @click.stop>
          <div class="modal-header-new">
            <div class="modal-title-wrap">
              <div class="modal-icon-badge">
                <ClipboardListIcon v-if="!editingId" :size="20" />
                <EditIcon v-else :size="20" />
              </div>
              <div>
                <h2>{{ editingId ? 'Editar Pendência' : 'Nova Pendência' }}</h2>
                <p class="modal-subtitle">Preencha os detalhes da atividade para a sua equipe</p>
              </div>
            </div>
            <button @click="showModal = false" class="close-btn-round" title="Fechar"><XIcon :size="20" /></button>
          </div>

          <form @submit.prevent="savePendency" class="modal-form-scrollable">
            <!-- SEÇÃO 1: IDENTIFICAÇÃO E CLIENTE -->
            <div class="form-card-section glass-effect">
              <div class="section-card-title">
                <TagIcon :size="16" />
                <span>Identificação & Cliente</span>
              </div>

              <div class="form-group" style="margin-bottom: 14px;">
                <label>Título / Assunto <span class="required-star">*</span></label>
                <input 
                  v-model="form.title" 
                  required 
                  class="input-glass highlight-input" 
                  placeholder="Ex: Ajuste fiscal, erro de impressão, configuração TEF..." 
                />
              </div>

              <div class="grid-2">
                <!-- Autocomplete de Cliente -->
                <div class="form-group customer-autocomplete" style="position: relative;">
                  <label>Cliente Vinculado <span class="required-star">*</span></label>
                  <div class="input-with-icon" v-if="!form.customer">
                    <SearchIcon :size="16" class="input-inner-icon" />
                    <input 
                      v-model="customerSearch" 
                      @input="handleCustomerSearch"
                      @focus="showCustomerDropdown = true"
                      class="input-glass with-left-icon" 
                      placeholder="Buscar por razão social ou telefone..." 
                    />
                  </div>

                  <!-- Dropdown Autocomplete -->
                  <div v-if="showCustomerDropdown && customerSearchResults.length > 0 && !form.customer" class="autocomplete-dropdown glass-effect">
                    <div 
                      v-for="c in customerSearchResults" 
                      :key="c.id" 
                      @click="selectCustomer(c)"
                      class="dropdown-item"
                    >
                      <div class="customer-item-main">
                        <span class="customer-name-bold">{{ c.name }}</span>
                        <span v-if="c.document" class="customer-doc-badge">{{ c.document }}</span>
                      </div>
                      <span class="sub">{{ formatPhone(c.phone) }} {{ c.city?.name ? `• ${c.city.name}` : '' }}</span>
                    </div>
                  </div>

                  <!-- Cliente Selecionado -->
                  <div v-if="form.customer" class="selected-customer-card glass-effect animate-in">
                    <div class="customer-selected-info">
                      <ContactIcon :size="18" class="customer-badge-icon" />
                      <div>
                        <strong>{{ selectedCustomerName }}</strong>
                        <small v-if="selectedCustomerObj?.phone">{{ formatPhone(selectedCustomerObj.phone) }}</small>
                      </div>
                    </div>
                    <button type="button" @click="clearSelectedCustomer" class="btn-change-customer" title="Trocar Cliente">
                      Trocar
                    </button>
                  </div>
                </div>

                <!-- Contato Específico -->
                <div class="form-group">
                  <label>Contato Específico <span class="optional-tag">(Opcional)</span></label>
                  <select v-model="form.contact" class="select-glass" :disabled="!form.customer">
                    <option :value="null">{{ form.customer ? 'Nenhum contato específico (Geral)' : 'Selecione um cliente primeiro' }}</option>
                    <option v-for="ct in availableContacts" :key="ct.id" :value="ct.id">
                      {{ ct.name || ct.remote_jid }} {{ ct.cellphone ? `(${formatPhone(ct.cellphone)})` : '' }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- SEÇÃO 2: ATRIBUIÇÃO, CLASSIFICAÇÃO & STATUS -->
            <div class="form-card-section glass-effect">
              <div class="section-card-title">
                <UserIcon :size="16" />
                <span>Atribuição & Classificação</span>
              </div>

              <div class="grid-2">
                <!-- Tipo de Operação -->
                <div class="form-group">
                  <label>Tipo de Operação <span class="required-star">*</span></label>
                  <select v-model="form.operation_type" required class="select-glass">
                    <option v-for="(label, key) in operationTypes" :key="key" :value="key">{{ label }}</option>
                  </select>
                </div>

                <!-- Responsável -->
                <div class="form-group">
                  <label>Responsável / Atendente <span class="required-star">*</span></label>
                  <select v-model="form.user" required class="select-glass">
                    <option :value="null">Selecione o responsável</option>
                    <option v-for="u in users" :key="u.id" :value="u.id">
                      {{ u.first_name ? `${u.first_name} ${u.last_name || ''}` : u.username }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="grid-2" style="margin-top: 6px;">
                <!-- Prioridade com Seletor Visual Interativo -->
                <div class="form-group">
                  <label>Prioridade <span class="required-star">*</span></label>
                  <div class="priority-pill-selector">
                    <button 
                      type="button" 
                      class="priority-pill low" 
                      :class="{ active: form.priority === 'low' }" 
                      @click="form.priority = 'low'"
                    >
                      <span class="pill-dot"></span>
                      <span>Baixa</span>
                    </button>
                    <button 
                      type="button" 
                      class="priority-pill medium" 
                      :class="{ active: form.priority === 'medium' }" 
                      @click="form.priority = 'medium'"
                    >
                      <span class="pill-dot"></span>
                      <span>Média</span>
                    </button>
                    <button 
                      type="button" 
                      class="priority-pill high" 
                      :class="{ active: form.priority === 'high' }" 
                      @click="form.priority = 'high'"
                    >
                      <span class="pill-dot"></span>
                      <span>Alta</span>
                    </button>
                  </div>
                </div>

                <!-- Status com Seletor Visual Interativo -->
                <div class="form-group">
                  <label>Status <span class="required-star">*</span></label>
                  <div class="status-pill-selector">
                    <button 
                      type="button" 
                      class="status-pill open" 
                      :class="{ active: form.status === 'open' }" 
                      @click="form.status = 'open'"
                    >
                      <span class="pill-dot"></span>
                      <span>Aberta</span>
                    </button>
                    <button 
                      type="button" 
                      class="status-pill closed" 
                      :class="{ active: form.status === 'closed' }" 
                      @click="form.status = 'closed'"
                    >
                      <CheckCircleIcon :size="14" />
                      <span>Finalizada</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- SEÇÃO 3: PRAZOS E DATAS -->
            <div class="form-card-section glass-effect">
              <div class="section-card-title">
                <CalendarIcon :size="16" />
                <span>Prazos & Agendamento</span>
              </div>

              <div class="grid-2">
                <!-- Horário de Abertura -->
                <div class="form-group">
                  <label>Data / Hora de Abertura <span class="required-star">*</span></label>
                  <input v-model="form.opening_date" type="datetime-local" required class="input-glass" />
                </div>

                <!-- Previsão -->
                <div class="form-group">
                  <label>Previsão de Conclusão <span class="optional-tag">(Opcional)</span></label>
                  <input v-model="form.forecast_date" type="datetime-local" class="input-glass" />
                </div>
              </div>
            </div>

            <!-- SEÇÃO 4: DETALHES & DESCRIÇÃO (OPCIONAL) -->
            <div class="form-card-section glass-effect">
              <div class="section-card-title">
                <FileTextIcon :size="16" />
                <span>Descrição & Observações <span class="optional-tag-badge">Opcional</span></span>
              </div>

              <div class="form-group" style="margin-bottom: 0;">
                <textarea 
                  v-model="form.description" 
                  class="input-glass textarea-modern" 
                  placeholder="Insira detalhes técnicos, dados de acesso, observações ou orientações sobre a pendência (opcional)..." 
                  rows="3"
                ></textarea>
              </div>
            </div>

            <!-- SEÇÃO 5: ANEXOS E IMAGENS (OPCIONAL) -->
            <div class="form-card-section glass-effect">
              <div class="section-card-title">
                <PaperclipIcon :size="16" />
                <span>Anexos & Imagens <span class="optional-tag-badge">Opcional • Suporta Ctrl+V</span></span>
              </div>

              <div 
                class="drag-drop-area modern-dropzone glass-effect" 
                @dragover.prevent="dragOver = true" 
                @dragleave="dragOver = false" 
                @drop.prevent="handleFileDrop"
                :class="{ 'drag-over': dragOver }"
                @click="triggerFileInput"
              >
                <input type="file" ref="fileInput" multiple accept="image/*" class="hidden-input" @change="handleFileSelect" />
                <div class="dropzone-content">
                  <UploadCloudIcon :size="28" class="dropzone-icon" />
                  <div>
                    <p class="dropzone-text">Clique, arraste ou <strong>cole imagens (Ctrl+V)</strong></p>
                    <span class="sub">PNG, JPG, GIF até 5MB</span>
                  </div>
                </div>
              </div>

              <!-- Lista de Novas Imagens Anexadas -->
              <div v-if="newImages.length > 0" class="images-preview-list">
                <div v-for="(img, idx) in newImages" :key="idx" class="image-preview-item">
                  <img :src="img" alt="Anexo" />
                  <button type="button" @click.stop="removeNewImage(idx)" class="remove-img-btn" title="Remover">&times;</button>
                </div>
              </div>

              <!-- Lista de Imagens Existentes no Banco -->
              <div v-if="existingImages.length > 0" class="images-preview-list existing-images-section">
                <div class="title">Imagens salvas:</div>
                <div v-for="img in existingImages" :key="img.id" class="image-preview-item">
                  <img :src="img.image" alt="Salva" />
                  <button type="button" @click.stop="deleteExistingImage(img.id)" class="remove-img-btn" title="Excluir">&times;</button>
                </div>
              </div>
            </div>

            <!-- Botões de Ação Finais -->
            <div class="modal-actions-container sticky-footer">
              <span class="required-note"><span class="required-star">*</span> Campos obrigatórios</span>
              <div class="modal-actions">
                <button type="button" @click="showModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary btn-save-pendency" :disabled="loadingSave">
                  <CheckCircleIcon v-if="!loadingSave" :size="18" />
                  <span>{{ loadingSave ? 'Salvando...' : (editingId ? 'Salvar Alterações' : 'Criar Pendência') }}</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Modal de Confirmação de Exclusão -->
    <Transition name="modal-fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content small-modal" @click.stop>
          <h2>Excluir Pendência</h2>
          <p>Tem certeza que deseja excluir a pendência <strong>{{ selectedDeleteTitle }}</strong>? Esta ação não pode ser desfeita.</p>
          <div class="modal-actions">
            <button @click="showDeleteModal = false" class="btn-secondary">Cancelar</button>
            <button @click="deletePendency" class="btn-danger-sm" :disabled="loadingDelete">
              {{ loadingDelete ? 'Excluindo...' : 'Excluir' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Movimentações (Histórico e Registro) -->
    <Transition name="modal-fade">
      <div v-if="showMovementsModal" class="modal-overlay" @click="showMovementsModal = false">
        <div class="modal-content medium-modal" @click.stop>
          <div class="modal-header">
            <h2>Movimentações: {{ selectedPendencyForMovements?.title }}</h2>
            <button @click="showMovementsModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <div class="modal-body movements-modal-body">
            <!-- 1. Lista de movimentações existentes (Histórico em cima) -->
            <div class="movements-history-section">
              <h3>Histórico de Andamentos</h3>
              <div v-if="loadingMovements" class="loading-inline">
                <div class="spinner-sm"></div>
                <span>Carregando histórico...</span>
              </div>
              <div v-else-if="!selectedPendencyForMovements?.movements || selectedPendencyForMovements.movements.length === 0" class="no-movements-placeholder">
                Nenhuma movimentação registrada. Use o campo abaixo para adicionar o primeiro andamento.
              </div>
              <div v-else class="movements-timeline">
                <div v-for="m in sortedMovementsForModal" :key="m.id" class="timeline-item glass-effect">
                  <div class="timeline-header">
                    <span class="timeline-user">
                      <UserIcon :size="14" />
                      {{ m.user_details ? `${m.user_details.first_name || ''} ${m.user_details.last_name || ''}`.trim() || m.user_details.username : 'Sistema' }}
                    </span>
                    <span class="timeline-date">{{ formatDateTime(m.created_at) }}</span>
                  </div>
                  <div class="timeline-content">
                    <p>{{ m.description }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Botão de Impressão no meio -->
            <div class="movements-middle-actions">
              <button type="button" @click="printPendency(selectedPendencyForMovements)" class="btn-print-report-middle">
                <PrinterIcon :size="16" /> Imprimir Relatório
              </button>
            </div>

            <hr class="modal-divider" />

            <!-- 3. Form para nova movimentação (Embaixo) -->
            <form @submit.prevent="addMovement" class="new-movement-form">
              <div class="form-group">
                <label>Nova Movimentação</label>
                <textarea 
                  v-model="newMovementText" 
                  required 
                  class="input-glass" 
                  placeholder="Descreva a atualização ou andamento da pendência..."
                  rows="3"
                ></textarea>
              </div>
              <div class="form-actions-right">
                <button type="submit" class="btn-primary" :disabled="loadingAddMovement">
                  {{ loadingAddMovement ? 'Adicionando...' : 'Adicionar Histórico' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Anexos da Pendência -->
    <Transition name="modal-fade">
      <div v-if="showAttachmentsModal" class="modal-overlay" role="dialog" aria-modal="true" @click="showAttachmentsModal = false">
        <div class="modal-content medium-modal" @click.stop>
          <div class="modal-header">
            <h2>Anexos: {{ selectedPendencyForAttachments?.title }}</h2>
            <button @click="showAttachmentsModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>

          <div class="modal-body attachments-modal-body">
            <!-- Spinner de Carregamento -->
            <div v-if="loadingAttachments" class="loading-inline">
              <div class="spinner-sm"></div>
              <span>Carregando anexos...</span>
            </div>

            <!-- Estado Vazio -->
            <div v-else-if="!selectedPendencyForAttachments?.images || selectedPendencyForAttachments.images.length === 0" class="no-attachments-placeholder">
              <PaperclipIcon :size="36" />
              <p>Nenhum anexo registrado nesta pendência.</p>
            </div>

            <!-- Galeria de Anexos -->
            <div v-else class="attachments-gallery-grid">
              <div v-for="img in selectedPendencyForAttachments.images" :key="img.id" class="attachment-card glass-effect">
                <div class="attachment-preview" @click="openLightbox(img.image)">
                  <img :src="img.image" alt="Anexo da Pendência" />
                  <div class="attachment-hover-overlay">
                    <Maximize2Icon :size="20" />
                    <span>Ampliar</span>
                  </div>
                </div>
                <div class="attachment-card-footer">
                  <span class="attachment-date">{{ formatDateTime(img.created_at) }}</span>
                  <div class="attachment-actions">
                    <a :href="img.image" :download="'anexo_pendencia_' + img.id" class="attachment-action-btn" title="Baixar Anexo" target="_blank">
                      <DownloadIcon :size="14" />
                    </a>
                    <button type="button" @click="deleteAttachmentInModal(img.id)" class="attachment-action-btn delete" title="Excluir Anexo">
                      <TrashIcon :size="14" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <hr class="modal-divider" />

            <!-- Upload de Novos Anexos no próprio modal -->
            <div class="modal-upload-section">
              <h3>Adicionar Novos Anexos</h3>
              <div 
                class="drag-drop-area glass-effect compact-drag" 
                @dragover.prevent="modalDragOver = true" 
                @dragleave="modalDragOver = false" 
                @drop.prevent="handleModalFileDrop"
                :class="{ 'drag-over': modalDragOver }"
                @click="triggerModalFileInput"
              >
                <input type="file" ref="modalFileInput" multiple accept="image/*" class="hidden-input" @change="handleModalFileSelect" />
                <UploadCloudIcon :size="24" />
                <p>Arraste ou clique para selecionar imagens</p>
                <span class="sub">PNG, JPG, GIF até 5MB</span>
              </div>

              <!-- Preview de Imagens Selecionadas no Modal -->
              <div v-if="modalNewImages.length > 0" class="modal-new-images-row">
                <div v-for="(img, idx) in modalNewImages" :key="idx" class="modal-img-preview">
                  <img :src="img" alt="Novo anexo" />
                  <button type="button" @click="modalNewImages.splice(idx, 1)" class="remove-btn">&times;</button>
                </div>
                <button type="button" @click="uploadModalAttachments" class="btn-primary btn-upload-now" :disabled="uploadingModalImages">
                  {{ uploadingModalImages ? 'Enviando...' : `Salvar Anexos (${modalNewImages.length})` }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal Lightbox (Visualizar Imagem cheia) -->
    <Transition name="fade">
      <div v-if="showLightbox" class="lightbox-overlay" @click="showLightbox = false">
        <div class="lightbox-content" @click.stop>
          <img :src="lightboxSrc" alt="Anexo Ampliado" />
          <button @click="showLightbox = false" class="close-lightbox-btn">&times;</button>
        </div>
      </div>
    </Transition>

    <!-- Modal de Confirmação de Finalização com Explicação -->
    <Transition name="modal-fade">
      <div v-if="showFinishModal" class="modal-overlay" @click="showFinishModal = false">
        <div class="modal-content small-modal" @click.stop>
          <div class="modal-header">
            <h2>Finalizar Pendência</h2>
            <button @click="showFinishModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          
          <div class="modal-body">
            <p>Para finalizar a pendência <strong>{{ selectedPendencyForFinish?.title }}</strong>, por favor forneça uma explicação ou motivo de conclusão:</p>
            
            <form @submit.prevent="submitFinish" class="finish-form">
              <div class="form-group" style="margin-top: 12px;">
                <textarea 
                  v-model="finishExplanation" 
                  required 
                  class="input-glass" 
                  placeholder="Digite a explicação da conclusão..."
                  rows="4"
                ></textarea>
              </div>
              
              <div class="modal-actions" style="margin-top: 18px; display: flex; justify-content: flex-end; gap: 10px;">
                <button type="button" @click="showFinishModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="loadingFinish">
                  {{ loadingFinish ? 'Finalizando...' : 'Confirmar Finalização' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import {
  ClipboardList as ClipboardListIcon,
  Search as SearchIcon,
  Filter as FilterIcon,
  Plus as PlusIcon,
  LayoutGrid as LayoutGridIcon,
  List as ListIcon,
  Edit as EditIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  Contact as ContactIcon,
  User as UserIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
  Phone as PhoneIcon,
  Image as ImageIcon,
  UploadCloud as UploadCloudIcon,
  History as HistoryIcon,
  Printer as PrinterIcon,
  CheckCircle as CheckCircleIcon,
  Send as SendIcon,
  Tag as TagIcon,
  AlertTriangle as AlertTriangleIcon,
  Activity as ActivityIcon,
  Paperclip as PaperclipIcon,
  Download as DownloadIcon,
  Maximize2 as Maximize2Icon,
  FileText as FileTextIcon
} from 'lucide-vue-next'
import { useChatStore } from '../store/chat'

// Constantes e Labels
const operationTypes = {
  suporte: 'Suporte',
  desenvolvimento: 'Desenvolvimento',
  consultoria: 'Consultoria / Assessoria',
  atualizacao: 'Atualização',
  reuniao: 'Reunião',
  tef: 'TEF',
  reforma_tributaria: 'Reforma Tributária'
}

const priorityLabels = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta'
}

const statusLabels = {
  open: 'Aberta',
  closed: 'Finalizada'
}

// Estados Reativos
const route = useRoute()
const chatStore = useChatStore()
const sendingReports = ref(false)
const pendencies = ref([])
const customers = ref([])
const users = ref([])
const contacts = ref([]) // Todos os contatos da empresa
const search = ref(route.query.search || '')
const viewMode = ref('grid')

// Filtros
const showFilters = ref(false)
const filterCustomer = ref('all')
const filterUser = ref(chatStore.user?.id || 'all')
const filterOperation = ref('all')
const filterStatus = ref('open')
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterForecastStartDate = ref('')
const filterForecastEndDate = ref('')

watch(() => chatStore.user, (newVal) => {
  if (newVal && (filterUser.value === 'all' || !filterUser.value)) {
    filterUser.value = newVal.id
  }
}, { immediate: true })

// Controle de Loading
const loadingList = ref(false)
const loadingSave = ref(false)
const loadingDelete = ref(false)

// Modais
const showModal = ref(false)
const showDeleteModal = ref(false)
const showLightbox = ref(false)
const lightboxSrc = ref('')
const showMovementsModal = ref(false)
const selectedPendencyForMovements = ref(null)
const newMovementText = ref('')
const loadingAddMovement = ref(false)
const loadingMovements = ref(false)

const showAttachmentsModal = ref(false)
const selectedPendencyForAttachments = ref(null)
const loadingAttachments = ref(false)
const modalFileInput = ref(null)
const modalDragOver = ref(false)
const modalNewImages = ref([])
const uploadingModalImages = ref(false)

const showFinishModal = ref(false)
const selectedPendencyForFinish = ref(null)
const finishExplanation = ref('')
const loadingFinish = ref(false)

// Form e Cadastro
const editingId = ref(null)
const selectedDeleteId = ref(null)
const selectedDeleteTitle = ref('')
const form = ref({
  title: '',
  operation_type: 'suporte',
  customer: null,
  contact: null,
  user: null,
  priority: 'medium',
  status: 'open',
  opening_date: '',
  forecast_date: '',
  description: ''
})

// Autocomplete de Clientes no Modal
const customerSearch = ref('')
const showCustomerDropdown = ref(false)
const customerSearchResults = ref([])
const selectedCustomerName = ref('')

const selectedCustomerObj = computed(() => {
  if (!form.value.customer) return null
  const targetId = Number(form.value.customer)
  return customers.value.find(c => c.id === targetId) || null
})

// Imagens/Anexos
const newImages = ref([]) // Array de strings base64
const existingImages = ref([]) // Array de objetos {id, image, created_at}
const dragOver = ref(false)
const fileInput = ref(null)

// Filtros Ativos
const activeFiltersCount = computed(() => {
  let count = 0
  if (filterCustomer.value !== 'all') count++
  if (filterUser.value !== 'all') count++
  if (filterOperation.value !== 'all') count++
  if (filterStatus.value !== 'all') count++
  if (filterStartDate.value) count++
  if (filterEndDate.value) count++
  if (filterForecastStartDate.value) count++
  if (filterForecastEndDate.value) count++
  return count
})

const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

// Contatos filtrados com base no cliente selecionado
const availableContacts = computed(() => {
  if (!form.value.customer) return []
  const targetId = Number(form.value.customer)
  return contacts.value.filter(ct => {
    if (!ct.customer) return false
    const ctCustId = typeof ct.customer === 'object' ? ct.customer.id : ct.customer
    return Number(ctCustId) === targetId
  })
})

// Aberturas de pendência ordenadas/filtradas no frontend reativamente
const filteredPendencies = computed(() => {
  return pendencies.value.filter(item => {
    // Busca por texto (titulo/descrição)
    if (search.value.trim()) {
      const query = search.value.toLowerCase()
      const titleMatch = item.title.toLowerCase().includes(query)
      const descMatch = (item.description || '').toLowerCase().includes(query)
      if (!titleMatch && !descMatch) return false
    }

    // Filtro de Cliente
    if (filterCustomer.value !== 'all') {
      const itemCustId = typeof item.customer === 'object' ? item.customer?.id : item.customer
      if (itemCustId != filterCustomer.value) return false
    }

    // Filtro de Responsável
    if (filterUser.value !== 'all') {
      const itemUserId = typeof item.user === 'object' ? item.user?.id : item.user
      if (itemUserId != filterUser.value) return false
    }

    // Filtro de Tipo Operação
    if (filterOperation.value !== 'all' && item.operation_type !== filterOperation.value) {
      return false
    }

    // Filtro de Status
    if (filterStatus.value !== 'all' && item.status !== filterStatus.value) {
      return false
    }

    // Filtro de Período (Abertura)
    if (filterStartDate.value) {
      if (!item.opening_date) return false
      const openDate = new Date(item.opening_date).toISOString().split('T')[0]
      if (openDate < filterStartDate.value) return false
    }
    if (filterEndDate.value) {
      if (!item.opening_date) return false
      const openDate = new Date(item.opening_date).toISOString().split('T')[0]
      if (openDate > filterEndDate.value) return false
    }

    // Filtro de Período (Previsão)
    if (filterForecastStartDate.value) {
      if (!item.forecast_date) return false
      const forecastDate = new Date(item.forecast_date).toISOString().split('T')[0]
      if (forecastDate < filterForecastStartDate.value) return false
    }
    if (filterForecastEndDate.value) {
      if (!item.forecast_date) return false
      const forecastDate = new Date(item.forecast_date).toISOString().split('T')[0]
      if (forecastDate > filterForecastEndDate.value) return false
    }

    return true
  })
})

// Lazy Loading / Infinite Scroll
const mainContentEl = ref(null)
const visibleItemsLimit = ref(20)

const displayedPendencies = computed(() => {
  return filteredPendencies.value.slice(0, visibleItemsLimit.value)
})

watch(
  [search, filterCustomer, filterUser, filterOperation, filterStatus, filterStartDate, filterEndDate, filterForecastStartDate, filterForecastEndDate],
  () => {
    visibleItemsLimit.value = 20
  }
)

const handleScroll = () => {
  if (!mainContentEl.value) return
  const el = mainContentEl.value
  const scrollTop = el.scrollTop
  const clientHeight = el.clientHeight
  const scrollHeight = el.scrollHeight
  
  if (scrollHeight - (scrollTop + clientHeight) < 150) {
    if (visibleItemsLimit.value < filteredPendencies.value.length) {
      visibleItemsLimit.value += 20
    }
  }
}

// Funções utilitárias
const formatPhone = (phone) => {
  if (!phone) return ''
  let nums = String(phone).replace(/\D/g, '')
  if (nums.startsWith('55') && nums.length >= 12) {
    nums = nums.substring(2)
  }
  if (nums.length === 0) return ''
  
  if (nums.length <= 10) {
    let formatted = '(' + nums.substring(0, 2)
    if (nums.length > 2) {
      formatted += ') ' + nums.substring(2, 6)
    }
    if (nums.length > 6) {
      formatted += '-' + nums.substring(6, 10)
    }
    return formatted
  } else {
    let formatted = '(' + nums.substring(0, 2)
    if (nums.length > 2) {
      formatted += ') ' + nums.substring(2, 7)
    }
    if (nums.length > 7) {
      formatted += '-' + nums.substring(7, 11)
    }
    return formatted
  }
}

const formatDateTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isOverdue = (item) => {
  if (item.status === 'closed' || !item.forecast_date) return false
  return new Date(item.forecast_date) < new Date()
}

// Limpar Filtros
const clearFilters = () => {
  filterCustomer.value = 'all'
  filterUser.value = 'all'
  filterOperation.value = 'all'
  filterStatus.value = 'all'
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterForecastStartDate.value = ''
  filterForecastEndDate.value = ''
}

const clearFiltersAndSearch = () => {
  clearFilters()
  search.value = ''
}

// Requisições e Carregamento de Dados
const fetchData = async () => {
  loadingList.value = true
  try {
    const [resPendencies, resCustomers, resUsers] = await Promise.all([
      axios.get('/api/v1/pendencies/'),
      axios.get('/api/v1/customers/'),
      axios.get('/api/v1/users/')
    ])
    pendencies.value = resPendencies.data
    customers.value = resCustomers.data
    users.value = resUsers.data.filter(u => u.role !== 'system') // Ignorar usuários do sistema
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loadingList.value = false
  }
}

// Autocomplete de Clientes
const handleCustomerSearch = () => {
  if (!customerSearch.value.trim()) {
    customerSearchResults.value = []
    return
  }
  const query = customerSearch.value.toLowerCase()
  customerSearchResults.value = customers.value.filter(c => 
    c.name.toLowerCase().includes(query) || 
    (c.fantasy_name || '').toLowerCase().includes(query) || 
    (c.phone || '').includes(query)
  ).slice(0, 5) // Limitar a 5 resultados
}

const selectCustomer = async (customer) => {
  form.value.customer = customer.id
  selectedCustomerName.value = customer.name
  customerSearch.value = ''
  customerSearchResults.value = []
  showCustomerDropdown.value = false
  form.value.contact = null // Resetar contato dependente

  try {
    const res = await axios.get(`/api/v1/contacts/?customer=${customer.id}`)
    contacts.value = res.data || []
  } catch (e) {
    contacts.value = []
  }
}

const clearSelectedCustomer = () => {
  form.value.customer = null
  selectedCustomerName.value = ''
  form.value.contact = null
}

const handleClickOutsideAutocomplete = (e) => {
  if (!e.target.closest('.customer-autocomplete')) {
    showCustomerDropdown.value = false
  }
}

// Upload e manipulação de arquivos
const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (e) => {
  const files = e.target.files
  processFiles(files)
}

const handleFileDrop = (e) => {
  dragOver.value = false
  const files = e.dataTransfer.files
  processFiles(files)
}

const processFiles = (files) => {
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file.type.startsWith('image/')) {
      alert('Apenas imagens são permitidas.')
      continue
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('A imagem excede o tamanho limite de 5MB.')
      continue
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      newImages.value.push(e.target.result)
    }
    reader.readAsDataURL(file)
  }
}

const removeNewImage = (idx) => {
  newImages.value.splice(idx, 1)
}

const handleModalPaste = (e) => {
  const items = e.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    if (items[i].type && items[i].type.startsWith('image/')) {
      const file = items[i].getAsFile()
      if (file) {
        if (file.size > 5 * 1024 * 1024) {
          alert('A imagem colada excede o tamanho limite de 5MB.')
          return
        }
        const reader = new FileReader()
        reader.onload = (evt) => {
          newImages.value.push(evt.target.result)
        }
        reader.readAsDataURL(file)
      }
    }
  }
}

const deleteExistingImage = async (imgId) => {
  if (!confirm('Deseja excluir permanentemente este anexo?')) return
  try {
    await axios.post(`/api/v1/pendencies/${editingId.value}/delete-image/`, { image_id: imgId })
    existingImages.value = existingImages.value.filter(img => img.id !== imgId)
    // Atualizar no objeto local na lista
    const localObj = pendencies.value.find(p => p.id === editingId.value)
    if (localObj) {
      localObj.images = localObj.images.filter(img => img.id !== imgId)
    }
  } catch (error) {
    console.error('Erro ao deletar imagem:', error)
    alert('Erro ao deletar imagem.')
  }
}

// Visualizador de Lightbox
const openLightbox = (src) => {
  lightboxSrc.value = src
  showLightbox.value = true
}

// Criação e Edição
const openCreateModal = () => {
  editingId.value = null
  newImages.value = []
  existingImages.value = []
  clearSelectedCustomer()
  
  // Setar valores padrão do formulário
  const now = new Date()
  const localIsoString = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  
  form.value = {
    title: '',
    operation_type: 'suporte',
    customer: null,
    contact: null,
    user: null,
    priority: 'medium',
    status: 'open',
    opening_date: localIsoString,
    forecast_date: '',
    description: ''
  }
  showModal.value = true
}

const editPendency = (item) => {
  editingId.value = item.id
  newImages.value = []
  existingImages.value = item.images || []
  
  // Setar formulário com dados
  const openDateLocal = item.opening_date ? new Date(item.opening_date) : new Date()
  const openIso = new Date(openDateLocal.getTime() - openDateLocal.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  
  let forecastIso = ''
  if (item.forecast_date) {
    const fDate = new Date(item.forecast_date)
    forecastIso = new Date(fDate.getTime() - fDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  }

  form.value = {
    title: item.title,
    operation_type: item.operation_type,
    customer: item.customer,
    contact: item.contact,
    user: item.user,
    priority: item.priority,
    status: item.status,
    opening_date: openIso,
    forecast_date: forecastIso,
    description: item.description || ''
  }

  if (item.customer_details) {
    selectedCustomerName.value = item.customer_details.name
  } else {
    selectedCustomerName.value = ''
  }

  if (item.customer) {
    const custId = typeof item.customer === 'object' ? item.customer.id : item.customer
    axios.get(`/api/v1/contacts/?customer=${custId}`).then(res => {
      contacts.value = res.data || []
    }).catch(() => {})
  }

  showModal.value = true
}

const savePendency = async () => {
  // Validação explícita de campos obrigatórios
  if (!form.value.title || !form.value.title.trim()) {
    alert('Por favor, preencha o campo Título / Assunto.')
    return
  }
  if (!form.value.operation_type) {
    alert('Por favor, selecione o Tipo de Operação.')
    return
  }
  if (!form.value.customer) {
    alert('Por favor, selecione e vincule um Cliente.')
    return
  }
  if (!form.value.user || form.value.user === 'null') {
    alert('Por favor, selecione um Responsável.')
    return
  }
  if (!form.value.priority) {
    alert('Por favor, selecione a Prioridade.')
    return
  }
  if (!form.value.status) {
    alert('Por favor, selecione o Status.')
    return
  }
  if (!form.value.opening_date) {
    alert('Por favor, defina o Horário de Abertura.')
    return
  }

  loadingSave.value = true
  try {
    const payload = {
      ...form.value,
      uploaded_images: newImages.value
    }

    // Se estiver vazio, define como null para a API
    if (!payload.forecast_date) payload.forecast_date = null

    if (editingId.value) {
      const res = await axios.put(`/api/v1/pendencies/${editingId.value}/`, payload)
      // Substituir na lista
      const idx = pendencies.value.findIndex(p => p.id === editingId.value)
      if (idx !== -1) {
        pendencies.value[idx] = res.data
      }
    } else {
      const res = await axios.post('/api/v1/pendencies/', payload)
      pendencies.value.push(res.data)
    }

    showModal.value = false
    await fetchData() // Recarregar para garantir a ordenação correta vinda do banco
  } catch (error) {
    console.error('Erro ao salvar pendência:', error)
    alert('Erro ao salvar pendência. Verifique se todos os campos obrigatórios estão corretos.')
  } finally {
    loadingSave.value = false
  }
}

// Exclusão
const confirmDelete = (item) => {
  selectedDeleteId.value = item.id
  selectedDeleteTitle.value = item.title
  showDeleteModal.value = true
}

const deletePendency = async () => {
  loadingDelete.value = true
  try {
    await axios.delete(`/api/v1/pendencies/${selectedDeleteId.value}/`)
    pendencies.value = pendencies.value.filter(p => p.id !== selectedDeleteId.value)
    showDeleteModal.value = false
  } catch (error) {
    console.error('Erro ao excluir:', error)
    alert('Erro ao excluir pendência.')
  } finally {
    loadingDelete.value = false
  }
}

const openMovementsModal = async (item) => {
  selectedPendencyForMovements.value = item
  newMovementText.value = ''
  showMovementsModal.value = true
  
  loadingMovements.value = true
  try {
    const res = await axios.get(`/api/v1/pendencies/${item.id}/`)
    const idx = pendencies.value.findIndex(p => p.id === item.id)
    if (idx !== -1) {
      pendencies.value[idx] = res.data
    }
    selectedPendencyForMovements.value = res.data
  } catch (error) {
    console.error('Erro ao buscar movimentações:', error)
  } finally {
    loadingMovements.value = false
  }
}

const addMovement = async () => {
  if (!newMovementText.value.trim()) return
  loadingAddMovement.value = true
  try {
    const payload = {
      pendency: selectedPendencyForMovements.value.id,
      description: newMovementText.value.trim()
    }
    await axios.post('/api/v1/pendency-movements/', payload)
    
    const resUpdated = await axios.get(`/api/v1/pendencies/${selectedPendencyForMovements.value.id}/`)
    const idx = pendencies.value.findIndex(p => p.id === selectedPendencyForMovements.value.id)
    if (idx !== -1) {
      pendencies.value[idx] = resUpdated.data
    }
    selectedPendencyForMovements.value = resUpdated.data
    newMovementText.value = ''
  } catch (error) {
    console.error('Erro ao adicionar movimentação:', error)
    alert('Erro ao adicionar movimentação.')
  } finally {
    loadingAddMovement.value = false
  }
}

const printPendency = (item) => {
  if (!item) return
  window.open(`/pendencies/${item.id}/print`, '_blank')
}

const openAttachmentsModal = async (item) => {
  selectedPendencyForAttachments.value = item
  showAttachmentsModal.value = true
  loadingAttachments.value = true
  modalNewImages.value = []
  try {
    const res = await axios.get(`/api/v1/pendencies/${item.id}/`)
    selectedPendencyForAttachments.value = res.data
    const idx = pendencies.value.findIndex(p => p.id === item.id)
    if (idx !== -1) {
      pendencies.value[idx] = res.data
    }
  } catch (error) {
    console.error('Erro ao buscar anexos:', error)
  } finally {
    loadingAttachments.value = false
  }
}

const triggerModalFileInput = () => {
  modalFileInput.value?.click()
}

const handleModalFileSelect = (e) => {
  const files = e.target.files
  processModalFiles(files)
  e.target.value = ''
}

const handleModalFileDrop = (e) => {
  modalDragOver.value = false
  const files = e.dataTransfer.files
  processModalFiles(files)
}

const processModalFiles = (files) => {
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (!file.type.startsWith('image/')) {
      alert('Apenas imagens são permitidas.')
      continue
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('A imagem excede o tamanho limite de 5MB.')
      continue
    }

    const reader = new FileReader()
    reader.onload = (ev) => {
      modalNewImages.value.push(ev.target.result)
    }
    reader.readAsDataURL(file)
  }
}

const uploadModalAttachments = async () => {
  if (!selectedPendencyForAttachments.value || modalNewImages.value.length === 0) return
  uploadingModalImages.value = true
  try {
    const pendencyId = selectedPendencyForAttachments.value.id
    const res = await axios.patch(`/api/v1/pendencies/${pendencyId}/`, {
      uploaded_images: modalNewImages.value
    })
    selectedPendencyForAttachments.value = res.data
    modalNewImages.value = []
    
    const idx = pendencies.value.findIndex(p => p.id === pendencyId)
    if (idx !== -1) {
      pendencies.value[idx] = res.data
    }
  } catch (error) {
    console.error("Erro ao enviar anexos:", error)
    alert("Erro ao enviar anexos.")
  } finally {
    uploadingModalImages.value = false
  }
}

const deleteAttachmentInModal = async (imgId) => {
  if (!selectedPendencyForAttachments.value) return
  if (!confirm('Deseja excluir permanentemente este anexo?')) return
  const pendencyId = selectedPendencyForAttachments.value.id
  try {
    await axios.post(`/api/v1/pendencies/${pendencyId}/delete-image/`, { image_id: imgId })
    selectedPendencyForAttachments.value.images = selectedPendencyForAttachments.value.images.filter(img => img.id !== imgId)
    
    const idx = pendencies.value.findIndex(p => p.id === pendencyId)
    if (idx !== -1) {
      pendencies.value[idx].images = pendencies.value[idx].images.filter(img => img.id !== imgId)
    }
  } catch (error) {
    console.error("Erro ao deletar anexo:", error)
    alert("Erro ao deletar anexo.")
  }
}

const sortedMovementsForModal = computed(() => {
  if (!selectedPendencyForMovements.value?.movements) return []
  return [...selectedPendencyForMovements.value.movements].sort((a, b) => {
    return new Date(b.created_at) - new Date(a.created_at)
  })
} )

const openFinishModal = (item) => {
  selectedPendencyForFinish.value = item
  finishExplanation.value = ''
  showFinishModal.value = true
}

const submitFinish = async () => {
  if (!finishExplanation.value.trim() || !selectedPendencyForFinish.value) return
  loadingFinish.value = true
  try {
    const pendencyId = selectedPendencyForFinish.value.id
    
    // 1. Atualiza o status para closed
    await axios.patch(`/api/v1/pendencies/${pendencyId}/`, { status: 'closed' })
    
    // 2. Cria a movimentação explicando a finalização
    const movementPayload = {
      pendency: pendencyId,
      description: `Finalização de Pendência. Explicação: ${finishExplanation.value.trim()}`
    }
    await axios.post('/api/v1/pendency-movements/', movementPayload)
    
    // 3. Recarrega os dados completos da pendência
    const resUpdated = await axios.get(`/api/v1/pendencies/${pendencyId}/`)
    
    const idx = pendencies.value.findIndex(p => p.id === pendencyId)
    if (idx !== -1) {
      pendencies.value[idx] = resUpdated.data
    }
    
    if (showMovementsModal.value && selectedPendencyForMovements.value?.id === pendencyId) {
      selectedPendencyForMovements.value = resUpdated.data
    }
    
    showFinishModal.value = false
    selectedPendencyForFinish.value = null
    finishExplanation.value = ''
  } catch (error) {
    console.error('Erro ao finalizar pendência:', error)
    alert('Erro ao finalizar pendência.')
  } finally {
    loadingFinish.value = false
  }
}

const getLastUpdater = (item) => {
  if (item.movements && item.movements.length > 0) {
    const lastMov = item.movements[item.movements.length - 1]
    if (lastMov.user_details) {
      return lastMov.user_details.first_name || lastMov.user_details.username
    }
  }
  if (item.user_details) {
    return item.user_details.first_name || item.user_details.username
  }
  return 'Sistema'
}

const sendDailyReports = async () => {
  if (!confirm('Deseja realmente enviar o relatório diário de pendências para o WhatsApp de toda a equipe?')) return
  sendingReports.value = true
  try {
    const res = await axios.post('/api/v1/pendencies/send-daily-reports/')
    alert(res.data.detail || 'Relatórios diários enviados com sucesso!')
  } catch (error) {
    console.error(error)
    alert('Erro ao enviar relatórios: ' + (error.response?.data?.detail || 'Erro interno.'))
  } finally {
    sendingReports.value = false
  }
}

// Ciclo de Vida
onMounted(() => {
  fetchData()
  window.addEventListener('click', handleClickOutsideAutocomplete)
  if (mainContentEl.value) {
    mainContentEl.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutsideAutocomplete)
  if (mainContentEl.value) {
    mainContentEl.value.removeEventListener('scroll', handleScroll)
  }
})
</script>

<style scoped>
.pendencies-page-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background: var(--bg-dark);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  padding: 30px;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-info h1 {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 4px;
  background: linear-gradient(135deg, var(--text-primary) 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-info p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-bar {
  display: flex;
  align-items: center;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 8px;
  width: 300px;
  transition: all 0.3s ease;
}

.search-bar:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.search-bar input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  margin-left: 10px;
  outline: none;
  font-size: 0.9rem;
  width: 100%;
}

.search-bar svg {
  color: var(--text-secondary);
}

/* Filtros */
.btn-filter-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
}

.btn-filter-toggle:hover {
  background: var(--border);
  color: var(--text-primary);
}

.btn-filter-active {
  border-color: var(--accent);
  color: var(--accent) !important;
  background: rgba(16, 185, 129, 0.05);
}

.filter-count-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: var(--accent);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}

.filters-container {
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.select-glass, .input-glass {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 14px;
  border-radius: 8px;
  outline: none;
  font-size: 0.9rem;
  width: 100%;
}

.select-glass option {
  background: #18181b;
  color: var(--text-primary);
}

.filter-actions-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.btn-clear-filters {
  background: transparent;
  border: none;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-clear-filters:hover {
  text-decoration: underline;
}

/* View Mode Toggle */
.view-switcher-toggle {
  display: flex;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 2px;
  border-radius: 8px;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background: var(--border);
  color: var(--accent);
}

/* Grid layout cards */
.pendencies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.pendency-card {
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 280px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.pendency-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

.pendency-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.pendency-card.high::before { background: #ef4444; }
.pendency-card.medium::before { background: #f59e0b; }
.pendency-card.low::before { background: #10b981; }

.card-header-new {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.card-top-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.card-actions-new {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.pendency-card:hover .card-actions-new {
  opacity: 1;
}

.card-customer-header-new {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-customer-header-new svg {
  color: var(--accent);
  flex-shrink: 0;
}

.card-customer-header-new.empty svg {
  color: var(--text-secondary);
  opacity: 0.5;
}

.customer-name-large {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--accent);
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.3px;
}

.card-customer-header-new.empty .customer-name-large {
  color: var(--text-secondary);
  opacity: 0.7;
}

.card-movements-btn-row {
  margin-top: 12px;
  margin-bottom: 4px;
}

.btn-movements-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  justify-content: center;
}

.btn-movements-inline:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.movement-badge-inline {
  background: var(--accent);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: 2px;
}

.priority-text.high {
  color: #ef4444;
  font-weight: 600;
}
.priority-text.medium {
  color: #f59e0b;
  font-weight: 600;
}
.priority-text.low {
  color: #10b981;
  font-weight: 600;
}

.status-indicator-inline {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}
.status-indicator-inline.open {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}
.status-indicator-inline.closed {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.operation-badge {
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(255,255,255,0.06);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.badge-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.priority-badge {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
}

.priority-badge.high { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.priority-badge.medium { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.priority-badge.low { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }

.card-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.pendency-card:hover .card-actions {
  opacity: 1;
}

.icon-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}

.icon-btn.delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.icon-btn.finish:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.movement-count-badge {
  font-size: 0.7rem;
  background: var(--accent);
  color: white;
  padding: 1px 5px;
  border-radius: 6px;
  margin-left: 4px;
  font-weight: 700;
  display: inline-block;
  vertical-align: middle;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.card-desc {
  color: var(--text-secondary);
  font-size: 0.88rem;
  line-height: 1.4;
  margin-bottom: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 15px;
  background: rgba(0, 0, 0, 0.15);
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.02);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.detail-row svg {
  color: var(--accent);
}

.detail-row.overdue svg {
  color: #ef4444;
}

.detail-row.overdue span {
  color: #f87171;
  font-weight: 600;
}

.attached-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 5px;
}

.image-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.image-thumb:hover {
  transform: scale(1.08);
}

.image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.status-indicator {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

.status-indicator.open { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.status-indicator.pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.status-indicator.closed { background: rgba(16, 185, 129, 0.15); color: #34d399; }

.created-at {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* List view style */
.pendencies-table-view {
  border-radius: 12px;
  overflow-x: auto;
}

.pendencies-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.pendencies-table th {
  padding: 16px 20px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
}

.pendencies-table td {
  padding: 16px 20px;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.pendencies-table tr:hover {
  background: rgba(255,255,255,0.01);
}

.title-cell {
  display: flex;
  flex-direction: column;
}

.tbl-title {
  font-weight: 700;
  color: var(--text-primary);
}

.tbl-operation {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.client-cell {
  display: flex;
  flex-direction: column;
}

.client-cell .subtext {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.overdue-text {
  color: #ef4444;
  font-weight: 600;
}

.table-images {
  display: inline-block;
}

.images-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: 20px;
  cursor: zoom-in;
  font-weight: 600;
}

.images-count-badge:hover {
  background: var(--border);
}

.table-actions {
  display: flex;
  gap: 4px;
}

.table-action-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.table-action-btn:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}

.table-action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.table-action-btn.finish:hover {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

/* Modal extra styles */
.large-modal {
  max-width: 680px;
}

.pendency-edit-modal {
  border-radius: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.modal-header-new {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.02);
}

.modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.modal-icon-badge {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-title-wrap h2 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.modal-subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 2px 0 0 0;
}

.modal-form-scrollable {
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-card-section {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
}

.section-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 14px;
}

.highlight-input {
  font-size: 0.98rem !important;
  font-weight: 600;
  border-color: rgba(16, 185, 129, 0.25) !important;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-inner-icon {
  position: absolute;
  left: 12px;
  color: var(--text-secondary);
  pointer-events: none;
}

.with-left-icon {
  padding-left: 36px !important;
}

.selected-customer-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.customer-selected-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.customer-badge-icon {
  color: var(--accent);
}

.customer-selected-info strong {
  display: block;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.customer-selected-info small {
  display: block;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.btn-change-customer {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-change-customer:hover {
  background: #ef4444;
  border-color: #ef4444;
  color: white;
}

.customer-item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.customer-name-bold {
  font-weight: 700;
  color: var(--text-primary);
}

.customer-doc-badge {
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.priority-pill-selector, .status-pill-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.status-pill-selector {
  grid-template-columns: 1fr 1fr;
}

.priority-pill, .status-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 0.83rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.priority-pill.low .pill-dot { background: #3b82f6; }
.priority-pill.medium .pill-dot { background: #f59e0b; }
.priority-pill.high .pill-dot { background: #ef4444; }
.status-pill.open .pill-dot { background: #f59e0b; }

.priority-pill.low.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  color: #60a5fa;
}

.priority-pill.medium.active {
  background: rgba(245, 158, 11, 0.15);
  border-color: #f59e0b;
  color: #fbbf24;
}

.priority-pill.high.active {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
  color: #f87171;
}

.status-pill.open.active {
  background: rgba(245, 158, 11, 0.15);
  border-color: #f59e0b;
  color: #fbbf24;
}

.status-pill.closed.active {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
  color: #34d399;
}

.textarea-modern {
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.optional-tag {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 400;
}

.optional-tag-badge {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: none;
  letter-spacing: normal;
  margin-left: auto;
}

.required-star {
  color: #ef4444;
  font-weight: 700;
}

.modern-dropzone {
  padding: 16px !important;
  border-radius: 10px !important;
  border-width: 1.5px !important;
}

.dropzone-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.dropzone-icon {
  color: var(--accent);
}

.dropzone-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.sticky-footer {
  position: sticky;
  bottom: 0;
  background: #121214;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-save-pendency {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px !important;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

@media (max-width: 600px) {
  .grid-2, .grid-3 {
    grid-template-columns: 1fr;
  }
  .priority-pill-selector, .status-pill-selector {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Autocomplete styling */
.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1010;
  max-height: 200px;
  overflow-y: auto;
  border-radius: 10px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.5);
  background: #18181b;
  border: 1px solid var(--border);
}

.dropdown-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.2s;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-item:hover {
  background: rgba(255,255,255,0.06);
}

.dropdown-item span {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.dropdown-item .sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Drag Drop styles */
.drag-drop-area {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.drag-drop-area:hover, .drag-drop-area.drag-over {
  border-color: var(--accent);
  background: rgba(16, 185, 129, 0.03);
}

.drag-drop-area svg {
  color: var(--text-secondary);
  transition: color 0.3s;
}

.drag-drop-area:hover svg {
  color: var(--accent);
}

.drag-drop-area p {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.drag-drop-area .sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.hidden-input {
  display: none;
}

.images-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 15px;
}

.image-preview-item {
  width: 70px;
  height: 70px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border);
}

.image-preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-img-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.85);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  cursor: pointer;
}

.remove-img-btn:hover {
  background: #ef4444;
}

.existing-images-section {
  flex-direction: column;
  width: 100%;
  align-items: flex-start;
  gap: 8px;
}

.existing-images-section .title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Modal Actions */
.modal-actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.required-note {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* Lightbox overlay */
.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 20px;
}

.lightbox-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.lightbox-content img {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  display: block;
}

.close-lightbox-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 2rem;
  color: white;
  background: rgba(0,0,0,0.5);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-lightbox-btn:hover {
  background: rgba(0,0,0,0.7);
}

/* Animations */
.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-state, .spinner-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  border-radius: 16px;
  gap: 15px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-fade-enter-from, .slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Empty State Stylings */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 40px;
  border-radius: 16px;
  max-width: 600px;
  margin: 40px auto;
  border: 1px solid var(--border);
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.03) 0%, transparent 80%), var(--bg-card);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  margin-bottom: 24px;
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
}

.empty-state:hover .empty-icon {
  transform: translateY(-4px) scale(1.05);
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: 0 10px 20px rgba(34, 181, 95, 0.15), inset 0 0 20px rgba(34, 181, 95, 0.05);
}

.empty-state h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  max-width: 400px;
  margin-bottom: 24px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 12px;
}

/* Estilos adicionais para Movimentações de Pendência */
.medium-modal {
  max-width: 650px;
  width: 90%;
}

.movements-modal-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.movements-middle-actions {
  display: flex;
  justify-content: center;
  margin: 10px 0;
}

.btn-print-report-middle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 16px;
  color: var(--text-primary);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-print-report-middle:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.finish-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.new-movement-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-actions-right {
  display: flex;
  justify-content: flex-end;
}

.modal-divider {
  border: 0;
  height: 1px;
  background: var(--border);
  margin: 5px 0;
}

.movements-history-section h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.loading-inline {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.spinner-sm {
  border: 2px solid rgba(255,255,255,0.1);
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border-left-color: var(--accent);
  animation: spin 1s linear infinite;
}

.no-movements-placeholder {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-style: italic;
  padding: 15px 0;
  text-align: center;
  background: rgba(255,255,255,0.02);
  border-radius: 8px;
  border: 1px dashed var(--border);
}

.movements-timeline {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 250px;
  overflow-y: auto;
  padding-right: 5px;
}

.timeline-item {
  border-radius: 8px;
  padding: 12px;
  border: 1px solid var(--border);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 0.8rem;
}

.timeline-user {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 700;
  color: var(--text-primary);
}

.timeline-date {
  color: var(--text-secondary);
}

.timeline-content p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.4;
  white-space: pre-wrap;
  margin: 0;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.close-btn-round {
  background: var(--glass);
  border: none;
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn-round:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* Lazy Loading Footer */
.load-more-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  border-radius: 16px;
  margin-top: 24px;
  margin-bottom: 24px;
  width: 100%;
}

.load-more-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.btn-load-more {
  padding: 10px 24px;
  font-weight: 600;
  transition: all 0.2s ease-in-out;
}

.btn-load-more:hover {
  transform: translateY(-1px);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 25px;
}

.btn-danger-sm {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-danger-sm:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

/* Botões Inline e Tabela de Anexos */
.btn-attachments-inline {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--surface-tinted);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-attachments-inline:hover {
  background: var(--hover-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.attachment-badge-inline {
  background: var(--accent);
  color: white;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 10px;
}

.btn-table-attachments {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface-tinted);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-table-attachments:hover {
  background: var(--hover-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.attachment-count-badge {
  background: var(--accent);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

/* Galeria de Anexos no Modal */
.attachments-modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.no-attachments-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 30px 20px;
  color: var(--text-secondary);
  background: var(--surface-tinted);
  border: 1px dashed var(--border);
  border-radius: 12px;
  text-align: center;
}

.attachments-gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.attachment-card {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
}

.attachment-preview {
  position: relative;
  height: 120px;
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  overflow: hidden;
}

.attachment-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.attachment-preview:hover img {
  transform: scale(1.06);
}

.attachment-hover-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.attachment-preview:hover .attachment-hover-overlay {
  opacity: 1;
}

.attachment-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--surface-tinted);
  border-top: 1px solid var(--border);
}

.attachment-date {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.attachment-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.attachment-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.attachment-action-btn:hover {
  background: var(--hover-bg);
  color: var(--accent);
}

.attachment-action-btn.delete:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.modal-upload-section h3 {
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.compact-drag {
  padding: 14px !important;
  text-align: center;
  font-size: 0.82rem;
}

.modal-new-images-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.modal-img-preview {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.modal-img-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-img-preview .remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}

.btn-upload-now {
  padding: 8px 16px;
  font-size: 0.85rem;
}
</style>
