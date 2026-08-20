#!/bin/bash
# Script para coletar status, logs e estado do repositório remoto git

KEY_PATH="${SSH_KEY_PATH:-/home/thalessilveirs/.ssh/id_ed25519}"
IP="${REMOTE_IP:-177.153.35.98}"
USER="${REMOTE_USER:-root}"
OUTPUT_FILE="/home/thalessilveirs/WDesk/remote_status.log"

echo "=== INICIANDO COLETA DE STATUS REMOTO ===" > "$OUTPUT_FILE"
date >> "$OUTPUT_FILE"

echo -e "\n=== 1. ÚLTIMAS MENSAGENS COM DETALHES DE MÍDIA ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose exec -T backend python manage.py shell -c \"
from tickets.models import Message
for m in Message.objects.all().order_by('-timestamp')[:15]:
    body_str = m.body[:40] if m.body else ''
    url_str = m.media_url[:40] + '...' if m.media_url else 'None'
    print(f'Msg: {body_str} | De mim: {m.from_me} | Tipo: {m.media_type} | URL: {url_str} | Data: {m.timestamp}')
\"" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 2. LOGS DO BACKEND COM FOCO EM MÍDIA (ÚLTIMAS 150 LINHAS) ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose logs backend --tail 150" >> "$OUTPUT_FILE" 2>&1

echo -e "\n=== 3. LOGS DO EVOLUTION GO COM FOCO EM MÍDIA (ÚLTIMAS 150 LINHAS) ===" >> "$OUTPUT_FILE"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$USER@$IP" "cd ~/WDesk && docker compose logs evolution-go --tail 150" >> "$OUTPUT_FILE" 2>&1

echo "=== COLETA CONCLUÍDA ===" >> "$OUTPUT_FILE"
echo "Status salvo em $OUTPUT_FILE"
