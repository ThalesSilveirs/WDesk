<template>
  <div class="cities-page-container animate-fade-in">
    <main class="main-content">
      <!-- Cabeçalho -->
      <header class="page-header glass-effect">
        <div class="header-info">
          <div style="display: flex; align-items: center; gap: 12px;">
            <MapPinIcon :size="28" style="color: var(--accent);" />
            <h1>Cidades (IBGE)</h1>
          </div>
          <p>Gerencie cidades e códigos IBGE para vinculação aos clientes</p>
        </div>
        <div class="header-actions">
          <div class="search-bar">
            <SearchIcon :size="20" />
            <input v-model="searchQuery" placeholder="Filtrar por nome ou código..." type="text" />
          </div>
          <button @click="syncWithIBGE" class="btn-secondary" :disabled="syncing" style="display: flex; align-items: center; gap: 8px;">
            <RefreshCwIcon v-if="!syncing" :size="20" />
            <span v-else class="spinner-mini"></span>
            {{ syncing ? 'Sincronizando...' : 'Sincronizar IBGE' }}
          </button>
          <button @click="openNewCityForm" class="btn-primary">
            <PlusIcon :size="20" /> Nova Cidade
          </button>
        </div>
      </header>

      <!-- Conteúdo Principal -->
      <div class="content-body">
        <!-- Form de Inclusão/Edição (Modal ou Box Destacado) -->
        <Transition name="modal-fade">
          <div v-if="showCityForm" class="modal-overlay" @click="closeCityForm">
            <div class="modal-content glass-effect" @click.stop>
              <div class="modal-header">
                <h2>{{ editingCityId ? 'Editar Cidade' : 'Nova Cidade' }}</h2>
                <button @click="closeCityForm" class="close-btn">&times;</button>
              </div>
              <div class="modal-body">
                <div class="form-group">
                  <label>Nome da Cidade *</label>
                  <input 
                    v-model="cityForm.name" 
                    type="text" 
                    placeholder="Ex: São Paulo"
                    class="input-glass premium-input"
                    required
                  />
                </div>
                <div class="form-group">
                  <label>UF (Estado) *</label>
                  <input 
                    v-model="cityForm.state" 
                    type="text" 
                    placeholder="Ex: SP"
                    maxlength="2"
                    class="input-glass premium-input"
                    style="text-transform: uppercase;"
                    required
                  />
                </div>
                <div class="form-group">
                  <label>Código IBGE *</label>
                  <input 
                    v-model="cityForm.ibge_code" 
                    type="text" 
                    placeholder="Ex: 3550308"
                    maxlength="7"
                    class="input-glass premium-input"
                    required
                  />
                </div>
              </div>
              <div class="modal-footer">
                <button @click="saveCity" class="btn-primary" :disabled="savingCity">
                  <CheckIcon :size="16" /> {{ savingCity ? 'Salvando...' : 'Salvar' }}
                </button>
                <button @click="closeCityForm" class="btn-secondary" :disabled="savingCity">
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Listagem de Cidades -->
        <div class="table-container glass-effect">
          <div v-if="filteredCities.length === 0" class="empty-state">
            <MapPinIcon :size="48" style="opacity: 0.3; margin-bottom: 15px;" />
            <p>Nenhuma cidade cadastrada ou encontrada para o filtro.</p>
          </div>
          <table v-else class="premium-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Estado (UF)</th>
                <th>Código IBGE</th>
                <th style="text-align: right;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="city in filteredCities" :key="city.id">
                <td style="font-weight: 600; color: var(--text-primary);">{{ city.name }}</td>
                <td><span class="state-pill">{{ city.state }}</span></td>
                <td><code>{{ city.ibge_code }}</code></td>
                <td style="text-align: right;">
                  <div style="display: flex; justify-content: flex-end; gap: 8px;">
                    <button @click="editCity(city)" class="action-icon-btn edit" title="Editar">
                      <EditIcon :size="16" />
                    </button>
                    <button @click="deleteCity(city.id)" class="action-icon-btn delete" title="Apagar">
                      <TrashIcon :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useChatStore } from '../store/chat'
import { 
  MapPin as MapPinIcon, 
  Plus as PlusIcon, 
  Search as SearchIcon, 
  Edit as EditIcon, 
  Trash as TrashIcon, 
  Check as CheckIcon,
  RefreshCw as RefreshCwIcon
} from 'lucide-vue-next'

