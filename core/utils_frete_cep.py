import requests
from geopy.distance import geodesic
from decouple import config
from threading import Lock

# Obter chave da API OpenCage do arquivo .env (usando python-decouple/config)
OPENCAGE_API_KEY = config("OPENCAGE_API_KEY", default=None)

# Contador thread-safe para requisições à OpenCage
_opencage_request_count = 0
_opencage_lock = Lock()

def get_opencage_request_count():
    global _opencage_request_count
    return _opencage_request_count

def validar_cep(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        if "erro" in dados:
            return {"erro": "CEP inválido."}
        return dados
    else:
        return {"erro": "Erro ao acessar a API ViaCEP."}

def obter_coordenadas(endereco):
    global _opencage_request_count
    url = f"https://api.opencagedata.com/geocode/v1/json?q={endereco}&key={OPENCAGE_API_KEY}"
    with _opencage_lock:
        _opencage_request_count += 1
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        if dados['results']:
            coordenadas = dados['results'][0]['geometry']
            return coordenadas['lat'], coordenadas['lng']
        else:
            return {"erro": "Coordenadas não encontradas para o endereço fornecido."}
    else:
        return {"erro": "Erro ao acessar a API OpenCage."}

def calcular_frete_cep(cep_destino, cep_referencia="08750580", raio_km=5, taxa_base=5, taxa_km=1, raio_limite_km=None):
    # Garantir que todos os argumentos numéricos sejam float para evitar erro de soma com Decimal
    try:
        raio_km = float(raio_km)
    except Exception:
        raio_km = 5.0
    try:
        taxa_base = float(taxa_base)
    except Exception:
        taxa_base = 5.0
    try:
        taxa_km = float(taxa_km)
    except Exception:
        taxa_km = 1.0
    if raio_limite_km is not None:
        try:
            raio_limite_km = float(raio_limite_km)
        except Exception:
            raio_limite_km = None
    """
    Calcula o custo do frete com base na distância entre dois CEPs.
    :param cep_destino: CEP de destino (string).
    :param cep_referencia: CEP de referência (string, padrão: 08750580).
    :param raio_km: Raio em km para a taxa base (int, padrão: 5).
    :param taxa_base: Valor base do frete (float, padrão: 5).
    :param taxa_km: Valor adicional por km acima do raio (float, padrão: 1).
    :param raio_limite_km: Raio máximo de entrega (float, opcional). Se informado, bloqueia entregas fora desse raio.
    :return: dict com distancia_km, custo_frete, erro (se houver)
    """
    import math
    # raio_limite_km agora é argumento explícito
    dados_referencia = validar_cep(cep_referencia)
    dados_destino = validar_cep(cep_destino)
    if "erro" in dados_referencia:
        return {"erro": f"CEP de referência inválido: {dados_referencia['erro']}"}
    if "erro" in dados_destino:
        return {"erro": f"CEP de destino inválido: {dados_destino['erro']}"}
    try:
        endereco_referencia = f"{dados_referencia['logradouro']}, {dados_referencia['localidade']}, {dados_referencia['uf']}"
        endereco_destino = f"{dados_destino['logradouro']}, {dados_destino['localidade']}, {dados_destino['uf']}"
        coord_referencia = obter_coordenadas(endereco_referencia)
        coord_destino = obter_coordenadas(endereco_destino)
        if "erro" in coord_referencia:
            return coord_referencia
        if "erro" in coord_destino:
            return coord_destino
    except KeyError:
        return {"erro": "Dados insuficientes para obter coordenadas."}
    distancia_km = geodesic(coord_referencia, coord_destino).km
    if raio_limite_km is not None and distancia_km > float(raio_limite_km):
        return {"erro": f"Fora do raio de entrega: {round(distancia_km,2)} km (limite: {raio_limite_km} km)", "distancia_km": round(distancia_km,2)}
    if distancia_km <= raio_km:
        custo = taxa_base
    else:
        custo = taxa_base + ((distancia_km - raio_km) * taxa_km)
    return {"distancia_km": round(distancia_km, 2), "custo_frete": round(custo, 2)}
