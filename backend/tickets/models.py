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
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(null=True, blank=True)
    document = models.CharField(max_length=20, null=True, blank=True) # CPF/CNPJ
    address = models.TextField(null=True, blank=True)
    profile_pic = models.URLField(null=True, blank=True)
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