const chatStore = useChatStore()

const citiesList = ref([])
const searchQuery = ref('')
const showCityForm = ref(false)
const editingCityId = ref(null)
const savingCity = ref(false)
const cityForm = ref({
  name: '',
  state: '',
  ibge_code: ''
})

const fetchCitiesList = async () => {
  try {
    citiesList.value = await chatStore.fetchCities()
  } catch (e) {
    console.error("Erro ao buscar cidades", e)
  }
}

const syncing = ref(false)

const syncWithIBGE = async () => {
  if (!confirm("Isso irá apagar todas as cidades cadastradas atualmente e reimportar a base completa de municípios do IBGE (mais de 5.500 registros). Deseja prosseguir?")) {
    return
  }
  syncing.value = true
  try {
    const response = await axios.post('/api/v1/cities/sync-ibge/')
    alert(`Importação concluída com sucesso! ${response.data.count} cidades cadastradas.`)
    await fetchCitiesList()
  } catch (err) {
    console.error("Erro ao sincronizar cidades com o IBGE", err)
    const errorMsg = err.response?.data?.error || "Erro na sincronização."
    alert(errorMsg)
  } finally {
    syncing.value = false
  }
}

const filteredCities = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return citiesList.value
  return citiesList.value.filter(city => 
    city.name.toLowerCase().includes(query) || 
    city.state.toLowerCase().includes(query) || 
    city.ibge_code.includes(query)
  )
})

const openNewCityForm = () => {
  editingCityId.value = null
  cityForm.value = { name: '', state: '', ibge_code: '' }
  showCityForm.value = true
}

const editCity = (city) => {
  editingCityId.value = city.id
  cityForm.value = { name: city.name, state: city.state, ibge_code: city.ibge_code }
  showCityForm.value = true
}

const closeCityForm = () => {
  showCityForm.value = false
}

const saveCity = async () => {
  if (!cityForm.value.name || !cityForm.value.state || !cityForm.value.ibge_code) {
    alert("Preencha todos os campos obrigatórios")
    return
  }
  
  savingCity.value = true
  try {
    cityForm.value.state = cityForm.value.state.toUpperCase()
    if (editingCityId.value) {
      await chatStore.updateCity(editingCityId.value, cityForm.value)
    } else {
      await chatStore.createCity(cityForm.value)
    }
    await fetchCitiesList()
    showCityForm.value = false
  } catch (e) {
    console.error("Erro ao salvar cidade", e)
    alert("Erro ao salvar cidade. Verifique se o código IBGE já está cadastrado.")
  } finally {
    savingCity.value = false
  }
}

const deleteCity = async (id) => {
  if (confirm("Tem certeza que deseja excluir esta cidade?")) {
    try {
      await chatStore.deleteCity(id)
      await fetchCitiesList()
    } catch (e) {
      alert("Erro ao excluir cidade")
    }
  }
}

onMounted(() => {
  fetchCitiesList()
})
</script>

<style scoped>
.cities-page-container {
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
  padding: 30px;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-radius: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  margin-bottom: 25px;
}

.header-info h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.search-bar {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px 16px;
  width: 320px;
  transition: all 0.3s;
}

.search-bar:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(34, 181, 95, 0.15);
}

.search-bar input {
  background: none;
  border: none;
  color: var(--text-primary);
  margin-left: 10px;
  width: 100%;
  font-size: 0.95rem;
  outline: none;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 12px rgba(34, 181, 95, 0.2);
}

.btn-primary:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.content-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-container {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  overflow-x: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.premium-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.premium-table th {
  padding: 14px 16px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}

.premium-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  font-size: 0.95rem;
}

.premium-table tr:last-child td {
  border-bottom: none;
}

.state-pill {
  background: rgba(34, 181, 95, 0.1);
  color: var(--accent);
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.8rem;
  display: inline-block;
}

.action-icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.action-icon-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.action-icon-btn.edit:hover {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.action-icon-btn.delete:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--text-secondary);
  text-align: center;
}

/* Modais */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--border);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.input-glass {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text-primary);
  outline: none;
  font-size: 0.95rem;
  transition: all 0.3s;
}

.input-glass:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(34, 181, 95, 0.15);
}

/* Transições */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.spinner-mini {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
