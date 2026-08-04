<template>
  <div class="customers-page-container">
    <main class="main-content">
      <header class="page-header glass-effect">
        <div class="header-info">
          <h1>Clientes</h1>
          <p>Gerencie sua base de contatos e CRM</p>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <SearchIcon :size="20" />
            <input v-model="search" placeholder="Buscar por nome ou telefone..." type="text" />
          </div>
          <button @click="showFilters = !showFilters" :class="{ 'btn-filter-active': showFilters || activeFiltersCount > 0 }" class="btn-filter-toggle" title="Filtrar Clientes">
            <FilterIcon :size="18" />
            <span>Filtros</span>
            <span v-if="activeFiltersCount > 0" class="filter-count-badge">{{ activeFiltersCount }}</span>
          </button>
          <div class="view-switcher-toggle">
            <button @click="setViewMode('grid')" :class="{ active: viewMode === 'grid' }" class="toggle-btn" title="Visualização em Grade">
              <LayoutGridIcon :size="18" />
            </button>
            <button @click="setViewMode('list')" :class="{ active: viewMode === 'list' }" class="toggle-btn" title="Visualização em Lista">
              <ListIcon :size="18" />
            </button>
          </div>
          <button @click="openCreateModal" class="btn-primary">
            <PlusIcon :size="20" /> Novo Cliente
          </button>
        </div>
      </header>

      <div class="content-wrapper" ref="contentWrapperRef" @scroll="handleScroll">
        <!-- Barra de Filtros (CRM) - Expansível -->
        <Transition name="slide-fade">
          <div class="filters-container glass-effect" v-if="showFilters">
            <div class="filter-group">
              <label>Status</label>
              <select v-model="filterStatus" class="select-glass">
                <option value="all">Todos os Status</option>
                <option value="active">Ativos</option>
                <option value="blocked">Bloqueados</option>
              </select>
            </div>
            
            <div class="filter-group">
              <label>Tipo de Cliente</label>
              <select v-model="filterType" class="select-glass">
                <option value="all">Todos os Tipos</option>
                <option value="pj">Pessoa Jurídica (CNPJ)</option>
                <option value="pf">Pessoa Física (CPF)</option>
              </select>
            </div>

            <div class="filter-group">
              <label>Estado (UF)</label>
              <select v-model="filterState" class="select-glass">
                <option value="all">Todos os Estados</option>
                <option v-for="uf in availableStates" :key="uf" :value="uf">{{ uf }}</option>
              </select>
            </div>

            <button v-if="hasActiveFilters" @click="clearFilters" class="btn-clear-filters">
              Limpar Filtros
            </button>
          </div>
        </Transition>

        <!-- Loading State -->
        <div v-if="loadingList" class="loading-state glass-effect animate-in">
          <div class="spinner"></div>
          <p>Carregando clientes...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredCustomers.length === 0" class="empty-state glass-effect animate-in">
          <div class="empty-icon">
            <SearchIcon v-if="hasActiveFilters || search.trim()" :size="40" />
            <UsersIcon v-else :size="40" />
          </div>
          <template v-if="hasActiveFilters || search.trim()">
            <h2>Nenhum resultado encontrado</h2>
            <p>Nenhum cliente corresponde aos filtros ou termos de busca aplicados.</p>
            <div class="empty-actions" style="margin-top: 15px;">
              <button @click="clearFiltersAndSearch" class="btn-primary">
                Limpar Filtros e Busca
              </button>
            </div>
          </template>
          <template v-else>
            <h2>Nenhum cliente cadastrado</h2>
            <p>Sua base de clientes está vazia. Comece adicionando seu primeiro cliente!</p>
            <div class="empty-actions" style="margin-top: 15px;">
              <button @click="openCreateModal" class="btn-primary">
                <PlusIcon :size="18" /> Novo Cliente
              </button>
            </div>
          </template>
        </div>

        <!-- Visualização em Grade (Cards) -->
        <div class="customers-grid" v-else-if="viewMode === 'grid'">
          <div v-for="customer in displayedCustomers" :key="customer.id" class="customer-card glass-effect animate-in" :class="{ 'blocked-card': customer.is_blocked }">
            <div class="card-header">
              <div class="avatar" :class="{ 'blocked-avatar': customer.is_blocked }">
                {{ customer.name.charAt(0).toUpperCase() }}
              </div>
              <div class="card-actions">
                <button @click="openTicket(customer)" class="icon-btn" title="Abrir Ticket">
                  <MessageSquarePlusIcon :size="18" />
                </button>
                <button @click="manageContacts(customer)" class="icon-btn" title="Contatos Adicionais">
                  <UsersIcon :size="18" />
                </button>
                <button @click="openCustomerHistory(customer)" class="icon-btn" title="Histórico de Atendimentos">
                  <HistoryIcon :size="18" />
                </button>
                <button @click="editCustomer(customer)" class="icon-btn" title="Editar">
                  <EditIcon :size="18" />
                </button>
                <button @click="confirmDelete(customer)" class="icon-btn delete" title="Excluir">
                  <TrashIcon :size="18" />
                </button>
              </div>
            </div>
            <div class="card-body">
              <div class="name-block">
                <h3>{{ customer.name }}</h3>
                <span v-if="customer.is_blocked" class="blocked-badge">Bloqueado</span>
              </div>
              <div v-if="customer.fantasy_name" class="fantasy-name">{{ customer.fantasy_name }}</div>
              
              <div class="info-item">
                <PhoneIcon :size="16" />
                <span>{{ formatPhone(customer.phone) }}</span>
              </div>
              <div v-if="customer.email" class="info-item">
                <MailIcon :size="16" />
                <span>{{ customer.email }}</span>
              </div>
              <div v-if="customer.cnpj || customer.cpf" class="info-item document-item">
                <FileTextIcon :size="16" />
                <span>{{ customer.cnpj ? 'CNPJ: ' + formatCNPJ(customer.cnpj) : 'CPF: ' + formatCPF(customer.cpf) }}</span>
              </div>
              <div v-if="customer.additional_contacts?.length > 0" class="additional-count">
                {{ customer.additional_contacts.length }} contato(s) adicional(is)
              </div>
            </div>
          </div>
        </div>

        <!-- Visualização em Tabela (List Table) -->
        <div class="customers-list-view glass-effect animate-in" v-else-if="viewMode === 'list'">
          <table class="customers-table">
            <thead>
              <tr>
                <th>Nome / Razão Social</th>
                <th>Nome Fantasia</th>
                <th>Documento</th>
                <th>Telefone</th>
                <th>Cidade/UF</th>
                <th>E-mail</th>
                <th>Status</th>
                <th class="actions-col">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="customer in displayedCustomers" :key="customer.id" :class="{ 'blocked-row': customer.is_blocked }">
                <td>
                  <div class="table-name-cell">
                    <div class="table-avatar" :class="{ 'blocked-avatar': customer.is_blocked }">
                      {{ customer.name.charAt(0).toUpperCase() }}
                    </div>
                    <span class="table-customer-name">{{ customer.name }}</span>
                  </div>
                </td>
                <td>{{ customer.fantasy_name || '-' }}</td>
                <td>{{ customer.cnpj ? formatCNPJ(customer.cnpj) : (customer.cpf ? formatCPF(customer.cpf) : '-') }}</td>
                <td>{{ formatPhone(customer.phone) }}</td>
                <td>
                  <span v-if="customer.city">{{ customer.city }}</span>
                  <span v-if="customer.state" class="state-pill">{{ customer.state }}</span>
                  <span v-if="!customer.city && !customer.state">-</span>
                </td>
                <td>{{ customer.email || '-' }}</td>
                <td>
                  <span v-if="customer.is_blocked" class="blocked-badge">Bloqueado</span>
                  <span v-else class="active-badge">Ativo</span>
                </td>
                <td class="actions-col">
                  <div class="table-actions">
                    <button @click="openTicket(customer)" class="table-action-btn" title="Abrir Ticket">
                      <MessageSquarePlusIcon :size="16" />
                    </button>
                    <button @click="manageContacts(customer)" class="table-action-btn" title="Contatos Adicionais">
                      <UsersIcon :size="16" />
                    </button>
                    <button @click="openCustomerHistory(customer)" class="table-action-btn" title="Histórico de Atendimentos">
                      <HistoryIcon :size="16" />
                    </button>
                    <button @click="editCustomer(customer)" class="table-action-btn" title="Editar">
                      <EditIcon :size="16" />
                    </button>
                    <button @click="confirmDelete(customer)" class="table-action-btn delete" title="Excluir">
                      <TrashIcon :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Footer de Paginação / Carregar Mais -->
        <div v-if="filteredCustomers.length > 0" class="pagination-footer">
          <p class="pagination-info">
            Exibindo {{ displayedCustomers.length }} de {{ filteredCustomers.length }} clientes
          </p>
          <button 
            v-if="displayLimit < filteredCustomers.length" 
            @click="displayLimit += 30" 
            class="btn-secondary btn-load-more"
          >
            Carregar mais clientes
          </button>
        </div>
      </div>
    </main>

    <!-- Modal de Cadastro/Edição de Cliente -->
    <Transition name="modal-fade">
      <div v-if="showModal" class="modal-overlay" @click="showModal = false">
        <div class="modal-content large-modal" @click.stop>
          <div class="modal-header-container">
            <div class="modal-header">
              <h2>{{ editingId ? 'Editar Cliente' : 'Novo Cliente' }}</h2>
              <button @click="showModal = false" class="close-btn-round"><XIcon :size="20" /></button>
            </div>
            
            <!-- Abas do Formulário -->
            <div class="tabs-nav">
              <button type="button" :class="{ active: activeTab === 'geral' }" @click="activeTab = 'geral'">Dados Gerais</button>
              <button type="button" :class="{ active: activeTab === 'contatos' }" @click="activeTab = 'contatos'">Contatos</button>
              <button type="button" :class="{ active: activeTab === 'enderecos' }" @click="activeTab = 'enderecos'">Endereços</button>
              <button type="button" :class="{ active: activeTab === 'financeiro' }" @click="activeTab = 'financeiro'">Financeiro</button>
              <button type="button" :class="{ active: activeTab === 'extra' }" @click="activeTab = 'extra'">Outros / CRM</button>
            </div>
          </div>

          <form @submit.prevent="saveCustomer" class="modal-form-scrollable">
            <!-- ABA 1: DADOS GERAIS -->
            <div v-if="activeTab === 'geral'" class="tab-pane">
              <div class="grid-2">
                <div class="form-group">
                  <label>Tipo de Cliente *</label>
                  <select v-model="clientType" class="select-glass">
                    <option value="PJ">Pessoa Jurídica (CNPJ)</option>
                    <option value="PF">Pessoa Física (CPF)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>{{ clientType === 'PJ' ? 'Razão Social *' : 'Nome Completo *' }}</label>
                  <input v-model="form.name" required class="input-glass" :placeholder="clientType === 'PJ' ? 'Ex: Confetti Eventos Ltda' : 'Ex: João da Silva'" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group" v-if="clientType === 'PJ'">
                  <label>Nome Fantasia</label>
                  <input v-model="form.fantasy_name" class="input-glass" placeholder="Ex: Confetti Eventos" />
                </div>
                <div class="form-group">
                  <label>{{ clientType === 'PJ' ? 'CNPJ *' : 'CPF *' }}</label>
                  <div v-if="clientType === 'PJ'" class="input-with-button">
                    <input 
                      v-model="form.cnpj" 
                      @input="form.cnpj = formatCNPJ($event.target.value)"
                      class="input-glass" 
                      placeholder="Ex: 00.000.000/0000-00" 
                      maxlength="18"
                      required
                    />
                    <button 
                      type="button" 
                      class="btn-search-cnpj" 
                      @click="searchCNPJ" 
                      :disabled="loadingCNPJ"
                      title="Buscar dados via CNPJ"
                    >
                      <SearchIcon v-if="!loadingCNPJ" :size="16" />
                      <span v-else class="spinner-mini"></span>
                    </button>
                  </div>
                  <input 
                    v-else
                    v-model="form.cpf" 
                    @input="form.cpf = formatCPF($event.target.value)"
                    class="input-glass" 
                    placeholder="Ex: 000.000.000-00" 
                    maxlength="14"
                    required
                  />
                </div>
                <div class="form-group" v-if="clientType === 'PF'">
                  <label>RG</label>
                  <input v-model="form.rg" class="input-glass" placeholder="Ex: 000000000" />
                </div>
              </div>

              <div class="grid-2" v-if="clientType === 'PJ'">
                <div class="form-group">
                  <label>Inscrição Estadual</label>
                  <input v-model="form.state_inscription" class="input-glass" placeholder="Isento ou Número" />
                </div>
                <div class="form-group">
                  <label>Inscrição Municipal</label>
                  <input v-model="form.municipal_inscription" class="input-glass" placeholder="Número" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group" v-if="clientType === 'PF'">
                  <label>Data de Nascimento</label>
                  <input v-model="form.birth_date" type="date" class="input-glass" />
                </div>
                <div class="form-group" v-if="clientType === 'PJ'">
                  <label>Data de Fundação</label>
                  <input v-model="form.foundation_date" type="date" class="input-glass" />
                </div>
              </div>

              <div class="checkbox-row" v-if="clientType === 'PJ'">
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.optante_simples" />
                  <span class="checkmark"></span>
                  Optante pelo Simples Nacional
                </label>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.consumidor_final" />
                  <span class="checkmark"></span>
                  Consumidor Final
                </label>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.nao_contribuinte" />
                  <span class="checkmark"></span>
                  Não Contribuinte
                </label>
              </div>
              <div class="checkbox-row" v-else>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.consumidor_final" />
                  <span class="checkmark"></span>
                  Consumidor Final
                </label>
                <label class="checkbox-container">
                  <input type="checkbox" v-model="form.nao_contribuinte" />
                  <span class="checkmark"></span>
                  Não Contribuinte
                </label>
              </div>
            </div>

            <!-- ABA 2: CONTATOS -->
            <div v-if="activeTab === 'contatos'" class="tab-pane">
              <div class="grid-2">
                <div class="form-group">
                  <label>Telefone Principal *</label>
                  <input 
                    v-model="form.phone" 
                    @input="form.phone = formatPhone($event.target.value)"
                    maxlength="15"
                    required 
                    class="input-glass" 
                    placeholder="Ex: (11) 99999-9999" 
                  />
                </div>
                <div class="form-group">
                  <label>WhatsApp</label>
                  <input 
                    v-model="form.whatsapp" 
                    @input="form.whatsapp = formatPhone($event.target.value)"
                    maxlength="15"
                    class="input-glass" 
                    placeholder="Ex: (11) 99999-9999" 
                  />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Celular</label>
                  <input 
                    v-model="form.mobile" 
                    @input="form.mobile = formatPhone($event.target.value)"
                    maxlength="15"
                    class="input-glass" 
                    placeholder="Ex: (11) 99999-9999" 
                  />
                </div>
                <div class="form-group">
                  <label>Telefone 2 (Fixo/Outro)</label>
                  <input 
                    v-model="form.phone2" 
                    @input="form.phone2 = formatPhone($event.target.value)"
                    maxlength="15"
                    class="input-glass" 
                    placeholder="Ex: (11) 3333-3333" 
                  />
                </div>
              </div>

              <div class="form-group">
                <label>E-mail Geral</label>
                <input v-model="form.email" type="email" class="input-glass" placeholder="contato@empresa.com" />
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>E-mail Comercial</label>
                  <input v-model="form.email_commercial" type="email" class="input-glass" placeholder="comercial@empresa.com" />
                </div>
                <div class="form-group">
                  <label>E-mail Financeiro</label>
                  <input v-model="form.email_financial" type="email" class="input-glass" placeholder="financeiro@empresa.com" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Contato Principal (Nome)</label>
                  <input v-model="form.contact_name" class="input-glass" placeholder="Ex: João Silva" />
                </div>
                <div class="form-group">
                  <label>Contato Secundário (Nome)</label>
                  <input v-model="form.contact_name2" class="input-glass" placeholder="Ex: Maria Souza" />
                </div>
              </div>
            </div>

            <!-- ABA 3: ENDEREÇOS -->
            <div v-if="activeTab === 'enderecos'" class="tab-pane">
              <div class="address-subtabs">
                <button type="button" :class="{ active: activeAddressTab === 'principal' }" @click="activeAddressTab = 'principal'">Principal</button>
                <button type="button" :class="{ active: activeAddressTab === 'cobranca' }" @click="activeAddressTab = 'cobranca'">Cobrança</button>
                <button type="button" :class="{ active: activeAddressTab === 'entrega' }" @click="activeAddressTab = 'entrega'">Entrega</button>
              </div>

              <!-- Endereço Principal -->
              <div v-if="activeAddressTab === 'principal'" class="subtab-pane">
                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP</label>
                    <input v-model="form.zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado (UF)</label>
                    <input v-model="form.state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group city-autocomplete-container" style="position: relative;">
                    <label>Cidade</label>
                    <input 
                      v-model="citySearchQuery" 
                      @input="handleCitySearch(); form.city = citySearchQuery; showCityDropdown = true;"
                      @focus="showCityDropdown = true"
                      class="input-glass" 
                      placeholder="Busque a cidade cadastrada..." 
                    />
                    <!-- Dropdown de Resultados -->
                    <div 
                      v-if="showCityDropdown && citySearchResults.length > 0" 
                      class="autocomplete-dropdown glass-effect"
                      style="position: absolute; top: 100%; left: 0; right: 0; z-index: 1000; max-height: 200px; overflow-y: auto; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; margin-top: 5px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);"
                    >
                      <div 
                        v-for="city in citySearchResults" 
                        :key="city.id" 
                        @click="selectCity(city)"
                        class="dropdown-item"
                        style="padding: 10px 15px; cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.2s; display: flex; justify-content: space-between; align-items: center;"
                      >
                        <span style="font-weight: 600; color: var(--text-primary);">{{ city.name }} - {{ city.state }}</span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">IBGE: {{ city.ibge_code }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro / Endereço</label>
                    <input v-model="form.address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número</label>
                    <input v-model="form.number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Complemento</label>
                    <input v-model="form.complement" class="input-glass" placeholder="Apto 42" />
                  </div>
                  <div class="form-group">
                    <label>Bairro</label>
                    <input v-model="form.neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>

              <!-- Endereço de Cobrança -->
              <div v-if="activeAddressTab === 'cobranca'" class="subtab-pane">
                <div class="subtab-header">
                  <h4>Endereço de Cobrança</h4>
                  <button type="button" @click="copyPrincipalToBilling" class="btn-secondary-sm">
                    <CopyIcon :size="14" /> Copiar do Principal
                  </button>
                </div>

                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP Cobrança</label>
                    <input v-model="form.billing_zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado Cobrança</label>
                    <input v-model="form.billing_state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group">
                    <label>Cidade Cobrança</label>
                    <input v-model="form.billing_city" class="input-glass" placeholder="São Paulo" />
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro Cobrança</label>
                    <input v-model="form.billing_address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número Cobrança</label>
                    <input v-model="form.billing_number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Bairro Cobrança</label>
                    <input v-model="form.billing_neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>

              <!-- Endereço de Entrega -->
              <div v-if="activeAddressTab === 'entrega'" class="subtab-pane">
                <div class="subtab-header">
                  <h4>Endereço de Entrega</h4>
                  <button type="button" @click="copyPrincipalToDelivery" class="btn-secondary-sm">
                    <CopyIcon :size="14" /> Copiar do Principal
                  </button>
                </div>

                <div class="grid-3">
                  <div class="form-group">
                    <label>CEP Entrega</label>
                    <input v-model="form.delivery_zip_code" class="input-glass" placeholder="00000-000" />
                  </div>
                  <div class="form-group">
                    <label>Estado Entrega</label>
                    <input v-model="form.delivery_state" class="input-glass" placeholder="SP" maxlength="2" />
                  </div>
                  <div class="form-group">
                    <label>Cidade Entrega</label>
                    <input v-model="form.delivery_city" class="input-glass" placeholder="São Paulo" />
                  </div>
                </div>

                <div class="address-main-row">
                  <div class="form-group address-field">
                    <label>Logradouro Entrega</label>
                    <input v-model="form.delivery_address" class="input-glass" placeholder="Av. Paulista" />
                  </div>
                  <div class="form-group number-field">
                    <label>Número Entrega</label>
                    <input v-model="form.delivery_number" class="input-glass" placeholder="1000" />
                  </div>
                </div>

                <div class="grid-2">
                  <div class="form-group">
                    <label>Bairro Entrega</label>
                    <input v-model="form.delivery_neighborhood" class="input-glass" placeholder="Bela Vista" />
                  </div>
                </div>
              </div>
            </div>

            <!-- ABA 4: FINANCEIRO -->
            <div v-if="activeTab === 'financeiro'" class="tab-pane">
              <div class="grid-2">
                <div class="form-group">
                  <label>Limite de Crédito (R$)</label>
                  <input v-model.number="form.credit_limit" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
                <div class="form-group">
                  <label>Vencimento do Limite de Crédito</label>
                  <input v-model="form.credit_limit_expiry" type="date" class="input-glass" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Percentual de Comissão (%)</label>
                  <input v-model.number="form.commission_rate" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
                <div class="form-group">
                  <label>Percentual Máximo Desconto (%)</label>
                  <input v-model.number="form.discount_rate" type="number" step="0.01" class="input-glass" placeholder="0.00" />
                </div>
              </div>

              <div class="grid-3">
                <div class="form-group">
                  <label>Código do Banco</label>
                  <input v-model.number="form.bank_code" type="number" class="input-glass" placeholder="341" />
                </div>
                <div class="form-group">
                  <label>Agência Bancária</label>
                  <input v-model="form.bank_agency" class="input-glass" placeholder="0001" />
                </div>
                <div class="form-group">
                  <label>Conta Bancária</label>
                  <input v-model="form.bank_account" class="input-glass" placeholder="12345-6" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Dia de Vencimento Fatura</label>
                  <input v-model.number="form.due_day" type="number" min="1" max="31" class="input-glass" placeholder="10" />
                </div>
                <div class="form-group">
                  <label>Forma/Condição de Pagamento</label>
                  <input v-model="form.payment_method" class="input-glass" placeholder="Boleto 30 dias, PIX" />
                </div>
              </div>

              <div class="form-group">
                <label>Observação Financeira</label>
                <textarea v-model="form.obs_financial" class="input-glass" placeholder="Restrições, formas específicas de faturamento..." rows="3" style="resize: vertical;"></textarea>
              </div>
            </div>

            <!-- ABA 5: OUTROS / CRM -->
            <div v-if="activeTab === 'extra'" class="tab-pane">
              <div class="grid-4">
                <div class="form-group">
                  <label>Código Representante</label>
                  <input v-model.number="form.representative_id" type="number" class="input-glass" placeholder="ID" />
                </div>
                <div class="form-group">
                  <label>Código Transportadora</label>
                  <input v-model.number="form.carrier_id" type="number" class="input-glass" placeholder="ID" />
                </div>
                <div class="form-group">
                  <label>Região Operacional</label>
                  <input v-model.number="form.region_id" type="number" class="input-glass" placeholder="Código" />
                </div>
                <div class="form-group">
                  <label>Grupo de Clientes</label>
                  <input v-model.number="form.group_id" type="number" class="input-glass" placeholder="Código" />
                </div>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label>Parecer de Análise de Crédito</label>
                  <textarea v-model="form.credit_opinion" class="input-glass" placeholder="Histórico ou parecer do departamento de crédito..." rows="3" style="resize: vertical;"></textarea>
                </div>
                <div class="form-group">
                  <label>Observação para Nota Fiscal</label>
                  <textarea v-model="form.obs_invoice" class="input-glass" placeholder="Textos fixos para NF..." rows="3" style="resize: vertical;"></textarea>
                </div>
              </div>

              <div class="form-group">
                <label>Observações Gerais</label>
                <textarea v-model="form.obs" class="input-glass" placeholder="Outras informações do cliente..." rows="3" style="resize: vertical;"></textarea>
              </div>

              <div class="checkbox-row" style="margin-top: 10px;">
                <label class="checkbox-container blocked-label">
                  <input type="checkbox" v-model="form.is_blocked" />
                  <span class="checkmark red-check"></span>
                  <strong>Bloquear Cliente (Bloqueia emissão de pedidos/tickets de forma automática)</strong>
                </label>
              </div>
            </div>

            <!-- Botões de Ação do Modal -->
            <div class="modal-actions-container">
              <span class="required-note">* Campos obrigatórios</span>
              <div class="modal-actions">
                <button type="button" @click="showModal = false" class="btn-secondary">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="loading">
                  {{ loading ? 'Salvando...' : 'Salvar Cliente' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Modal de Gerenciamento de Contatos Adicionais -->
    <Transition name="modal-fade">
      <div v-if="showContactsModal" class="modal-overlay" @click="showContactsModal = false">
        <div class="modal-content contacts-modal" @click.stop>
          <div class="modal-header">
            <div>
              <h2>Contatos de {{ selectedCustomer.name }}</h2>
              <p style="color: var(--text-secondary); font-size: 0.9rem;">Gerencie as pessoas vinculadas a esta empresa</p>
            </div>
            <button @click="showContactsModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          
          <div class="contacts-list">
            <div v-for="contact in selectedCustomer.additional_contacts" :key="contact.id" class="contact-item-row">
              <div class="contact-info-header">
                <div class="contact-avatar">
                  {{ contact.name.charAt(0).toUpperCase() }}
                </div>
                <div class="contact-title-group">
                  <strong>{{ contact.name }}</strong>
                  <div class="contact-badges" v-if="contact.sector || contact.role">
                    <span v-if="contact.sector" class="contact-badge sector">{{ contact.sector }}</span>
                    <span v-if="contact.role" class="contact-badge role">{{ contact.role }}</span>
                  </div>
                </div>
                <div class="contact-actions-mini">
                  <button @click="startEditingContact(contact)" class="icon-btn edit small" title="Editar contato">
                    <EditIcon :size="14" />
                  </button>
                  <button @click="deleteContact(contact.id)" class="icon-btn delete small" title="Excluir contato">
                    <TrashIcon :size="14" />
                  </button>
                </div>
              </div>
              
              <div class="contact-meta-details">
                <span v-if="contact.phone" class="meta-item" title="Telefone Fixo">
                  <PhoneIcon :size="12" /> {{ formatPhone(contact.phone) }}
                </span>
                <span v-if="contact.cellphone" class="meta-item" title="Celular">
                  <SmartphoneIcon :size="12" /> {{ formatPhone(contact.cellphone) }}
                </span>
                <span v-if="contact.whatsapp" class="meta-item whatsapp" title="WhatsApp">
                  <svg class="whatsapp-icon-mini" viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M12.012 2c-5.506 0-9.989 4.478-9.99 9.984a9.96 9.96 0 001.37 5.054L2 22l5.177-1.354a9.97 9.97 0 004.822 1.254h.008c5.502 0 9.985-4.477 9.986-9.984A10.002 10.002 0 0012.012 2zm5.835 14.16c-.25.706-1.443 1.293-1.99 1.347-.497.05-1.147.25-3.327-.655-2.79-1.157-4.59-4.004-4.73-4.188-.137-.184-1.116-1.48-1.116-2.825 0-1.344.706-2.003.955-2.27.25-.267.548-.334.73-.334.183 0 .365.003.523.01.162.008.38-.063.593.453.22.53.75 1.83.816 1.964.066.134.11.29.02.47-.09.18-.135.29-.27.447-.135.156-.285.348-.407.467-.136.133-.28.277-.12.553.16.276.71.1.2.98.67 1.05.6 1.486.9 1.286.3-.2.628-.26.928-.1.3.16 1.9.896 2.083.986.183.09.305.134.35.213.046.08.046.463-.204 1.17z"/></svg>
                  {{ formatPhone(contact.whatsapp) }}
                </span>
                <span v-if="contact.email" class="meta-item" title="E-mail">
                  <MailIcon :size="12" /> {{ contact.email }}
                </span>
                <span v-if="contact.birth_date" class="meta-item" title="Data de Nascimento">
                  <CalendarIcon :size="12" /> {{ formatDate(contact.birth_date) }}
                </span>
              </div>
              
              <div v-if="contact.observation" class="contact-observation-text">
                <strong>Obs:</strong> {{ contact.observation }}
              </div>
            </div>

            <div v-if="!selectedCustomer.additional_contacts?.length" class="empty-mini">
              Nenhum contato adicional cadastrado.
            </div>
          </div>

          <div class="add-contact-form">
            <h4>{{ editingContactId ? 'Editar Contato' : 'Adicionar Novo Contato' }}</h4>
            <div class="form-grid">
              <div class="form-group">
                <label>Nome *</label>
                <input v-model="newContact.name" class="input-glass" placeholder="Nome da Pessoa" />
              </div>
              <div class="form-group">
                <label>E-mail</label>
                <input v-model="newContact.email" class="input-glass" type="email" placeholder="email@exemplo.com" />
              </div>
              <div class="form-group">
                <label>Telefone Fixo</label>
                <input v-model="newContact.phone" class="input-glass" placeholder="(51) 3333-3333" />
              </div>
              <div class="form-group">
                <label>Celular</label>
                <input v-model="newContact.cellphone" class="input-glass" placeholder="(51) 99999-9999" />
              </div>
              <div class="form-group">
                <label>WhatsApp</label>
                <input v-model="newContact.whatsapp" class="input-glass" placeholder="(51) 99999-9999" />
              </div>
              <div class="form-group">
                <label>Data de Nascimento</label>
                <input v-model="newContact.birth_date" class="input-glass" type="date" />
              </div>
              <div class="form-group">
                <label>Setor</label>
                <input v-model="newContact.sector" class="input-glass" placeholder="Ex: Financeiro" />
              </div>
              <div class="form-group">
                <label>Cargo</label>
                <input v-model="newContact.role" class="input-glass" placeholder="Ex: Gerente" />
              </div>
              <div class="form-group full-width">
                <label>Observação</label>
                <textarea v-model="newContact.observation" class="input-glass" placeholder="Detalhes adicionais..." rows="2"></textarea>
              </div>
            </div>
            <div class="form-actions-row">
              <button @click="addContact" class="btn-primary-sm block" :disabled="loadingContact">
                {{ loadingContact ? 'Salvando...' : (editingContactId ? 'Salvar Alterações' : 'Adicionar Contato') }}
              </button>
              <button v-if="editingContactId" @click="cancelEditingContact" class="btn-secondary-sm block" type="button">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Modal de Seleção de Contato para Abrir Ticket -->
    <Transition name="modal-fade">
      <div v-if="showTicketModal" class="modal-overlay" @click="showTicketModal = false">
        <div class="modal-content ticket-contact-modal" @click.stop>
          <div class="modal-header">
            <div>
              <h2>Abrir Ticket para {{ selectedCustomerForTicket?.name }}</h2>
              <p style="color: var(--text-secondary); font-size: 0.9rem;">Escolha o contato para iniciar o atendimento</p>
            </div>
            <button @click="showTicketModal = false" class="close-btn-round"><XIcon :size="20" /></button>
          </div>
          
          <div class="contacts-list select-contacts-list">
            <!-- Contato Principal -->
            <div 
              @click="confirmOpenTicket({ name: selectedCustomerForTicket?.name, phone: selectedCustomerForTicket?.phone })" 
              class="contact-select-item"
            >
              <div class="contact-avatar main-avatar">
                P
              </div>
              <div class="contact-details-mini">
                <strong>{{ selectedCustomerForTicket?.name }} <span class="tag-main">Principal</span></strong>
                <span>{{ formatPhone(selectedCustomerForTicket?.phone) }}</span>
              </div>
            </div>

            <!-- Contatos Adicionais -->
            <div 
              v-for="contact in selectedCustomerForTicket?.additional_contacts" 
              :key="contact.id" 
              @click="confirmOpenTicket({ name: contact.name, phone: contact.phone || contact.whatsapp || contact.cellphone })"
              class="contact-select-item"
            >
              <div class="contact-avatar">
                {{ contact.name.charAt(0).toUpperCase() }}
              </div>
              <div class="contact-details-mini">
                <strong>{{ contact.name }}</strong>
                <span>{{ formatPhone(contact.phone || contact.whatsapp || contact.cellphone) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
    <!-- Modal de Histórico de Atendimento -->
    <HistoryModal
      :show="showHistoryModal"
      :customerId="historyParams.customerId"
      :customerName="historyParams.customerName"
      initialTab="customer"
      @close="showHistoryModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'
import { 
  Users as UsersIcon, 
  Search as SearchIcon, 
  Plus as PlusIcon,
  Phone as PhoneIcon,
  Mail as MailIcon,
  FileText as FileTextIcon,
  Edit as EditIcon,
  Trash2 as TrashIcon,
  X as XIcon,
  MessageSquarePlus as MessageSquarePlusIcon,
  Copy as CopyIcon,
  LayoutGrid as LayoutGridIcon,
  List as ListIcon,
  Filter as FilterIcon,
  History as HistoryIcon,
  Smartphone as SmartphoneIcon,
  Calendar as CalendarIcon
} from 'lucide-vue-next'
import HistoryModal from '../components/dashboard/HistoryModal.vue'
import { useChatStore } from '../store/chat'

const chatStore = useChatStore()
const router = useRouter()
const route = useRoute()
const contentWrapperRef = ref(null)
const customers = ref([])
const search = ref(route.query.search || '')
const showModal = ref(false)
const showContactsModal = ref(false)
const showTicketModal = ref(false)
const selectedCustomerForTicket = ref(null)

const showHistoryModal = ref(false)
const historyParams = ref({
  customerId: null,
  customerName: ''
})

const openCustomerHistory = (customer) => {
  historyParams.value = {
    customerId: customer.id,
    customerName: customer.name
  }
  showHistoryModal.value = true
}

const clientType = ref('PJ')
const loadingCNPJ = ref(false)

const searchCNPJ = async () => {
  const cnpjClean = (form.value.cnpj || '').replace(/\D/g, '')
  if (cnpjClean.length !== 14) {
    alert('Por favor, informe um CNPJ válido com 14 dígitos.')
    return
  }
  loadingCNPJ.value = true
  try {
    const response = await axios.get(`https://brasilapi.com.br/api/cnpj/v1/${cnpjClean}`)
    const data = response.data
    
    if (data) {
      // Preenche os campos principais
      form.value.name = data.razao_social || data.nome_fantasia || form.value.name
      form.value.fantasy_name = data.nome_fantasia || data.razao_social || form.value.fantasy_name
      
      // Email
      if (data.email) {
        form.value.email = data.email
      }
      
      // Telefone
      if (data.ddd_telefone_1) {
        form.value.phone = data.ddd_telefone_1
      }
      
      // Endereço
      form.value.zip_code = data.cep ? data.cep.replace(/^(\d{5})(\d{3})$/, '$1-$2') : form.value.zip_code
      form.value.address = data.logradouro || form.value.address
      form.value.number = data.numero || form.value.number
      form.value.complement = data.complemento || form.value.complement
      form.value.neighborhood = data.bairro || form.value.neighborhood
      
      if (data.municipio) {
        form.value.city = data.municipio
      }
      if (data.uf) {
        form.value.state = data.uf
      }
      
      // Tenta buscar o relacionamento de cidade no banco para associar
      if (data.municipio && data.uf) {
        try {
          const normalizeString = (str) => {
            if (!str) return ''
            return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim()
          }
          
          const cities = await chatStore.fetchCities(data.municipio)
          const matchedCity = cities.find(c => 
            normalizeString(c.name) === normalizeString(data.municipio) && 
            normalizeString(c.state) === normalizeString(data.uf)
          )
          
          if (matchedCity) {
            form.value.city = matchedCity.name
            form.value.state = matchedCity.state
            form.value.city_relationship = matchedCity.id
            citySearchQuery.value = matchedCity.name
          } else {
            const closeMatch = cities.find(c => normalizeString(c.name) === normalizeString(data.municipio))
            if (closeMatch) {
              form.value.city = closeMatch.name
              form.value.state = closeMatch.state
              form.value.city_relationship = closeMatch.id
              citySearchQuery.value = closeMatch.name
            } else {
              citySearchQuery.value = data.municipio
            }
          }
        } catch (cityErr) {
          console.error("Erro ao buscar relacionamento da cidade do CNPJ", cityErr)
        }
      }
    }
  } catch (e) {
    console.error("Erro ao buscar CNPJ", e)
    alert("Erro ao buscar CNPJ. Verifique se o número está correto ou tente novamente mais tarde.")
  } finally {
    loadingCNPJ.value = false
  }
}

const formatCPF = (val) => {
  if (!val) return ''
  const nums = val.replace(/\D/g, '')
  let formatted = ''
  if (nums.length > 0) formatted += nums.substring(0, 3)
  if (nums.length > 3) formatted += '.' + nums.substring(3, 6)
  if (nums.length > 6) formatted += '.' + nums.substring(6, 9)
  if (nums.length > 9) formatted += '-' + nums.substring(9, 11)
  return formatted
}

const formatCNPJ = (val) => {
  if (!val) return ''
  const nums = val.replace(/\D/g, '')
  let formatted = ''
  if (nums.length > 0) formatted += nums.substring(0, 2)
  if (nums.length > 2) formatted += '.' + nums.substring(2, 5)
  if (nums.length > 5) formatted += '.' + nums.substring(5, 8)
  if (nums.length > 8) formatted += '/' + nums.substring(8, 12)
  if (nums.length > 12) formatted += '-' + nums.substring(12, 14)
  return formatted
}

const formatPhone = (val) => {
  if (!val) return ''
  let nums = String(val).replace(/\D/g, '')
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

// Busca e Auto-complete de Cidades
const citySearchQuery = ref('')
const citySearchResults = ref([])
const showCityDropdown = ref(false)

const handleCitySearch = async () => {
  const query = citySearchQuery.value.trim()
  if (query.length < 2) {
    citySearchResults.value = []
    return
  }
  try {
    const results = await chatStore.fetchCities(query)
    citySearchResults.value = results
  } catch (err) {
    console.error("Erro ao buscar cidades para preenchimento", err)
  }
}

const selectCity = (city) => {
  form.value.city = city.name
  form.value.state = city.state
  form.value.city_relationship = city.id
  citySearchQuery.value = city.name
  showCityDropdown.value = false
}


// Modo de visualização (grade ou lista)
const viewMode = ref(localStorage.getItem('wdesk_customers_view_mode') || 'grid')
const setViewMode = (mode) => {
  viewMode.value = mode
  localStorage.setItem('wdesk_customers_view_mode', mode)
}

// Estados dos filtros (CRM)
const showFilters = ref(false)
const filterStatus = ref('all')
const filterType = ref('all')
const filterState = ref('all')

const availableStates = computed(() => {
  const states = customers.value.map(c => c.state).filter(Boolean).map(s => s.trim().toUpperCase())
  return [...new Set(states)].sort()
})

const activeFiltersCount = computed(() => {
  let count = 0
  if (filterStatus.value !== 'all') count++
  if (filterType.value !== 'all') count++
  if (filterState.value !== 'all') count++
  return count
})

const hasActiveFilters = computed(() => {
  return filterStatus.value !== 'all' || filterType.value !== 'all' || filterState.value !== 'all' || search.value !== ''
})

const clearFilters = () => {
  filterStatus.value = 'all'
  filterType.value = 'all'
  filterState.value = 'all'
  search.value = ''
}
const loading = ref(false)
const loadingContact = ref(false)
const selectedCustomer = ref(null)
const editingId = ref(null)

// Abas de navegação
const activeTab = ref('geral')
const activeAddressTab = ref('principal')

const defaultForm = () => ({
  name: '',
  fantasy_name: '',
  cnpj: '',
  cpf: '',
  rg: '',
  state_inscription: '',
  municipal_inscription: '',
  birth_date: '',
  foundation_date: '',
  phone: '',
  phone2: '',
  mobile: '',
  whatsapp: '',
  email: '',
  email_commercial: '',
  email_financial: '',
  contact_name: '',
  contact_name2: '',
  address: '',
  zip_code: '',
  number: '',
  complement: '',
  neighborhood: '',
  city: '',
  state: '',
  city_relationship: null,
  billing_zip_code: '',
  billing_address: '',
  billing_number: '',
  billing_neighborhood: '',
  billing_city: '',
  billing_state: '',
  delivery_zip_code: '',
  delivery_address: '',
  delivery_number: '',
  delivery_neighborhood: '',
  delivery_city: '',
  delivery_state: '',
  credit_limit: null,
  credit_limit_expiry: '',
  commission_rate: null,
  discount_rate: null,
  bank_code: null,
  bank_agency: '',
  bank_account: '',
  due_day: null,
  payment_method: '',
  optante_simples: false,
  consumidor_final: true,
  nao_contribuinte: false,
  representative_id: null,
  carrier_id: null,
  region_id: null,
  group_id: null,
  obs: '',
  obs_financial: '',
  obs_invoice: '',
  credit_opinion: '',
  is_blocked: false,
  document: '' // Mantido para compatibilidade histórica do backend
})

const form = ref(defaultForm())

const newContact = ref({
  name: '',
  phone: '',
  cellphone: '',
  whatsapp: '',
  email: '',
  birth_date: '',
  sector: '',
  role: '',
  observation: ''
})

const editingContactId = ref(null)

const startEditingContact = (contact) => {
  editingContactId.value = contact.id
  newContact.value = {
    name: contact.name || '',
    phone: contact.phone || '',
    cellphone: contact.cellphone || '',
    whatsapp: contact.whatsapp || '',
    email: contact.email || '',
    birth_date: contact.birth_date || '',
    sector: contact.sector || '',
    role: contact.role || '',
    observation: contact.observation || '',
    customer: selectedCustomer.value.id
  }
}

const cancelEditingContact = () => {
  editingContactId.value = null
  newContact.value = {
    name: '',
    phone: '',
    cellphone: '',
    whatsapp: '',
    email: '',
    birth_date: '',
    sector: '',
    role: '',
    observation: '',
    customer: selectedCustomer.value.id
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`
  }
  return dateStr
}

const loadingList = ref(true)
const displayLimit = ref(30)

const filteredCustomers = computed(() => {
  return customers.value.filter(c => {
    // 1. Filtro por texto de busca
    if (search.value) {
      const s = search.value.toLowerCase()
      const matchesSearch = 
        c.name.toLowerCase().includes(s) || 
        c.phone.includes(s) || 
        (c.email && c.email.toLowerCase().includes(s)) ||
        (c.fantasy_name && c.fantasy_name.toLowerCase().includes(s)) ||
        (c.cnpj && c.cnpj.includes(s)) ||
        (c.cpf && c.cpf.includes(s))
      if (!matchesSearch) return false
    }
    
    // 2. Filtro por status
    if (filterStatus.value === 'active' && c.is_blocked) return false
    if (filterStatus.value === 'blocked' && !c.is_blocked) return false
    
    // 3. Filtro por tipo de cliente (PF / PJ)
    if (filterType.value === 'pj' && !c.cnpj) return false
    if (filterType.value === 'pf' && !c.cpf) return false
    
    // 4. Filtro por estado (UF)
    if (filterState.value !== 'all') {
      const cState = (c.state || '').trim().toUpperCase()
      if (cState !== filterState.value) return false
    }
    
    return true
  })
})

const displayedCustomers = computed(() => {
  return filteredCustomers.value.slice(0, displayLimit.value)
})

const handleScroll = (e) => {
  const el = e?.target || contentWrapperRef.value || document.documentElement
  if (!el) return
  const scrollTop = el.scrollTop
  const clientHeight = el.clientHeight
  const scrollHeight = el.scrollHeight

  if (scrollHeight - (scrollTop + clientHeight) < 350) {
    if (displayLimit.value < filteredCustomers.value.length) {
      displayLimit.value += 30
    }
  }
}

watch([search, filterStatus, filterType, filterState], () => {
  displayLimit.value = 30
})

const clearFiltersAndSearch = () => {
  search.value = ''
  filterStatus.value = 'all'
  filterType.value = 'all'
  filterState.value = 'all'
}

const fetchCustomers = async () => {
  loadingList.value = true
  try {
    const response = await axios.get(`/api/v1/customers/`)
    customers.value = response.data
    displayLimit.value = 30
  } catch (e) {
    console.error("Erro ao buscar clientes", e)
  } finally {
    loadingList.value = false
  }
}

const openCreateModal = () => {
  editingId.value = null
  form.value = defaultForm()
  clientType.value = 'PJ'
  activeTab.value = 'geral'
  activeAddressTab.value = 'principal'
  citySearchQuery.value = ''
  citySearchResults.value = []
  showModal.value = true
}

const editCustomer = (customer) => {
  editingId.value = customer.id
  // Garante que campos não preenchidos fiquem devidamente inicializados
  const merged = { ...defaultForm(), ...customer }
  
  // Aplica as máscaras ao carregar
  merged.cpf = formatCPF(merged.cpf)
  merged.cnpj = formatCNPJ(merged.cnpj)
  merged.phone = formatPhone(merged.phone)
  merged.phone2 = formatPhone(merged.phone2)
  merged.mobile = formatPhone(merged.mobile)
  merged.whatsapp = formatPhone(merged.whatsapp)
  
  form.value = merged
  
  if (merged.cpf && !merged.cnpj) {
    clientType.value = 'PF'
  } else {
    clientType.value = 'PJ'
  }
  
  if (merged.city_relationship_details) {
    citySearchQuery.value = merged.city_relationship_details.name
  } else {
    citySearchQuery.value = merged.city || ''
  }
  citySearchResults.value = []
  
  activeTab.value = 'geral'
  activeAddressTab.value = 'principal'
  showModal.value = true
}

const copyPrincipalToBilling = () => {
  form.value.billing_zip_code = form.value.zip_code
  form.value.billing_address = form.value.address
  form.value.billing_number = form.value.number
  form.value.billing_neighborhood = form.value.neighborhood
  form.value.billing_city = form.value.city
  form.value.billing_state = form.value.state
}

const copyPrincipalToDelivery = () => {
  form.value.delivery_zip_code = form.value.zip_code
  form.value.delivery_address = form.value.address
  form.value.delivery_number = form.value.number
  form.value.delivery_neighborhood = form.value.neighborhood
  form.value.delivery_city = form.value.city
  form.value.delivery_state = form.value.state
}

const saveCustomer = async () => {
  loading.value = true
  
  const payload = { ...form.value }
  
  // Limpa caracteres de formatação do CPF/CNPJ e Telefones para salvar no banco
  payload.cnpj = (payload.cnpj || '').replace(/\D/g, '')
  payload.cpf = (payload.cpf || '').replace(/\D/g, '')
  payload.phone = (payload.phone || '').replace(/\D/g, '')
  payload.phone2 = (payload.phone2 || '').replace(/\D/g, '')
  payload.mobile = (payload.mobile || '').replace(/\D/g, '')
  payload.whatsapp = (payload.whatsapp || '').replace(/\D/g, '')
  
  // Limpa campos que não pertencem ao tipo de cliente selecionado
  if (clientType.value === 'PF') {
    payload.cnpj = ''
    payload.foundation_date = null
    payload.optante_simples = false
    payload.fantasy_name = ''
    payload.state_inscription = ''
    payload.municipal_inscription = ''
  } else {
    payload.cpf = ''
    payload.rg = ''
    payload.birth_date = null
  }
  
  // Garante sincronização de document para compatibilidade histórica do backend
  payload.document = payload.cnpj || payload.cpf || ''
  
  const numericFields = [
    'credit_limit', 'commission_rate', 'discount_rate', 'bank_code', 
    'due_day', 'representative_id', 'carrier_id', 'region_id', 'group_id'
  ]
  numericFields.forEach(field => {
    if (payload[field] === '' || payload[field] === undefined || payload[field] === null) {
      payload[field] = null
    }
  })
  
  const dateFields = ['birth_date', 'foundation_date', 'credit_limit_expiry']
  dateFields.forEach(field => {
    if (!payload[field]) {
      payload[field] = null
    }
  })

  try {
    if (editingId.value) {
      await axios.put(`/api/v1/customers/${editingId.value}/`, payload)
    } else {
      await axios.post(`/api/v1/customers/`, payload)
    }
    
    showModal.value = false
    await fetchCustomers()
  } catch (e) {
    console.error("Erro ao salvar cliente", e.response?.data)
    alert("Erro ao salvar cliente. Verifique o preenchimento dos campos.")
  } finally {
    loading.value = false
  }
}

const manageContacts = (customer) => {
  selectedCustomer.value = customer
  editingContactId.value = null
  newContact.value = {
    name: '',
    phone: '',
    cellphone: '',
    whatsapp: '',
    email: '',
    birth_date: '',
    sector: '',
    role: '',
    observation: '',
    customer: customer.id
  }
  showContactsModal.value = true
}

const addContact = async () => {
  if (!newContact.value.name) return
  loadingContact.value = true
  const payload = {
    ...newContact.value,
    birth_date: newContact.value.birth_date || null
  }
  try {
    if (editingContactId.value) {
      await axios.put(`/api/v1/customer-contacts/${editingContactId.value}/`, payload)
      editingContactId.value = null
    } else {
      await axios.post(`/api/v1/customer-contacts/`, payload)
    }
    newContact.value = {
      name: '',
      phone: '',
      cellphone: '',
      whatsapp: '',
      email: '',
      birth_date: '',
      sector: '',
      role: '',
      observation: '',
      customer: selectedCustomer.value.id
    }
    await fetchCustomers()
    selectedCustomer.value = customers.value.find(c => c.id === selectedCustomer.value.id)
  } catch (e) {
    alert("Erro ao salvar contato")
  } finally {
    loadingContact.value = false
  }
}

const deleteContact = async (id) => {
  if (!confirm("Excluir este contato?")) return
  try {
    await axios.delete(`/api/v1/customer-contacts/${id}/`)
    await fetchCustomers()
    selectedCustomer.value = customers.value.find(c => c.id === selectedCustomer.value.id)
  } catch (e) {
    alert("Erro ao excluir contato")
  }
}

const confirmDelete = async (customer) => {
  if (confirm(`Deseja realmente excluir o cliente ${customer.name}?`)) {
    try {
      await axios.delete(`/api/v1/customers/${customer.id}/`)
      await fetchCustomers()
    } catch (e) {
      alert("Erro ao excluir cliente")
    }
  }
}

const openTicket = (customer) => {
  if (customer.additional_contacts && customer.additional_contacts.length > 0) {
    selectedCustomerForTicket.value = customer
    showTicketModal.value = true
  } else {
    confirmOpenTicket({ name: customer.name, phone: customer.phone }, customer.id)
  }
}

const confirmOpenTicket = async (contact, customerId = null) => {
  const custId = customerId || selectedCustomerForTicket.value?.id
  if (!custId) return
  showTicketModal.value = false
  try {
    await axios.post(`/api/v1/customers/${custId}/open_ticket/`, {
      name: contact.name,
      phone: contact.phone
    })
    router.push('/')
  } catch (e) {
    alert("Erro ao abrir ticket")
  }
}

const handleDocumentClick = (e) => {
  if (!e.target.closest('.city-autocomplete-container')) {
    showCityDropdown.value = false
  }
}

onMounted(() => {
  fetchCustomers()
  document.addEventListener('click', handleDocumentClick)
  if (contentWrapperRef.value) {
    contentWrapperRef.value.addEventListener('scroll', handleScroll, { passive: true })
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
  if (contentWrapperRef.value) {
    contentWrapperRef.value.removeEventListener('scroll', handleScroll)
  }
})
</script>

<style scoped>
.customers-page-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  padding: 25px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-info h1 {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.header-info p { color: var(--text-secondary); font-size: 0.95rem; }

.header-actions {
  display: flex;
  gap: 20px;
  align-items: center;
}

.search-bar {
  background: var(--glass);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 300px;
}

.search-bar input {
  background: none;
  border: none;
  color: var(--text-primary);
  width: 100%;
  outline: none;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-primary:hover { transform: translateY(-2px); }

.content-wrapper {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.customers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 25px;
}

.customer-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 25px;
  border-radius: 24px;
  transition: all 0.3s;
  position: relative;
}

.customer-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-5px);
  border-color: rgba(16, 185, 129, 0.3);
}

.blocked-card {
  border-color: rgba(239, 68, 68, 0.4) !important;
  background: rgba(239, 68, 68, 0.02) !important;
}

.blocked-card:hover {
  border-color: rgba(239, 68, 68, 0.7) !important;
  background: rgba(239, 68, 68, 0.05) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.avatar {
  width: 50px;
  height: 50px;
  background: var(--brand-gradient);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 800;
}

.blocked-avatar {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
}

.card-actions { display: flex; gap: 8px; }

.icon-btn {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.icon-btn.delete:hover { background: #ef4444; border-color: #ef4444; }

.icon-btn.small { padding: 4px; }

.name-block {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.name-block h3 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

.blocked-badge {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.fantasy-name {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 15px;
  font-style: italic;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.document-item {
  margin-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.03);
  padding-top: 6px;
}

.additional-count {
  margin-top: 15px;
  font-size: 0.75rem;
  color: var(--accent);
  font-weight: 600;
  background: rgba(16, 185, 129, 0.1);
  display: inline-block;
  padding: 2px 8px;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding-top: 100px;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.2;
}

/* Modais e Layouts de Formulário Complexo */
.large-modal {
  width: 850px !important;
  max-width: 95% !important;
  height: 90vh;
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  overflow: hidden;
}

.modal-header-container {
  padding: 30px 30px 10px 30px;
  background: rgba(255, 255, 255, 0.01);
  border-bottom: 1px solid var(--border);
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
.close-btn-round:hover { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

/* Tabs de Navegação */
.tabs-nav {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.tabs-nav button {
  background: none;
  border: 1px solid transparent;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.tabs-nav button:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.03);
}

.tabs-nav button.active {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--accent);
}

/* Área de formulário rolável */
.modal-form-scrollable {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.25s ease-out forwards;
}

/* Sub-abas de Endereços */
.address-subtabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
}

.address-subtabs button {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.address-subtabs button.active {
  border-bottom-color: var(--accent);
  color: var(--accent);
}

.subtab-pane {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.2s ease-out forwards;
}

.subtab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 10px;
}

.subtab-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

/* Campos de Endereço Customizados */
.address-main-row {
  display: flex;
  gap: 20px;
}
.address-field { flex: 3; }
.number-field { flex: 1; }

/* Grid Auxiliares */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.checkbox-row {
  display: flex;
  flex-wrap: wrap;
  gap: 25px;
  margin-top: 10px;
  padding: 10px 0;
}

/* Checkbox estilizado */
.checkbox-container {
  display: flex;
  align-items: center;
  position: relative;
  padding-left: 30px;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--text-primary);
  user-select: none;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 20px;
  width: 20px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 6px;
  transition: all 0.2s;
}

.checkbox-container:hover input ~ .checkmark {
  border-color: var(--accent);
}

.checkbox-container input:checked ~ .checkmark {
  background-color: var(--accent);
  border-color: var(--accent);
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-container .checkmark:after {
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.blocked-label {
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 12px 15px 12px 45px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.05);
  flex: 1;
}

.red-check {
  left: 15px;
  top: 12px;
}

.checkbox-container:hover input ~ .red-check {
  border-color: #ef4444;
}

.checkbox-container input:checked ~ .red-check {
  background-color: #ef4444;
  border-color: #ef4444;
}

/* Rodapé das Ações do Modal */
.modal-actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border);
  padding-top: 25px;
  margin-top: 10px;
}

.required-note {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.modal-actions {
  display: flex;
  gap: 15px;
}

.btn-secondary {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--border);
}

.btn-secondary-sm {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-secondary-sm:hover {
  background: var(--border);
}

/* Contacts Modal Específicos */
.contacts-modal {
  max-width: 680px !important;
}

/* Ticket Contact Selector Modal */
.ticket-contact-modal {
  max-width: 500px;
}

.select-contacts-list {
  max-height: 350px;
  margin-bottom: 0px;
}

.contact-select-item {
  display: flex;
  align-items: center;
  gap: 15px;
  background: var(--glass);
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid var(--border);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.contact-select-item:hover {
  background: var(--glass-hover);
  border-color: var(--primary);
  transform: translateY(-2px);
}

.contact-select-item .main-avatar {
  background: var(--primary);
  color: white;
}

.tag-main {
  background: rgba(var(--primary-rgb), 0.15);
  color: var(--primary);
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 6px;
}

.contacts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
  max-height: 250px;
  overflow-y: auto;
  padding-right: 10px;
}

.contact-item-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--glass);
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.contact-info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.contact-avatar {
  width: 32px;
  height: 32px;
  background: var(--border);
  color: var(--text-primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.contact-title-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.contact-title-group strong {
  font-size: 0.95rem;
}

.contact-badges {
  display: flex;
  gap: 6px;
}

.contact-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.contact-badge.sector {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.contact-badge.role {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.contact-meta-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  padding-left: 44px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item.whatsapp {
  color: #25d366;
}

.whatsapp-icon-mini {
  fill: currentColor;
}

.contact-observation-text {
  font-size: 0.78rem;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.03);
  padding: 6px 10px;
  border-radius: 6px;
  margin-left: 44px;
  border-left: 2px solid var(--border);
}

.add-contact-form {
  border-top: 1px solid var(--border);
  padding-top: 20px;
}

.add-contact-form h4 {
  margin-bottom: 15px;
  font-size: 1rem;
}

.add-contact-form .form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 15px;
}

.add-contact-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.add-contact-form .form-group.full-width {
  grid-column: span 3;
}

.add-contact-form label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.add-contact-form .input-glass,
.add-contact-form textarea {
  width: 100% !important;
  box-sizing: border-box !important;
}

.contact-actions-mini {
  display: flex;
  gap: 8px;
}

.form-actions-row {
  display: flex;
  gap: 12px;
  margin-top: 15px;
}

.form-actions-row .block {
  margin-top: 0 !important;
  flex: 1;
}

.icon-btn.edit {
  color: var(--accent);
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.icon-btn.edit:hover {
  background: var(--accent);
  color: white;
}

.btn-primary-sm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary-sm.block { width: 100%; margin-top: 10px; }

.animate-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-mini { text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 20px; }

/* View switcher styles */
.view-switcher-toggle {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 3px;
  gap: 2px;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 8px;
  border-radius: 9px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.03);
}

.toggle-btn.active {
  color: var(--accent);
  background: rgba(16, 185, 129, 0.15);
}

/* List view table styles */
.customers-list-view {
  width: 100%;
  overflow-x: auto;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-card, rgba(255, 255, 255, 0.03));
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
}

.customers-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.9rem;
}

.customers-table th {
  padding: 16px 20px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.02);
}

.customers-table td {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  vertical-align: middle;
}

.customers-table tr:last-child td {
  border-bottom: none;
}

.customers-table tr {
  transition: background-color 0.2s ease;
}

.customers-table tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.blocked-row {
  opacity: 0.75;
  background: rgba(239, 68, 68, 0.02) !important;
}

.blocked-row:hover {
  background: rgba(239, 68, 68, 0.04) !important;
}

.table-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--brand-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
}

.table-avatar.blocked-avatar {
  background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
}

.table-customer-name {
  font-weight: 500;
}

.state-pill {
  display: inline-block;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 6px;
}

.active-badge {
  display: inline-block;
  background: rgba(16, 185, 129, 0.1);
  color: var(--accent);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.actions-col {
  text-align: right !important;
}

.table-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.table-action-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.table-action-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(16, 185, 129, 0.05);
}

.table-action-btn.delete:hover {
  color: #ef4444;
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

/* CRM Filter styles */
.filters-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
  padding: 16px 20px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg-card, rgba(255, 255, 255, 0.02));
  margin-bottom: 20px;
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
}

.btn-filter-toggle {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  height: 38px;
}

.btn-filter-toggle:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-filter-toggle.btn-filter-active {
  color: var(--accent);
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.1);
}

.filter-count-badge {
  background: var(--accent);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* Slide Fade Transition for filter drawer */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 300px;
  opacity: 1;
  overflow: hidden;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  border-top-width: 0 !important;
  border-bottom-width: 0 !important;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.select-glass {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 0.85rem;
  outline: none;
  cursor: pointer;
  min-width: 160px;
  transition: all 0.2s ease;
}

.select-glass:focus {
  border-color: var(--accent);
  background: rgba(255, 255, 255, 0.08);
}

.select-glass option {
  background: #1e1e24;
  color: white;
}

.btn-clear-filters {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 38px;
  display: flex;
  align-items: center;
}

.btn-clear-filters:hover {
  background: rgba(239, 68, 68, 0.18);
  border-color: #ef4444;
}

@media (max-width: 768px) {
  .filters-container {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  .select-glass {
    width: 100%;
  }
  .btn-clear-filters {
    justify-content: center;
  }
  .view-switcher-toggle {
    display: flex;
    width: 100%;
    justify-content: center;
  }
  .view-switcher-toggle .toggle-btn {
    flex: 1;
    justify-content: center;
  }
  .page-header {
    padding: 15px 20px;
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .search-bar {
    width: 100%;
  }
  .btn-primary {
    justify-content: center;
  }
  .content-wrapper {
    padding: 15px;
  }
  .customers-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .large-modal {
    width: 95% !important;
    height: 95vh;
  }
  .modal-form-scrollable {
    padding: 20px;
  }
  .grid-2, .grid-3, .grid-4 {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  .address-main-row {
    flex-direction: column;
    gap: 15px;
  }
  .checkbox-row {
    flex-direction: column;
    gap: 15px;
  }
  .modal-actions-container {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
    text-align: center;
  }
  .modal-actions {
    justify-content: center;
  }
  .tabs-nav {
    padding-bottom: 5px;
  }
}

.pagination-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 30px 0 10px 0;
  width: 100%;
}

.pagination-info {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.btn-load-more {
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-load-more:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

/* Loading State & Animations */
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  border-radius: 16px;
  gap: 15px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  margin-top: 20px;
}

.loading-state p {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.95rem;
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
  to {
    transform: rotate(360deg);
  }
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-fade-enter-from, .slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.input-with-button {
  display: flex;
  position: relative;
  width: 100%;
}

.input-with-button .input-glass {
  flex: 1;
  padding-right: 48px;
  width: 100%;
}

.btn-search-cnpj {
  position: absolute;
  right: 4px;
  top: 4px;
  bottom: 4px;
  width: 40px;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
}

.btn-search-cnpj:hover:not(:disabled) {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
}

.btn-search-cnpj:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-mini {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
