import os
import psycopg2
import redis
import base64
import mimetypes
import uuid
from django.conf import settings

# Setup shared Redis connection pool using celery broker url
_redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
redis_pool = redis.ConnectionPool.from_url(_redis_url, max_connections=50)
redis_client = redis.Redis(connection_pool=redis_pool)

def get_evolution_token(instance_name, force_refresh=False):
    """
    Recupera o token da Evolution API para a instância especificada.
    Primeiro tenta buscar no cache do Redis (se force_refresh for False). 
    Se não encontrar ou se force_refresh for True, busca no banco da Evolution e salva no Redis.
    """
    cache_key = f"evo_token_{instance_name}"
    if not force_refresh:
        try:
            cached_token = redis_client.get(cache_key)
            if cached_token:
                return cached_token.decode('utf-8')
        except Exception as e:
            print(f"[TOKEN CACHE] Erro ao ler Redis: {e}")

    # Consultar banco evogo_users
    evo_token = "your-token-here"
    try:
        db_pass = os.environ.get('DB_PASSWORD', 'postgres')
        db_host = os.environ.get('DB_HOST', 'db')
        conn = psycopg2.connect(
            dbname="evogo_users",
            user="postgres",
            password=db_pass,
            host=db_host
        )
        cur = conn.cursor()
        cur.execute("SELECT token FROM instances WHERE name = %s;", (instance_name,))
        row = cur.fetchone()
        if row:
            evo_token = row[0]
            # Salvar no Redis com TTL de 12 horas (43200 segundos)
            try:
                redis_client.set(cache_key, evo_token, ex=43200)
            except Exception as e:
                print(f"[TOKEN CACHE] Erro ao salvar Redis: {e}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[TOKEN FETCH] Erro ao buscar token no banco: {e}")
        evo_token = getattr(settings, 'EVOLUTION_API_KEY', 'your-token-here')

    return evo_token

def get_br_jid_variant(jid):
    """
    Retorna a variação do nono dígito para JIDs do WhatsApp no Brasil (+55).
    Se tiver 13 dígitos (55 + DDD + 9 + 8 dig), retorna a versão de 12 dígitos sem o 9.
    Se tiver 12 dígitos (55 + DDD + 8 dig), retorna a versão de 13 dígitos com o 9.
    """
    if not jid or '@s.whatsapp.net' not in str(jid):
        return None
    num = str(jid).split('@')[0]
    if len(num) == 13 and num.startswith('55') and num[4] == '9':
        return f"{num[:4]}{num[5:]}@s.whatsapp.net"
    elif len(num) == 12 and num.startswith('55'):
        return f"{num[:4]}9{num[4:]}@s.whatsapp.net"
    return None


import re
import urllib.request
import ssl
from datetime import datetime

def parse_ics_datetime(dt_str):
    """
    Converte strings de data/hora do formato iCalendar para ISO string.
    Exemplos:
    20260721T140000Z -> 2026-07-21T14:00:00Z
    20260721 -> 2026-07-21
    """
    if not dt_str:
        return ''
    if ':' in dt_str:
        dt_str = dt_str.split(':')[-1]
    dt_str = dt_str.strip()
    
    try:
        if 'T' in dt_str:
            clean = dt_str.replace('Z', '')
            if len(clean) >= 15:
                dt = datetime.strptime(clean[:15], '%Y%m%dT%H%M%S')
                suffix = 'Z' if dt_str.endswith('Z') else ''
                return dt.strftime('%Y-%m-%dT%H:%M:%S') + suffix
        elif len(dt_str) >= 8:
            dt = datetime.strptime(dt_str[:8], '%Y%m%d')
            return dt.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"[ICS PARSE DATE ERR] {dt_str}: {e}")
    return dt_str

def parse_ics_content(ics_text):
    """
    Faz o parse manual de conteúdo de arquivo iCalendar (.ics).
    Retorna uma lista de dicionários de eventos.
    """
    if not ics_text:
        return []

    unfolded = re.sub(r'\r?\n[ \t]', '', ics_text)
    lines = unfolded.splitlines()

    events = []
    current_event = None
    in_vevent = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line == 'BEGIN:VEVENT':
            in_vevent = True
            current_event = {
                'title': '',
                'description': '',
                'location': '',
                'start': '',
                'end': '',
                'allDay': False,
                'uid': ''
            }
            continue
        elif line == 'END:VEVENT':
            if in_vevent and current_event:
                if not current_event['title']:
                    current_event['title'] = '(Sem título)'
                if not current_event['end']:
                    current_event['end'] = current_event['start']
                events.append(current_event)
            in_vevent = False
            current_event = None
            continue

        if in_vevent and current_event:
            if ':' in line:
                key_part, val = line.split(':', 1)
                key = key_part.split(';')[0].upper()
                val_clean = val.replace('\\,', ',').replace('\\;', ';').replace('\\n', '\n').replace('\\N', '\n')

                if key == 'SUMMARY':
                    current_event['title'] = val_clean
                elif key == 'DESCRIPTION':
                    current_event['description'] = val_clean
                elif key == 'LOCATION':
                    current_event['location'] = val_clean
                elif key == 'DTSTART':
                    current_event['start'] = parse_ics_datetime(val)
                    if 'T' not in val:
                        current_event['allDay'] = True
                elif key == 'DTEND':
                    current_event['end'] = parse_ics_datetime(val)
                elif key == 'UID':
                    current_event['uid'] = val_clean

    return events

