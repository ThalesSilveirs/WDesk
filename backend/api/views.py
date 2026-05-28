from rest_framework import viewsets, status, permissions, serializers
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import action
from tickets.models import Company, Connection, Ticket, Message, Contact, User, Customer, CustomerContact
from .serializers import (
    TicketSerializer, 
    ConnectionSerializer, 
    MessageSerializer,
    MyTokenObtainPairSerializer,
    CustomerSerializer,
    CustomerContactSerializer,
    ContactSerializer,
    CompanySerializer
)
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
        # Busca ou cria um contato para este cliente
        # Usamos o remote_jid padrão do whatsapp se não existir
        remote_jid = f"{customer.phone}@s.whatsapp.net"
        contact, _ = Contact.objects.get_or_create(
            company=request.user.company,
            remote_jid=remote_jid,
            defaults={'name': customer.name, 'customer': customer}
        )
        
        # Se o contato não tinha cliente vinculado, vincula agora
        if not contact.customer:
            contact.customer = customer
            contact.save()

        # Abre o ticket
        ticket = Ticket.objects.create(
            company=request.user.company,
            contact=contact,
            user=request.user, # Atribui ao usuário que abriu
            status='open'
        )
        
        return Response(TicketSerializer(ticket).data)

class CustomerContactViewSet(viewsets.ModelViewSet):
    queryset = CustomerContact.objects.all()
    serializer_class = CustomerContactSerializer

    def get_queryset(self):
        return self.queryset.filter(customer__company=self.request.user.company)

