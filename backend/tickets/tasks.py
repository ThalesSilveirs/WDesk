from celery import shared_task
from .models import Connection, Contact, Ticket, Message, Customer, CustomerContact
import json
import redis
from django.conf import settings
from api.serializers import MessageSerializer

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60
)
def process_webhook_event(self, connection_id, payload):
    import re
    import time
    import json
    import requests
    import uuid
    import os
    from django.db import transaction
    from django.utils import timezone
    from django.db.models import Q
    from tickets.models import Connection, Contact, Ticket, Message, Customer, CustomerContact, MessageReaction, User
    from api.serializers import MessageSerializer, TicketSerializer, ConnectionSerializer

    try:
        connection = Connection.objects.select_related('company').get(id=connection_id)
    except Connection.DoesNotExist:
        print(f"[WEBHOOK TASK] Conexão {connection_id} não encontrada.")
        return

    company = connection.company
    data = payload
    event_type = str(data.get('event') or data.get('eventType') or '').lower().replace('_', '.')
    
    # Evolution GO envia payloads sem o campo 'event'.
    # Detecta o formato pelo conteúdo de 'data': se tiver 'Info' ou 'Message', é uma mensagem.
    payload_data_peek = data.get('data', {})
    if not event_type and isinstance(payload_data_peek, dict):
        if 'Info' in payload_data_peek or 'Message' in payload_data_peek:
            event_type = 'message'
            print(f"[WEBHOOK TASK] Detectado formato Evolution GO (sem campo 'event'). Tratando como mensagem.")
    
    # Busca exaustiva pelo nome da instância em todos os campos possíveis
    instance_name = (
        data.get('instance') or
        data.get('instanceName') or
        data.get('instance_name') or
        data.get('data', {}).get('instance') or
        data.get('data', {}).get('instanceName') or
        data.get('sender')
    )
    
    print(f"[WEBHOOK TASK] Processando evento: {event_type} | Instância: {instance_name}")
    
    # Tratamento de Status da Conexão
    if event_type in ['connection.update', 'connection_update']:
        payload_data = data.get('data', {})
        state = payload_data.get('state') or payload_data.get('status')
        
        state = str(state).lower()
        
        if state in ['open', 'connected', 'online']:
            connection.status = 'connected'
            connection.qrcode = None
        elif state in ['close', 'disconnected', 'refused', 'logout']:
            connection.status = 'disconnected'
        elif state in ['connecting', 'qrcode', 'pairing']:
            connection.status = 'connecting'
        
        connection.save()
        
        # Notificar Realtime
        event_payload = {
            "company_id": str(connection.company.id),
            "type": "connection_update",
            "payload": ConnectionSerializer(connection).data
        }
        from django.core.serializers.json import DjangoJSONEncoder
        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
        print(f"[WEBHOOK TASK] Status da Instância {instance_name} atualizado para {connection.status}")
        return

    # Tratamento de Mensagens Editadas
    if event_type in ['messages.edited', 'messages_edited', 'message_edited', 'message.edited', 'messages.update', 'messages_update']:
        payload_data = data.get('data', {})
        info = payload_data.get('key', {}) or {}
        
        update_data = payload_data.get('update', {}) or {}
        edited_msg = payload_data.get('editedMessage') or \
                     payload_data.get('message') or \
                     update_data.get('message') or \
                     update_data.get('editedMessage')
        
        new_body = ""
        msg_id = None
        
        if isinstance(edited_msg, dict):
            protocol_msg = edited_msg.get('protocolMessage') or {}
            if protocol_msg:
                msg_id = protocol_msg.get('key', {}).get('id')
                edited_payload = protocol_msg.get('editedMessage') or {}
                if isinstance(edited_payload, dict):
                    new_body = edited_payload.get('conversation') or \
                               edited_payload.get('extendedTextMessage', {}).get('text') or \
                               edited_payload.get('text')
            
            if not new_body:
                new_body = edited_msg.get('conversation') or \
                           edited_msg.get('extendedTextMessage', {}).get('text') or \
                           payload_data.get('text')
        elif isinstance(edited_msg, str):
            new_body = edited_msg
            
        if not msg_id:
            msg_id = info.get('id') or info.get('ID') or payload_data.get('messageId')
        
        if msg_id and new_body:
            message = Message.objects.filter(message_id=msg_id, ticket__company=connection.company).first()
            if message:
                message.body = new_body
                message.is_edited = True
                message.edited_at = timezone.now()
                message.save()
                
                ticket = message.ticket
                last_msg = ticket.messages.order_by('-timestamp', '-id').first()
                if last_msg and last_msg.id == message.id:
                    ticket.last_message = new_body
                    ticket.save()
                    
                    ticket_payload = {
                        "company_id": str(ticket.company.id),
                        "type": "ticket_updated",
                        "payload": TicketSerializer(ticket).data
                    }
                    from django.core.serializers.json import DjangoJSONEncoder
                    redis_client.publish('company_events', json.dumps(ticket_payload, cls=DjangoJSONEncoder))
                
                event_payload = {
                    "company_id": str(ticket.company.id),
                    "type": "message_updated",
                    "payload": MessageSerializer(message).data
                }
                from django.core.serializers.json import DjangoJSONEncoder
                redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
        return

    # Aceita formatos variados
    msg_events = ['message', 'messages.upsert', 'messages_upsert', 'message_upsert', 'message.upsert', 'groupinfo', 'group.info']
    if event_type in msg_events:
        payload_data = data.get('data', {})
        messages_list = payload_data.get('messages')
        if not messages_list:
            messages_list = [payload_data] if isinstance(payload_data, dict) else []
        
        for msg_item in messages_list:
            if not msg_item: continue
            
            info = msg_item.get('Info', {}) or msg_item.get('key', {}) or {}
            message_content = msg_item.get('Message', {}) or msg_item.get('message', {}) or {}
            
            # --- DETECTAR EDIÇÃO (CLIENT-SIDE) ---
            protocol_msg = message_content.get('protocolMessage') or {}
            if protocol_msg.get('type') == 14 or 'editedMessage' in protocol_msg:
                target_msg_id = protocol_msg.get('key', {}).get('id')
                edited_payload = protocol_msg.get('editedMessage') or {}
                new_body = ""
                if isinstance(edited_payload, dict):
                    new_body = edited_payload.get('conversation') or \
                               edited_payload.get('extendedTextMessage', {}).get('text') or \
                               edited_payload.get('text')
                
                if target_msg_id and new_body:
                    message = Message.objects.filter(message_id=target_msg_id, ticket__company=connection.company).first()
                    if message:
                        message.body = new_body
                        message.is_edited = True
                        message.edited_at = timezone.now()
                        message.save()
                        
                        ticket = message.ticket
                        last_msg = ticket.messages.order_by('-timestamp', '-id').first()
                        if last_msg and last_msg.id == message.id:
                            ticket.last_message = new_body
                            ticket.save()
                            
                            ticket_payload = {
                                "company_id": str(ticket.company.id),
                                "type": "ticket_updated",
                                "payload": TicketSerializer(ticket).data
                            }
                            from django.core.serializers.json import DjangoJSONEncoder
                            redis_client.publish('company_events', json.dumps(ticket_payload, cls=DjangoJSONEncoder))
                        
                        event_payload = {
                            "company_id": str(ticket.company.id),
                            "type": "message_updated",
                            "payload": MessageSerializer(message).data
                        }
                        from django.core.serializers.json import DjangoJSONEncoder
                        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
                continue
            
            # --- DETECTAR REAÇÃO ---
            reaction_msg = message_content.get('reactionMessage')
            if reaction_msg:
                target_msg_id = reaction_msg.get('key', {}).get('id')
                emoji = reaction_msg.get('text')
                from_me = info.get('fromMe') or info.get('IsFromMe') or msg_item.get('fromMe') or msg_item.get('key', {}).get('fromMe') or False
                
                if isinstance(from_me, str):
                    from_me = from_me.lower() == 'true'
                else:
                    from_me = bool(from_me)
                
                sender_jid = info.get('participant') or info.get('remoteJid') or msg_item.get('key', {}).get('remoteJid')
                if from_me:
                    sender_jid = connection.instance_name
                
                target_message = Message.objects.filter(message_id=target_msg_id, ticket__company=connection.company).first()
                if target_message:
                    if not emoji:
                        MessageReaction.objects.filter(message=target_message, sender_jid=sender_jid).delete()
                    else:
                        MessageReaction.objects.update_or_create(
                            message=target_message,
                            sender_jid=sender_jid,
                            defaults={'emoji': emoji, 'from_me': from_me}
                        )
                    
                    event_payload = {
                        "company_id": str(target_message.ticket.company.id),
                        "type": "message_reactions_updated",
                        "payload": {
                            "message_id": target_message.id,
                            "reactions": MessageReactionSerializer(target_message.reactions.all(), many=True).data
                        }
                    }
                    from django.core.serializers.json import DjangoJSONEncoder
                    redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
                continue
            

            
            # Busca exaustiva pelo corpo da mensagem
            body = message_content.get('conversation') or \
                   message_content.get('extendedTextMessage', {}).get('text') or \
                   message_content.get('imageMessage', {}).get('caption') or \
                   message_content.get('videoMessage', {}).get('caption') or \
                   msg_item.get('text') or \
                   msg_item.get('content')
            
            # Identifica o JID remoto
            remote_jid = (
                info.get('Chat') or
                info.get('remoteJid') or
                msg_item.get('remoteJid') or
                msg_item.get('key', {}).get('remoteJid') or
                info.get('Sender') or
                data.get('data', {}).get('key', {}).get('remoteJid')
            )
            
            if not remote_jid or 'status@broadcast' in str(remote_jid) or '@g.us' in str(remote_jid):
                continue
            
            # Detecta se a mensagem foi enviada pela própria instância
            from_me = info.get('IsFromMe')
            if from_me is None: from_me = info.get('fromMe')
            if from_me is None: from_me = msg_item.get('fromMe')
            if from_me is None: from_me = msg_item.get('key', {}).get('fromMe')
            if from_me is None: from_me = False
            
            if isinstance(from_me, str):
                from_me = from_me.lower() == 'true'
            else:
                from_me = bool(from_me)
            
            # Identifica o ID da mensagem e deduplica
            msg_id = info.get('ID') or msg_item.get('messageId') or info.get('id') or msg_item.get('key', {}).get('id')
            if not msg_id:
                continue
            
            cache_key = f"webhook_msg_{msg_id}"
            if redis_client.get(cache_key):
                print(f"[WEBHOOK TASK] Mensagem {msg_id} já processada. Ignorando.")
                continue
            redis_client.setex(cache_key, 30, "1")
            
            # --- EXTRAÇÃO DE MÍDIA ---
            media_type = None
            media_url = None
            mimetype = None
            file_name = None
            
            actual_msg = message_content
            if 'viewOnceMessage' in actual_msg:
                actual_msg = actual_msg['viewOnceMessage'].get('message', {})
            elif 'viewOnceMessageV2' in actual_msg:
                actual_msg = actual_msg['viewOnceMessageV2'].get('message', {})
            
            img_obj = actual_msg.get('imageMessage') or actual_msg.get('ImageMessage')
            vid_obj = actual_msg.get('videoMessage') or actual_msg.get('VideoMessage')
            aud_obj = actual_msg.get('audioMessage') or actual_msg.get('AudioMessage')
            doc_obj = actual_msg.get('documentMessage') or actual_msg.get('DocumentMessage')
            stk_obj = actual_msg.get('stickerMessage') or actual_msg.get('StickerMessage')
            contact_obj = actual_msg.get('contactMessage') or actual_msg.get('ContactMessage') or msg_item.get('contactMessage')
            contacts_array_obj = actual_msg.get('contactsArrayMessage') or actual_msg.get('ContactsArrayMessage') or msg_item.get('contactsArrayMessage')
            
            if img_obj:
                media_type = 'image'
                mimetype = img_obj.get('mimetype') or 'image/jpeg'
            elif vid_obj:
                media_type = 'video'
                mimetype = vid_obj.get('mimetype') or 'video/mp4'
            elif aud_obj:
                media_type = 'audio'
                mimetype = aud_obj.get('mimetype') or 'audio/mp4'
            elif doc_obj:
                media_type = 'document'
                mimetype = doc_obj.get('mimetype') or 'application/octet-stream'
                file_name = doc_obj.get('title') or doc_obj.get('fileName') or doc_obj.get('filename') or None
            elif stk_obj:
                media_type = 'image'
                mimetype = stk_obj.get('mimetype') or 'image/webp'
            elif contact_obj:
                media_type = 'contact'
                mimetype = 'text/vcard'
                vcard_str = contact_obj.get('vcard') or ''
                disp_name = contact_obj.get('displayName') or contact_obj.get('name') or ''
                phone_match = re.search(r'waid=(\d+)', vcard_str) or re.search(r'TEL[^:]*:([+\d\s()-]+)', vcard_str)
                extracted_phone = phone_match.group(1).strip() if phone_match else ''
                if not disp_name:
                    fn_match = re.search(r'FN:(.*?)(?:\r?\n|$)', vcard_str)
                    disp_name = fn_match.group(1).strip() if fn_match else 'Contato'
                
                contact_data = {
                    "name": disp_name,
                    "phone": extracted_phone,
                    "vcard": vcard_str
                }
                media_url = json.dumps(contact_data)
                file_name = disp_name
                if not body:
                    body = f"👤 Contato: {disp_name}" + (f" ({extracted_phone})" if extracted_phone else "")
            elif contacts_array_obj:
                media_type = 'contact'
                mimetype = 'text/vcard'
                contact_list = contacts_array_obj.get('contacts', [])
                disp_name = contacts_array_obj.get('displayName') or (contact_list[0].get('displayName') if contact_list else 'Contatos')
                parsed_contacts = []
                for c in contact_list:
                    vcard_str = c.get('vcard') or ''
                    c_name = c.get('displayName') or ''
                    phone_match = re.search(r'waid=(\d+)', vcard_str) or re.search(r'TEL[^:]*:([+\d\s()-]+)', vcard_str)
                    c_phone = phone_match.group(1).strip() if phone_match else ''
                    if not c_name:
                        fn_match = re.search(r'FN:(.*?)(?:\r?\n|$)', vcard_str)
                        c_name = fn_match.group(1).strip() if fn_match else 'Contato'
                    parsed_contacts.append({"name": c_name, "phone": c_phone, "vcard": vcard_str})
                
                media_url = json.dumps(parsed_contacts)
                file_name = disp_name
                if not body:
                    names = ", ".join([c['name'] for c in parsed_contacts[:3]])
                    body = f"👤 Contatos: {names}"
            
            if not mimetype:
                mimetype = actual_msg.get('mimetype') or 'image/jpeg'
            
            payload_base64 = actual_msg.get('base64') or msg_item.get('base64')
            if payload_base64:
                if not str(payload_base64).startswith('data:'):
                    payload_base64 = f"data:{mimetype};base64,{payload_base64}"
                media_url = payload_base64
            
            if not media_url:
                if img_obj:
                    media_url = img_obj.get('base64') or img_obj.get('url')
                elif vid_obj:
                    media_url = vid_obj.get('base64') or vid_obj.get('url')
                elif aud_obj:
                    media_url = aud_obj.get('base64') or aud_obj.get('url')
                elif doc_obj:
                    media_url = doc_obj.get('base64') or doc_obj.get('url')
                elif stk_obj:
                    media_url = stk_obj.get('base64') or stk_obj.get('url')
            
            if not media_type:
                raw_type = str(msg_item.get('type') or info.get('MediaType') or info.get('Type') or '').lower()
                if 'image' in raw_type: media_type = 'image'
                elif 'video' in raw_type: media_type = 'video'
                elif 'audio' in raw_type: media_type = 'audio'
                elif 'document' in raw_type: media_type = 'document'
            
            if not media_url:
                media_url = msg_item.get('base64') or msg_item.get('url') or msg_item.get('content')
            
            # --- DOWNLOAD DE MÍDIA DA EVOLUTION API ---
            is_whatsapp_cdn = media_url and 'whatsapp.net' in str(media_url)
            if media_type and (not media_url or is_whatsapp_cdn or not str(media_url).startswith('data:')):
                try:
                    evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
                    from tickets.utils import get_evolution_token
                    evo_key = get_evolution_token(connection.instance_name)
                    
                    headers = {
                        "Content-Type": "application/json",
                        "apikey": evo_key,
                        "ApiKey": evo_key,
                        "api-key": evo_key,
                        "Authorization": f"Bearer {evo_key}"
                    }
                    payload = {
                        "message": {
                            "key": {
                                "id": msg_id,
                                "remoteJid": remote_jid,
                                "fromMe": from_me
                            }
                        },
                        "convertToMp4": False
                    }
                    download_url = f"{evo_url}/chat/getBase64FromMediaMessage/{connection.instance_name}"
                    res = requests.post(download_url, json=payload, headers=headers, timeout=10)
                    if res.status_code != 200:
                        fallback_payload = {
                            "message": {
                                "key": {
                                    "id": msg_id
                                }
                            },
                            "convertToMp4": False
                        }
                        res = requests.post(download_url, json=fallback_payload, headers=headers, timeout=10)
                    
                    if res.status_code == 200:
                        res_data = res.json()
                        base64_result = res_data.get('base64')
                        if base64_result:
                            media_url = base64_result
                except Exception as media_err:
                    print(f"[WEBHOOK TASK MEDIA] Falha na chamada da Evolution API: {str(media_err)}")
            
            if media_url and not str(media_url).startswith('http') and not str(media_url).startswith('data:'):
                clean_base64 = str(media_url).replace('\n', '').replace('\r', '').strip()
                media_url = f"data:{mimetype};base64,{clean_base64}"
            
            if not body and not media_url:
                continue
            
            # --- EXTRAÇÃO DE CITADOS / RESPOSTAS ---
            quoted_msg_id = None
            quoted_msg_body = None
            quoted_msg_sender = None
            
            context_info = None
            for key_type in ['extendedTextMessage', 'imageMessage', 'videoMessage', 'audioMessage', 'documentMessage', 'stickerMessage']:
                msg_type_data = message_content.get(key_type)
                if isinstance(msg_type_data, dict):
                    context_info = msg_type_data.get('contextInfo')
                    if context_info:
                        break
            if not context_info:
                context_info = message_content.get('contextInfo')
            
            contact_name = msg_item.get('pushName') or info.get('PushName') or data.get('data', {}).get('pushName') or remote_jid.split('@')[0]
            
            if context_info:
                quoted_msg_id = context_info.get('stanzaId') or context_info.get('stanzaID')
                if quoted_msg_id:
                    db_quoted = Message.objects.filter(message_id=quoted_msg_id).first()
                    if db_quoted:
                        quoted_msg_body = db_quoted.body
                        quoted_msg_sender = "Você" if db_quoted.from_me else (contact_name or "Cliente")
                    else:
                        participant = context_info.get('participant')
                        if participant:
                            p_num = str(participant).split('@')[0].split(':')[0]
                            c_num = str(remote_jid).split('@')[0].split(':')[0]
                            if p_num == c_num:
                                quoted_msg_sender = contact_name or "Cliente"
                            else:
                                quoted_msg_sender = "Você"
                        else:
                            quoted_msg_sender = "Você"
                        
                        quoted_msg_content = context_info.get('quotedMessage') or {}
                        if quoted_msg_content:
                            quoted_body = quoted_msg_content.get('conversation') or \
                                          quoted_msg_content.get('extendedTextMessage', {}).get('text')
                            
                            if not quoted_body:
                                if 'imageMessage' in quoted_msg_content:
                                    quoted_body = quoted_msg_content['imageMessage'].get('caption') or "📷 Foto"
                                elif 'videoMessage' in quoted_msg_content:
                                    quoted_body = quoted_msg_content['videoMessage'].get('caption') or "🎥 Vídeo"
                                elif 'audioMessage' in quoted_msg_content:
                                    quoted_body = "🎵 Áudio"
                                elif 'documentMessage' in quoted_msg_content:
                                    quoted_body = quoted_msg_content['documentMessage'].get('title') or "📄 Documento"
                                elif 'contactMessage' in quoted_msg_content:
                                    quoted_body = f"👤 {quoted_msg_content['contactMessage'].get('displayName') or 'Contato'}"
                                elif 'contactsArrayMessage' in quoted_msg_content:
                                    quoted_body = "👤 Contatos"
                                elif 'stickerMessage' in quoted_msg_content:
                                    quoted_body = "🎨 Figurinha"
                            
                            quoted_msg_body = quoted_body
            
            # Cria/Recupera Contato
            phone_number = remote_jid.split('@')[0]
            phone_digits = re.sub(r'\D', '', phone_number)
            
            customer = Customer.objects.filter(
                company=connection.company,
                phone__icontains=phone_digits[-8:]
            ).first()
            
            if not customer:
                additional_contact = Contact.objects.filter(
                    customer__company=connection.company,
                    phone__icontains=phone_digits[-8:]
                ).first()
                if not additional_contact:
                    additional_contact = Contact.objects.filter(
                        customer__company=connection.company,
                        whatsapp__icontains=phone_digits[-8:]
                    ).first()
                if additional_contact:
                    customer = additional_contact.customer
                    contact_name = additional_contact.name
            
            if from_me and not customer:
                print(f"[WEBHOOK TASK] Ignorando mensagem fromMe para número não cadastrado: {phone_number}")
                continue
            
            # Preserve manually linked customer and custom contact name
            from tickets.utils import get_br_jid_variant
            existing_contact = Contact.objects.filter(remote_jid=remote_jid, company=connection.company).first()
            if not existing_contact:
                variant_jid = get_br_jid_variant(remote_jid)
                if variant_jid:
                    existing_contact = Contact.objects.filter(remote_jid=variant_jid, company=connection.company).first()
            if not existing_contact and len(phone_digits) >= 8:
                from django.db.models import Q
                existing_contact = Contact.objects.filter(
                    Q(whatsapp__icontains=phone_digits[-8:]) |
                    Q(cellphone__icontains=phone_digits[-8:]) |
                    Q(phone__icontains=phone_digits[-8:]),
                    company=connection.company
                ).first()

            if existing_contact:
                if existing_contact.remote_jid != remote_jid:
                    if not Contact.objects.filter(remote_jid=remote_jid, company=connection.company).exists():
                        existing_contact.remote_jid = remote_jid
                        existing_contact.save()
                if existing_contact.customer:
                    customer = existing_contact.customer
                if existing_contact.name:
                    contact_name = existing_contact.name
            
            contact, contact_created = Contact.objects.update_or_create(
                remote_jid=remote_jid,
                company=connection.company,
                defaults={'name': contact_name, 'customer': customer}
            )
            
            # --- BUSCA FOTO DE PERFIL ---
            if contact_created or not contact.profile_pic:
                # Usar cache Redis para evitar buscar foto de perfil da Evolution repetidamente
                profile_pic_cache_key = f"contact_pic_fetch_{remote_jid}"
                if not redis_client.get(profile_pic_cache_key):
                    redis_client.setex(profile_pic_cache_key, 86400, "1") # 24 horas de "já tentamos"
                    try:
                        evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
                        from tickets.utils import get_evolution_token
                        evo_key = get_evolution_token(connection.instance_name)
                        clean_number = remote_jid.split('@')[0]
                        
                        headers = {
                            "Content-Type": "application/json",
                            "apikey": evo_key,
                            "ApiKey": evo_key,
                            "api-key": evo_key,
                            "Authorization": f"Bearer {evo_key}",
                            "instance": connection.instance_name,
                            "instanceName": connection.instance_name
                        }
                        
                        url = None
                        
                        # Chamada única de busca: POST /user/avatar com JID completo
                        try:
                            url_post = f"{evo_url}/user/avatar?instance={connection.instance_name}"
                            payload = {"number": remote_jid, "preview": False}
                            res = requests.post(url_post, json=payload, headers=headers, timeout=8)
                            if res.status_code == 200:
                                data_pic = res.json()
                                if isinstance(data_pic, dict):
                                    url = data_pic.get('profilePictureUrl') or data_pic.get('url')
                                    if not url:
                                        data_block = data_pic.get('data') or {}
                                        if isinstance(data_block, dict):
                                            url = data_block.get('url') or data_block.get('profilePictureUrl')
                        except Exception as e:
                            print(f"[WEBHOOK PIC] Falha ao buscar avatar da Evolution API: {e}")
                        
                        if url:
                            contact.profile_pic = url
                            contact.save()
                            
                            if contact.customer:
                                contact.customer.profile_pic = url
                                contact.customer.save()
                    except Exception as e:
                        pass
            
            # Abre ou Recupera Ticket (Atomicamente para evitar duplicidade)
            with transaction.atomic():
                ticket = Ticket.objects.filter(
                    contact=contact,
                    company=connection.company,
                    status__in=['open', 'pending']
                ).order_by('-id').select_for_update().first()
                
                if not ticket:
                    ticket = Ticket.objects.create(
                        contact=contact,
                        company=connection.company,
                        status='open'
                    )
                
                # Salva a Mensagem
                msg_obj, msg_created = Message.objects.update_or_create(
                    message_id=msg_id,
                    defaults={
                        'ticket': ticket,
                        'from_me': from_me,
                        'body': body or "",
                        'media_url': media_url,
                        'media_type': media_type,
                        'file_name': file_name,
                        'quoted_message_id': quoted_msg_id,
                        'quoted_message_body': quoted_msg_body,
                        'quoted_message_sender': quoted_msg_sender
                    }
                )
                
                ticket.last_message = body or (f"📷 Foto" if media_type == 'image' else (f"🎵 Áudio" if media_type == 'audio' else (f"👤 Contato" if media_type == 'contact' else f"📄 Documento")))
                if not from_me:
                    ticket.unread_count += 1
                ticket.save()
            
            if msg_created:
                event_payload = {
                    "company_id": str(ticket.company.id),
                    "type": "new_message",
                    "payload": MessageSerializer(msg_obj).data
                }
                from django.core.serializers.json import DjangoJSONEncoder
                redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))

                # --- VERIFICAR E ENVIAR MENSAGEM DE AUSÊNCIA ---
                if not from_me:
                    try:
                        _maybe_send_absence_message(connection, remote_jid, ticket)
                    except Exception as abs_err:
                        print(f"[WEBHOOK TASK ABSENCE] Erro ao tentar enviar mensagem de ausência: {abs_err}")

