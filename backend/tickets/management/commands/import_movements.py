import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from tickets.models import Pendency, PendencyMovement

User = get_user_model()

class Command(BaseCommand):
    help = "Importa movimentacoes de pendencias a partir de um arquivo CSV"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Caminho para o arquivo CSV de movimentacoes")

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        self.stdout.write(f"Iniciando importacao de {csv_file_path}...")

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
                # Tenta detectar se e separado por ponto e virgula ou virgula
                first_line = f.readline()
                delimiter = ';' if ';' in first_line else ','
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delimiter)
                self.stdout.write(f"Colunas detectadas: {', '.join(reader.fieldnames or [])}")
                
                success_count = 0
                error_count = 0
                
                for row in reader:
                    # Mapeamento flexivel de colunas
                    pendency_ref = row.get('pendency_id') or row.get('pendencia_id') or row.get('pendency_title') or row.get('titulo_pendencia') or row.get('pendency') or row.get('titulo')
                    description = row.get('description') or row.get('descricao') or row.get('texto') or row.get('text')
                    created_at_str = row.get('created_at') or row.get('data') or row.get('date')
                    username = row.get('username') or row.get('usuario') or row.get('user')
                    
                    if not pendency_ref or not description:
                        self.stderr.write(f"Linha ignorada por falta de pendencia ou descricao: {row}")
                        error_count += 1
                        continue
                        
                    # Buscar pendencia
                    pendency = None
                    try:
                        pendency = Pendency.objects.get(id=pendency_ref.strip())
                    except (Pendency.DoesNotExist, ValueError):
                        # Se nao achar por ID, tenta por titulo
                        pendency = Pendency.objects.filter(title__iexact=pendency_ref.strip()).first()
                        
                    if not pendency:
                        self.stderr.write(f"Pendencia nao encontrada para a referencia: '{pendency_ref}'")
                        error_count += 1
                        continue
                        
                    # Buscar usuario
                    user = None
                    if username:
                        u_clean = username.strip()
                        user = User.objects.filter(username__iexact=u_clean).first() or User.objects.filter(email__iexact=u_clean).first()
                    
                    # Fallback para o usuario atribuido na pendencia
                    if not user:
                        user = pendency.user
                        
                    # Converter data
                    created_at = None
                    if created_at_str:
                        date_str = created_at_str.strip()
                        for date_fmt in (
                            '%Y-%m-%d %H:%M:%S', 
                            '%d/%m/%Y %H:%M:%S', 
                            '%Y-%m-%d %H:%M', 
                            '%d/%m/%Y %H:%M', 
                            '%Y-%m-%dT%H:%M:%S.%fZ', 
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%d',
                            '%d/%m/%Y'
                        ):
                            try:
                                naive_dt = datetime.strptime(date_str, date_fmt)
                                created_at = make_aware(naive_dt)
                                break
                            except ValueError:
                                continue
                                
                    # Criar movimentacao
                    movement = PendencyMovement.objects.create(
                        pendency=pendency,
                        user=user,
                        description=description.strip()
                    )
                    
                    # Sobrescrever data de criacao contornando o auto_now_add
                    if created_at:
                        PendencyMovement.objects.filter(pk=movement.pk).update(created_at=created_at)
                        
                    success_count += 1
                    
            self.stdout.write(self.style.SUCCESS(f"Importacao concluida! {success_count} movimentacoes criadas. {error_count} erros."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro ao ler o arquivo CSV: {e}"))
