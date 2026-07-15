import os
import csv
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from tickets.models import Company, Customer, Contact, CustomerContact, Pendency, PendencyMovement

User = get_user_model()

def clean_doc_string(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() == 'NULL':
        return None
    if 'E+' in val_str or 'e+' in val_str:
        try:
            val_clean = val_str.replace(',', '.')
            float_val = float(val_clean)
            int_str = str(int(float_val))
            return int_str
        except Exception:
            pass
    digits = ''.join(c for c in val_str if c.isdigit())
    return digits if digits else None

def parse_date(val):
    if not val or str(val).strip().upper() in ('NULL', '', 'NONE'):
        return None
    val_str = str(val).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_decimal(val):
    if not val or str(val).strip().upper() in ('NULL', '', 'NONE'):
        return None
    try:
        val_clean = str(val).strip().replace(',', '.')
        return Decimal(val_clean)
    except Exception:
        return None

def parse_int(val):
    if not val or str(val).strip().upper() in ('NULL', '', 'NONE'):
        return None
    try:
        val_clean = str(val).strip().split('.')[0]
        return int(val_clean)
    except Exception:
        return None

def parse_bool(val):
    if not val or str(val).strip().upper() in ('NULL', '', 'NONE', '0', 'FALSE'):
        return False
    val_str = str(val).strip().upper()
    if val_str in ('1', 'TRUE', 'Y', 'S', 'SIM'):
        return True
    return False

def parse_datetime(date_str, time_str):
    if not date_str or str(date_str).strip().upper() in ('NULL', '', 'NONE'):
        return None
    d_str = str(date_str).strip()
    t_str = str(time_str).strip() if (time_str and str(time_str).strip().upper() != 'NULL') else '00:00:00'
    
    # Strip quotes
    d_str = d_str.replace('"', '').replace("'", "")
    t_str = t_str.replace('"', '').replace("'", "")
    
    full_str = f"{d_str} {t_str}"
    for fmt in (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
    ):
        try:
            naive_dt = datetime.strptime(full_str, fmt)
            return make_aware(naive_dt)
        except ValueError:
            continue
            
    # Try just date
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            naive_dt = datetime.strptime(d_str, fmt)
            return make_aware(naive_dt)
        except ValueError:
            continue
            
    return None

class Command(BaseCommand):
    help = "Importa clientes, relacionamentos e movimentações históricas a partir de arquivos CSV sem duplicar."

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, default='/app/dados', help="Diretório onde estão os arquivos CSV")

    def handle(self, *args, **options):
        dados_dir = options['dir']
        self.stdout.write(f"Buscando arquivos CSV no diretório: {dados_dir}")

        # Localizar arquivos
        clientes_file = None
        rel_file = None
        mov_file = None

        if not os.path.exists(dados_dir):
            self.stderr.write(self.style.ERROR(f"Diretório {dados_dir} não encontrado."))
            return

        for filename in os.listdir(dados_dir):
            if filename.startswith('clientes') and filename.endswith('.csv'):
                clientes_file = os.path.join(dados_dir, filename)
            elif filename.startswith('relacionamentos') and filename.endswith('.csv'):
                rel_file = os.path.join(dados_dir, filename)
            elif filename.startswith('mov_relacionamentos') and filename.endswith('.csv'):
                mov_file = os.path.join(dados_dir, filename)

        if not clientes_file or not rel_file or not mov_file:
            self.stderr.write(self.style.ERROR("Não foi possível encontrar todos os arquivos necessários (clientes, relacionamentos, mov_relacionamentos) no diretório especificado."))
            return

        # Obter empresa padrão
        company = Company.objects.first()
        if not company:
            self.stderr.write(self.style.ERROR("Nenhuma empresa (Company) cadastrada no sistema. Crie uma primeiro."))
            return

        self.stdout.write(f"Empresa selecionada: {company.name}")

        # Obter usuários para mapeamento
        users = list(User.objects.all())
        def get_user_by_ref(usuario_id, user_str):
            try:
                u_id = int(str(usuario_id).strip())
                for u in users:
                    if u.id == u_id:
                        return u
            except Exception:
                pass
            if user_str:
                u_clean = str(user_str).strip().lower()
                for u in users:
                    if u.username.lower() == u_clean:
                        return u
                for u in users:
                    if u.email.lower() == u_clean:
                        return u
                for u in users:
                    full_name = f"{u.first_name} {u.last_name}".strip().lower()
                    if u_clean in full_name or full_name in u_clean:
                        return u
            return users[0] if users else None

        # Ler arquivos
        try:
            with transaction.atomic():
                # 1. Limpar dados anteriores
                self.stdout.write("Limpando movimentações, pendências, contatos adicionais e clientes anteriores...")
                PendencyMovement.objects.all().delete()
                Pendency.objects.all().delete()
                CustomerContact.objects.all().delete()
                Customer.objects.all().delete()

                # 2. Importar Clientes
                self.stdout.write(f"Importando clientes de {clientes_file}...")
                with open(clientes_file, mode='r', encoding='utf-8-sig') as f:
                    delimiter = ';' if ';' in f.readline() else ','
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    customer_count = 0
                    for row in reader:
                        legacy_id = parse_int(row.get('id'))
                        name = row.get('nome')
                        if not legacy_id or not name:
                            continue
                        
                        phone = row.get('telefone') or row.get('celular') or row.get('whatsapp') or "(50) 0000-0000"
                        phone = str(phone).strip()
                        cnpj_clean = clean_doc_string(row.get('cnpj'))
                        cpf_clean = clean_doc_string(row.get('cpf'))
                        doc_comp = cnpj_clean or cpf_clean or ''

                        customer = Customer.objects.create(
                            id=legacy_id,
                            company=company,
                            name=name,
                            phone=phone,
                            fantasy_name=row.get('nomefantasia'),
                            cnpj=cnpj_clean,
                            cpf=cpf_clean,
                            rg=row.get('rg'),
                            state_inscription=row.get('inscricao'),
                            municipal_inscription=row.get('inscr_mun'),
                            birth_date=parse_date(row.get('data_nasc')),
                            foundation_date=parse_date(row.get('data_fundacao')),
                            optante_simples=parse_bool(row.get('optante_simples')),
                            consumidor_final=parse_bool(row.get('consumidor_final')),
                            nao_contribuinte=parse_bool(row.get('nao_contribuinte')),
                            phone2=row.get('telefone2'),
                            mobile=row.get('celular'),
                            whatsapp=row.get('whatsapp'),
                            email=row.get('email'),
                            email_commercial=row.get('email_comercial'),
                            email_financial=row.get('email_financeiro'),
                            contact_name=row.get('contato'),
                            contact_name2=row.get('contato2'),
                            address=row.get('endereco'),
                            zip_code=row.get('cep'),
                            number=row.get('numero'),
                            complement=row.get('complemento'),
                            neighborhood=row.get('bairro'),
                            city=row.get('cidade'),
                            state=row.get('estado'),
                            billing_zip_code=row.get('cep_cob'),
                            billing_address=row.get('endereco_cob'),
                            billing_number=row.get('numero_cob'),
                            billing_neighborhood=row.get('bairro_cob'),
                            billing_city=row.get('cidade_cob'),
                            billing_state=row.get('estado_cob'),
                            delivery_zip_code=row.get('cep_ent'),
                            delivery_address=row.get('endereco_ent'),
                            delivery_number=row.get('numero_ent'),
                            delivery_neighborhood=row.get('bairro_ent'),
                            delivery_city=row.get('cidade_ent'),
                            delivery_state=row.get('estado_ent'),
                            credit_limit=parse_decimal(row.get('limite_credito')),
                            credit_limit_expiry=parse_date(row.get('vencto_lc')),
                            commission_rate=parse_decimal(row.get('comissao')),
                            discount_rate=parse_decimal(row.get('desconto')),
                            bank_code=parse_int(row.get('banco')),
                            bank_agency=row.get('agencia'),
                            bank_account=row.get('conta'),
                            due_day=parse_int(row.get('dia_vencimento_fatura')),
                            payment_method=row.get('forma_pagamento'),
                            representative_id=parse_int(row.get('representante')),
                            carrier_id=parse_int(row.get('transportadora')),
                            region_id=parse_int(row.get('regiao')),
                            group_id=parse_int(row.get('grupo')),
                            obs=row.get('obs'),
                            obs_financial=row.get('obs_financeira'),
                            obs_invoice=row.get('obs_nf'),
                            credit_opinion=row.get('parecer_credito'),
                            is_blocked=parse_bool(row.get('bloqueio')),
                            document=doc_comp
                        )
                        customer_count += 1
                self.stdout.write(self.style.SUCCESS(f"{customer_count} clientes importados."))

                # 3. Re-vincular contatos de chat aos clientes
                self.stdout.write("Re-vinculando contatos de chat aos novos registros de clientes...")
                relinked_count = 0
                for contact in Contact.objects.all():
                    jid_digits = ''.join(c for c in contact.remote_jid.split('@')[0] if c.isdigit())
                    customer = None
                    if len(jid_digits) > 8:
                        for cust in Customer.objects.all():
                            cust_phone = ''.join(c for c in (cust.phone or '') if c.isdigit())
                            cust_mobile = ''.join(c for c in (cust.mobile or '') if c.isdigit())
                            cust_wa = ''.join(c for c in (cust.whatsapp or '') if c.isdigit())
                            if (cust_phone and (cust_phone in jid_digits or jid_digits in cust_phone)) or \
                               (cust_mobile and (cust_mobile in jid_digits or jid_digits in cust_mobile)) or \
                               (cust_wa and (cust_wa in jid_digits or jid_digits in cust_wa)):
                                customer = cust
                                break
                    if not customer and contact.name:
                        customer = Customer.objects.filter(name__iexact=contact.name.strip()).first()
                    if customer:
                        contact.customer = customer
                        contact.save()
                        relinked_count += 1
                self.stdout.write(self.style.SUCCESS(f"{relinked_count} contatos de chat re-vinculados com sucesso."))

                # 4. Importar Relacionamentos (Pendências)
                self.stdout.write(f"Importando relacionamentos de {rel_file}...")
                
                tipo_crm_map = {
                    1: 'suporte',
                    2: 'desenvolvimento',
                    3: 'consultoria',
                    4: 'atualizacao',
                    5: 'reuniao',
                    6: 'tef',
                    7: 'reforma_tributaria'
                }

                with open(rel_file, mode='r', encoding='utf-8-sig') as f:
                    delimiter = ';' if ';' in f.readline() else ','
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    pendency_count = 0
                    for row in reader:
                        legacy_id = parse_int(row.get('id'))
                        title = row.get('assunto') or "Sem Assunto"
                        if not legacy_id:
                            continue

                        cust_id = parse_int(row.get('cliente_id'))
                        customer = None
                        if cust_id:
                            customer = Customer.objects.filter(id=cust_id).first()

                        usr_id = parse_int(row.get('usuario_id'))
                        usr_name = row.get('abertura_usuario')
                        user = get_user_by_ref(usr_id, usr_name)

                        legacy_status = str(row.get('status')).strip()
                        closed_date_str = row.get('encerramento_data')
                        if legacy_status == '1' or (closed_date_str and str(closed_date_str).strip().upper() != 'NULL'):
                            status = 'closed'
                        else:
                            status = 'open'

                        urgencia = str(row.get('urgencia')).strip()
                        priority = 'high' if urgencia == '1' else 'medium'

                        crm_id = parse_int(row.get('tipo_crm_id'))
                        operation_type = tipo_crm_map.get(crm_id, 'suporte')

                        opening_date = parse_datetime(row.get('abertura_data'), row.get('abertura_hora'))
                        forecast_date = parse_datetime(row.get('previsao_data'), row.get('previsao_hora'))
                        closing_date = parse_datetime(row.get('encerramento_data'), row.get('encerramento_hora'))

                        pendency = Pendency.objects.create(
                            id=legacy_id,
                            company=company,
                            customer=customer,
                            user=user,
                            title=title.strip(),
                            description=(row.get('detalhe') or '').strip(),
                            status=status,
                            priority=priority,
                            operation_type=operation_type,
                            opening_date=opening_date or make_aware(datetime.now()),
                            forecast_date=forecast_date
                        )

                        created_at = opening_date or make_aware(datetime.now())
                        updated_at = closing_date or forecast_date or opening_date or make_aware(datetime.now())
                        Pendency.objects.filter(pk=pendency.pk).update(created_at=created_at, updated_at=updated_at)
                        
                        pendency_count += 1
                self.stdout.write(self.style.SUCCESS(f"{pendency_count} pendências importadas."))

                # 5. Importar Movimentações
                self.stdout.write(f"Importando movimentações de {mov_file}...")
                with open(mov_file, mode='r', encoding='utf-8-sig') as f:
                    delimiter = ';' if ';' in f.readline() else ','
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    movement_count = 0
                    missing_pendencies = set()
                    for row in reader:
                        legacy_id = parse_int(row.get('id'))
                        rel_id = parse_int(row.get('relacionamento_id'))
                        description = row.get('descricao')
                        
                        if not rel_id or not description:
                            continue
                        
                        pendency = Pendency.objects.filter(id=rel_id).first()
                        if not pendency:
                            missing_pendencies.add(rel_id)
                            continue

                        usr_id = parse_int(row.get('usuario_id'))
                        user = get_user_by_ref(usr_id, None) or pendency.user

                        movement = PendencyMovement.objects.create(
                            id=legacy_id,
                            pendency=pendency,
                            user=user,
                            description=description.strip()
                        )

                        created_at = parse_datetime(row.get('data'), row.get('hora'))
                        if created_at:
                            PendencyMovement.objects.filter(pk=movement.pk).update(created_at=created_at)

                        movement_count += 1
                        
                if missing_pendencies:
                    self.stdout.write(self.style.WARNING(f"Aviso: {len(missing_pendencies)} movimentações foram ignoradas porque as pendências legadas correspondentes não existem. IDs ausentes: {sorted(list(missing_pendencies))[:20]}..."))
                self.stdout.write(self.style.SUCCESS(f"{movement_count} movimentações importadas."))

                # 6. Ajustar Sequences do Postgres
                self.stdout.write("Ajustando sequências primárias no PostgreSQL...")
                with connection.cursor() as cursor:
                    cursor.execute("SELECT setval(pg_get_serial_sequence('tickets_customer', 'id'), coalesce(max(id), 1)) FROM tickets_customer;")
                    cursor.execute("SELECT setval(pg_get_serial_sequence('tickets_pendency', 'id'), coalesce(max(id), 1)) FROM tickets_pendency;")
                    cursor.execute("SELECT setval(pg_get_serial_sequence('tickets_pendencymovement', 'id'), coalesce(max(id), 1)) FROM tickets_pendencymovement;")
                self.stdout.write(self.style.SUCCESS("Sequências ajustadas com sucesso!"))

            self.stdout.write(self.style.SUCCESS("Importação concluída com sucesso total!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro durante a importação: {e}"))
            import traceback
            traceback.print_exc()