@shared_task
def send_wa_message_task(message_id, quoted_msg_id=None):
    from tickets.models import Message, Connection
    from api.serializers import MessageSerializer
    from tickets.utils import get_evolution_token
    import requests
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    try:
        message = Message.objects.select_related('ticket__contact', 'ticket__company').get(id=message_id)
        ticket = message.ticket
        
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            print(f"[CELERY SEND] Nenhuma conexão WhatsApp encontrada para a empresa do ticket {ticket.id}")
            return
            
        evo_token = get_evolution_token(connection.instance_name)
        evo_url = "http://evolution-go:8080"
        evo_key = evo_token
        
        url = f"{evo_url}/send/text?apikey={evo_key}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_key,
            "ApiKey": evo_key,
            "api-key": evo_key,
            "Authorization": f"Bearer {evo_key}",
            "instance": connection.instance_name
        }
        
        clean_number = ticket.contact.remote_jid.split('@')[0]
        
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": message.body
        }
        
        if quoted_msg_id:
            quoted_msg = Message.objects.filter(id=quoted_msg_id).first()
            if quoted_msg:
                payload["quoted"] = {
                    "messageId": quoted_msg.message_id,
                    "participant": ticket.contact.remote_jid
                }
                
        print(f"[CELERY SEND] Enviando mensagem {message.id} para {clean_number} via Evolution API...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            evolution_data = response.json()
            real_id = (
                evolution_data.get('data', {}).get('Info', {}).get('ID') or 
                evolution_data.get('key', {}).get('id') or 
                message.message_id
            )
            message.message_id = real_id
            message.save()
            print(f"[CELERY SEND] Mensagem {message.id} enviada com sucesso. Novo ID: {real_id}")
            
            # Notificar Realtime via Redis Pub/Sub que o message_id foi atualizado
            event_payload = {
                "company_id": str(ticket.company.id),
                "type": "message_updated",
                "payload": MessageSerializer(message).data
            }
            redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
        else:
            print(f"[CELERY SEND] Erro de status no envio da Evolution API para mensagem {message.id}: {response.status_code} | {response.text}")
            
    except Exception as e:
        print(f"[CELERY SEND] Exceção geral ao enviar mensagem {message_id}: {str(e)}")

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
        from tickets.utils import get_evolution_token
        evo_token = get_evolution_token(connection.instance_name)
        
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
            # 1. Delete all message reactions
            cursor.execute("""
                DELETE FROM tickets_messagereaction 
                WHERE message_id IN (
                    SELECT id FROM tickets_message 
                    WHERE ticket_id IN (
                        SELECT id FROM tickets_ticket WHERE company_id = %s
                    )
                )
            """, [str(company_id)])

            # 2. Delete all messages from tickets belonging to the company
            cursor.execute("""
                DELETE FROM tickets_message 
                WHERE ticket_id IN (
                    SELECT id FROM tickets_ticket WHERE company_id = %s
                )
            """, [str(company_id)])
            
            # 3. Delete all tickets belonging to the company
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


@shared_task
def measure_evo_latency_task(connection_id):
    import time
    import requests
    from django.conf import settings
    from tickets.models import Connection
    
    try:
        connection = Connection.objects.select_related('company').get(id=connection_id)
        company = connection.company
        
        evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')
        from tickets.utils import get_evolution_token
        evo_key = get_evolution_token(connection.instance_name)
        
        url = f"{evo_url}/instance/all"
        headers = {
            "apikey": evo_key,
            "ApiKey": evo_key,
            "api-key": evo_key,
            "Authorization": f"Bearer {evo_key}"
        }
        
        start_time = time.time()
        res = requests.get(url, headers=headers, timeout=5.0)
        end_time = time.time()
        
        if res.status_code == 200:
            latency_ms = int((end_time - start_time) * 1000)
            latency_str = f"{latency_ms}ms"
        else:
            latency_str = "Instável"
    except Exception as e:
        print(f"[LATENCY TASK] Erro ao medir latência: {str(e)}")
        latency_str = "Instável"
        
    try:
        latency_cache_key = f"evo_latency_{connection_id}"
        redis_client.setex(latency_cache_key, 120, latency_str)
    except Exception as redis_err:
        print(f"[LATENCY TASK] Erro ao salvar latência no Redis: {redis_err}")


def _maybe_send_absence_message(connection, remote_jid, ticket):
    from zoneinfo import ZoneInfo
    from datetime import datetime
    from django.utils import timezone
    from tickets.models import AbsenceSchedule, Message
    import requests
    import json
    from django.conf import settings
    from api.serializers import MessageSerializer

    try:
        company = connection.company
        # 1. Busca AbsenceSchedule da empresa
        schedule_obj = AbsenceSchedule.objects.filter(company=company).first()
        if not schedule_obj or not schedule_obj.enabled:
            return

        # 2. Verifica se a empresa está fora do horário comercial
        tz = ZoneInfo(schedule_obj.timezone or 'America/Sao_Paulo')
        now_local = datetime.now(tz)
        
        # O dia da semana: 0 (Segunda) a 6 (Domingo) em Python/datetime
        current_day = now_local.weekday()
        current_time_str = now_local.strftime('%H:%M')

        # Procura o dia correspondente na agenda
        day_schedule = None
        for item in schedule_obj.schedule:
            if int(item.get('day')) == current_day:
                day_schedule = item
                break

        is_outside = True
        if day_schedule and day_schedule.get('active'):
            start_str = day_schedule.get('start', '08:00')
            end_str = day_schedule.get('end', '18:00')
            
            # Compara strings de horários no formato HH:MM
            if start_str <= current_time_str <= end_str:
                is_outside = False

        if not is_outside:
            return

        # 3. Verifica cooldown no Redis (4 horas = 14400 segundos)
        cooldown_key = f"absence_sent_{company.id}_{remote_jid}"
        if redis_client.get(cooldown_key):
            print(f"[ABSENCE] Cooldown ativo para {remote_jid}. Mensagem de ausência não enviada.")
            return

        redis_client.setex(cooldown_key, 14400, "1")

        # 4. Envia mensagem de ausência via Evolution API
        evo_url = company.evolution_api_url or settings.EVOLUTION_API_URL
        from tickets.utils import get_evolution_token
        evo_key = get_evolution_token(connection.instance_name)
        
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_key,
            "Authorization": f"Bearer {evo_key}"
        }
        
        clean_number = remote_jid.split('@')[0]
        url = f"{evo_url}/send/text?apikey={evo_key}&instance={connection.instance_name}"
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": schedule_obj.message
        }
        
        print(f"[ABSENCE] Enviando mensagem de ausência para {remote_jid}...")
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # 5. Salva a mensagem de ausência no banco
        msg_id = f"absence_{ticket.id}_{int(timezone.now().timestamp() * 1000)}"
        if res.status_code in [200, 201]:
            try:
                res_data = res.json()
                msg_id = res_data.get('key', {}).get('id', msg_id)
            except:
                pass

        absence_msg = Message.objects.create(
            ticket=ticket,
            user=None,
            from_me=True,
            body=schedule_obj.message,
            message_id=msg_id
        )

        ticket.last_message = schedule_obj.message
        ticket.save()

        # Notifica o frontend
        event_payload = {
            "company_id": str(company.id),
            "type": "new_message",
            "payload": MessageSerializer(absence_msg).data
        }
        from django.core.serializers.json import DjangoJSONEncoder
        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))

    except Exception as e:
        print(f"[ABSENCE ERROR] Falha no processamento da mensagem de ausência: {str(e)}")


