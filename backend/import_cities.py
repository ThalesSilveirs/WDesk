import os
import django
import urllib.request
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tickets.models import City

def import_cities():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    print("Buscando cidades da API do IBGE...")
    try:
        import gzip
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            response_data = response.read()
            if response.info().get('Content-Encoding') == 'gzip' or response_data.startswith(b'\x1f\x8b'):
                response_data = gzip.decompress(response_data)
            data = json.loads(response_data.decode('utf-8'))
    except Exception as e:
        print(f"Erro ao buscar dados do IBGE: {e}")
        return

    print(f"Total de {len(data)} cidades encontradas. Processando...")
    
    print("Limpando a tabela de cidades existente...")
    City.objects.all().delete()
    
    cities_to_create = []
    created_count = 0
    
    for item in data:
        ibge_code = str(item.get('id'))
        name = item.get('nome')
        
        # Obter a sigla do estado
        state = None
        micro = item.get('microrregiao')
        if micro:
            meso = micro.get('mesorregiao')
            if meso:
                uf = meso.get('UF')
                if uf:
                    state = uf.get('sigla')
              
        if not state:
            # Fallback para o caminho de regiao-imediata
            regiao_imediata = item.get('regiao-imediata')
            if regiao_imediata:
                regiao_inter = regiao_imediata.get('regiao-intermediaria')
                if regiao_inter:
                    uf = regiao_inter.get('UF')
                    if uf:
                        state = uf.get('sigla')
        
        if not state:
            state = 'XX' # Fallback
          
        cities_to_create.append(City(
            ibge_code=ibge_code,
            name=name,
            state=state
        ))
        created_count += 1

    if cities_to_create:
        City.objects.bulk_create(cities_to_create, batch_size=500)

    print(f"Importação concluída!")
    print(f"Criadas: {created_count}")

if __name__ == '__main__':
    import_cities()
