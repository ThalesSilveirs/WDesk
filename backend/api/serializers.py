from rest_framework import serializers
from tickets.models import Company, User, Connection, Contact, Ticket, Message, Customer, CustomerContact, MessageReaction

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
        fields = ['id', 'name', 'is_active', 'evolution_api_url', 'evolution_api_key']

class UserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 'company', 'department', 'status')

    def get_status(self, obj):
        import redis
        from django.conf import settings
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

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'

class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    additional_contacts = CustomerContactSerializer(many=True, read_only=True)
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'company': {'read_only': True}
        }

class ContactSerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    class Meta:
        model = Contact
        fields = '__all__'

class MessageReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReaction
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    contact_name = serializers.CharField(source='ticket.contact.name', read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    contact_details = ContactSerializer(source='contact', read_only=True)
    attendant_details = UserSerializer(source='user', read_only=True)
    last_messages = MessageSerializer(source='messages', many=True, read_only=True)
    customer_details = CustomerSerializer(source='contact.customer', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
