from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid

class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Evolution API Settings
    evolution_api_url = models.CharField(max_length=255, null=True, blank=True)
    evolution_api_key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('attendant', 'Attendant'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendant')
    department = models.CharField(max_length=100, null=True, blank=True) # Área de atuação

class Connection(models.Model):
    STATUS_CHOICES = (
        ('disconnected', 'Disconnected'),
        ('connecting', 'Connecting'),
        ('connected', 'Connected'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='connections')
    name = models.CharField(max_length=100)
    instance_name = models.CharField(max_length=100, unique=True) # Evolution API Instance Name
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disconnected')
    qrcode = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    
    # Identificação
    name = models.CharField(max_length=255, verbose_name="Razão Social / Nome")
    fantasy_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(max_length=14, null=True, blank=True, db_index=True)
    cpf = models.CharField(max_length=11, null=True, blank=True, db_index=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    state_inscription = models.CharField(max_length=20, null=True, blank=True, verbose_name="Inscrição Estadual")
    municipal_inscription = models.CharField(max_length=20, null=True, blank=True, verbose_name="Inscrição Municipal")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    foundation_date = models.DateField(null=True, blank=True, verbose_name="Data de Fundação")
    
    # Contatos
    phone = models.CharField(max_length=20, db_index=True, verbose_name="Telefone Principal")
    phone2 = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone 2")
    mobile = models.CharField(max_length=20, null=True, blank=True, verbose_name="Celular")
    whatsapp = models.CharField(max_length=20, null=True, blank=True, verbose_name="WhatsApp")
    email = models.EmailField(null=True, blank=True)
    email_commercial = models.EmailField(max_length=100, null=True, blank=True, verbose_name="E-mail Comercial")
    email_financial = models.EmailField(max_length=100, null=True, blank=True, verbose_name="E-mail Financeiro")
    contact_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Contato Principal")
    contact_name2 = models.CharField(max_length=100, null=True, blank=True, verbose_name="Contato 2")
    
    # Endereço Principal (compatível com campo antigo 'address')
    address = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    complement = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    
    # Endereço de Cobrança
    billing_zip_code = models.CharField(max_length=10, null=True, blank=True)
    billing_address = models.CharField(max_length=150, null=True, blank=True)
    billing_number = models.CharField(max_length=20, null=True, blank=True)
    billing_neighborhood = models.CharField(max_length=100, null=True, blank=True)
    billing_city = models.CharField(max_length=100, null=True, blank=True)
    billing_state = models.CharField(max_length=2, null=True, blank=True)
    
    # Endereço de Entrega
    delivery_zip_code = models.CharField(max_length=10, null=True, blank=True)
    delivery_address = models.CharField(max_length=150, null=True, blank=True)
    delivery_number = models.CharField(max_length=20, null=True, blank=True)
    delivery_neighborhood = models.CharField(max_length=100, null=True, blank=True)
    delivery_city = models.CharField(max_length=100, null=True, blank=True)
    delivery_state = models.CharField(max_length=2, null=True, blank=True)

    # Financeiro / Crédito
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_limit_expiry = models.DateField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bank_code = models.IntegerField(null=True, blank=True)
    bank_agency = models.CharField(max_length=20, null=True, blank=True)
    bank_account = models.CharField(max_length=20, null=True, blank=True)
    due_day = models.IntegerField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    optante_simples = models.BooleanField(default=False)
    consumidor_final = models.BooleanField(default=True)
    nao_contribuinte = models.BooleanField(default=False)
    
    # Outros Campos Auxiliares do ERP
    representative_id = models.IntegerField(null=True, blank=True)
    carrier_id = models.IntegerField(null=True, blank=True)
    region_id = models.IntegerField(null=True, blank=True)
    group_id = models.IntegerField(null=True, blank=True)
    
    # Observações e Controles
    obs = models.TextField(null=True, blank=True)
    obs_financial = models.TextField(null=True, blank=True)
    obs_invoice = models.TextField(null=True, blank=True)
    credit_opinion = models.TextField(null=True, blank=True)
    
    # Status e Sistema
    is_blocked = models.BooleanField(default=False)
    profile_pic = models.URLField(null=True, blank=True)
    document = models.CharField(max_length=20, null=True, blank=True) # CPF/CNPJ original para compatibilidade
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

class CustomerContact(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='additional_contacts')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.customer.name})"

class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    remote_jid = models.CharField(max_length=100) # Ex: 5511999999999@s.whatsapp.net
    name = models.CharField(max_length=255, null=True, blank=True)
    profile_pic = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'remote_jid')

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tickets')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    subject = models.CharField(max_length=255, null=True, blank=True)
    resolution = models.TextField(null=True, blank=True)
    
    last_message = models.TextField(null=True, blank=True)
    unread_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    from_me = models.BooleanField(default=False)
    body = models.TextField()
    media_url = models.TextField(null=True, blank=True)
    media_type = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    message_id = models.CharField(max_length=255, unique=True) # WhatsApp Message ID

    class Meta:
        ordering = ['timestamp', 'id']