def send_daily_open_tickets_report_for_user(user, company, connection, current_date):
    """
    Envia o relatório diário de conversas abertas e pendentes para o atendente.
    """
    from tickets.models import Ticket
    from tickets.utils import get_evolution_token
    from django.conf import settings
    import requests
    import re

    clean_number = re.sub(r'\D', '', user.whatsapp or '')
    if not clean_number:
        return False

    # Busca tickets em aberto ou pendentes deste atendente
    open_tickets = Ticket.objects.filter(
        company=company,
        user=user,
        status__in=['open', 'pending']
    ).select_related('contact', 'contact__customer').order_by('-updated_at')

    if not open_tickets.exists():
        return False

    user_name = (user.first_name or user.username).strip()
    date_str = current_date.strftime('%d/%m/%Y')
    total_count = open_tickets.count()

    msg = f"💬 *Relatório Diário de Conversas - WDesk*\n\n"
    msg += f"Olá, *{user_name}*! Você possui *{total_count}* conversa(s) em andamento / aguardando retorno hoje ({date_str}):\n\n"

    for t in open_tickets[:15]: # Limita a 15 itens para formatação limpa
        contact_name = t.contact.name if t.contact and t.contact.name else "Contato"
        phone_raw = t.contact.remote_jid.split('@')[0] if t.contact and t.contact.remote_jid else ""
        customer_name = t.contact.customer.name if t.contact and t.contact.customer else None
        
        status_label = "Em Aberto 🔴" if t.status == 'open' else "Pendente 🟡"
        unread_info = f" | Não lidas: {t.unread_count}" if t.unread_count > 0 else ""
        
        display_title = f"*{contact_name}*"
        if customer_name and customer_name != contact_name:
            display_title += f" - {customer_name}"
        elif phone_raw:
            display_title += f" ({phone_raw})"

        msg += f"• {display_title}\n"
        msg += f"   ┗ _Status: {status_label}{unread_info}_\n"
        if t.last_message:
            snippet = t.last_message.strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            msg += f"   ┗ _Última: \"{snippet}\"_\n"
        msg += "\n"

    if total_count > 15:
        msg += f"_... e mais {total_count - 15} conversas ativas._\n\n"

    msg += f"📊 *Total de Conversas:* {total_count}\n"
    msg += "👉 Acesse o painel do WDesk para dar continuidade aos atendimentos. 🚀"

    try:
        evo_token = get_evolution_token(connection.instance_name)
        evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')

        url = f"{evo_url}/send/text?apikey={evo_token}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "Authorization": f"Bearer {evo_token}"
        }
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": msg
        }

        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"[DAILY TICKETS REPORT] Enviado com sucesso para {user.username} ({clean_number})")
            return True
        else:
            print(f"[DAILY TICKETS REPORT] Falha ao enviar para {user.username}: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"[DAILY TICKETS REPORT] Erro ao enviar relatório de conversas para {user.username}: {e}")
        return False


def send_daily_pendencies_report_for_user(user, company, connection, current_date):
    """
    Envia o relatório diário de pendências para o usuário.
    """
    from tickets.models import Pendency
    from tickets.utils import get_evolution_token
    from django.utils import timezone
    from django.conf import settings
    import requests
    import re

    clean_number = re.sub(r'\D', '', user.whatsapp or '')
    if not clean_number:
        return False

    # Busca pendências não finalizadas do usuário
    user_pendencies = Pendency.objects.filter(
        user=user,
        company=company
    ).exclude(status='closed').select_related('customer')

    # Se a empresa tiver a opção "somente suporte" ativada, filtra pelo tipo de operação 'suporte'
    if getattr(company, 'pendency_report_only_support', False):
        user_pendencies = user_pendencies.filter(operation_type='suporte')

    if not user_pendencies.exists():
        return False

    # Agrupa as pendências
    overdue = []
    today_due = []
    other_open = []

    for p in user_pendencies:
        if p.forecast_date:
            local_forecast = timezone.localtime(p.forecast_date)
            forecast_date_only = local_forecast.date()
            if forecast_date_only < current_date:
                overdue.append((p, local_forecast))
            elif forecast_date_only == current_date:
                today_due.append((p, local_forecast))
            else:
                other_open.append((p, local_forecast))
        else:
            other_open.append((p, None))

    date_str = current_date.strftime('%d/%m/%Y')
    user_name = (user.first_name or user.username).strip()
    msg = f"📋 *Relatório Diário de Pendências - WDesk*\n\n"
    if getattr(company, 'pendency_report_only_support', False):
        msg += f"Olá, *{user_name}*! Aqui está o resumo das suas pendências de suporte para hoje ({date_str}):\n\n"
    else:
        msg += f"Olá, *{user_name}*! Aqui está o resumo das suas pendências para hoje ({date_str}):\n\n"

    priority_map = {
        'high': 'Alta 🔴',
        'medium': 'Média 🟡',
        'low': 'Baixa 🔵'
    }

    if overdue:
        msg += "⚠️ *PENDÊNCIAS ATRASADAS:*\n"
        for p, local_forecast in overdue:
            client_name = p.customer.name if p.customer else "Sem Cliente"
            priority_label = priority_map.get(p.priority, 'Normal')
            forecast_str = local_forecast.strftime('%d/%m/%Y às %H:%M')
            msg += f"🔴 *{p.title}* - {client_name}\n"
            msg += f"   ┗ _Previsão: {forecast_str} | Prioridade: {priority_label}_\n"
        msg += "\n"

    if today_due:
        msg += "📅 *PREVISTAS PARA HOJE:*\n"
        for p, local_forecast in today_due:
            client_name = p.customer.name if p.customer else "Sem Cliente"
            priority_label = priority_map.get(p.priority, 'Normal')
            forecast_str = local_forecast.strftime('%d/%m/%Y às %H:%M')
            msg += f"🟡 *{p.title}* - {client_name}\n"
            msg += f"   ┗ _Previsão: {forecast_str} | Prioridade: {priority_label}_\n"
        msg += "\n"

    if other_open:
        msg += "📝 *OUTRAS PENDÊNCIAS ATIVAS:*\n"
        for p, local_forecast in other_open:
            client_name = p.customer.name if p.customer else "Sem Cliente"
            priority_label = priority_map.get(p.priority, 'Normal')
            if local_forecast:
                forecast_str = local_forecast.strftime('%d/%m/%Y às %H:%M')
                time_info = f"Previsão: {forecast_str} | "
            else:
                time_info = ""
            msg += f"🔵 *{p.title}* - {client_name}\n"
            msg += f"   ┗ _{time_info}Prioridade: {priority_label}_\n"
        msg += "\n"

    msg += f"📊 *Total de Pendências:* {user_pendencies.count()}\n\n"
    msg += "Tenha um excelente dia de trabalho! 🚀"

    try:
        evo_token = get_evolution_token(connection.instance_name)
        evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')

        url = f"{evo_url}/send/text?apikey={evo_token}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "Authorization": f"Bearer {evo_token}"
        }
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": msg
        }

        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"[DAILY PENDENCIES REPORT] Enviado com sucesso para {user.username} ({clean_number})")
            return True
        else:
            print(f"[DAILY PENDENCIES REPORT] Falha ao enviar para {user.username}: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"[DAILY PENDENCIES REPORT] Erro ao enviar relatório para {user.username}: {e}")
        return False


@shared_task
def process_daily_notifications_task(company_id=None):
    from tickets.models import Connection, User, Company
    from django.utils import timezone
    from django.core.cache import cache
    from datetime import time
    import time as time_lib

    current_datetime = timezone.localtime()
    current_date = current_datetime.date()
    current_time = current_datetime.time()

    if company_id:
        companies = Company.objects.filter(id=company_id)
    else:
        companies = Company.objects.filter(is_active=True)

    for company in companies:
        connection = Connection.objects.filter(company=company, status='connected').first() or Connection.objects.filter(company=company).first()
        if not connection:
            continue

        users_query = User.objects.filter(company=company, is_active=True).exclude(whatsapp__isnull=True).exclude(whatsapp='')
        
        for user in users_query:
            user_time = getattr(user, 'notification_time', None) or time(8, 0)
            
            # Se não for disparo manual de teste, valida o horário preferencial do usuário
            if not company_id and current_time < user_time:
                continue

            # Envia Pendências se ativado no perfil do usuário
            if getattr(user, 'notify_daily_pendencies', True):
                cache_key_pend = f"daily_pend_sent_{user.id}_{current_date}"
                if company_id or not cache.get(cache_key_pend):
                    if not company_id:
                        cache.set(cache_key_pend, True, 86400)
                    send_daily_pendencies_report_for_user(user, company, connection, current_date)
                    time_lib.sleep(1.0) # Evitar flood

            # Envia Conversas Abertas se ativado no perfil do usuário
            if getattr(user, 'notify_daily_open_tickets', True):
                cache_key_tick = f"daily_tickets_sent_{user.id}_{current_date}"
                if company_id or not cache.get(cache_key_tick):
                    if not company_id:
                        cache.set(cache_key_tick, True, 86400)
                    send_daily_open_tickets_report_for_user(user, company, connection, current_date)
                    time_lib.sleep(1.0)


@shared_task
def send_daily_pendencies_reports(company_id=None):
    return process_daily_notifications_task(company_id=company_id)


@shared_task
def send_pendency_created_whatsapp_notification(pendency_id):
    from tickets.models import Pendency, Connection
    from tickets.utils import get_evolution_token
    from django.utils import timezone
    from django.conf import settings
    import requests
    import re

    try:
        pendency = Pendency.objects.select_related('company', 'user', 'created_by', 'customer').get(id=pendency_id)
    except Pendency.DoesNotExist:
        print(f"[PENDENCY NOTIFICATION] Pendência {pendency_id} não encontrada.")
        return

    user = pendency.user
    if not user or not user.whatsapp:
        print(f"[PENDENCY NOTIFICATION] Usuário responsável não possui WhatsApp cadastrado.")
        return

    clean_number = re.sub(r'\D', '', user.whatsapp)
    if not clean_number:
        return

    company = pendency.company
    connection = Connection.objects.filter(company=company, status='connected').first()
    if not connection:
        connection = Connection.objects.filter(company=company).first()

    if not connection:
        print(f"[PENDENCY NOTIFICATION] Sem conexão WhatsApp para a empresa {company.name}")
        return

    creator_name = (pendency.created_by.first_name or pendency.created_by.username) if pendency.created_by else "Um usuário"
    user_name = user.first_name or user.username
    customer_name = pendency.customer.name if pendency.customer else "Não informado"
    
    priority_map = {
        'high': 'Alta 🔴',
        'medium': 'Média 🟡',
        'low': 'Baixa 🔵'
    }
    priority_label = priority_map.get(pendency.priority, 'Média 🟡')

    if pendency.forecast_date:
        forecast_str = timezone.localtime(pendency.forecast_date).strftime('%d/%m/%Y às %H:%M')
    else:
        forecast_str = "Não informada"

    msg = f"📌 *Nova Pendência Atribuída - WDesk*\n\n"
    msg += f"Olá, *{user_name}*! Uma nova pendência foi atribuída a você por *{creator_name}*:\n\n"
    msg += f"🔹 *Título:* {pendency.title}\n"
    msg += f"🏢 *Cliente:* {customer_name}\n"
    msg += f"🏷️ *Tipo:* {pendency.get_operation_type_display()}\n"
    msg += f"⚡ *Prioridade:* {priority_label}\n"
    msg += f"📅 *Previsão:* {forecast_str}\n"
    if pendency.description:
        msg += f"📝 *Descrição:* {pendency.description}\n"

    try:
        evo_token = get_evolution_token(connection.instance_name)
        evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')

        url = f"{evo_url}/send/text?apikey={evo_token}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "Authorization": f"Bearer {evo_token}"
        }
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": msg
        }

        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"[PENDENCY NOTIFICATION] Notificação enviada para {user.username} ({clean_number})")
        else:
            print(f"[PENDENCY NOTIFICATION] Falha ao enviar para {user.username}: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[PENDENCY NOTIFICATION] Erro ao enviar notificação para {user.username}: {e}")