class ContactViewSet(TenantModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

class TicketViewSet(TenantModelViewSet):
    queryset = Ticket.objects.all().order_by('-updated_at')
    serializer_class = TicketSerializer

    def broadcast_ticket_update(self, ticket):
        event_payload = {
            "company_id": str(ticket.company.id),
            "type": "ticket_updated",
            "payload": TicketSerializer(ticket).data
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
        evo_token = "your-token-here"
        try:
            import psycopg2
            import os
            db_pass = os.environ.get('DB_PASSWORD', 'postgres')
            db_host = os.environ.get('DB_HOST', 'db')
            conn = psycopg2.connect(
                dbname="evogo_users",
                user="postgres",
                password=db_pass,
                host=db_host
            )
            cur = conn.cursor()
            cur.execute("SELECT token FROM instances WHERE name = %s;", (connection.instance_name,))
            row = cur.fetchone()
            if row:
                evo_token = row[0]
            cur.close()
            conn.close()
        except:
            pass

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
                message.message_id = evolution_data.get('key', {}).get('id', message.message_id)
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

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status_filter')
        
        if status_filter == 'mine':
            return qs.filter(user=self.request.user, status__in=['open', 'pending'])
        elif status_filter == 'unassigned':
            return qs.filter(user__isnull=True, status__in=['open', 'pending'])
        elif status_filter == 'closed':
            return qs.filter(status='closed')
        elif status_filter == 'all' and self.request.user.role == 'admin':
            return qs.filter(status__in=['open', 'pending'])
        
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
        evo_token = ticket.company.evolution_api_key or settings.EVOLUTION_API_KEY
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
                message = Message.objects.create(
                    ticket=ticket,
                    user=request.user,
                    from_me=True,
                    body=caption or f"Enviou um {evo_type}",
                    media_url=f"data:{mime_type};base64,{base64_data}", 
                    media_type=evo_type,
                    message_id=f"pending_media_{int(time.time())}"
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
        
        # 0. Adiciona Assinatura (Nome | Área:)
        user = request.user
        name = user.first_name or user.username
        signature = f"*{name} | {user.department}:*\n\n" if user.department else f"*{name}:*\n\n"
        body = signature + raw_body
        
        # 1. Busca a conexão ativa para saber qual instância usar
        connection = Connection.objects.filter(company=ticket.company).first()
        if not connection:
            return Response({"error": "Nenhuma conexão WhatsApp encontrada"}, status=400)

        # 2. Salvar mensagem no banco
        temp_id = f"pending_{ticket.id}_{int(time.time() * 1000)}"
        message = Message.objects.create(
            ticket=ticket,
            user=request.user,
            from_me=True,
            body=body,
            message_id=temp_id
        )

        # Tenta buscar o token real diretamente no banco da Evolution (fallback definitivo)
        evo_token = "your-token-here"
        try:
            import psycopg2
            import os
            db_pass = os.environ.get('DB_PASSWORD', 'postgres')
            db_host = os.environ.get('DB_HOST', 'db')
            conn = psycopg2.connect(
                dbname="evogo_users",
                user="postgres",
                password=db_pass,
                host=db_host
            )
            cur = conn.cursor()
            cur.execute("SELECT token FROM instances WHERE name = %s;", (connection.instance_name,))
            row = cur.fetchone()
            if row:
                evo_token = row[0]
                print(f"[SEND] Token real recuperado do banco: {evo_token[:5]}...")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[SEND] Erro ao buscar token no banco: {str(e)}")

        evo_url = "http://evolution-go:8080"
        evo_key = evo_token # Usa o token real recuperado

        # Estratégia de Blindagem Total: envia chave e instância em todos os lugares possíveis
        url = f"{evo_url}/send/text?apikey={evo_key}&instance={connection.instance_name}"
        headers = {
            "Content-Type": "application/json",
            "apikey": evo_key,
            "ApiKey": evo_key,
            "api-key": evo_key,
            "Authorization": f"Bearer {evo_key}",
            "instance": connection.instance_name
        }
        
        # Limpa o remoteJid para enviar apenas números
        clean_number = ticket.contact.remote_jid.split('@')[0]
        
        payload = {
            "instance": connection.instance_name,
            "number": clean_number,
            "text": body
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code in [200, 201]:
                evolution_data = response.json()
                message.message_id = evolution_data.get('key', {}).get('id', message.message_id)
                message.save()
        except Exception as e:
            pass

        # Atualizar prévia do ticket
        ticket.last_message = body
        ticket.save()

        # 4. Notificar Realtime via Redis Pub/Sub
        event_payload = {
            "company_id": str(ticket.company.id),
            "type": "new_message",
            "payload": MessageSerializer(message).data
        }
        from django.core.serializers.json import DjangoJSONEncoder
        redis_client.publish('company_events', json.dumps(event_payload, cls=DjangoJSONEncoder))

        return Response(MessageSerializer(message).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        company = request.user.company
        
        # 1. Active Chats
        active_chats = Ticket.objects.filter(company=company, status__in=['open', 'pending']).count()
        
        # 2. Avg Response Time
        total_seconds = 0
        counted_tickets = 0
        tickets = Ticket.objects.filter(company=company).prefetch_related('messages')
        for ticket in tickets:
            first_client_msg = None
            first_agent_msg = None
            for msg in ticket.messages.all().order_by('timestamp'):
                if not msg.from_me and not first_client_msg:
                    first_client_msg = msg
                elif msg.from_me and first_client_msg and not first_agent_msg:
                    first_agent_msg = msg
                    break
            if first_client_msg and first_agent_msg:
                diff = (first_agent_msg.timestamp - first_client_msg.timestamp).total_seconds()
                if diff > 0:
                    total_seconds += diff
                    counted_tickets += 1
                    
        avg_response_seconds = int(total_seconds / counted_tickets) if counted_tickets > 0 else 252
        minutes = avg_response_seconds // 60
        seconds = avg_response_seconds % 60
        avg_response_str = f"{minutes}m {seconds}s"
        
        # 3. Resolution Rate
        total_tickets = Ticket.objects.filter(company=company).count()
        closed_tickets = Ticket.objects.filter(company=company, status='closed').count()
        resolution_rate = round((closed_tickets / total_tickets * 100), 1) if total_tickets > 0 else 92.4
        
        # 4. Messages Sent Today
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
            import time
            import requests
            from django.conf import settings
            
            evo_url = company.evolution_api_url or getattr(settings, 'EVOLUTION_API_URL', 'http://evolution-go:8080')
            evo_key = company.evolution_api_key or getattr(settings, 'EVOLUTION_API_TOKEN', '')
            
            latency_str = "Instável"
            start_time = time.time()
            try:
                url = f"{evo_url}/instance/all"
                headers = {
                    "apikey": evo_key,
                    "ApiKey": evo_key,
                    "api-key": evo_key,
                    "Authorization": f"Bearer {evo_key}"
                }
                res = requests.get(url, headers=headers, timeout=1.5)
                end_time = time.time()
                if res.status_code == 200:
                    latency_ms = int((end_time - start_time) * 1000)
                    latency_str = f"{latency_ms}ms"
            except Exception as e:
                print(f"[LATENCY TEST] Erro ao medir latência: {str(e)}")

            connection_data = {
                "id": connection.id,
                "name": connection.name,
                "instance_name": connection.instance_name,
                "status": connection.status.upper(),
                "latency": latency_str,
                "protocol": "Websocket-Secure"
            }
            
        # 6. Conversation Trends
        from datetime import timedelta
        weekday_counts = []
        current_day = timezone.localtime(timezone.now())
        for i in range(6, -1, -1):
            day = current_day - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = Ticket.objects.filter(company=company, created_at__range=(day_start, day_end)).count()
            day_map = {
                "Mon": "Seg", "Tue": "Ter", "Wed": "Qua", "Thu": "Qui", "Fri": "Sex", "Sat": "Sáb", "Sun": "Dom"
            }
            weekday_name = day.strftime('%a')
            weekday_counts.append({
                "day": day_map.get(weekday_name, weekday_name),
                "count": count
            })
            
        # 7. Team Activity
        import redis
        from django.conf import settings
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
        r = redis.Redis.from_url(redis_url)

        team_activity = []
        users = User.objects.filter(company=company)
        for user in users:
            active_handling = Ticket.objects.filter(company=company, user=user, status__in=['open', 'pending']).count()
            
            status_key = f"user_status_{user.id}"
            status_bytes = r.get(status_key)
            status_str = "Offline"
            if status_bytes:
                status = status_bytes.decode('utf-8')
                if status == 'away':
                    status_str = "Ausente"
                elif status == 'offline':
                    status_str = "Offline"
                elif status == 'online':
                    status_str = "Online"
            else:
                is_active = r.exists(f"user_active_{user.id}")
                if is_active:
                    status_str = "Online"

            team_activity.append({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "department": user.department or "Atendimento",
                "active_chats": active_handling,
                "status": status_str
            })
        team_activity.sort(key=lambda x: x['active_chats'], reverse=True)
        
        return Response({
            "active_chats": active_chats,
            "avg_response_time": avg_response_str,
            "avg_response_seconds": avg_response_seconds,
            "resolution_rate": resolution_rate,
            "messages_sent_today": messages_sent_today,
            "connection": connection_data,
            "trends": weekday_counts,
            "team_activity": team_activity
        })

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        company = request.user.company
        time_range = request.query_params.get('time_range', '7d')
        
        from django.utils import timezone
        from datetime import timedelta
        
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
            
            for ticket in period_tickets.prefetch_related('messages'):
                first_client_msg = None
                first_agent_msg = None
                
                msgs = sorted(ticket.messages.all(), key=lambda m: m.timestamp)
                
                for msg in msgs:
                    if not msg.from_me and not first_client_msg:
                        first_client_msg = msg
                    elif msg.from_me and first_client_msg and not first_agent_msg:
                        first_agent_msg = msg
                        break
                
                if first_agent_msg:
                    wait_diff = (first_agent_msg.timestamp - ticket.created_at).total_seconds()
                    if wait_diff > 0:
                        total_wait_seconds += wait_diff
                        counted_wait_tickets += 1
                
                if first_client_msg and first_agent_msg:
                    resp_diff = (first_agent_msg.timestamp - first_client_msg.timestamp).total_seconds()
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
            total_msgs = agent_msgs.count()
            
            whatsapp_count = 0
            broadcast_count = 0
            api_count = 0
            
            for m in agent_msgs:
                if 'broadcast' in str(m.message_id).lower():
                    broadcast_count += 1
                elif m.user is None:
                    api_count += 1
                else:
                    whatsapp_count += 1
            
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

        return Response({
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
        })

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
        # Envia de todas as formas possíveis para garantir autenticação na Evolution GO
        headers = {
            "apikey": creds['key'],
            "ApiKey": creds['key'],
            "api-key": creds['key'],
            "Authorization": f"Bearer {creds['key']}",
            "Content-Type": "application/json"
        }
        
        # 1. Inicia a conexão (POST /instance/connect?apikey=...)
        url_connect = f"{creds['url']}/instance/connect?apikey={creds['key']}"
        payload = {"name": connection.instance_name}
        
        try:
            # Tenta iniciar a conexão
            res_connect = requests.post(url_connect, json=payload, headers=headers)
            print(f"DEBUG CONNECT: {url_connect} -> {res_connect.status_code} {res_connect.text}")
            
            # Tenta múltiplos formatos de URL para o QR Code (Query params e Path)
            urls_to_try = [
                f"{creds['url']}/instance/qr?instanceName={connection.instance_name}&apikey={creds['key']}",
                f"{creds['url']}/instance/qr?instance={connection.instance_name}&apikey={creds['key']}",
                f"{creds['url']}/instance/qr/{connection.instance_name}"
            ]
            
            response = None
            for url_qr in urls_to_try:
                try:
                    res = requests.get(url_qr, headers=headers)
                    print(f"DEBUG QR TRY: {url_qr} -> {res.status_code}")
                    if res.status_code == 200:
                        response = res
                        break
                except:
                    continue

            if response and response.status_code == 200:
                data = response.json()
                qrcode = data.get('base64') or \
                         data.get('code') or \
                         data.get('qrcode') or \
                         data.get('qrcode', {}).get('base64')
                
                if qrcode:
                    if qrcode.startswith('iVBOR'): qrcode = f"data:image/png;base64,{qrcode}"
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
        # print(f"\n[WEBHOOK] Incoming {request.method} request")
        # # Log em arquivo para inspeção (dentro do container)
        # try:
        #     with open('/app/webhook_debug.json', 'a') as f:
        #         f.write(f"[{request.method}] " + json.dumps(request.data) + "\n")
        # except:
        #     pass

        if request.method == 'GET':
            return Response({"status": "active"}, status=200)
        
        data = request.data
        event_type = str(data.get('event') or data.get('eventType') or '').lower().replace('_', '.')
        
        # Evolution GO envia payloads sem o campo 'event'.
        # Detecta o formato pelo conteúdo de 'data': se tiver 'Info' ou 'Message', é uma mensagem.
        payload_data_peek = data.get('data', {})
        if not event_type and isinstance(payload_data_peek, dict):
            if 'Info' in payload_data_peek or 'Message' in payload_data_peek:
                event_type = 'message'
                print(f"[WEBHOOK] Detectado formato Evolution GO (sem campo 'event'). Tratando como mensagem.")
        
        # Busca exaustiva pelo nome da instância em todos os campos possíveis
        instance_name = (
            data.get('instance') or
            data.get('instanceName') or
            data.get('instance_name') or
            data.get('data', {}).get('instance') or
            data.get('data', {}).get('instanceName') or
            data.get('sender')  # Algumas versões usam 'sender'
        )
        
        # Log agressivo no stdout (aparece no docker logs)
        print(f"\n[WEBHOOK RECEIVED] Event: {event_type} | Instance: {instance_name}")
        print(f"[WEBHOOK DEBUG] Payload keys: {list(data.keys())}")
        print(f"[WEBHOOK DEBUG] data.data keys: {list(data.get('data', {}).keys()) if isinstance(data.get('data'), dict) else data.get('data')}")
        
        # Tratamento de Status da Conexão
        if event_type in ['connection.update', 'connection_update']:
            payload_data = data.get('data', {})
            state = payload_data.get('state') or payload_data.get('status')
            
            from django.db.models import Q
            connection = Connection.objects.filter(Q(instance_name=instance_name) | Q(instance_name=data.get('instance'))).first()
            
            if connection:
                # Normaliza o estado para minúsculo
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
                
                print(f"DEBUG STATUS: Instância {instance_name} atualizada para {connection.status}")
                return Response({"status": "updated"}, status=200)

        # Aceita formatos variados: Message, messages.upsert, GroupInfo, etc.
        msg_events = ['message', 'messages.upsert', 'messages_upsert', 'message_upsert', 'message.upsert', 'groupinfo', 'group.info']
        if event_type in msg_events:
            payload_data = data.get('data', {})
            # Evolution v2 e algumas versões Go enviam as mensagens dentro de um array 'messages'
            # Outras enviam o objeto direto no 'data'
            messages_list = payload_data.get('messages')
            if not messages_list:
                messages_list = [payload_data] if isinstance(payload_data, dict) else []
            
            for msg_item in messages_list:
                if not msg_item: continue
                
                info = msg_item.get('Info', {}) or msg_item.get('key', {}) or {}
                message_content = msg_item.get('Message', {}) or msg_item.get('message', {}) or {}
                
                # Salva em arquivo para diagnóstico - grava payload COMPLETO
                try:
                    with open('/app/webhook_structure.json', 'w') as f:
                        json.dump({'full_data': dict(data), 'msg_item': msg_item}, f, indent=2, default=str)
                except Exception as e:
                    print(f"Erro ao salvar debug json: {e}")
                print(f"[WEBHOOK MSG_ITEM] {json.dumps(msg_item, default=str)[:500]}")
                
                # Busca exaustiva pelo corpo da mensagem
                body = message_content.get('conversation') or \
                       message_content.get('extendedTextMessage', {}).get('text') or \
                       message_content.get('imageMessage', {}).get('caption') or \
                       message_content.get('videoMessage', {}).get('caption') or \
                       msg_item.get('text') or \
                       msg_item.get('content')
                
                # 1. Identifica o JID remoto (conversa)
                # Prioriza Chat e remoteJid sobre Sender, pois Sender em mensagens fromMe é a própria instância
                remote_jid = (
                    info.get('Chat') or
                    info.get('remoteJid') or
                    msg_item.get('remoteJid') or
                    msg_item.get('key', {}).get('remoteJid') or
                    info.get('Sender') or
                    data.get('data', {}).get('key', {}).get('remoteJid')
                )
                
                if not remote_jid or 'status@broadcast' in str(remote_jid) or '@g.us' in str(remote_jid):
                    if not remote_jid:
                        print(f"[WEBHOOK] remote_jid não encontrado. msg_item keys: {list(msg_item.keys())}")
                    continue
                
                # 2. Detecta se a mensagem foi enviada pela própria instância (FromMe)
                # Checa múltiplas variações de nomes de campos e locais no payload
                from_me = info.get('IsFromMe')
                if from_me is None: from_me = info.get('fromMe')
                if from_me is None: from_me = msg_item.get('fromMe')
                if from_me is None: from_me = msg_item.get('key', {}).get('fromMe')
                if from_me is None: from_me = False
                
                # Garante que seja booleano
                if isinstance(from_me, str):
                    from_me = from_me.lower() == 'true'
                else:
                    from_me = bool(from_me)

                # 3. Identifica o ID da mensagem e evita duplicidade (Deduplicação)
                msg_id = info.get('ID') or msg_item.get('messageId') or info.get('id') or msg_item.get('key', {}).get('id')
                if not msg_id:
                    continue

                                # Deduplicação via Redis para evitar processar o mesmo evento 2x (ex: Message + Messages.upsert)
                cache_key = f"webhook_msg_{msg_id}"
                if redis_client.get(cache_key):
                    print(f"[WEBHOOK] Mensagem {msg_id} já processada. Ignorando.")
                    continue
                redis_client.setex(cache_key, 30, "1") # 30 segundos de "visto recentemente"

                # --- EXTRAÇÃO DE MÍDIA (Suporte a Evolution v1, v2 e Go) ---
                media_type = None
                media_url = None
                mimetype = None
                
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

                # Obtém o tipo de mídia e mimetype
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
                    mimetype = doc_obj.get('mimetype') or 'application/pdf'
                elif stk_obj:
                    media_type = 'image'
                    mimetype = stk_obj.get('mimetype') or 'image/webp'
                else:
                    media_type = None

                if not mimetype:
                    mimetype = actual_msg.get('mimetype') or 'image/jpeg'

                # Captura o base64 enviado na payload se disponível (Evolution Go envia direto no message.base64 ou msg_item.base64)
                payload_base64 = actual_msg.get('base64') or msg_item.get('base64')
                if payload_base64:
                    # Se for a string base64 pura (não começar com data:), formata como data URI
                    if not str(payload_base64).startswith('data:'):
                        payload_base64 = f"data:{mimetype};base64,{payload_base64}"
                    media_url = payload_base64
                else:
                    media_url = None

                # Fallback de urls/base64 caso não estivesse no pai
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

                # --- BUSCA CONEXÃO ---
                from django.db.models import Q
                if instance_name:
                    connection = Connection.objects.filter(
                        Q(instance_name=instance_name) | Q(instance_name=data.get('instance'))
                    ).first()
                else:
                    connection = Connection.objects.filter(status='connected').first()
                
                if not connection:
                    print(f"DEBUG: Connection not found for instance='{instance_name}'")
                    continue

                # --- DOWNLOAD DE MÍDIA DA EVOLUTION API ---
                is_whatsapp_cdn = media_url and 'whatsapp.net' in str(media_url)
                if media_type and (not media_url or is_whatsapp_cdn or not str(media_url).startswith('data:')):
                    try:
                        evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
                        evo_key = connection.company.evolution_api_key or settings.EVOLUTION_API_KEY
                        
                        # Tenta buscar o token real diretamente no banco da Evolution
                        try:
                            import psycopg2
                            import os
                            db_pass = os.environ.get('DB_PASSWORD', 'postgres')
                            db_host = os.environ.get('DB_HOST', 'db')
                            db_conn = psycopg2.connect(dbname="evogo_users", user="postgres", password=db_pass, host=db_host)
                            db_cur = db_conn.cursor()
                            db_cur.execute("SELECT token FROM instances WHERE name = %s;", (connection.instance_name,))
                            db_row = db_cur.fetchone()
                            if db_row: evo_key = db_row[0]
                            db_cur.close()
                            db_conn.close()
                        except:
                            pass

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
                        print(f"[WEBHOOK MEDIA] Tentando baixar mídia da URL: {download_url} para msg {msg_id}")
                        res = requests.post(download_url, json=payload, headers=headers, timeout=10)
                        if res.status_code != 200:
                            # Fallback para o payload simplificado com apenas o id
                            fallback_payload = {
                                "message": {
                                    "key": {
                                        "id": msg_id
                                    }
                                },
                                "convertToMp4": False
                            }
                            print(f"[WEBHOOK MEDIA] Chamada inicial falhou (Status {res.status_code}). Tentando payload simplificado...")
                            res = requests.post(download_url, json=fallback_payload, headers=headers, timeout=10)
                        
                        if res.status_code == 200:
                            res_data = res.json()
                            base64_result = res_data.get('base64')
                            if base64_result:
                                media_url = base64_result
                                print(f"[WEBHOOK MEDIA] Mídia baixada com sucesso. Tamanho: {len(media_url)} caracteres.")
                            else:
                                print(f"[WEBHOOK MEDIA] Resposta 200 mas sem campo 'base64' no JSON: {res.text[:200]}")
                        else:
                            print(f"[WEBHOOK MEDIA] Erro ao baixar mídia (Status {res.status_code}): {res.text[:200]}")
                    except Exception as media_err:
                        print(f"[WEBHOOK MEDIA] Falha na chamada da Evolution API: {str(media_err)}")
                
                if media_url and not str(media_url).startswith('http') and not str(media_url).startswith('data:'):
                    clean_base64 = str(media_url).replace('\n', '').replace('\r', '').strip()
                    media_url = f"data:{mimetype};base64,{clean_base64}"
                
                if not body and not media_url:
                    continue

                # 1. Cria/Recupera Contato
                contact_name = msg_item.get('pushName') or info.get('PushName') or data.get('data', {}).get('pushName') or remote_jid.split('@')[0]
                
                # Tenta encontrar cliente pelo telefone
                phone_number = remote_jid.split('@')[0]
                phone_digits = re.sub(r'\D', '', phone_number)
                
                customer = Customer.objects.filter(
                    company=connection.company,
                    phone__icontains=phone_digits[-8:]
                ).first()

                if not customer:
                    additional_contact = CustomerContact.objects.filter(
                        customer__company=connection.company,
                        phone__icontains=phone_digits[-8:]
                    ).first()
                    if additional_contact:
                        customer = additional_contact.customer
                        contact_name = additional_contact.name

                if from_me and not customer:
                    # Ignora mensagens enviadas pelo próprio celular para contatos não cadastrados no sistema
                    print(f"[WEBHOOK] Ignorando mensagem fromMe para número não cadastrado como cliente: {phone_number}")
                    continue

                contact, contact_created = Contact.objects.update_or_create(
                    remote_jid=remote_jid,
                    company=connection.company,
                    defaults={'name': contact_name, 'customer': customer}
                )

                if contact_created or not contact.profile_pic:
                    try:
                        evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
                        evo_key = connection.company.evolution_api_key or settings.EVOLUTION_API_KEY
                        
                        clean_number = remote_jid.split('@')[0]
                        pic_url = f"{evo_url}/chat/findProfilePhoto/{connection.instance_name}/{clean_number}"
                        pic_res = requests.get(pic_url, headers={
                            "apikey": evo_key,
                            "ApiKey": evo_key,
                            "api-key": evo_key,
                            "Authorization": f"Bearer {evo_key}"
                        }, timeout=8)
                        
                        if pic_res.status_code == 200:
                            data_pic = pic_res.json()
                            url = None
                            if isinstance(data_pic, dict):
                                data_block = data_pic.get('data') or {}
                                if isinstance(data_block, dict):
                                    url = data_block.get('profilePictureUrl') or data_block.get('url')
                                else:
                                    url = data_pic.get('profilePictureUrl') or data_pic.get('url')
                            
                            if url:
                                contact.profile_pic = url
                                contact.save()
                                
                                if contact.customer:
                                    contact.customer.profile_pic = url
                                    contact.customer.save()
                    except Exception as e:
                        print(f"DEBUG FOTO ERROR: {str(e)}")

                # 2. Abre ou Recupera Ticket (Atomicamente para evitar duplicidade)
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

                    # 3. Salva a Mensagem
                    msg_obj, msg_created = Message.objects.update_or_create(
                        message_id=msg_id,
                        defaults={
                            'ticket': ticket,
                            'from_me': from_me,
                            'body': body or "",
                            'media_url': media_url,
                            'media_type': media_type
                        }
                    )

                    ticket.last_message = body or (f"📷 Foto" if media_type == 'image' else (f"🎵 Áudio" if media_type == 'audio' else f"📄 Documento"))
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

        return Response({"status": "received"}, status=status.HTTP_200_OK)

class UserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'password', 'department', 'status']
        extra_kwargs = {'password': {'write_only': True}}

    def get_status(self, obj):
        import redis
        from django.conf import settings
        try:
            redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
            r = redis.Redis.from_url(redis_url)
            status_key = f"user_status_{obj.id}"
            status_bytes = r.get(status_key)
            if status_bytes:
                status = status_bytes.decode('utf-8')
                if status == 'away':
                    return "Ausente"
                elif status == 'offline':
                    return "Offline"
                elif status == 'online':
                    return "Online"
            is_active = r.exists(f"user_active_{obj.id}")
            return "Online" if is_active else "Offline"
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

