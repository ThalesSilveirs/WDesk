import requests
import json

def run_test():
    url = "http://desk.wadm.inf.br:8080"
    apikey = "0f00f38b042ada23b3437e74b0141dd4d40ac50daf2afd9c8c524b79958a54cd"
    
    print(f"=== TESTANDO CONEXÃO DIRETA COM EVOLUTION API ({url}) ===")
    
    headers = {
        "apikey": apikey,
        "Authorization": f"Bearer {apikey}"
    }
    
    # 1. Listar todas as instâncias
    try:
        res = requests.get(f"{url}/instance/all", headers=headers, timeout=10)
        print(f"1. /instance/all: Status Code {res.status_code}")
        if res.status_code == 200:
            instances = res.json()
            print(f"Instâncias encontradas: {json.dumps(instances, indent=2)}")
            if isinstance(instances, list) and len(instances) > 0:
                first_inst = instances[0]
                instance_name = first_inst.get('name') or first_inst.get('instanceName')
                instance_token = first_inst.get('token') or apikey
                
                # Testar se há números de teste para buscar avatar
                # Vamos tentar com um número qualquer que costuma ter whatsapp, por exemplo o número de suporte ou um número gerado
                test_number = "5511999999999" # número de teste
                
                print(f"\n--- Testando busca de avatar para a instância {instance_name} ---")
                
                # 2. POST /user/avatar
                url_avatar = f"{url}/user/avatar?instance={instance_name}"
                headers_avatar = {
                    "Content-Type": "application/json",
                    "apikey": instance_token,
                    "Authorization": f"Bearer {instance_token}"
                }
                payload = {"number": test_number, "preview": False}
                
                print(f"Chamando POST {url_avatar}")
                print(f"Headers: {headers_avatar}")
                print(f"Payload: {payload}")
                
                res_avatar = requests.post(url_avatar, json=payload, headers=headers_avatar, timeout=10)
                print(f"POST /user/avatar Status Code: {res_avatar.status_code}")
                try:
                    print(f"POST /user/avatar Response: {json.dumps(res_avatar.json(), indent=2)}")
                except:
                    print(f"POST /user/avatar Text: {res_avatar.text}")
                    
                # 3. GET /chat/findProfilePhoto
                url_photo = f"{url}/chat/findProfilePhoto/{instance_name}/{test_number}"
                print(f"\nChamando GET {url_photo}")
                res_photo = requests.get(url_photo, headers=headers_avatar, timeout=10)
                print(f"GET /chat/findProfilePhoto Status Code: {res_photo.status_code}")
                try:
                    print(f"GET /chat/findProfilePhoto Response: {json.dumps(res_photo.json(), indent=2)}")
                except:
                    print(f"GET /chat/findProfilePhoto Text: {res_photo.text}")
        else:
            print(f"Falha ao listar instâncias: {res.text}")
    except Exception as e:
        print(f"Erro na conexão com a Evolution API: {e}")

if __name__ == "__main__":
    run_test()
