#!/bin/bash
# Script para coletar status, logs e estado do repositório remoto git

KEY_PATH="/home/thalessilveirs/Documentos/wdesk.key"
IP="163.176.157.42"
USER="ubuntu"
OUTPUT_FILE="/home/thalessilveirs/WDesk/remote_status.log"

echo "=== INICIANDO COLETA DE STATUS REMOTO ===" > "$OUTPUT_FILE"
date >> "$OUTPUT_FILE"

echo -e "\n=== 1. GIT STATUS E BRANCH ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && git status" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 2. GIT DIFF ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && git diff" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 3. CHAT.JS REMOTE CONTENT ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && grep -n 'socketUrl' frontend/src/store/chat.js" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 4. DOCKER PS ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "docker ps" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 5. CONEXÕES NO BANCO DE DADOS DJANGO ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose exec -T backend python manage.py shell -c \"
from tickets.models import Connection
for c in Connection.objects.all():
    print(f'Instancia: {c.instance_name} | Status: {c.status} | Token: {c.company.evolution_api_key}')
\"" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 6. ÚLTIMAS MENSAGENS COM TIMESTAMP ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose exec -T backend python manage.py shell -c \"
from tickets.models import Message
for m in Message.objects.all().order_by('-timestamp')[:10]:
    print(f'Msg: {m.body[:50]} | De mim: {m.from_me} | Data: {m.timestamp} | Contato: {m.ticket.contact.name} ({m.ticket.contact.remote_jid})')
\"" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 7. LOGS RECENTES DO BACKEND (ÚLTIMAS 200 LINHAS) ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose logs backend --tail 200" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 8. LOGS RECENTES DA EVOLUTION GO (ÚLTIMAS 200 LINHAS) ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose logs evolution-go --tail 200" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 9. LOGS RECENTES DO NGINX (ÚLTIMAS 100 LINHAS) ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose logs nginx --tail 100" >> "$OUTPUT_FILE" 2>&1

echo "=== COLETA CONCLUÍDA ===" >> "$OUTPUT_FILE"
echo "Status salvo em $OUTPUT_FILE"
