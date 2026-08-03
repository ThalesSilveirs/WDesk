from rest_framework import viewsets, status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import action
try:
    import psutil
except ImportError:
    psutil = None

from tickets.models import Company, Connection, Ticket, Message, Contact, User, Customer, CustomerContact, MessageReaction, QuickReply, AbsenceSchedule, City, Pendency, PendencyImage, PendencyMovement, WebcalFeed
from .serializers import (
    TicketSerializer, 
    TicketListSerializer,
    ConnectionSerializer, 
    MessageSerializer,
    MyTokenObtainPairSerializer,
    CustomerSerializer,
    CustomerContactSerializer,
    ContactSerializer,
    CompanySerializer,
    MessageReactionSerializer,
    QuickReplySerializer,
    AbsenceScheduleSerializer,
    CitySerializer,
    PendencySerializer,
    PendencyListSerializer,
    PendencyMovementSerializer,
    WebcalFeedSerializer
)
from tickets.utils import fetch_and_parse_webcal
from rest_framework_simplejwt.views import TokenObtainPairView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import redis
from django.conf import settings
import requests
import time
import base64
import mimetypes
import re
import uuid

# Conexão Redis para Pub/Sub
redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class TenantModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet que filtra os dados pelo company_id do usuário logado.
    """
    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

class CustomerViewSet(TenantModelViewSet):
    queryset = Customer.objects.all().order_by('name')
    serializer_class = CustomerSerializer

    @action(detail=True, methods=['post'])
    def open_ticket(self, request, pk=None):
        customer = self.get_object()
        
        contact_phone = request.data.get('phone')
        contact_name = request.data.get('name')
        
        if not contact_phone:
            contact_phone = customer.phone
        if not contact_name:
            contact_name = customer.name
            
        import re
        phone_digits = re.sub(r'\D', '', str(contact_phone or ''))
        if phone_digits:
            if len(phone_digits) in [10, 11] and not phone_digits.startswith('55'):
                phone_digits = '55' + phone_digits
            elif not phone_digits.startswith('55') and len(phone_digits) < 12:
                phone_digits = '55' + phone_digits
            remote_jid = f"{phone_digits}@s.whatsapp.net"
        else:
            remote_jid = None
        
        contact = None
        if remote_jid:
            from tickets.utils import get_br_jid_variant
            contact = Contact.objects.filter(
                company=request.user.company,
                remote_jid=remote_jid
            ).first()

            if not contact:
                variant_jid = get_br_jid_variant(remote_jid)
                if variant_jid:
                    contact = Contact.objects.filter(company=request.user.company, remote_jid=variant_jid).first()

            if not contact and len(phone_digits) >= 8:
                from django.db.models import Q
                contact = Contact.objects.filter(
                    Q(whatsapp__icontains=phone_digits[-8:]) |
                    Q(cellphone__icontains=phone_digits[-8:]) |
                    Q(phone__icontains=phone_digits[-8:]),
                    company=request.user.company
                ).first()

            if contact and contact.remote_jid != remote_jid:
                if not Contact.objects.filter(company=request.user.company, remote_jid=remote_jid).exists():
                    contact.remote_jid = remote_jid
                    contact.save()

        if not contact:
            contact = Contact.objects.create(
                company=request.user.company,
                remote_jid=remote_jid,
                name=contact_name,
                customer=customer,
                phone=contact_phone
            )
        
        # Se o contato não tinha cliente vinculado, vincula agora
        if not contact.customer:
            contact.customer = customer
            contact.save()

        # Reutiliza ticket aberto existente se houver para não duplicar
        ticket = Ticket.objects.filter(
            company=request.user.company,
            contact=contact,
            status__in=['open', 'pending']
        ).order_by('-id').first()

        if not ticket:
            ticket = Ticket.objects.create(
                company=request.user.company,
                contact=contact,
                user=request.user,
                status='open'
            )
        else:
            if not ticket.user:
                ticket.user = request.user
                ticket.save()
        
        return Response(TicketSerializer(ticket).data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
        from django.db.models import Q
        customers = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(fantasy_name__icontains=query)
        )[:15]
        return Response(CustomerSerializer(customers, many=True).data)

class CustomerContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = CustomerContactSerializer

    def get_queryset(self):
        return self.queryset.filter(customer__company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def perform_update(self, serializer):
        serializer.save(company=self.request.user.company)

class ContactViewSet(TenantModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_update(self, serializer):
        contact = serializer.save()
        tickets = Ticket.objects.filter(contact=contact, status__in=['open', 'pending'])
        for ticket in tickets:
            event_payload = {
                "company_id": str(ticket.company.id),
                "type": "ticket_updated",
                "payload": TicketSerializer(ticket).data
            }
            from django.core.serializers.json import DjangoJSONEncoder
            try:
                redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
            except Exception as e:
                print(f"[CONTACT UPDATE BROADCAST] Erro ao notificar Redis: {str(e)}")

    @action(detail=True, methods=['get'])
    def avatar(self, request, pk=None):
        contact = self.get_object()
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
        
        # Cache Redis
        cache_key = f"contact_avatar_url_{contact.id}"
        if not force_refresh:
            try:
                cached_url = redis_client.get(cache_key)
                if cached_url:
                    url_str = cached_url.decode('utf-8')
                    return Response({"profile_pic": url_str if url_str != "none" else None})
            except Exception as cache_err:
                print(f"[AVATAR PROXY] Erro ao ler Redis: {cache_err}")
        
        # Busca conexão WhatsApp da empresa
        connection = Connection.objects.filter(company=contact.company, status='connected').first()
        if not connection:
            connection = Connection.objects.filter(company=contact.company).first()
            
        if not connection:
            return Response({"profile_pic": contact.profile_pic})
            
        from tickets.utils import get_evolution_token
        evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
        try:
            evo_key = get_evolution_token(connection.instance_name)
        except Exception as evo_token_err:
            print(f"[AVATAR PROXY] Erro ao buscar token Evolution: {evo_token_err}")
            return Response({"profile_pic": contact.profile_pic})
        
        clean_number = contact.remote_jid.split('@')[0]
        
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_key,
            "ApiKey": evo_key,
            "api-key": evo_key,
            "Authorization": f"Bearer {evo_key}",
            "instance": connection.instance_name,
            "instanceName": connection.instance_name
        }
        
        profile_url = None
        
        # Chamada única de busca: POST /user/avatar com JID completo
        try:
            url_post = f"{evo_url}/user/avatar?instance={connection.instance_name}"
            payload = {"number": contact.remote_jid, "preview": False}
            res = requests.post(url_post, json=payload, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    # Parser robusto para as diferentes estruturas do JSON
                    profile_url = data.get('profilePictureUrl') or data.get('url')
                    if not profile_url:
                        data_block = data.get('data') or {}
                        if isinstance(data_block, dict):
                            profile_url = data_block.get('url') or data_block.get('profilePictureUrl')
        except Exception as e:
            print(f"[AVATAR PROXY] Erro ao buscar avatar da Evolution API: {e}")
                
        # Salva no banco de dados e no cache
        if profile_url:
            contact.profile_pic = profile_url
            contact.save()
            if contact.customer:
                contact.customer.profile_pic = profile_url
                contact.customer.save()
            try:
                redis_client.setex(cache_key, 3600, profile_url) # Cache de 1 hora
            except:
                pass
        else:
            try:
                redis_client.setex(cache_key, 600, "none") # Cache negativo de 10 minutos
            except:
                pass
            
        return Response({"profile_pic": profile_url})


class TicketViewSet(TenantModelViewSet):
    queryset = Ticket.objects.all().order_by('-updated_at')
    serializer_class = TicketSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        return TicketSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        status_filter = request.query_params.get('status_filter')
        limit = request.query_params.get('limit')
        
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        elif status_filter == 'closed':
            queryset = queryset[:200]  # Limite padrão de segurança
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def broadcast_ticket_update(self, ticket):
        event_payload = {
            "company_id": str(ticket.company.id),
            "type": "ticket_updated",
            "payload": TicketListSerializer(ticket).data
        }
        from django.core.serializers.json import DjangoJSONEncoder
        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))

    def perform_update(self, serializer):
        ticket = serializer.save()
        self.broadcast_ticket_update(ticket)

    def perform_destroy(self, instance):
        ticket_id = instance.id
        company_id = str(instance.company.id)
        instance.delete()
        
        event_payload = {
            "company_id": company_id,
            "type": "ticket_deleted",
            "payload": {"id": ticket_id}
        }
        from django.core.serializers.json import DjangoJSONEncoder
        try:
            redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
        except Exception as e:
            print(f"[DELETE BROADCAST] Erro ao notificar Redis: {str(e)}")

    def send_system_whatsapp_message(self, ticket, body_text):
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return

        # 1. Salvar no banco
        message = Message.objects.create(
            ticket=ticket,
            user=None,
            from_me=True,
            body=body_text,
            message_id=f"system_{ticket.id}_{int(time.time() * 1000)}"
        )

        # 2. Enviar via Evolution API
        from tickets.utils import get_evolution_token
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
            "text": body_text
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                evolution_data = response.json()
                real_id = (
                    evolution_data.get('data', {}).get('Info', {}).get('ID') or 
                    evolution_data.get('key', {}).get('id') or 
                    message.message_id
                )
                message.message_id = real_id
                message.save()
        except Exception as e:
            print(f"[SYSTEM SEND] Erro ao enviar mensagem automatizada: {str(e)}")

        # Atualizar prévia do ticket
        ticket.last_message = body_text
        ticket.save()

        # Notificar Realtime via Redis Pub/Sub
        try:
            import redis
            import json
            r = redis.Redis(host='redis', port=6379, db=0)
            from .serializers import MessageSerializer
            serializer = MessageSerializer(message)
            r.publish(
                f"company_{ticket.company.id}_chats",
                json.dumps({
                    "type": "new_message",
                    "ticket_id": ticket.id,
                    "message": serializer.data
                })
            )
        except Exception as redis_err:
            print(f"[SYSTEM SEND] Erro ao notificar Redis: {str(redis_err)}")

    @action(detail=True, methods=['post'])
    def reset_unread(self, request, pk=None):
        ticket = self.get_object()
        ticket.unread_count = 0
        ticket.save()
        return Response({'status': 'unread count reset'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        ticket = self.get_object()
        before_id = request.query_params.get('before')
        limit = int(request.query_params.get('limit', 50))
        
        queryset = Message.objects.filter(ticket=ticket).select_related('user', 'ticket', 'ticket__contact').prefetch_related('reactions').order_by('-timestamp')
        
        if before_id:
            try:
                # Tenta buscar pelo ID numérico primeiro
                if str(before_id).isdigit():
                    before_msg = Message.objects.get(id=before_id, ticket=ticket)
                else:
                    before_msg = Message.objects.get(message_id=before_id, ticket=ticket)
                queryset = queryset.filter(timestamp__lt=before_msg.timestamp)
            except Message.DoesNotExist:
                pass
                
        messages = queryset[:limit]
        return Response(MessageSerializer(reversed(messages), many=True, context={'request': request}).data)

    def get_queryset(self):
        qs = super().get_queryset().select_related('contact', 'contact__customer', 'user')
        status_filter = self.request.query_params.get('status_filter')
        
        if status_filter == 'mine':
            qs = qs.filter(user=self.request.user, status__in=['open', 'pending'])
        elif status_filter == 'unassigned':
            qs = qs.filter(user__isnull=True, status__in=['open', 'pending'])
        elif status_filter == 'closed':
            qs = qs.filter(status='closed')
        elif status_filter == 'all' and self.request.user.role == 'admin':
            qs = qs.filter(status__in=['open', 'pending'])
        
        contact_id = self.request.query_params.get('contact')
        customer_id = self.request.query_params.get('customer')
        if contact_id:
            qs = qs.filter(contact_id=contact_id)
        if customer_id:
            qs = qs.filter(contact__customer_id=customer_id)
            
        return qs

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        ticket = self.get_object()
        if ticket.user:
            return Response({"error": "Ticket já tem um atendente"}, status=400)
        
        ticket.user = request.user
        ticket.save()
        self.broadcast_ticket_update(ticket)
        
        # Envia mensagem do sistema
        atendente_nome = request.user.first_name.strip() or request.user.username
        msg_text = f"_Seu atendimento foi iniciado por *{atendente_nome}*_"
        self.send_system_whatsapp_message(ticket, msg_text)
        
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        ticket = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({"error": "Usuário destino não informado"}, status=400)
            
        try:
            new_user = User.objects.get(id=user_id, company=request.user.company)
            ticket.user = new_user
            ticket.save()
            self.broadcast_ticket_update(ticket)
            
            # Envia mensagem do sistema
            atendente_nome = new_user.first_name.strip() or new_user.username
            msg_text = f"_Seu atendimento foi transferido para *{atendente_nome}*_"
            self.send_system_whatsapp_message(ticket, msg_text)
            
            return Response(TicketSerializer(ticket).data)
        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado na sua empresa"}, status=404)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        ticket = self.get_object()
        resolution = request.data.get('resolution', '')
        ticket.status = 'closed'
        ticket.resolution = resolution
        ticket.save()
        self.broadcast_ticket_update(ticket)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def send_media(self, request, pk=None):
        ticket = self.get_object()
        file_obj = request.FILES.get('file')
        caption = request.data.get('caption', '')
        
        if not file_obj:
            return Response({"error": "Nenhum arquivo enviado"}, status=400)

        # 1. Busca a conexão ativa
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp encontrada"}, status=400)

        # 2. Preparar Base64
        file_content = file_obj.read()
        base64_data = base64.b64encode(file_content).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(file_obj.name)
        
        # Se for o áudio gravado no frontend, força a ser do tipo áudio (evitando que .webm seja confundido com video/webm)
        if 'audio_record' in file_obj.name.lower():
            mime_type = 'audio/webm'
        # Fallback de tipo de arquivo por extensão caso o SO não reconheça (e.g. webm/ogg)
        elif not mime_type or mime_type == 'application/octet-stream':
            ext = file_obj.name.split('.')[-1].lower()
            if ext in ['ogg', 'mp3', 'wav', 'webm', 'm4a', 'aac']:
                mime_type = f'audio/{ext}'
            elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                mime_type = f'image/{ext}'
            elif ext in ['mp4', 'avi', 'mov', 'mkv']:
                mime_type = f'video/{ext}'
            else:
                mime_type = 'application/octet-stream'
        
        # 3. Determinar o tipo (Evolution Go espera: image, audio, video, document)
        evo_type = 'document'
        if 'image' in mime_type: evo_type = 'image'
        elif 'audio' in mime_type: evo_type = 'audio'
        elif 'video' in mime_type: evo_type = 'video'

        # Tenta buscar o token real diretamente no banco da Evolution
        from tickets.utils import get_evolution_token
        evo_token = get_evolution_token(connection.instance_name)

        evo_url = "http://evolution-go:8080"
        evo_key = evo_token

        # Estratégia de Blindagem Total para Mídia
        url = f"{evo_url}/send/media?apikey={evo_key}&instance={connection.instance_name}"
        headers = {
            "apikey": evo_key,
            "ApiKey": evo_key,
            "api-key": evo_key,
            "Authorization": f"Bearer {evo_key}",
            "instance": connection.instance_name
        }
        
        payload = {
            "instance": connection.instance_name,
            "number": ticket.contact.remote_jid.split('@')[0],
            "url": base64_data,
            "type": evo_type,
            "caption": caption,
            "filename": file_obj.name
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                evolution_data = response.json()
                real_id = (
                    evolution_data.get('data', {}).get('Info', {}).get('ID') or 
                    evolution_data.get('key', {}).get('id') or 
                    f"pending_media_{int(time.time())}"
                )
                message = Message.objects.create(
                    ticket=ticket,
                    user=request.user,
                    from_me=True,
                    body=caption or f"Enviou um {evo_type}",
                    media_url=f"data:{mime_type};base64,{base64_data}", 
                    media_type=evo_type,
                    message_id=real_id
                )
                # Atualizar prévia do ticket
                ticket.last_message = caption or f"📷 Foto" if evo_type == 'image' else (f"🎵 Áudio" if evo_type == 'audio' else f"📄 Documento")
                ticket.save()
                
                return Response(MessageSerializer(message).data)
            else:
                return Response({"error": f"Erro Evolution: {response.text}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        ticket = self.get_object()
        raw_body = request.data.get('body')
        quoted_msg_id = request.data.get('quoted_message_id')
        
        # 0. Adiciona Assinatura (Nome | Área:)
        user = request.user
        name = user.first_name or user.username
        signature = f"*{name} | {user.department}:*\n\n" if user.department else f"*{name}:*\n\n"
        body = signature + raw_body
        
        # 1. Busca a conexão ativa para saber qual instância usar
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp encontrada"}, status=400)

        # Busca a mensagem citada se houver
        quoted_msg = None
        if quoted_msg_id:
            from django.db.models import Q
            quoted_msg = Message.objects.filter(ticket=ticket).filter(
                Q(id=quoted_msg_id) | Q(message_id=quoted_msg_id)
            ).first()

        # 2. Salvar mensagem no banco
        temp_id = f"pending_{ticket.id}_{int(time.time() * 1000)}"
        message = Message.objects.create(
            ticket=ticket,
            user=request.user,
            from_me=True,
            body=body,
            message_id=temp_id,
            quoted_message_id=quoted_msg.message_id if quoted_msg else None,
            quoted_message_body=quoted_msg.body if quoted_msg else None,
            quoted_message_sender="Você" if quoted_msg and quoted_msg.from_me else (ticket.contact.name or "Cliente")
        )

        # Atualizar prévia do ticket
        ticket.last_message = body
        ticket.save()

        # 3. Notificar Realtime via Redis Pub/Sub (com ID pendente temporário)
        event_payload = {
            "company_id": str(ticket.company.id),
            "type": "new_message",
            "payload": MessageSerializer(message).data
        }
        from django.core.serializers.json import DjangoJSONEncoder
        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))

        # 4. Dispara a tarefa assíncrona no Celery para chamar a Evolution API em background
        from tickets.tasks import send_wa_message_task
        send_wa_message_task.delay(message.id, quoted_msg.id if quoted_msg else None)

        return Response(MessageSerializer(message).data)

    @action(detail=True, methods=['post'])
    def react_message(self, request, pk=None):
        ticket = self.get_object()
        message_id = request.data.get('message_id')
        emoji = request.data.get('emoji')

        from django.shortcuts import get_object_or_404
        message = get_object_or_404(Message, id=message_id, ticket=ticket)
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp ativa encontrada"}, status=400)

        from tickets.utils import get_evolution_token
        evo_token = get_evolution_token(connection.instance_name)

        evo_url = getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')
        url = f"{evo_url}/message/react?apikey={evo_token}&instance={connection.instance_name}"
        
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "ApiKey": evo_token,
            "api-key": evo_token,
            "Authorization": f"Bearer {evo_token}",
            "instance": connection.instance_name
        }
        
        my_jid = connection.instance_name
        
        # Ajuste o payload para a estrutura flat exigida pelo Evolution Go (whatsmeow)
        payload = {
            "number": ticket.contact.remote_jid,
            "id": message.message_id,
            "fromMe": message.from_me,
            "reaction": emoji if emoji else ""  # String vazia remove a reação no WhatsApp
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                if not emoji:
                    MessageReaction.objects.filter(message=message, sender_jid=my_jid).delete()
                else:
                    MessageReaction.objects.update_or_create(
                        message=message,
                        sender_jid=my_jid,
                        defaults={'emoji': emoji, 'from_me': True}
                    )
                
                reactions_data = MessageReactionSerializer(message.reactions.all(), many=True).data
                event_payload = {
                    "company_id": str(ticket.company.id),
                    "type": "message_reactions_updated",
                    "payload": {
                        "message_id": message.id,
                        "reactions": reactions_data
                    }
                }
                from django.core.serializers.json import DjangoJSONEncoder
                redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
                
                return Response({"status": "success", "reactions": reactions_data})
            else:
                return Response({"error": f"Erro Evolution API: {response.text}"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def edit_message(self, request, pk=None):
        ticket = self.get_object()
        message_id = request.data.get('message_id')
        new_body = request.data.get('body')

        if not message_id or not new_body:
            return Response({"error": "Parâmetros 'message_id' e 'body' são obrigatórios"}, status=400)

        from django.shortcuts import get_object_or_404
        message = get_object_or_404(Message, id=message_id, ticket=ticket)
        
        if not message.from_me:
            return Response({"error": "Você só pode editar suas próprias mensagens"}, status=400)

        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp ativa encontrada"}, status=400)

        from tickets.utils import get_evolution_token
        evo_token = get_evolution_token(connection.instance_name)

        evo_url = getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')
        url = f"{evo_url}/message/edit?apikey={evo_token}&instance={connection.instance_name}"
        
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_token,
            "ApiKey": evo_token,
            "api-key": evo_token,
            "Authorization": f"Bearer {evo_token}",
            "instance": connection.instance_name
        }
        
        # Ajuste o payload para a estrutura flat exigida pelo Evolution Go (whatsmeow)
        payload = {
            "chat": ticket.contact.remote_jid,
            "message": new_body,
            "messageId": message.message_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                message.body = new_body
                message.is_edited = True
                message.save()
                
                event_payload = {
                    "company_id": str(ticket.company.id),
                    "type": "message_updated",
                    "payload": MessageSerializer(message).data
                }
                from django.core.serializers.json import DjangoJSONEncoder
                redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))
                
                return Response({"status": "success", "message": MessageSerializer(message).data})
            else:
                return Response({"error": f"Erro Evolution API: {response.text}"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        company = request.user.company
        cache_key = f"company_stats_{company.id}"
        
        # Tenta buscar do Redis (Cache curto de apenas 3 segundos para tempo real)
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return Response(json.loads(cached_data.decode('utf-8')))
        except Exception as e:
            print(f"[STATS CACHE] Erro ao ler Redis: {e}")
        
        # 1. Atendimentos Ativos (Abertos + Pendentes)
        active_chats = Ticket.objects.filter(company=company, status__in=['open', 'pending']).count()
        
        # 2. Tempo Médio de Resposta (Entre 1a msg do cliente e 1a resposta do agente)
        from django.db.models import OuterRef, Subquery
        
        first_client_msg_ts = Message.objects.filter(
            ticket=OuterRef('pk'),
            from_me=False
        ).order_by('timestamp').values('timestamp')[:1]

        first_agent_msg_ts = Message.objects.filter(
            ticket=OuterRef('pk'),
            from_me=True,
            timestamp__gt=Subquery(first_client_msg_ts)
        ).order_by('timestamp').values('timestamp')[:1]

        tickets_with_times = Ticket.objects.filter(company=company).annotate(
            first_client_time=Subquery(first_client_msg_ts),
            first_agent_time=Subquery(first_agent_msg_ts)
        ).exclude(first_client_time__isnull=True).exclude(first_agent_time__isnull=True).values('first_client_time', 'first_agent_time')

        total_seconds = 0
        counted_tickets = 0
        for t in tickets_with_times:
            diff = (t['first_agent_time'] - t['first_client_time']).total_seconds()
            if diff > 0:
                total_seconds += diff
                counted_tickets += 1
                    
        avg_response_seconds = int(total_seconds / counted_tickets) if counted_tickets > 0 else 0
        if avg_response_seconds > 0:
            minutes = avg_response_seconds // 60
            seconds = avg_response_seconds % 60
            avg_response_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        else:
            avg_response_str = "0s"
        
        # 3. Taxa de Resolução Real (Closed / Total)
        total_tickets = Ticket.objects.filter(company=company).count()
        closed_tickets = Ticket.objects.filter(company=company, status='closed').count()
        resolution_rate = round((closed_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0.0
        
        # 4. Mensagens Enviadas Hoje
        from django.utils import timezone
        today = timezone.localtime(timezone.now()).date()
        messages_sent_today = Message.objects.filter(
            ticket__company=company,
            from_me=True,
            timestamp__date=today
        ).count()
        
        # 5. WhatsApp Instance
        connection = Connection.objects.filter(company=company).first()
        connection_data = None
        if connection:
            connection_data = {
                "id": connection.id,
                "name": connection.name,
                "instance_name": connection.instance_name,
                "status": connection.status.upper(),
                "latency": "Online" if connection.status == "connected" else "0ms",
                "protocol": "HTTP REST"
            }
            
        # 6. Conversation Trends (Otimizado em 1 query com TruncDay e Count)
        from datetime import timedelta
        from django.db.models.functions import TruncDay
        from django.db.models import Count
        
        day_map = {
            "Mon": "Seg", "Tue": "Ter", "Wed": "Qua", "Thu": "Qui", "Fri": "Sex", "Sat": "Sáb", "Sun": "Dom"
        }
        
        current_day = timezone.localtime(timezone.now())
        seven_days_ago = (current_day - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        weekday_counts = []
        counts_dict = {}
        for i in range(6, -1, -1):
            d = current_day - timedelta(days=i)
            weekday_name = d.strftime('%a')
            translated_name = day_map.get(weekday_name, weekday_name)
            counts_dict[d.date()] = {
                "day": translated_name,
                "count": 0
            }
            weekday_counts.append(d.date())
            
        db_counts = (
            Ticket.objects.filter(
                company=company,
                created_at__gte=seven_days_ago
            )
            .annotate(day_date=TruncDay('created_at'))
            .values('day_date')
            .annotate(count=Count('id'))
        )
        
        for item in db_counts:
            dt = item['day_date']
            d_date = dt.date() if hasattr(dt, 'date') else dt
            if d_date in counts_dict:
                counts_dict[d_date]['count'] = item['count']
                
        weekday_counts = [counts_dict[d] for d in weekday_counts]
            
        # 7. Team Activity (Otimizado com annotate e mget para Redis)
        from django.db.models import Count, Q
        
        team_activity = []
        users = list(
            User.objects.filter(company=company).annotate(
                active_chats=Count(
                    'tickets',
                    filter=Q(tickets__company=company, tickets__status__in=['open', 'pending'])
                )
            )
        )
        
        if users:
            status_keys = [f"user_status_{user.id}" for user in users]
            active_keys = [f"user_active_{user.id}" for user in users]
            all_keys = status_keys + active_keys
            
            try:
                redis_results = redis_client.mget(all_keys)
            except Exception as e:
                print(f"[STATS REDIS] Erro no mget: {e}")
                redis_results = [None] * len(all_keys)
                
            status_values = redis_results[:len(status_keys)]
            active_values = redis_results[len(status_keys):]
            
            for idx, user in enumerate(users):
                status_bytes = status_values[idx]
                status_str = "Online" if user.is_active else "Offline"
                if status_bytes:
                    status = status_bytes.decode('utf-8')
                    if status == 'away':
                        status_str = "Ausente"
                    elif status == 'offline':
                        status_str = "Offline"
                    elif status == 'online':
                        status_str = "Online"
                else:
                    is_active = active_values[idx]
                    if is_active:
                        status_str = "Online"
                
                team_activity.append({
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "department": user.department or "Atendimento",
                    "active_chats": user.active_chats,
                    "status": status_str
                })
        
        team_activity.sort(key=lambda x: x['active_chats'], reverse=True)
        
        response_data = {
            "active_chats": active_chats,
            "avg_response_time": avg_response_str,
            "avg_response_seconds": avg_response_seconds,
            "resolution_rate": resolution_rate,
            "messages_sent_today": messages_sent_today,
            "connection": connection_data,
            "trends": weekday_counts,
            "team_activity": team_activity
        }
        
        # Salva no Redis por apenas 3 segundos para permitir atualização em tempo real
        try:
            redis_client.setex(cache_key, 3, json.dumps(response_data))
        except Exception as e:
            print(f"[STATS CACHE] Erro ao salvar Redis: {e}")
            
        return Response(response_data)


    @action(detail=False, methods=['get'])
    def analytics(self, request):
        company = request.user.company
        time_range = request.query_params.get('time_range', '7d')
        cache_key = f"company_analytics_{company.id}_{time_range}"
        
        # Tenta buscar do Redis
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return Response(json.loads(cached_data.decode('utf-8')))
        except Exception as e:
            print(f"[ANALYTICS CACHE] Erro ao ler Redis: {e}")
            
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import OuterRef, Subquery, Count, Q
        
        now = timezone.localtime(timezone.now())
        
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            # previous period: yesterday
            prev_start_date = start_date - timedelta(days=1)
            prev_end_date = start_date - timedelta(microseconds=1)
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
            end_date = now
            # previous period: days 31 to 60 ago
            prev_start_date = now - timedelta(days=60)
            prev_end_date = now - timedelta(days=30)
        else: # default 7d
            start_date = now - timedelta(days=7)
            end_date = now
            # previous period: days 8 to 14 ago
            prev_start_date = now - timedelta(days=14)
            prev_end_date = now - timedelta(days=7)

        def get_period_stats(start, end):
            period_tickets = Ticket.objects.filter(company=company, created_at__range=(start, end))
            total_tickets = period_tickets.count()
            
            total_response_seconds = 0
            counted_response_tickets = 0
            
            total_wait_seconds = 0
            counted_wait_tickets = 0
            
            # Otimizado com Subqueries e values para evitar instanciar modelos Message completos
            first_client_msg_ts = Message.objects.filter(
                ticket=OuterRef('pk'),
                from_me=False
            ).order_by('timestamp').values('timestamp')[:1]

            first_agent_msg_ts = Message.objects.filter(
                ticket=OuterRef('pk'),
                from_me=True,
                timestamp__gt=Subquery(first_client_msg_ts)
            ).order_by('timestamp').values('timestamp')[:1]

            tickets_with_times = period_tickets.annotate(
                first_client_time=Subquery(first_client_msg_ts),
                first_agent_time=Subquery(first_agent_msg_ts)
            ).values('created_at', 'first_client_time', 'first_agent_time')
            
            for t in tickets_with_times:
                first_agent_time = t['first_agent_time']
                first_client_time = t['first_client_time']
                created_at = t['created_at']
                
                if first_agent_time:
                    wait_diff = (first_agent_time - created_at).total_seconds()
                    if wait_diff > 0:
                        total_wait_seconds += wait_diff
                        counted_wait_tickets += 1
                
                if first_client_time and first_agent_time:
                    resp_diff = (first_agent_time - first_client_time).total_seconds()
                    if resp_diff > 0:
                        total_response_seconds += resp_diff
                        counted_response_tickets += 1
            
            avg_wait_seconds = int(total_wait_seconds / counted_wait_tickets) if counted_wait_tickets > 0 else 0
            avg_response_seconds = int(total_response_seconds / counted_response_tickets) if counted_response_tickets > 0 else 0
            
            closed_tickets = period_tickets.filter(status='closed').count()
            resolution_rate = round((closed_tickets / total_tickets * 100), 1) if total_tickets > 0 else 0.0
            
            open_count = period_tickets.filter(status='open').count()
            pending_count = period_tickets.filter(status='pending').count()
            
            if total_tickets > 0:
                open_pct = round((open_count / total_tickets * 100), 0)
                pending_pct = round((pending_count / total_tickets * 100), 0)
                closed_pct = 100 - open_pct - pending_pct
            else:
                open_pct = 0.0
                pending_pct = 0.0
                closed_pct = 0.0
            
            agent_msgs = Message.objects.filter(
                ticket__company=company,
                from_me=True,
                timestamp__range=(start, end)
            )
            
            # Contagem de canais otimizada no banco via aggregation
            counts = agent_msgs.aggregate(
                total=Count('id'),
                broadcast=Count('id', filter=Q(message_id__icontains='broadcast')),
                api=Count('id', filter=Q(user__isnull=True) & ~Q(message_id__icontains='broadcast')),
                whatsapp=Count('id', filter=Q(user__isnull=False) & ~Q(message_id__icontains='broadcast'))
            )
            
            total_msgs = counts['total'] or 0
            broadcast_count = counts['broadcast'] or 0
            api_count = counts['api'] or 0
            whatsapp_count = counts['whatsapp'] or 0
            
            if total_msgs > 0:
                whatsapp_pct = round((whatsapp_count / total_msgs * 100), 0)
                broadcast_pct = round((broadcast_count / total_msgs * 100), 0)
                api_pct = 100 - whatsapp_pct - broadcast_pct
            else:
                whatsapp_pct = 82.0
                broadcast_pct = 12.0
                api_pct = 6.0
            
            if total_tickets > 0:
                csat_base = 85.0
                resolution_factor = (resolution_rate / 100.0) * 10.0
                response_penalty = 0.0
                if avg_response_seconds > 180:
                    response_penalty = min(15.0, (avg_response_seconds - 180) / 60.0)
                
                csat = round(min(100.0, max(60.0, csat_base + resolution_factor - response_penalty)), 1)
            else:
                csat = 95.0
                
            return {
                "total_tickets": total_tickets,
                "avg_wait_seconds": avg_wait_seconds,
                "avg_response_seconds": avg_response_seconds,
                "resolution_rate": resolution_rate,
                "csat": csat,
                "status_distribution": {
                    "open": {"count": open_count, "percentage": open_pct},
                    "pending": {"count": pending_count, "percentage": pending_pct},
                    "closed": {"count": closed_tickets, "percentage": closed_pct}
                },
                "channels": {
                    "whatsapp": {"percentage": whatsapp_pct},
                    "broadcast": {"percentage": broadcast_pct},
                    "api": {"percentage": api_pct}
                }
            }

        current_stats = get_period_stats(start_date, end_date)
        prev_stats = get_period_stats(prev_start_date, prev_end_date)

        def format_duration(seconds):
            if seconds <= 0:
                return "0s"
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if minutes > 0:
                return f"{int(minutes)}m {int(remaining_seconds)}s"
            return f"{int(remaining_seconds)}s"

        # Total tickets trend
        ticket_diff = current_stats["total_tickets"] - prev_stats["total_tickets"]
        if prev_stats["total_tickets"] > 0:
            ticket_pct = round((ticket_diff / prev_stats["total_tickets"]) * 100, 1)
        else:
            ticket_pct = 100.0 if ticket_diff > 0 else 0.0
        
        ticket_sign = "+" if ticket_pct >= 0 else ""
        ticket_trend_text = f"{ticket_sign}{ticket_pct}% vs período anterior"
        ticket_trend_class = "positive" if ticket_pct >= 0 else "negative"

        # Wait time trend
        wait_diff_sec = current_stats["avg_wait_seconds"] - prev_stats["avg_wait_seconds"]
        if wait_diff_sec <= 0:
            wait_trend_text = f"-{format_duration(abs(wait_diff_sec))} mais rápido" if wait_diff_sec != 0 else "Sem alteração vs período anterior"
            wait_trend_class = "positive"
        else:
            wait_trend_text = f"+{format_duration(wait_diff_sec)} de espera"
            wait_trend_class = "negative"

        # Response time trend
        resp_diff_sec = current_stats["avg_response_seconds"] - prev_stats["avg_response_seconds"]
        if resp_diff_sec <= 0:
            resp_trend_text = f"-{format_duration(abs(resp_diff_sec))} mais rápido" if resp_diff_sec != 0 else "Sem alteração vs período anterior"
            resp_trend_class = "positive"
        else:
            resp_trend_text = f"+{format_duration(resp_diff_sec)} de espera"
            resp_trend_class = "negative"

        # CSAT trend
        csat_diff = current_stats["csat"] - prev_stats["csat"]
        csat_sign = "+" if csat_diff >= 0 else ""
        csat_trend_text = f"{csat_sign}{csat_diff:.1f}% vs período anterior"
        csat_trend_class = "positive" if csat_diff >= 0 else "negative"

        response_data = {
            "total_tickets": current_stats["total_tickets"],
            "avg_wait_time": format_duration(current_stats["avg_wait_seconds"]),
            "first_response": format_duration(current_stats["avg_response_seconds"]),
            "csat": current_stats["csat"],
            "trends": {
                "total_tickets": {
                    "text": ticket_trend_text,
                    "class": ticket_trend_class
                },
                "avg_wait_time": {
                    "text": wait_trend_text,
                    "class": wait_trend_class
                },
                "first_response": {
                    "text": resp_trend_text,
                    "class": resp_trend_class
                },
                "csat": {
                    "text": csat_trend_text,
                    "class": csat_trend_class
                }
            },
            "status_distribution": current_stats["status_distribution"],
            "channels": current_stats["channels"]
        }
        
        # Salva no Redis por 120 segundos
        try:
            redis_client.setex(cache_key, 120, json.dumps(response_data))
        except Exception as e:
            print(f"[ANALYTICS CACHE] Erro ao salvar Redis: {e}")
            
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def generate_report(self, request):
        import csv
        from django.http import HttpResponse
        
        company = request.user.company
        tickets = Ticket.objects.filter(company=company).select_related('contact', 'contact__customer', 'user').order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="relatorio_atendimentos.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'ID Ticket', 
            'Cliente / Razão Social', 
            'Contato', 
            'Telefone', 
            'Status', 
            'Prioridade', 
            'Atendente Responsável', 
            'Data de Abertura', 
            'Última Atualização',
            'Resolução'
        ])
        
        status_map = {'open': 'Aberta', 'pending': 'Pendente', 'closed': 'Finalizada'}
        priority_map = {'low': 'Baixa', 'medium': 'Média', 'high': 'Alta'}
        
        for ticket in tickets:
          customer_name = ticket.contact.customer.name if (ticket.contact and ticket.contact.customer) else ''
          contact_name = ticket.contact.name if ticket.contact else 'Sem Nome'
          phone = ticket.contact.remote_jid.split('@')[0] if (ticket.contact and ticket.contact.remote_jid) else ''
          attendant_name = (ticket.user.first_name or ticket.user.username) if ticket.user else 'Não atribuído'
          created_str = ticket.created_at.strftime('%d/%m/%Y %H:%M') if ticket.created_at else ''
          updated_str = ticket.updated_at.strftime('%d/%m/%Y %H:%M') if ticket.updated_at else ''
          
          writer.writerow([
              ticket.id,
              customer_name,
              contact_name,
              phone,
              status_map.get(ticket.status, ticket.status),
              priority_map.get(ticket.priority, ticket.priority),
              attendant_name,
              created_str,
              updated_str,
              ticket.resolution or ''
          ])
          
        return response

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        message = request.data.get('message')
        customer_ids = request.data.get('customer_ids', [])
        
        if not message:
            return Response({"error": "Mensagem não informada"}, status=400)
            
        company = request.user.company
        connection = Connection.objects.filter(company=company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp ativa encontrada para a sua empresa"}, status=400)
            
        customers = Customer.objects.filter(company=company)
        if customer_ids:
            customers = customers.filter(id__in=customer_ids)
            
        if not customers.exists():
            return Response({"error": "Nenhum cliente selecionado ou encontrado"}, status=400)
            
        from tickets.tasks import send_broadcast_task
        customer_phones = list(customers.values_list('phone', flat=True))
        
        send_broadcast_task.delay(
            company_id=str(company.id),
            connection_id=connection.id,
            user_id=request.user.id,
            phones=customer_phones,
            message=message
        )
        
        return Response({"status": "Broadcast iniciado", "target_count": len(customer_phones)})

    @action(detail=False, methods=['get'])
    def generate_report(self, request):
        import csv
        from django.http import HttpResponse
        
        company = request.user.company
        tickets = Ticket.objects.filter(company=company).order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tickets_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Ticket ID', 'Cliente', 'WhatsApp/JID', 'Status', 'Prioridade', 'Atendente', 'Assunto', 'Resolução', 'Criado em', 'Atualizado em'])
        
        for t in tickets:
            writer.writerow([
                t.id,
                t.contact.name or '',
                t.contact.remote_jid,
                t.get_status_display(),
                t.get_priority_display(),
                f"{t.user.first_name} {t.user.last_name}" if t.user else 'Não atribuído',
                t.subject or '',
                t.resolution or '',
                t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                t.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
        return response

class ConnectionViewSet(TenantModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer

    def get_evo_creds(self, company):
        return {
            "url": company.evolution_api_url or settings.EVOLUTION_API_URL,
            "key": company.evolution_api_key or settings.EVOLUTION_API_KEY
        }

    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        connection = self.get_object()
        creds = self.get_evo_creds(connection.company)
        from tickets.utils import get_evolution_token, redis_client
        evo_token = get_evolution_token(connection.instance_name, force_refresh=True) or creds['key']

        headers = {
            "apikey": evo_token,
            "ApiKey": evo_token,
            "api-key": evo_token,
            "Authorization": f"Bearer {evo_token}",
            "Content-Type": "application/json"
        }
        
        def fetch_qr(token_to_use):
            url_qr = f"{creds['url']}/instance/qr?instanceName={connection.instance_name}"
            for attempt in range(8):
                time.sleep(1.5)
                try:
                    res = requests.get(url_qr, headers={"apikey": token_to_use})
                    print(f"DEBUG QR TRY attempt {attempt+1}: {res.status_code}")
                    if res.status_code == 200:
                        return res
                except Exception as e:
                    print(f"DEBUG QR TRY ERR: {e}")
            return None

        try:
            # 1. Inicia a conexão (POST /instance/connect)
            url_connect = f"{creds['url']}/instance/connect"
            payload = {"name": connection.instance_name}
            res_connect = requests.post(url_connect, json=payload, headers=headers)
            print(f"DEBUG CONNECT: {url_connect} -> {res_connect.status_code} {res_connect.text}")
            
            response = fetch_qr(evo_token)

            # Se não obteve QR Code (instância em estado travado), recria a instância na Evolution API
            if not response or response.status_code != 200:
                print(f"[CONNECT] QR Code não gerado. Recriando instância '{connection.instance_name}' na Evolution API...")
                headers_global = {"apikey": creds['key'], "Content-Type": "application/json"}
                try:
                    res_all = requests.get(f"{creds['url']}/instance/all", headers=headers_global, timeout=5)
                    if res_all.status_code == 200:
                        instances = res_all.json().get('data', [])
                        target = next((i for i in instances if i.get('name') == connection.instance_name), None)
                        if target and target.get('id'):
                            requests.delete(f"{creds['url']}/instance/delete/{target['id']}", headers=headers_global, timeout=5)
                except Exception as ex_del:
                    print(f"[CONNECT] Erro ao deletar instância antiga: {ex_del}")

                # Criar com novo token
                new_token = str(uuid.uuid4())
                res_create = requests.post(
                    f"{creds['url']}/instance/create",
                    json={"name": connection.instance_name, "token": new_token},
                    headers=headers_global,
                    timeout=10
                )
                if res_create.status_code in [200, 201]:
                    evo_token = new_token
                    redis_client.delete(f"evo_token_{connection.instance_name}")
                    headers_inst = {"apikey": new_token, "Content-Type": "application/json"}
                    requests.post(url_connect, json=payload, headers=headers_inst, timeout=5)
                    response = fetch_qr(new_token)

            if response and response.status_code == 200:
                data = response.json()
                inner_data = data.get('data', {}) if isinstance(data.get('data'), dict) else data
                qrcode = inner_data.get('qrcode') or \
                         inner_data.get('base64') or \
                         data.get('qrcode') or \
                         data.get('base64')
                
                if not qrcode and inner_data.get('code'):
                    qrcode = inner_data.get('code')
                elif not qrcode and data.get('code'):
                    qrcode = data.get('code')

                if qrcode:
                    if isinstance(qrcode, dict):
                        qrcode = qrcode.get('base64') or qrcode.get('code') or qrcode.get('qrcode')
                    if isinstance(qrcode, str):
                        if qrcode.startswith('iVBOR'):
                            qrcode = f"data:image/png;base64,{qrcode}"
                        connection.qrcode = qrcode
                        connection.status = 'connecting'
                        connection.save()
                        return Response({"qrcode": qrcode, "status": connection.status})
                
                return Response({"error": "QR Code ainda não disponível. Tente novamente em instantes.", "data": data}, status=400)
            
            return Response({"error": f"Erro ao buscar QR Code. Verifique se a instância '{connection.instance_name}' existe na Evolution API."}, status=400)
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def sync_status(self, request, pk=None):
        connection = self.get_object()
        creds = self.get_evo_creds(connection.company)
        headers = {
            "apikey": creds['key'], 
            "ApiKey": creds['key'],
            "api-key": creds['key'],
            "Authorization": f"Bearer {creds['key']}"
        }
        
        # Evolution GO Status (Tenta múltiplos formatos: Path e Query Params)
        urls_to_try = [
            f"{creds['url']}/instance/status/{connection.instance_name}",
            f"{creds['url']}/instance/connectionState/{connection.instance_name}",
            f"{creds['url']}/instance/status?instanceName={connection.instance_name}&apikey={creds['key']}",
            f"{creds['url']}/instance/status?instance={connection.instance_name}&apikey={creds['key']}",
            f"{creds['url']}/instance/all" # Fallback para listar todas
        ]
        
        try:
            response = None
            for url in urls_to_try:
                try:
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        response = res
                        # Se for o endpoint /instance/all, precisamos filtrar
                        if "/instance/all" in url:
                            data_all = res.json()
                            instances = data_all.get('data', []) if isinstance(data_all, dict) else data_all
                            target = next((i for i in instances if i.get('name') == connection.instance_name or i.get('instanceName') == connection.instance_name), None)
                            if target:
                                # Simula a estrutura esperada para o restante do código
                                response._content = json.dumps(target).encode('utf-8')
                                break
                            else:
                                response = None # Continua se não achou na lista
                                continue
                        break
                except:
                    continue

            if response and response.status_code == 200:
                data = response.json()
                # Pega o estado de forma case-insensitive
                raw_state = data.get('instance', {}).get('state') or \
                            data.get('state') or \
                            data.get('status') or \
                            data.get('connectionState', {}).get('state') or \
                            data.get('connected') # Suporte ao campo booleano do /instance/all
                
                # Se for booleano True do campo 'connected', mapeia para 'connected'
                if raw_state is True: raw_state = "connected"
                elif raw_state is False: raw_state = "disconnected"
                
                state = str(raw_state).lower()
                
                if state in ['open', 'connected', 'online']:
                    connection.status = 'connected'
                elif state in ['connecting', 'qrcode', 'pairing']:
                    connection.status = 'connecting'
                else:
                    connection.status = 'disconnected'
                
                connection.save()

                # --- FORÇAR CONFIGURAÇÃO DE WEBHOOK ---
                webhook_url = f"http://backend:8000/api/v1/webhooks/evolution"
                webhook_payload = {
                    "url": webhook_url,
                    "webhook": webhook_url,
                    "enabled": True,
                    "events": ["MESSAGE", "MESSAGES_UPSERT", "MESSAGES_UPDATE", "SEND_MESSAGE", "CONNECTION_UPDATE", "Message", "READ_RECEIPT", "PRESENCE", "HISTORY_SYNC", "CHAT_PRESENCE", "CALL", "CONNECTION", "QRCODE"]
                }
                
                # Tenta endpoints de atualização de instância (comum na Evolution GO)
                webhook_endpoints = [
                    f"{creds['url']}/webhook/set/{connection.instance_name}",
                    f"{creds['url']}/instance/update/{connection.instance_name}",
                    f"{creds['url']}/instance/set/{connection.instance_name}",
                    f"{creds['url']}/instance/settings/{connection.instance_name}"
                ]
                
                webhook_configured = False
                for endpoint in webhook_endpoints:
                    try:
                        print(f"[SYNC] Tentativa em {endpoint}")
                        wh_res = requests.post(endpoint, json=webhook_payload, headers=headers, timeout=2)
                        print(f"[SYNC] Resultado: {wh_res.status_code} | {wh_res.text}")
                        if wh_res.status_code in [200, 201]:
                            webhook_configured = True
                            print(f"[SYNC] Webhook configurado com sucesso via API em {endpoint}")
                            break
                    except requests.exceptions.RequestException as e:
                        print(f"[SYNC] Erro na tentativa de webhook em {endpoint}: {e}")

                if not webhook_configured:
                    print("[SYNC] API falhou. Tentando atualização direta no banco de dados evogo_users...")
                    try:
                        import psycopg2
                        import os
                        db_pass = os.environ.get('DB_PASSWORD', 'postgres')
                        db_host = os.environ.get('DB_HOST', 'db')
                        conn = psycopg2.connect(dbname="evogo_users", user="postgres", password=db_pass, host=db_host)
                        cur = conn.cursor()
                        # Lista otimizada de eventos para Evolution GO
                        event_list = "MESSAGE,Message,GroupInfo,Chat,Connection,MESSAGES_UPSERT,MESSAGES_UPDATE,SEND_MESSAGE,CONNECTION_UPDATE,READ_RECEIPT,PRESENCE,HISTORY_SYNC,CHAT_PRESENCE,CALL,QRCODE"
                        cur.execute("UPDATE instances SET webhook = %s, events = %s WHERE name = %s;", 
                                    (webhook_url, event_list, connection.instance_name))
                        conn.commit()
                        cur.close()
                        conn.close()
                        print("[SYNC] Webhook configurado diretamente no banco de dados!")
                    except Exception as db_e:
                        print(f"[SYNC] Falha ao atualizar banco de dados diretamente: {db_e}")
                
                # --- BUSCAR ID REAL E CONFIGURAR VIA ADVANCED SETTINGS ---
                try:
                    all_instances = requests.get(f"{creds['url']}/instance/all", headers=headers, timeout=5).json()
                    print(f"[SYNC] Buscando: '{connection.instance_name}'")
                    print(f"[SYNC] Resposta Evolution: {json.dumps(all_instances)[:500]}")
                    
                    instances = all_instances.get('data', []) if isinstance(all_instances, dict) else all_instances
                    instance_id = next((i['id'] for i in instances if str(i.get('name', '')).strip() == connection.instance_name.strip()), None)
                    
                    if instance_id:
                        print(f"[SYNC] ID encontrado: {instance_id}. Configurando Advanced Settings...")
                        # Usa o token da própria instância para maior chance de sucesso
                        instance_token = next((i['token'] for i in instances if str(i.get('name', '')).strip() == connection.instance_name.strip()), creds['key'])
                        
                        adv_url = f"{creds['url']}/instance/{instance_id}/advanced-settings"
                        adv_payload = {
                            "webhook": webhook_url,
                            "webhook_enabled": True,
                            "webhook_events": ["MESSAGE", "MESSAGES_UPSERT", "MESSAGES_UPDATE", "SEND_MESSAGE", "CONNECTION_UPDATE", "Message", "READ_RECEIPT", "PRESENCE", "HISTORY_SYNC", "CHAT_PRESENCE", "CALL", "CONNECTION", "QRCODE"]
                        }
                        # Tenta com o token da instância, o token mestre do banco e depois com a chave global
                        tokens_to_try = [
                            instance_token, 
                            creds['key'],
                            creds['key']
                        ]
                        
                        for tkn in tokens_to_try:
                            if not tkn: continue
                            try:
                                # Usa apenas o token atual para evitar conflitos de headers
                                current_headers = {
                                    "apikey": tkn,
                                    "Authorization": f"Bearer {tkn}",
                                    "Content-Type": "application/json"
                                }
                                res = requests.put(adv_url, json=adv_payload, headers=current_headers, timeout=3)
                                print(f"[SYNC] PUT Advanced Settings (Token: {tkn[:5]}...) | Status: {res.status_code} | Resposta: {res.text[:100]}")
                                if res.status_code in [200, 201, 204]: break
                            except Exception as e:
                                print(f"[SYNC] Erro ao tentar token {tkn[:5]}: {e}")
                                continue
                    else:
                        print(f"[SYNC] ID não encontrado para a instância {connection.instance_name}")
                except Exception as e:
                    print(f"[SYNC] Erro ao buscar ID ou configurar Advanced Settings: {str(e)}")
                # --------------------------------------------------------
                # --------------------------------------

                return Response({"status": connection.status, "raw": data})
            
            error_msg = f"Falha ao obter status. Tentativas: {[u.split('?')[0] for u in urls_to_try]}. Última resposta: {response.status_code if response else 'Sem resposta'}"
            return Response({"status": "disconnected", "error": error_msg}, status=400)
        except Exception as e:
            return Response({"error": f"Erro interno: {str(e)}"}, status=500)

    @action(detail=True, methods=['post'])
    def logout(self, request, pk=None):
        connection = self.get_object()
        creds = self.get_evo_creds(connection.company)
        headers = {
            "apikey": creds['key'], 
            "ApiKey": creds['key'],
            "Authorization": f"Bearer {creds['key']}"
        }
        
        # Evolution GO Logout (DELETE /instance/logout?instanceName=...&apikey=...)
        url = f"{creds['url']}/instance/logout?instanceName={connection.instance_name}&apikey={creds['key']}"
        
        try:
            requests.delete(url, headers=headers)
            connection.status = 'disconnected'
            connection.qrcode = None
            connection.save()
            return Response({"status": "disconnected"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def perform_create(self, serializer):
        # Ao criar no banco, tentamos criar na Evolution também
        instance = serializer.save(company=self.request.user.company)
        creds = self.get_evo_creds(instance.company)
        
        url = f"{creds['url']}/instance/create"
        headers = {
            "Content-Type": "application/json",
            "apikey": creds['key']
        }
        payload = {
            "name": instance.instance_name,
            "token": str(uuid.uuid4()), # Token interno da instância
            "number": "" # Opcional
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code not in [200, 201]:
                # Se falhar na Evolution, remove do nosso banco para não ficar "zumbi"
                instance_name = instance.instance_name
                instance.delete()
                
                error_data = response.json() if response.status_code != 404 else {"message": "Endpoint não encontrado"}
                error_msg = error_data.get('message') or error_data.get('error') or response.text
                
                print(f"[CREATE] Erro na Evolution ({response.status_code}): {error_msg}")
                raise serializers.ValidationError({"error": f"Erro na Evolution API: {error_msg}"})
        except requests.exceptions.RequestException as e:
            instance.delete()
            raise serializers.ValidationError({"error": f"Não foi possível conectar à Evolution API: {str(e)}"})
        except Exception as e:
            if not isinstance(e, serializers.ValidationError):
                instance.delete()
                raise serializers.ValidationError({"error": f"Erro inesperado: {str(e)}"})
            raise e

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post', 'get'], url_path='evolution')
    def evolution(self, request):
        if request.method == 'GET':
            return Response({"status": "active"}, status=200)
        
        data = request.data
        
        instance_name = (
            data.get('instance') or
            data.get('instanceName') or
            data.get('instance_name') or
            data.get('data', {}).get('instance') or
            data.get('data', {}).get('instanceName') or
            data.get('sender')
        )
        
        if not instance_name:
            return Response({"status": "error", "message": "Instance name not found in payload"}, status=400)
        
        connection = Connection.objects.filter(instance_name=instance_name).only('id').first()
        if not connection:
            alt_instance = data.get('instance')
            if alt_instance and alt_instance != instance_name:
                connection = Connection.objects.filter(instance_name=alt_instance).only('id').first()
        
        if not connection:
            print(f"[WEBHOOK] Instância '{instance_name}' não cadastrada no sistema. Ignorando.")
            return Response({"status": "ignored", "reason": "connection_not_found"}, status=200)
        
        from tickets.tasks import process_webhook_event
        process_webhook_event.delay(connection.id, data)
        return Response({"status": "queued"}, status=200)

class UserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'password', 'department', 'status', 'whatsapp', 'avatar']
        extra_kwargs = {'password': {'write_only': True}}

    def get_status(self, obj):
        try:
            from api.serializers import get_cached_user_status
            return get_cached_user_status(obj.id)
        except Exception:
            return "Offline"

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserViewSet(TenantModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar as configurações da empresa do usuário logado.
    """
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retorna apenas a empresa do usuário logado
        return Company.objects.filter(id=self.request.user.company.id)

    @action(detail=False, methods=['get', 'patch'])
    def mine(self, request):
        company = request.user.company
        if not company:
            return Response({"error": "Usuário não vinculado a uma empresa"}, status=400)
            
        if request.method == 'GET':
            serializer = self.get_serializer(company)
            return Response(serializer.data)
        
        if request.user.role != 'admin':
            return Response({"error": "Apenas administradores podem alterar as configurações"}, status=403)
            
        serializer = self.get_serializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reset_conversations(self, request):
        print(f"[RESET] Request by user {request.user.username} (Role: {request.user.role})")
        if request.user.role != 'admin':
            return Response({"error": "Apenas administradores podem realizar esta ação"}, status=403)
        
        company = request.user.company
        if not company:
            return Response({"error": "Usuário não vinculado a uma empresa"}, status=400)

        try:
            from tickets.tasks import reset_company_conversations_task
            # Trigger clean up in background Celery task
            reset_company_conversations_task.delay(str(company.id))
            return Response({"message": "O processo de limpeza foi iniciado em segundo plano. As conversas serão apagadas em breve."})
        except Exception as e:
            print(f"[RESET] Celery scheduling failed, falling back to optimized SQL delete: {str(e)}")
            # Fallback to direct optimized SQL delete
            try:
                from django.db import connection as db_connection
                with db_connection.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM tickets_messagereaction 
                        WHERE message_id IN (
                            SELECT id FROM tickets_message 
                            WHERE ticket_id IN (
                                SELECT id FROM tickets_ticket WHERE company_id = %s
                            )
                        )
                    """, [str(company.id)])
                    cursor.execute("""
                        DELETE FROM tickets_message 
                        WHERE ticket_id IN (
                            SELECT id FROM tickets_ticket WHERE company_id = %s
                        )
                    """, [str(company.id)])
                    cursor.execute("""
                        DELETE FROM tickets_ticket 
                        WHERE company_id = %s
                    """, [str(company.id)])
                return Response({"message": "Todas as conversas foram apagadas com sucesso (fallback SQL)."})
            except Exception as sql_e:
                print(f"[RESET] FALLBACK SQL ERROR: {str(sql_e)}")
                return Response({"error": f"Erro ao resetar: {str(sql_e)}"}, status=500)


class QuickReplyViewSet(TenantModelViewSet):
    queryset = QuickReply.objects.all().order_by('title')
    serializer_class = QuickReplySerializer

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, created_by=self.request.user)


class AbsenceScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = AbsenceScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AbsenceSchedule.objects.filter(company=self.request.user.company)

    @action(detail=False, methods=['get', 'patch'])
    def mine(self, request):
        company = request.user.company
        if not company:
            return Response({"error": "Usuário não vinculado a uma empresa"}, status=400)
            
        schedule_obj, created = AbsenceSchedule.objects.get_or_create(
            company=company,
            defaults={
                'enabled': False,
                'timezone': 'America/Sao_Paulo',
                'schedule': [
                    {"day": 0, "start": "08:00", "end": "18:00", "active": True},
                    {"day": 1, "start": "08:00", "end": "18:00", "active": True},
                    {"day": 2, "start": "08:00", "end": "18:00", "active": True},
                    {"day": 3, "start": "08:00", "end": "18:00", "active": True},
                    {"day": 4, "start": "08:00", "end": "18:00", "active": True},
                    {"day": 5, "start": "08:00", "end": "12:00", "active": False},
                    {"day": 6, "start": "08:00", "end": "12:00", "active": False},
                ]
            }
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(schedule_obj)
            return Response(serializer.data)
            
        if request.user.role != 'admin':
            return Response({"error": "Apenas administradores podem alterar os horários de ausência"}, status=403)
            
        serializer = self.get_serializer(schedule_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        queryset = City.objects.all()
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(ibge_code__icontains=q))
        return queryset


class PendencyViewSet(TenantModelViewSet):
    queryset = Pendency.objects.all()
    serializer_class = PendencySerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return PendencyListSerializer
        return PendencySerializer

    def perform_create(self, serializer):
        from tickets.tasks import send_pendency_created_whatsapp_notification
        pendency = serializer.save(company=self.request.user.company, created_by=self.request.user)
        if pendency.user and pendency.user != self.request.user:
            send_pendency_created_whatsapp_notification.delay(pendency.id)

    def get_queryset(self):
        from django.db.models import Case, When, Value, IntegerField, Prefetch, Q
        from tickets.models import PendencyMovement
        qs = super().get_queryset().select_related('customer', 'contact', 'user', 'created_by')

        # Filtro de Busca textual
        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(contact__name__icontains=search_query)
            )

        # Filtros
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
            
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
            
        operation_type = self.request.query_params.get('operation_type')
        if operation_type:
            qs = qs.filter(operation_type=operation_type)
            
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
            
        start_date = self.request.query_params.get('start_date')
        if start_date:
            qs = qs.filter(opening_date__date__gte=start_date)
            
        end_date = self.request.query_params.get('end_date')
        if end_date:
            qs = qs.filter(opening_date__date__lte=end_date)

        # Ordenação customizada: Prioridade (Alta > Média > Baixa) e Data de Previsão
        qs = qs.annotate(
            priority_order=Case(
                When(priority='high', then=Value(1)),
                When(priority='medium', then=Value(2)),
                When(priority='low', then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by('priority_order', 'forecast_date')

        return qs.prefetch_related(
            'images',
            Prefetch('movements', queryset=PendencyMovement.objects.select_related('user'))
        )

    @action(detail=True, methods=['post'], url_path='delete-image')
    def delete_image(self, request, pk=None):
        pendency = self.get_object()
        image_id = request.data.get('image_id')
        if not image_id:
            return Response({"error": "image_id não informado"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            img = pendency.images.get(id=image_id)
            img.delete()
            return Response({"status": "image deleted"})
        except PendencyImage.DoesNotExist:
            return Response({"error": "Imagem não encontrada neste ticket"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='send-daily-reports')
    def send_daily_reports(self, request):
        if request.user.role != 'admin':
            return Response({"detail": "Permissão negada. Apenas administradores podem disparar os relatórios."}, status=status.HTTP_403_FORBIDDEN)
        
        from tickets.tasks import send_daily_pendencies_reports
        send_daily_pendencies_reports.delay(company_id=str(request.user.company.id))
        
        return Response({"detail": "Envio dos relatórios diários de pendências iniciado!"}, status=status.HTTP_200_OK)


class PendencyMovementViewSet(viewsets.ModelViewSet):
    queryset = PendencyMovement.objects.all()
    serializer_class = PendencyMovementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(pendency__company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WebcalFeedViewSet(viewsets.ModelViewSet):
    queryset = WebcalFeed.objects.all()
    serializer_class = WebcalFeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company, user=self.request.user)

    @action(detail=False, methods=['get'], url_path='events')
    def get_calendar_events(self, request):
        user = request.user
        all_events = []

        # 1. Buscar feeds WebCAL ativos
        feeds = WebcalFeed.objects.filter(company=user.company, is_active=True)
        for feed in feeds:
            feed_events = fetch_and_parse_webcal(feed.url)
            for evt in feed_events:
                evt['feed_id'] = feed.id
                evt['feed_name'] = feed.name
                evt['color'] = feed.color
                evt['source'] = 'webcal'
                all_events.append(evt)

        # 2. Buscar Pendências do WDesk
        pendencies = Pendency.objects.select_related('customer', 'user').filter(company=user.company)
        for p in pendencies:
            date_val = p.forecast_date or p.opening_date
            if not date_val:
                continue
            date_iso = date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val)
            
            cust_name = p.customer.name if p.customer else None
            cust_phone = p.customer.phone if (p.customer and getattr(p.customer, 'phone', None)) else None
            user_name = f"{p.user.first_name or ''} {p.user.last_name or ''}".strip() or p.user.username if p.user else None
            op_name = p.get_operation_type_display() if hasattr(p, 'get_operation_type_display') else getattr(p, 'operation_type', None)
            
            if p.status == 'open':
                status_label = 'Aberta'
                color = '#3b82f6'
            elif p.status == 'pending':
                status_label = 'Em Andamento'
                color = '#f59e0b'
            else:
                status_label = 'Finalizada'
                color = '#10b981'

            if p.priority == 'high' and p.status != 'closed':
                color = '#ef4444'
                priority_label = 'Alta'
            elif p.priority == 'medium' and p.status != 'closed':
                color = '#f59e0b'
                priority_label = 'Média'
            else:
                priority_label = 'Baixa' if p.priority == 'low' else ('Média' if p.priority == 'medium' else 'Alta')

            all_events.append({
                'id': f"pendency_{p.id}",
                'title': f"[Pendência #{p.id}] {p.title}",
                'description': p.description or '',
                'location': cust_name or '',
                'customer_name': cust_name,
                'customer_phone': cust_phone,
                'assigned_user': user_name,
                'operation_name': op_name,
                'opening_date': p.opening_date.isoformat() if (p.opening_date and hasattr(p.opening_date, 'isoformat')) else str(p.opening_date or ''),
                'forecast_date': p.forecast_date.isoformat() if (p.forecast_date and hasattr(p.forecast_date, 'isoformat')) else (str(p.forecast_date) if p.forecast_date else None),
                'start': date_iso,
                'end': date_iso,
                'allDay': False,
                'color': color,
                'source': 'pendency',
                'pendency_id': p.id,
                'priority': p.priority,
                'priority_label': priority_label,
                'status': p.status,
                'status_label': status_label
            })

        return Response(all_events, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='preview')
    def preview_feed(self, request):
        url = request.data.get('url')
        if not url:
            return Response({"error": "URL do feed não informada."}, status=status.HTTP_400_BAD_REQUEST)
        events = fetch_and_parse_webcal(url)
        return Response({"count": len(events), "events": events[:20]}, status=status.HTTP_200_OK)


class SystemMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        metrics = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "memory_used_mb": 0,
            "memory_total_mb": 0,
            "swap_percent": 0.0,
            "swap_used_mb": 0,
            "swap_total_mb": 0,
            "timestamp": int(time.time())
        }

        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                metrics.update({
                    "cpu_percent": round(cpu, 1),
                    "memory_percent": round(mem.percent, 1),
                    "memory_used_mb": round(mem.used / (1024 * 1024)),
                    "memory_total_mb": round(mem.total / (1024 * 1024)),
                    "swap_percent": round(swap.percent, 1),
                    "swap_used_mb": round(swap.used / (1024 * 1024)),
                    "swap_total_mb": round(swap.total / (1024 * 1024)),
                })
            except Exception:
                pass
        else:
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                mem_dict = {}
                for line in lines:
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        mem_dict[key] = int(val)
                
                total = mem_dict.get('MemTotal', 0)
                available = mem_dict.get('MemAvailable', mem_dict.get('MemFree', 0))
                used = total - available
                if total > 0:
                    metrics["memory_percent"] = round((used / total) * 100, 1)
                    metrics["memory_used_mb"] = round(used / 1024)
                    metrics["memory_total_mb"] = round(total / 1024)
                
                swap_total = mem_dict.get('SwapTotal', 0)
                swap_free = mem_dict.get('SwapFree', 0)
                swap_used = swap_total - swap_free
                if swap_total > 0:
                    metrics["swap_percent"] = round((swap_used / swap_total) * 100, 1)
                    metrics["swap_used_mb"] = round(swap_used / 1024)
                    metrics["swap_total_mb"] = round(swap_total / 1024)
            except Exception:
                pass

        return Response(metrics, status=status.HTTP_200_OK)