@shared_task
def send_ticket_transferred_whatsapp_notification(ticket_id, transferred_by_user_id):
    from tickets.models import Ticket, User, Connection
    from tickets.utils import get_evolution_token
    from django.utils import timezone
    from django.conf import settings
    import requests
    import re

    try:
        ticket = Ticket.objects.select_related('company', 'user', 'contact', 'contact__customer').get(id=ticket_id)
    except Ticket.DoesNotExist:
        print(f"[TICKET TRANSFER NOTIFICATION] Ticket {ticket_id} não encontrado.")
        return

    user = ticket.user
    if not user or not user.whatsapp:
        print(f"[TICKET TRANSFER NOTIFICATION] Usuário destino não possui WhatsApp cadastrado.")
        return

    clean_number = re.sub(r'\D', '', user.whatsapp)
    if not clean_number:
        return

    company = ticket.company
    connection = Connection.objects.filter(company=company, status='connected').first()
    if not connection:
        connection = Connection.objects.filter(company=company).first()

    if not connection:
        print(f"[TICKET TRANSFER NOTIFICATION] Sem conexão WhatsApp para a empresa {company.name}")
        return

    try:
        transferred_by = User.objects.get(id=transferred_by_user_id)
        transferred_by_name = (transferred_by.first_name or transferred_by.username).strip()
    except User.DoesNotExist:
        transferred_by_name = "Um atendente"

    user_name = (user.first_name or user.username).strip()

    # Informações do contato e cliente
    contact_name = ticket.contact.name if ticket.contact and ticket.contact.name else "Contato"
    phone_raw = ticket.contact.remote_jid.split('@')[0] if ticket.contact and ticket.contact.remote_jid else ""
    phone_str = f" ({phone_raw})" if phone_raw else ""
    customer_name = ticket.contact.customer.name if ticket.contact and ticket.contact.customer else None

    # Horário formatado
    now_str = timezone.localtime().strftime('%d/%m/%Y às %H:%M')

    msg = f"🔄 *Atendimento Transferido - WDesk*\n\n"
    msg += f"Olá, *{user_name}*! Um atendimento aberto foi transferido para você por *{transferred_by_name}*:\n\n"
    msg += f"👤 *Contato:* {contact_name}{phone_str}\n"
    if customer_name:
        msg += f"🏢 *Cliente:* {customer_name}\n"
    if ticket.last_message:
        last_msg_snippet = ticket.last_message.strip()
        if len(last_msg_snippet) > 120:
            last_msg_snippet = last_msg_snippet[:117] + "..."
        msg += f"💬 *Última Mensagem:* _{last_msg_snippet}_\n"
    msg += f"⏰ *Horário:* {now_str}\n\n"
    msg += f"👉 Acesse o painel do WDesk para dar continuidade ao atendimento."

    try:
        evo_token = get_evolution_token(connection.instance_name)
        evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')

        url = f"{evo_url}/send/text?apikey={evo_token}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "Authorization": f"Bearer {evo_token}"
        }
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": msg
        }

        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"[TICKET TRANSFER NOTIFICATION] Notificação enviada para {user.username} ({clean_number})")
        else:
            print(f"[TICKET TRANSFER NOTIFICATION] Falha ao enviar para {user.username}: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[TICKET TRANSFER NOTIFICATION] Erro ao enviar notificação para {user.username}: {e}")




