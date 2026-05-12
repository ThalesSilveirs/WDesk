import requests
import json

url = "http://localhost:8000/api/v1/webhooks/evolution/"
payload = {
  "event": "MESSAGES_UPSERT",
  "instance": "instancia01",
  "data": {
    "key": {
      "remoteJid": "555194794505@s.whatsapp.net",
      "fromMe": False,
      "id": "TEST_ID_PYTHON_1"
    },
    "message": {
      "conversation": "Olá, esta é uma mensagem de teste do Antigravity via Python!"
    },
    "pushName": "Suporte Antigravity"
  }
}

try:
    print(f"Enviando para {url}...")
    response = requests.post(url, json=payload, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
except Exception as e:
    print(f"Erro: {e}")
