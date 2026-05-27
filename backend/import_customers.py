import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configuração do ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection, transaction
from tickets.models import Company, Customer

def clean_doc_string(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() == 'NULL':
        return None
    # Corrige notação científica comum em exports do Excel/DBeaver
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

def import_data():
    # Identifica a empresa padrão para associar os clientes
    company = Company.objects.first()
    if not company:
        print("Erro: Nenhuma empresa (Company) cadastrada no sistema. Cadastre uma empresa primeiro.")
        return

    print(f"Empresa destino selecionada: {company.name} (ID: {company.id})")

    sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clientes.sql')
    if not os.path.exists(sql_file_path):
        print(f"Erro: Arquivo {sql_file_path} não encontrado.")
        return

    print("Lendo o arquivo SQL...")
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Redireciona a tabela original public.clientes para nossa tabela temporária
    sql_content = sql_content.replace('INSERT INTO public.clientes', 'INSERT INTO public.clientes_temp')

    columns = [
        "id", "nome", "nomefantasia", "endereco", "numero", "complemento", "bairro", "cidade", "estado", "cnpj", "cpf", 
        "inscricao", "inscr_mun", "contato", "telefone", "contato2", "telefone2", "celular", "whatsapp", "email", 
        "regiao", "cep", "obs", "cadastro", "comissao", "banco", "representante", "desconto", "condicao", "transportadora", 
        "data_fundacao", "bloqueio", "alteracao", "especie", "conta", "cep_cob", "endereco_cob", "numero_cob", "cidade_cob", 
        "bairro_cob", "estado_cob", "agencia", "retencao", "cep_ent", "endereco_ent", "numero_ent", "bairro_ent", 
        "cidade_ent", "estado_ent", "limite_credito", "vencto_lc", "direto", "contato_producao", "email_contato", 
        "naoenviar_cartorio", "grupo", "contacontabil", "codhistorico", "tabela", "rg", "data_nasc", "nome_pai", 
        "nome_mae", "renda_identificada", "parecer_credito", "empresa", "tempo_servico", "cargo", "marca", "sexo", 
        "estadocivil", "profissao", "conta_debito", "percentual", "tipocliente", "situacao_cliente", "expedidor", 
        "deposito_entrada", "deposito_saida", "obs_financeira", "site", "optante_simples", "rota", "sequencia", 
        "conta_contabil_debito", "conta_contabil_credito", "email_comercial", "suframa", "cfop", "nao_cobrar_tarifa", 
        "meta_mensal_venda", "consumidor_final", "data_contrato", "dias_meta_vendas", "capital_social", 
        "dia_vencimento_fatura", "forma_pagamento", "vencimento_mes_subsequente", "obs_nf", "saldo_financeiro", 
        "dias_atraso", "valor_credito_receber", "data_credito", "nao_contribuinte", "tipo_ocorrencia_crm", 
        "email_financeiro", "sem_juros_cobranca", "sem_protesto_cobranca", "sem_multa_cobranca", "nao_considera_relatorios", 
        "sequencia_lote", "fornecedor_id"
    ]

    print("Criando tabela temporária no PostgreSQL...")
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS public.clientes_temp;")
        create_table_sql = "CREATE TABLE public.clientes_temp (" + ", ".join([f'"{col}" TEXT' for col in columns]) + ");"
        cursor.execute(create_table_sql)
        
        print("Inserindo dados na tabela temporária...")
        cursor.execute(sql_content)
        
        print("Buscando registros inseridos...")
        cursor.execute("SELECT * FROM public.clientes_temp;")
        rows = cursor.fetchall()
        
        # Mapeia nome da coluna -> índice da tupla
        col_idx = {col: i for i, col in enumerate(columns)}

    print(f"Total de registros encontrados no SQL: {len(rows)}")
    
    count_created = 0
    count_updated = 0
    
    with transaction.atomic():
        for row in rows:
            # Helper para pegar valor da linha pelo nome da coluna
            def get_val(col_name):
                return row[col_idx[col_name]]

            name = get_val("nome")
            if not name or str(name).strip().upper() == 'NULL':
                continue
                
            # Telefone principal (obrigatório no modelo)
            phone = get_val("telefone") or get_val("celular") or get_val("whatsapp") or "(50) 0000-0000"
            phone = str(phone).strip()
            
            # Documento CPF/CNPJ limpos
            cnpj_clean = clean_doc_string(get_val("cnpj"))
            cpf_clean = clean_doc_string(get_val("cpf"))
            doc_comp = cnpj_clean or cpf_clean or ''
            
            # Busca se o cliente já existe por nome e telefone, ou pelo documento limpo
            customer = None
            if doc_comp:
                customer = Customer.objects.filter(company=company).filter(cnpj=doc_comp).first()
                if not customer:
                    customer = Customer.objects.filter(company=company).filter(cpf=doc_comp).first()
            if not customer:
                customer = Customer.objects.filter(company=company, name=name, phone=phone).first()
                
            is_new = customer is None
            if is_new:
                customer = Customer(company=company, name=name, phone=phone)
            
            # Mapeamento de dados gerais
            customer.fantasy_name = get_val("nomefantasia")
            customer.cnpj = cnpj_clean
            customer.cpf = cpf_clean
            customer.rg = get_val("rg")
            customer.state_inscription = get_val("inscricao")
            customer.municipal_inscription = get_val("inscr_mun")
            customer.birth_date = parse_date(get_val("data_nasc"))
            customer.foundation_date = parse_date(get_val("data_fundacao"))
            customer.optante_simples = parse_bool(get_val("optante_simples"))
            customer.consumidor_final = parse_bool(get_val("consumidor_final"))
            customer.nao_contribuinte = parse_bool(get_val("nao_contribuinte"))
            
            # Contatos
            customer.phone = phone
            customer.phone2 = get_val("telefone2")
            customer.mobile = get_val("celular")
            customer.whatsapp = get_val("whatsapp")
            customer.email = get_val("email")
            customer.email_commercial = get_val("email_comercial")
            customer.email_financial = get_val("email_financeiro")
            customer.contact_name = get_val("contato")
            customer.contact_name2 = get_val("contato2")
            
            # Endereço Principal
            customer.address = get_val("endereco")
            customer.zip_code = get_val("cep")
            customer.number = get_val("numero")
            customer.complement = get_val("complemento")
            customer.neighborhood = get_val("bairro")
            customer.city = get_val("cidade")
            customer.state = get_val("estado")
            
            # Endereço de Cobrança
            customer.billing_zip_code = get_val("cep_cob")
            customer.billing_address = get_val("endereco_cob")
            customer.billing_number = get_val("numero_cob")
            customer.billing_neighborhood = get_val("bairro_cob")
            customer.billing_city = get_val("cidade_cob")
            customer.billing_state = get_val("estado_cob")
            
            # Endereço de Entrega
            customer.delivery_zip_code = get_val("cep_ent")
            customer.delivery_address = get_val("endereco_ent")
            customer.delivery_number = get_val("numero_ent")
            customer.delivery_neighborhood = get_val("bairro_ent")
            customer.delivery_city = get_val("cidade_ent")
            customer.delivery_state = get_val("estado_ent")
            
            # Financeiro
            customer.credit_limit = parse_decimal(get_val("limite_credito"))
            customer.credit_limit_expiry = parse_date(get_val("vencto_lc"))
            customer.commission_rate = parse_decimal(get_val("comissao"))
            customer.discount_rate = parse_decimal(get_val("desconto"))
            customer.bank_code = parse_int(get_val("banco"))
            customer.bank_agency = get_val("agencia")
            customer.bank_account = get_val("conta")
            customer.due_day = parse_int(get_val("dia_vencimento_fatura"))
            customer.payment_method = get_val("forma_pagamento")
            
            # Auxiliares ERP
            customer.representative_id = parse_int(get_val("representante"))
            customer.carrier_id = parse_int(get_val("transportadora"))
            customer.region_id = parse_int(get_val("regiao"))
            customer.group_id = parse_int(get_val("grupo"))
            
            # Obs
            customer.obs = get_val("obs")
            customer.obs_financial = get_val("obs_financeira")
            customer.obs_invoice = get_val("obs_nf")
            customer.credit_opinion = get_val("parecer_credito")
            
            # Status
            customer.is_blocked = parse_bool(get_val("bloqueio"))
            customer.document = doc_comp
            
            customer.save()
            if is_new:
                count_created += 1
            else:
                count_updated += 1

    # Limpa tabela temporária
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS public.clientes_temp;")

    print(f"Sucesso! Clientes criados: {count_created} | Clientes atualizados: {count_updated}")

if __name__ == '__main__':
    import_data()
