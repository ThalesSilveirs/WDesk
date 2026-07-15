import csv
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tickets.models import Customer, Contact

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
        
        # Auto-generate remote_jid if possible
        remote_jid = None
        raw_phone = whatsapp or cellphone or phone
        if raw_phone:
            import re
            phone_digits = re.sub(r'\D', '', raw_phone)
            if phone_digits:
                if len(phone_digits) in [10, 11] and not phone_digits.startswith('55'):
                    phone_digits = '55' + phone_digits
                remote_jid = f"{phone_digits}@s.whatsapp.net"

        # Check if contact already exists by remote_jid (if available) or customer/name
        contact = None
        if remote_jid:
            contact = Contact.objects.filter(company=customer.company, remote_jid=remote_jid).first()
            
        if not contact:
            contact = Contact.objects.filter(customer=customer, name=nome.strip()).first()
            
        defaults = {
            'phone': phone.strip() if phone else None,
            'cellphone': cellphone.strip() if cellphone else None,
            'whatsapp': whatsapp.strip() if whatsapp else None,
            'email': email.strip() if email else None,
            'birth_date': birth_date,
            'sector': sector.strip() if sector else None,
            'role': role.strip() if role else None,
            'observation': observation.strip() if observation else None,
            'customer': customer,
            'name': nome.strip(),
        }
        if remote_jid:
            defaults['remote_jid'] = remote_jid
            
        if contact:
            # Update existing
            for k, v in defaults.items():
                setattr(contact, k, v)
            contact.save()
            updated_count += 1
        else:
            # Create new
            Contact.objects.create(
                company=customer.company,
                **defaults
            )
            created_count += 1

print(f"Import complete! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}")
