# services/bcb_service.py
import requests
from datetime import datetime, timedelta
from functools import lru_cache

# IDs das séries no Sistema do Banco Central (SGS)
SERIE_CDI_DIARIO = 11
SERIE_IPCA_MENSAL = 433

@lru_cache(maxsize=16)
def buscar_serie_bcb(codigo_serie, data_inicial_str):
    """
    Busca dados na API do Banco Central (SGS).
    Retorna lista de dicionários: [{'data': 'dd/mm/aaaa', 'valor': '0.12'}, ...]
    """
    try:
        # URL Oficial do BCB (Aberta e Gratuita)
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json&dataInicial={data_inicial_str}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao conectar no BCB (Série {codigo_serie}): {e}")
        return []

def calcular_cdi_acumulado(data_inicio, percentual_cdi=100.0):
    """
    Calcula quanto 1 real rendeu de 'data_inicio' até hoje baseado no CDI.
    percentual_cdi: 100 para 100% do CDI, 110 para 110%, etc.
    """
    if isinstance(data_inicio, datetime):
        data_inicio_str = data_inicio.strftime("%d/%m/%Y")
    else:
        return 1.0

    dados = buscar_serie_bcb(SERIE_CDI_DIARIO, data_inicio_str)
    
    fator_acumulado = 1.0
    fator_percentual = percentual_cdi / 100.0
    
    for item in dados:
        try:
            # O BCB entrega a taxa diária em % (ex: 0.050788)
            taxa_diaria = float(item['valor'])
            
            # Fórmula CDI: Fator = Fator * (1 + (TaxaDiaria/100 * %Contratado))
            # O percentual incide sobre a taxa, não sobre o montante final direto na diária simples
            fator_diario = 1 + ((taxa_diaria / 100.0) * fator_percentual)
            fator_acumulado *= fator_diario
        except:
            continue
            
    return fator_acumulado

def calcular_ipca_acumulado(data_inicio, taxa_fixa_anual=0.0):
    """
    Calcula IPCA acumulado + Taxa Fixa (Ex: IPCA + 6%).
    Nota: IPCA tem defasagem de ~1 mês.
    """
    if isinstance(data_inicio, datetime):
        data_inicio_str = data_inicio.strftime("%d/%m/%Y")
    else:
        return 1.0
        
    dados = buscar_serie_bcb(SERIE_IPCA_MENSAL, data_inicio_str)
    
    fator_acumulado = 1.0
    
    # Transforma taxa fixa anual em mensal aproximada para compor
    # (1 + Anual) = (1 + Mensal)^12
    taxa_fixa_mensal = ((1 + (taxa_fixa_anual / 100.0)) ** (1/12)) - 1
    
    for item in dados:
        try:
            ipca_mensal = float(item['valor']) / 100.0
            # Combina IPCA do mês + pedacinho da taxa fixa
            fator_mensal = (1 + ipca_mensal) * (1 + taxa_fixa_mensal)
            fator_acumulado *= fator_mensal
        except:
            continue
            
    return fator_acumulado