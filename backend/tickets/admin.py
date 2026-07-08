from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Company, User, Connection, Contact, Ticket, Message, Pendency, PendencyImage

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('company', 'role')}),
    )
    list_display = ('username', 'email', 'company', 'role', 'is_staff')
    list_filter = ('company', 'role', 'is_staff')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created_at', 'is_active')
    search_fields = ('name',)

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'instance_name', 'company', 'status', 'created_at')
    list_filter = ('status', 'company')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('remote_jid', 'name', 'company', 'created_at')
    search_fields = ('remote_jid', 'name')
    list_filter = ('company',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact', 'user', 'company', 'status', 'updated_at')
    list_filter = ('status', 'company', 'user')
    search_fields = ('contact__remote_jid', 'contact__name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'from_me', 'timestamp')
    list_filter = ('from_me', 'timestamp')
    readonly_fields = ('timestamp',)

@admin.register(Pendency)
class PendencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'customer', 'user', 'status', 'priority', 'operation_type', 'opening_date', 'forecast_date')
    list_filter = ('status', 'priority', 'operation_type', 'company', 'user')
    search_fields = ('title', 'description', 'customer__name')

@admin.register(PendencyImage)
class PendencyImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'pendency', 'created_at')

