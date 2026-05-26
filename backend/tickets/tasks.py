from celery import shared_task
from .models import Connection, Contact, Ticket, Message
import json
import redis
from django.conf import settings
from api.serializers import MessageSerializer

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

@shared_task
def process_webhook_event(connection_id, payload):
    connection = Connection.objects.get(id=connection_id)
    company = connection.company
    
    event_type = payload.get('event')
    data = payload.get('data', {})

    if event_type == 'messages.upsert':
        # Extrair dados básicos (Simplificado para o exemplo)
        remote_jid = data.get('key', {}).get('remoteJid')
        body = data.get('message', {}).get('conversation') or data.get('message', {}).get('extendedTextMessage', {}).get('text')
        message_id = data.get('key', {}).get('id')
        from_me = data.get('key', {}).get('fromMe', False)

        if not body: return
        if not remote_jid or 'status@broadcast' in str(remote_jid) or '@g.us' in str(remote_jid):
            return

        # 1. Obter ou criar contato
        contact, _ = Contact.objects.get_or_create(
            company=company,
            remote_jid=remote_jid,
            defaults={'name': data.get('pushName', remote_jid)}
        )

        # 2. Obter ou criar ticket aberto
        ticket = Ticket.objects.filter(
            company=company,
            contact=contact,
            status__in=['open', 'pending']
        ).order_by('-id').first()

        if not ticket:
            status = 'closed' if from_me else 'open'
            ticket = Ticket.objects.create(
                company=company,
                contact=contact,
                status=status,
                last_message=body
            )
        else:
            ticket.last_message = body
            ticket.save()

        # 3. Salvar mensagem
        msg, msg_created = Message.objects.get_or_create(
            message_id=message_id,
            defaults={
                'ticket': ticket,
                'from_me': from_me,
                'body': body
            }
        )

        # 4. Notificar Realtime
        if msg_created:
            event_payload = {
                "company_id": str(company.id),
                "type": "new_message",
                "payload": MessageSerializer(msg).data
            }
            redis_client.publish('company_events', json.dumps(event_payload))

@shared_task
def send_wa_message_task(ticket_id, body):
    # Aqui chamaria a Evolution API via requests.post
    # connection = connection_da_empresa
    # requests.post(f"{EVOLUTION_URL}/message/sendText/{instance}", ...)
    pass

@shared_task
def send_broadcast_task(company_id, connection_id, user_id, phones, message):
    from tickets.models import Connection, User, Contact, Ticket, Message
    import requests
    import time
    import uuid
    from django.conf import settings
    from api.serializers import MessageSerializer
    
    try:
        connection = Connection.objects.get(id=connection_id)
        user = User.objects.get(id=user_id)
        company = connection.company
        
        # Obter Token
        evo_token = company.evolution_api_key or settings.EVOLUTION_API_KEY
        try:
            import psycopg2
            import os
            db_pass = os.environ.get('DB_PASSWORD', 'postgres')
            db_host = os.environ.get('DB_HOST', 'db')
            conn = psycopg2.connect(dbname="evogo_users", user="postgres", password=db_pass, host=db_host)
            cur = conn.cursor()
            cur.execute("SELECT token FROM instances WHERE name = %s;", (connection.instance_name,))
            row = cur.fetchone()
            if row: evo_token = row[0]
            cur.close()
            conn.close()
        except: pass
        
        evo_url = "http://evolution-go:8080"
        evo_key = evo_token
        
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_key,
            "Authorization": f"Bearer {evo_key}"
        }
        
        for phone in phones:
            clean_number = phone.strip().replace('+', '').replace(' ', '').replace('-', '')
            # Enviar para a Evolution
            url = f"{evo_url}/send/text?apikey={evo_key}&instance={connection.instance_name}"
            payload = {
                "instance": connection.instance_name,
                "number": clean_number,
                "text": message
            }
            
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=5)
                # Criar ticket se não existir e salvar mensagem
                remote_jid = f"{clean_number}@s.whatsapp.net"
                contact, _ = Contact.objects.get_or_create(
                    company=company,
                    remote_jid=remote_jid,
                    defaults={'name': clean_number}
                )
                
                ticket, _ = Ticket.objects.get_or_create(
                    company=company,
                    contact=contact,
                    status='open',
                    defaults={'user': user, 'last_message': message}
                )
                
                ticket.last_message = message
                ticket.save()
                
                temp_id = f"broadcast_{ticket.id}_{int(time.time() * 1000)}"
                msg_id = temp_id
                if res.status_code in [200, 201]:
                    msg_id = res.json().get('key', {}).get('id', temp_id)
                    
                msg = Message.objects.create(
                    ticket=ticket,
                    user=user,
                    from_me=True,
                    body=message,
                    message_id=msg_id
                )
                
                # Notificar UI via Redis Pub/Sub
                event_payload = {
                    "company_id": str(company.id),
                    "type": "new_message",
                    "payload": MessageSerializer(msg).data
                }
                redis_client.publish('company_events', json.dumps(event_payload))
                
            except Exception as e:
                print(f"Erro ao enviar broadcast para {phone}: {e}")
                
            # Evitar rate limiting do WhatsApp
            time.sleep(1.5)
            
    except Exception as err:
        print(f"Erro geral no broadcast: {err}")


@shared_task
def reset_company_conversations_task(company_id):
    from tickets.models import Company
    from django.db import connection as db_connection
    
    try:
        company = Company.objects.get(id=company_id)
        print(f"[RESET TASK] Starting reset for company: {company.name} ({company_id})")
        
        with db_connection.cursor() as cursor:
            # 1. Delete all messages from tickets belonging to the company
            cursor.execute("""
                DELETE FROM tickets_message 
                WHERE ticket_id IN (
                    SELECT id FROM tickets_ticket WHERE company_id = %s
                )
            """, [str(company_id)])
            
            # 2. Delete all tickets belonging to the company
            cursor.execute("""
                DELETE FROM tickets_ticket 
                WHERE company_id = %s
            """, [str(company_id)])
            
        print(f"[RESET TASK] Reset completed successfully for company {company.name}")
        
        # Publish real-time event to reset UI for all logged-in users of the company
        try:
            event_payload = {
                "company_id": str(company_id),
                "type": "reset_conversations",
                "payload": {}
            }
            redis_client.publish('company_events', json.dumps(event_payload))
        except Exception as redis_err:
            print(f"[RESET TASK] Error publishing redis event: {redis_err}")
            
    except Exception as e:
        print(f"[RESET TASK] ERROR: {str(e)}")


