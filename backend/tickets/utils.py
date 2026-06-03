import os
import psycopg2
import redis
from django.conf import settings

# Setup Redis connection using celery broker url
redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

def get_evolution_token(instance_name):
    """
    Recupera o token da Evolution API para a instância especificada.
    Primeiro tenta buscar no cache do Redis. Se não encontrar,
    busca no banco da Evolution e salva no Redis com TTL de 12 horas.
    """
    cache_key = f"evo_token_{instance_name}"
    try:
        cached_token = redis_client.get(cache_key)
        if cached_token:
            return cached_token.decode('utf-8')
    except Exception as e:
        print(f"[TOKEN CACHE] Erro ao ler Redis: {e}")

    # Fallback para consulta psycopg2
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
        # Retorna o token de fallback padrão configurado
        evo_token = getattr(settings, 'EVOLUTION_API_KEY', 'your-token-here')

    return evo_token
