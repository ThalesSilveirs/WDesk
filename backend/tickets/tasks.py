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

        # 1. Obter ou criar contato
        contact, _ = Contact.objects.get_or_create(
            company=company,
            remote_jid=remote_jid,
            defaults={'name': data.get('pushName', remote_jid)}
        )

        # 2. Obter ou criar ticket aberto
        ticket, created = Ticket.objects.get_or_create(
            company=company,
            contact=contact,
            status='open',
            defaults={'last_message': body}
        )
        
        if not created:
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
