from rest_framework import serializers
from tickets.models import Company, User, Connection, Contact, Ticket, Message, Customer, CustomerContact, MessageReaction, QuickReply, AbsenceSchedule, City, Pendency, PendencyImage, PendencyMovement, WebcalFeed

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['company_id'] = str(self.user.company.id) if self.user.company else None
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adiciona campos customizados no payload do token
        token['company_id'] = str(user.company.id) if user.company else None
        return token

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'is_active', 'evolution_api_url', 'evolution_api_key', 'pendency_report_time', 'pendency_report_only_support']

import threading
import redis
from django.conf import settings
redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
redis_conn = redis.Redis.from_url(redis_url)

_local_cache = threading.local()

def get_cached_user_status(user_id):
    if not hasattr(_local_cache, 'user_statuses'):
        _local_cache.user_statuses = {}
    if user_id not in _local_cache.user_statuses:
        try:
            status_key = f"user_status_{user_id}"
            status_bytes = redis_conn.get(status_key)
            if status_bytes:
                status = status_bytes.decode('utf-8')
                if status == 'away':
                    res = "Ausente"
                elif status == 'offline':
                    res = "Offline"
                elif status == 'online':
                    res = "Online"
                else:
                    res = "Offline"
            else:
                is_active = redis_conn.exists(f"user_active_{user_id}")
                res = "Online" if is_active else "Offline"
        except Exception:
            res = "Offline"
        _local_cache.user_statuses[user_id] = res
    return _local_cache.user_statuses[user_id]

def clear_local_cache():
    if hasattr(_local_cache, 'user_statuses'):
        _local_cache.user_statuses.clear()

class UserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 'company', 'department', 'status', 'whatsapp')

    def get_status(self, obj):
        return get_cached_user_status(obj.id)

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'

class ConnectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        exclude = ('qrcode',)

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class ContactNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    additional_contacts = serializers.SerializerMethodField()
    city_relationship_details = CitySerializer(source='city_relationship', read_only=True)
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True}
        }

    def get_additional_contacts(self, obj):
        return ContactNestedSerializer(obj.contacts.all(), many=True, context=self.context).data

class ContactSerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    class Meta:
        model = Contact
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True}
        }

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)
        if data.get('birth_date') == '':
            data['birth_date'] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        # Auto-gerar remote_jid se estiver ausente mas houver whatsapp/cellphone/phone
        remote_jid = attrs.get('remote_jid')
        company = attrs.get('company')
        
        if not company and 'request' in self.context:
            company = self.context['request'].user.company
            attrs['company'] = company

        if remote_jid and '@s.whatsapp.net' in str(remote_jid):
            num = str(remote_jid).split('@')[0]
            import re
            num_digits = re.sub(r'\D', '', num)
            if len(num_digits) in [10, 11] and not num_digits.startswith('55'):
                remote_jid = f"55{num_digits}@s.whatsapp.net"
                attrs['remote_jid'] = remote_jid
            
        if not remote_jid and company:
            raw_phone = attrs.get('whatsapp') or attrs.get('cellphone') or attrs.get('phone')
            if raw_phone:
                import re
                phone_digits = re.sub(r'\D', '', raw_phone)
                if phone_digits:
                    if len(phone_digits) in [10, 11] and not phone_digits.startswith('55'):
                        phone_digits = '55' + phone_digits
                    generated_jid = f"{phone_digits}@s.whatsapp.net"
                    
                    from tickets.models import Contact
                    existing = Contact.objects.filter(company=company, remote_jid=generated_jid).first()
                    if existing:
                        if not self.instance or self.instance.id != existing.id:
                            raise serializers.ValidationError({
                                "whatsapp": "Já existe um contato com este número de WhatsApp cadastrado."
                            })
                    attrs['remote_jid'] = generated_jid
        return attrs

class CustomerContactSerializer(ContactSerializer):
    pass

class MessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReaction
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    contact_name = serializers.CharField(source='ticket.contact.name', read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    ticket_user_id = serializers.IntegerField(source='ticket.user_id', read_only=True, allow_null=True)

    class Meta:
        model = Message
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    contact_details = ContactSerializer(source='contact', read_only=True)
    attendant_details = UserSerializer(source='user', read_only=True)
    last_messages = serializers.SerializerMethodField()
    customer_details = CustomerSerializer(source='contact.customer', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

    def get_last_messages(self, obj):
        # Limita para as últimas 10 mensagens para evitar sobrecarga na listagem/detalhes
        messages = obj.messages.order_by('-timestamp')[:10]
        return MessageSerializer(reversed(messages), many=True, context=self.context).data

class TicketListSerializer(serializers.ModelSerializer):
    contact_details = ContactSerializer(source='contact', read_only=True)
    attendant_details = UserSerializer(source='user', read_only=True)
    customer_details = CustomerSerializer(source='contact.customer', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'


class QuickReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickReply
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True},
            'created_by': {'read_only': True}
        }


class AbsenceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbsenceSchedule
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True}
        }


class CustomerLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name']


class UserLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ContactLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'remote_jid']


class PendencyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendencyImage
        fields = ['id', 'image', 'created_at']


class PendencyMovementSerializer(serializers.ModelSerializer):
    user_details = UserLightSerializer(source='user', read_only=True)

    class Meta:
        model = PendencyMovement
        fields = ['id', 'pendency', 'user', 'user_details', 'description', 'created_at']
        extra_kwargs = {
            'user': {'read_only': True}
        }


class PendencySerializer(serializers.ModelSerializer):
    images = PendencyImageSerializer(many=True, read_only=True)
    movements = PendencyMovementSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    customer_details = CustomerLightSerializer(source='customer', read_only=True)
    user_details = UserLightSerializer(source='user', read_only=True)
    contact_details = ContactLightSerializer(source='contact', read_only=True)
    created_by_details = UserLightSerializer(source='created_by', read_only=True)

    class Meta:
        model = Pendency
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True},
            'created_by': {'read_only': True}
        }

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        pendency = super().create(validated_data)
        for img_base64 in uploaded_images:
            PendencyImage.objects.create(pendency=pendency, image=img_base64)
        return pendency

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        pendency = super().update(instance, validated_data)
        for img_base64 in uploaded_images:
            PendencyImage.objects.create(pendency=pendency, image=img_base64)
        return pendency


class WebcalFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebcalFeed
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True},
            'user': {'read_only': True}
        }




