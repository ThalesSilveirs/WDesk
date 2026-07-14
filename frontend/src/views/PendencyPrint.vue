<template>
  <div class="print-page-container">
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Carregando dados para impressão...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <h2>Erro ao carregar a pendência</h2>
      <p>{{ error }}</p>
      <button @click="goBack" class="no-print btn-secondary">Voltar</button>
    </div>

    <div v-else class="print-content">
      <!-- Barra de Ações (Oculta na impressão) -->
      <div class="print-actions-bar no-print">
        <button @click="goBack" class="btn-secondary">Voltar</button>
        <button @click="triggerPrint" class="btn-primary">Imprimir / Salvar PDF</button>
      </div>

      <!-- Cabeçalho do Relatório -->
      <header class="report-header">
        <div class="company-brand">
          <h1>WDesk</h1>
          <p class="subtitle">Sistema de Gestão & CRM</p>
        </div>
        <div class="report-title">
          <h2>Relatório de Pendência #{{ pendency.id }}</h2>
          <p>Gerado em {{ currentDateTime }}</p>
        </div>
      </header>

      <!-- Metadados da Pendência -->
      <section class="metadata-section">
        <h3 class="section-title">Dados Gerais</h3>
        <div class="metadata-grid">
          <div class="meta-item">
            <strong>Título/Assunto:</strong>
            <span>{{ pendency.title }}</span>
          </div>
          <div class="meta-item">
            <strong>Tipo de Operação:</strong>
            <span>{{ operationTypes[pendency.operation_type] || pendency.operation_type }}</span>
          </div>
          <div class="meta-item">
            <strong>Prioridade:</strong>
            <span class="badge" :class="pendency.priority">{{ priorityLabels[pendency.priority] || pendency.priority }}</span>
          </div>
          <div class="meta-item">
            <strong>Status:</strong>
            <span class="badge" :class="pendency.status">{{ statusLabels[pendency.status] || pendency.status }}</span>
          </div>
          <div class="meta-item">
            <strong>Cliente:</strong>
            <span>{{ pendency.customer_details?.name || 'Não vinculado' }}</span>
          </div>
          <div class="meta-item">
            <strong>Contato:</strong>
            <span>{{ pendency.contact_details?.name || pendency.contact_details?.remote_jid || 'Não vinculado' }}</span>
          </div>
          <div class="meta-item">
            <strong>Responsável:</strong>
            <span>{{ pendency.user_details ? `${pendency.user_details.first_name || ''} ${pendency.user_details.last_name || ''}`.trim() || pendency.user_details.username : 'Não atribuído' }}</span>
          </div>
          <div class="meta-item">
            <strong>Data de Abertura:</strong>
            <span>{{ formatDateTime(pendency.opening_date) }}</span>
          </div>
          <div class="meta-item">
            <strong>Previsão de Entrega:</strong>
            <span>{{ pendency.forecast_date ? formatDateTime(pendency.forecast_date) : 'Não informada' }}</span>
          </div>
          <div class="meta-item">
            <strong>Última Atualização:</strong>
            <span>{{ formatDateTime(pendency.updated_at) }}</span>
          </div>
        </div>
      </section>

      <!-- Descrição da Pendência -->
      <section class="description-section">
        <h3 class="section-title">Descrição dos Dados / Detalhes</h3>
        <div class="description-content">
          <p>{{ pendency.description || 'Sem descrição detalhada registrada.' }}</p>
        </div>
      </section>

      <!-- Histórico de Movimentações -->
      <section class="movements-section">
        <h3 class="section-title">Histórico de Movimentações</h3>
        <div v-if="!pendency.movements || pendency.movements.length === 0" class="no-data">
          Nenhuma movimentação registrada para esta pendência até o momento.
        </div>
        <table v-else class="movements-table">
          <thead>
            <tr>
              <th style="width: 20%;">Data/Hora</th>
              <th style="width: 25%;">Responsável</th>
              <th style="width: 55%;">Histórico da Movimentação</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in sortedMovements" :key="m.id">
              <td class="date-cell">{{ formatDateTime(m.created_at) }}</td>
              <td class="user-cell">
                {{ m.user_details ? `${m.user_details.first_name || ''} ${m.user_details.last_name || ''}`.trim() || m.user_details.username : 'Sistema' }}
              </td>
              <td class="desc-cell">{{ m.description }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Assinatura / Rodapé de Controle -->
      <footer class="report-footer">
        <div class="signature-line">
          <div class="signature-box">
            <div class="line"></div>
            <p>Responsável pelo Atendimento</p>
          </div>
          <div class="signature-box">
            <div class="line"></div>
            <p>Assinatura do Cliente (Se aplicável)</p>
          </div>
        </div>
        <p class="footer-note">WDesk ERP - Documento gerado eletronicamente para fins de acompanhamento.</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const pendency = ref(null)

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
  pending: 'Pendente',
  closed: 'Finalizada'
}

const currentDateTime = computed(() => {
  return new Date().toLocaleString('pt-BR')
})

const sortedMovements = computed(() => {
  if (!pendency.value?.movements) return []
  // Ordem cronológica (mais antiga para mais recente)
  return [...pendency.value.movements].sort((a, b) => {
    return new Date(a.created_at) - new Date(b.created_at)
  })
})

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