def fetch_and_parse_webcal(url):
    """
    Baixa a URL de WebCAL/iCal e faz o parse dos eventos.
    """
    if not url:
        return []

    clean_url = url.strip()
    if clean_url.startswith('webcal://'):
        clean_url = 'https://' + clean_url[9:]
    elif clean_url.startswith('webcals://'):
        clean_url = 'https://' + clean_url[10:]
    elif not clean_url.startswith('http://') and not clean_url.startswith('https://'):
        clean_url = 'https://' + clean_url

    try:
        req = urllib.request.Request(
            clean_url,
            headers={'User-Agent': 'WDesk-Calendar/1.0'}
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=12) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return parse_ics_content(content)
    except Exception as e:
        print(f"[WEBCAL FETCH ERR] {url} -> {clean_url}: {e}")
        return []

def save_media_file(media_data, mimetype=None, company_id=None, original_filename=None):
    """
    Salva uma mídia (recebida em Base64 ou bytes) diretamente no sistema de arquivos (MEDIA_ROOT)
    em vez de armazenar o Base64 massivo no banco de dados.
    Retorna a URL relativa do arquivo (ex: '/media/1/uuid.jpg').
    """
    if not media_data:
        return None

    # Se já for uma URL HTTP ou relativa, não precisa converter
    if isinstance(media_data, str) and (media_data.startswith('http://') or media_data.startswith('https://') or media_data.startswith('/media/')):
        return media_data

    # Se for string JSON (ex: contato vcard), não é arquivo de mídia
    if isinstance(media_data, str) and (media_data.startswith('{') or media_data.startswith('[')):
        return media_data

    try:
        raw_bytes = None
        detected_ext = None

        if isinstance(media_data, bytes):
            raw_bytes = media_data
        elif isinstance(media_data, str):
            clean_str = media_data.strip()
            # Extrair MIME type se estiver no formato data:mimetype;base64,xxxx
            if clean_str.startswith('data:'):
                try:
                    header, base64_content = clean_str.split(',', 1)
                    if ';base64' in header:
                        header_mime = header[5:].split(';')[0]
                        if header_mime:
                            mimetype = header_mime
                    raw_bytes = base64.b64decode(base64_content)
                except Exception:
                    raw_bytes = base64.b64decode(clean_str)
            else:
                raw_bytes = base64.b64decode(clean_str)

        if not raw_bytes:
            return media_data

        # Detectar extensão do arquivo
        if mimetype:
            mime_clean = mimetype.split(';')[0].strip().lower()
            if mime_clean in ['audio/ogg', 'audio/ogg; codecs=opus']:
                detected_ext = '.ogg'
            elif mime_clean == 'audio/mp4':
                detected_ext = '.m4a'
            elif mime_clean == 'audio/mpeg':
                detected_ext = '.mp3'
            elif mime_clean == 'image/jpeg':
                detected_ext = '.jpg'
            elif mime_clean == 'image/png':
                detected_ext = '.png'
            elif mime_clean == 'image/webp':
                detected_ext = '.webp'
            elif mime_clean == 'video/mp4':
                detected_ext = '.mp4'
            elif mime_clean == 'application/pdf':
                detected_ext = '.pdf'
            else:
                guessed = mimetypes.guess_extension(mime_clean)
                if guessed:
                    detected_ext = guessed

        if not detected_ext and original_filename:
            _, file_ext = os.path.splitext(original_filename)
            if file_ext:
                detected_ext = file_ext.lower()

        if not detected_ext:
            detected_ext = '.bin'

        # Diretório da empresa
        media_root = getattr(settings, 'MEDIA_ROOT', '/app/media')
        company_folder = str(company_id or 'global')
        target_dir = os.path.join(media_root, company_folder)
        os.makedirs(target_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex[:16]}{detected_ext}"
        file_path = os.path.join(target_dir, unique_name)

        with open(file_path, 'wb') as f:
            f.write(raw_bytes)

        return f"/media/{company_folder}/{unique_name}"
    except Exception as e:
        print(f"[SAVE MEDIA ERR] Erro ao salvar arquivo em disco: {e}")
        # Em caso de qualquer falha, retorna o dado original para não perder a mensagem
        return media_data

