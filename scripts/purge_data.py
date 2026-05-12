
import os
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
django.setup()

from tickets.models import Message, Ticket, Contact, Customer, CustomerContact

def purge():
    print("Iniciando limpeza total da base de dados...")
    
    m_count = Message.objects.count()
    Message.objects.all().delete()
    print(f"- {m_count} Mensagens removidas.")
    
    t_count = Ticket.objects.count()
    Ticket.objects.all().delete()
    print(f"- {t_count} Tickets removidos.")
    
    cc_count = CustomerContact.objects.count()
    CustomerContact.objects.all().delete()
    print(f"- {cc_count} Contatos Adicionais removidos.")
    
    c_count = Contact.objects.count()
    Contact.objects.all().delete()
    print(f"- {c_count} Contatos de WhatsApp removidos.")
    
    cust_count = Customer.objects.count()
    Customer.objects.all().delete()
    print(f"- {cust_count} Clientes removidos.")
    
    print("\nLimpeza concluída com sucesso! A base está pronta para novos testes.")

if __name__ == "__main__":
    purge()
