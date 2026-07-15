import csv
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tickets.models import Customer, CustomerContact

csv_path = '/app/contatos_cliente_202607151129.csv'

created_count = 0
updated_count = 0
skipped_count = 0

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cliente_id = row.get('cliente_id')
        nome = row.get('nome')
        
        if not cliente_id or not nome:
            skipped_count += 1
            continue
            
        try:
            customer = Customer.objects.get(id=int(cliente_id))
        except Customer.DoesNotExist:
            print(f"Customer with ID {cliente_id} not found. Skipping contact {nome}.")
            skipped_count += 1
            continue
            
        # Parse fields
        phone = row.get('fone') or None
        cellphone = row.get('celular') or None
        whatsapp = row.get('whatsapp') or None
        email = row.get('email') or None
        sector = row.get('setor') or None
        role = row.get('cargo') or None
        observation = row.get('observacao') or None
        
        # Handle birth date
        birth_date = None
        data_nasc = row.get('data_nasc')
        if data_nasc:
            try:
                # Assuming format 'YYYY-MM-DD'
                birth_date = datetime.strptime(data_nasc.strip(), '%Y-%m-%d').date()
            except ValueError:
                try:
                    # Try format 'DD/MM/YYYY'
                    birth_date = datetime.strptime(data_nasc.strip(), '%d/%m/%Y').date()
                except ValueError:
                    pass
        
        contact, created = CustomerContact.objects.update_or_create(
            customer=customer,
            name=nome.strip(),
            defaults={
                'phone': phone.strip() if phone else None,
                'cellphone': cellphone.strip() if cellphone else None,
                'whatsapp': whatsapp.strip() if whatsapp else None,
                'email': email.strip() if email else None,
                'birth_date': birth_date,
                'sector': sector.strip() if sector else None,
                'role': role.strip() if role else None,
                'observation': observation.strip() if observation else None,
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1

print(f"Import complete! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}")