const goBack = () => {
  router.back()
}

const triggerPrint = () => {
  window.print()
}

onMounted(async () => {
  try {
    const res = await axios.get(`/api/v1/pendencies/${route.params.id}/`)
    pendency.value = res.data
    loading.value = false
    
    // Dispara a impressão automaticamente logo após o carregamento
    setTimeout(() => {
      window.print()
    }, 500)
  } catch (err) {
    console.error('Erro ao buscar pendência:', err)
    error.value = 'Não foi possível carregar os dados desta pendência. Verifique se o ID está correto ou se você está logado.'
    loading.value = false
  }
})
</script>

<style scoped>
/* Estilos para a página em modo web */
.print-page-container {
  min-height: 100vh;
  background-color: #f4f4f5;
  color: #18181b;
  padding: 40px 20px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  display: flex;
  justify-content: center;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  max-width: 400px;
  width: 100%;
  text-align: center;
  height: fit-content;
  margin-top: 100px;
}

.spinner {
  border: 4px solid rgba(0,0,0,0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #10b981;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.print-content {
  background: white;
  max-width: 800px;
  width: 100%;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* Barra de Ações superior */
.print-actions-bar {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #e4e4e7;
  padding-bottom: 20px;
}

.btn-primary, .btn-secondary {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: #10b981;
  color: white;
}

.btn-primary:hover {
  background-color: #059669;
}

.btn-secondary {
  background-color: #e4e4e7;
  color: #27272a;
}

.btn-secondary:hover {
  background-color: #d4d4d8;
}

/* Cabeçalho do Relatório */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid #18181b;
  padding-bottom: 15px;
}

.company-brand h1 {
  font-size: 2rem;
  font-weight: 800;
  color: #18181b;
  margin: 0;
  line-height: 1;
}

.company-brand .subtitle {
  font-size: 0.85rem;
  color: #71717a;
  margin: 4px 0 0 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.report-title {
  text-align: right;
}

.report-title h2 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.report-title p {
  font-size: 0.85rem;
  color: #71717a;
  margin: 4px 0 0 0;
}

/* Seções */
.section-title {
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  border-bottom: 1px solid #d4d4d8;
  padding-bottom: 6px;
  margin-top: 0;
  margin-bottom: 15px;
  color: #18181b;
  letter-spacing: 0.5px;
}

/* Metadados */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 24px;
}

.meta-item {
  display: flex;
  font-size: 0.9rem;
}

.meta-item strong {
  width: 140px;
  flex-shrink: 0;
  color: #52525b;
}

.meta-item span {
  color: #18181b;
}

.badge {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 4px;
  display: inline-block;
}

.badge.high { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
.badge.medium { background-color: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
.badge.low { background-color: #d1fae5; color: #047857; border: 1px solid #6ee7b7; }

.badge.open { background-color: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
.badge.pending { background-color: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
.badge.closed { background-color: #d1fae5; color: #047857; border: 1px solid #6ee7b7; }

/* Descrição */
.description-content {
  background-color: #f8f8fa;
  padding: 15px;
  border-radius: 6px;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  color: #27272a;
  border: 1px solid #e4e4e7;
}

/* Movimentações */
.no-data {
  font-size: 0.9rem;
  color: #71717a;
  font-style: italic;
  padding: 10px 0;
}

.movements-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 0.85rem;
}

.movements-table th {
  background-color: #f4f4f5;
  border-bottom: 2px solid #d4d4d8;
  color: #27272a;
  font-weight: 700;
  text-align: left;
  padding: 8px 12px;
}

.movements-table td {
  border-bottom: 1px solid #e4e4e7;
  padding: 10px 12px;
  vertical-align: top;
  line-height: 1.4;
  color: #27272a;
}

.date-cell {
  white-space: nowrap;
  font-weight: 600;
  color: #52525b;
}

.user-cell {
  font-weight: 600;
}

.desc-cell {
  white-space: pre-wrap;
}

/* Rodapé e Assinaturas */
.report-footer {
  margin-top: 20px;
  border-top: 1px solid #e4e4e7;
  padding-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.signature-line {
  display: flex;
  justify-content: space-between;
  gap: 40px;
}

.signature-box {
  flex: 1;
  text-align: center;
}

.signature-box .line {
  border-bottom: 1px solid #71717a;
  height: 40px;
  margin-bottom: 8px;
}

.signature-box p {
  font-size: 0.8rem;
  color: #52525b;
  margin: 0;
}

.footer-note {
  font-size: 0.75rem;
  color: #a1a1aa;
  text-align: center;
  margin: 0;
}

/* CSS de Impressão */
@media print {
  body {
    background-color: white;
    color: black;
  }
  
  .print-page-container {
    background-color: white;
    padding: 0;
  }
  
  .print-content {
    box-shadow: none;
    padding: 0;
    max-width: 100%;
  }

  .no-print {
    display: none !important;
  }

  /* Garantir que tabelas e seções quebrem página de forma elegante */
  .metadata-section, .description-section, .movements-section, .report-footer {
    page-break-inside: avoid;
  }

  .movements-table tr {
    page-break-inside: avoid;
  }
}
</style>
