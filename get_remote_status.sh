#!/bin/bash
# Script para coletar status, logs do sistema, diagnósticos e estado dos containers

KEY_PATH="${SSH_KEY_PATH:-/home/thalessilveirs/.ssh/id_ed25519}"
IP="${REMOTE_IP:-177.153.35.98}"
USER="${REMOTE_USER:-root}"
OUTPUT_FILE="/home/thalessilveirs/WDesk/remote_status.log"

echo "=== INICIANDO COLETA DE STATUS REMOTO ===" > "$OUTPUT_FILE"
date >> "$OUTPUT_FILE"

run_remote() {
    local title="$1"
    local cmd="$2"
    echo -e "\n=== $title ===" >> "$OUTPUT_FILE"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "$cmd" >> "$OUTPUT_FILE" 2>&1
}

# 1. Recursos do Sistema e Uptime
run_remote "1. RECURSOS DO SISTEMA (UPTIME, RAM E DISCO)" '
echo "--- UPTIME E LOAD AVERAGE ---"
uptime
echo -e "\n--- MEMÓRIA RAM & SWAP (free -h) ---"
free -h
echo -e "\n--- ESPAÇO EM DISCO (df -h) ---"
df -h
'

# 2. Verificação de OOM Killer e Erros Críticos do Kernel/Sistema
run_remote "2. EVENTOS DE OOM KILLER / ERROS DO KERNEL (dmesg / journalctl)" '
echo "--- EVENTOS OOM (Out Of Memory) NO DMESG ---"
dmesg -T | grep -i -E "oom|killed process|out of memory|segfault" | tail -n 30 || echo "Nenhum evento de OOM recente no buffer do dmesg."
echo -e "\n--- ERROS DO BOOT ATUAL/ANTERIOR (journalctl) ---"
journalctl -p err..emerg --no-pager -n 40
'

# 3. Status dos Containers Docker
run_remote "3. STATUS DOS CONTAINERS DOCKER (docker compose ps)" '
cd ~/WDesk && docker compose ps
'

# 4. Conexões Ativas no Banco de Dados Postgres
run_remote "4. CONEXÕES ATIVAS NO POSTGRESQL" '
cd ~/WDesk && docker compose exec -T db psql -U postgres -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;" || echo "Não foi possível consultar pg_stat_activity"
'

# 5. Logs do Banco de Dados (Postgres)
run_remote "5. LOGS DO BANCO DE DADOS (db - últimas 100 linhas)" '
cd ~/WDesk && docker compose logs db --tail 100
'

# 6. Logs do Backend (Django / Gunicorn)
run_remote "6. LOGS DO BACKEND (backend - últimas 150 linhas)" '
cd ~/WDesk && docker compose logs backend --tail 150
'

# 7. Logs do Worker (Celery)
run_remote "7. LOGS DO CELERY WORKER (worker - últimas 150 linhas)" '
cd ~/WDesk && docker compose logs worker --tail 150
'

# 8. Logs do Evolution GO
run_remote "8. LOGS DO EVOLUTION GO (evolution-go - últimas 150 linhas)" '
cd ~/WDesk && docker compose logs evolution-go --tail 150
'

# 9. Logs do Redis
run_remote "9. LOGS DO REDIS (redis - últimas 80 linhas)" '
cd ~/WDesk && docker compose logs redis --tail 80
'

# 10. Logs do Nginx (erros 50x / rate limit)
run_remote "10. LOGS DO NGINX (nginx - últimas 100 linhas)" '
cd ~/WDesk && docker compose logs nginx --tail 100
'

# 11. Últimas Mensagens no Banco
run_remote "11. ÚLTIMAS MENSAGENS REGISTRADAS NO BANCO" '
cd ~/WDesk && docker compose exec -T backend python manage.py shell -c "
from tickets.models import Message
for m in Message.objects.all().order_by(\"-timestamp\")[:10]:
    body_str = m.body[:40] if m.body else \"\"
    url_str = m.media_url[:40] + \"...\" if m.media_url else \"None\"
    print(f\"Msg: {body_str} | De mim: {m.from_me} | Tipo: {m.media_type} | URL: {url_str} | Data: {m.timestamp}\")
" || echo "Falha ao consultar mensagens"
'

echo -e "\n=== COLETA CONCLUÍDA ===" >> "$OUTPUT_FILE"
echo "Status e diagnóstico completos salvos em $OUTPUT_FILE"
