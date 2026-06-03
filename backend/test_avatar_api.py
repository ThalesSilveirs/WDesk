import os
import sys
import django
import requests

# Inicializa o Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings
from tickets.models import Connection, Contact
from tickets.utils import get_evolution_token

def run_test():
    print("=== INICIANDO TESTE DA EVOLUTION API ===")
    
    connection = Connection.objects.first()
    if not connection:
        print("Nenhuma conexão cadastrada no banco de dados.")
        return
        
    print(f"Instância encontrada: {connection.instance_name} (Status: {connection.status})")
    
    contact = Contact.objects.filter(profile_pic__isnull=True).first()
    if not contact:
        contact = Contact.objects.first()
        
    if not contact:
        print("Nenhum contato encontrado no banco de dados.")
        return
        
    print(f"Contato de teste: {contact.name} ({contact.remote_jid})")
    
    evo_url = connection.company.evolution_api_url or settings.EVOLUTION_API_URL
    try:
        evo_key = get_evolution_token(connection.instance_name)
    except Exception as e:
        print(f"Erro ao buscar token: {e}")
        return
        
    print(f"Evo URL: {evo_url}")
    print(f"Evo Key: {evo_key[:10]}... (tamanho {len(evo_key)})")
    
    clean_number = contact.remote_jid.split('@')[0]
    print(f"Número limpo: {clean_number}")
    
    # 1. Testando POST /user/avatar (Evolution GO)
    print("\n--- Testando Tentativa 1: POST /user/avatar ---")
    url_post = f"{evo_url}/user/avatar?instance={connection.instance_name}"
    payload = {"number": clean_number, "preview": False}
    headers = {
        "Content-Type": "application/json",
        "apikey": evo_key,
        "Authorization": f"Bearer {evo_key}",
        "instance": connection.instance_name,
        "instanceName": connection.instance_name
    }
    
    try:
        print(f"POST {url_post}")
        print(f"Payload: {payload}")
        print(f"Headers: {headers}")
        res = requests.post(url_post, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        print(f"Response Headers: {dict(res.headers)}")
        try:
            print(f"Response Body (JSON): {res.json()}")
        except:
            print(f"Response Body (Text): {res.text}")
    except Exception as e:
        print(f"Erro na requisição POST: {e}")
        
    # 2. Testando GET /chat/findProfilePhoto (Legacy / Node)
    print("\n--- Testando Tentativa 2: GET /chat/findProfilePhoto ---")
    url_get = f"{evo_url}/chat/findProfilePhoto/{connection.instance_name}/{clean_number}"
    try:
        print(f"GET {url_get}")
        res = requests.get(url_get, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        try:
            print(f"Response Body (JSON): {res.json()}")
        except:
            print(f"Response Body (Text): {res.text}")
    except Exception as e:
        print(f"Erro na requisição GET: {e}")

if __name__ == "__main__":
    run_test()
