# services/fixed_income_service.py
from datetime import datetime
from .bcb_service import calcular_cdi_acumulado, calcular_ipca_acumulado

def calcular_renda_fixa(investimento):
    """
    Calcula o valor atualizado (Bruto) de um investimento em Renda Fixa
    usando dados reais do Banco Central.
    """
    if not investimento.data_compra or not investimento.preco_compra:
        return 0.0

    valor_inicial = investimento.preco_compra * investimento.quantidade
    
    # Se já foi vendido ou data futura, retorna o valor original ou de venda
    if investimento.data_compra > datetime.now():
        return valor_inicial

    indice = investimento.indice # CDI, IPCA, PRE
    taxa = investimento.taxa_contratada or 0.0 # Ex: 100, 110, 12, 6
    
    valor_atual = valor_inicial

    try:
        # --- LÓGICA 1: PRÉ-FIXADO (Cálculo Matemático Puro) ---
        if indice == 'PRE':
            # Juros Compostos: M = C * (1 + i)^t
            # i = taxa anual / 100
            # t = anos decorridos (dias corridos / 365)
            
            dias_corridos = (datetime.now() - investimento.data_compra).days
            anos = dias_corridos / 365.0
            
            fator = (1 + (taxa / 100.0)) ** anos
            valor_atual = valor_inicial * fator

        # --- LÓGICA 2: CDI / PÓS-FIXADO (Consulta BCB) ---
        elif indice == 'CDI':
            # Ex: taxa = 110 (significa 110% do CDI)
            # Se taxa for 0 ou None, assumimos 100%
            percentual = taxa if taxa > 0 else 100.0
            
            fator_cdi = calcular_cdi_acumulado(investimento.data_compra, percentual)
            valor_atual = valor_inicial * fator_cdi

        # --- LÓGICA 3: IPCA + (Consulta BCB) ---
        elif indice == 'IPCA':
            # Ex: taxa = 6 (significa IPCA + 6%)
            fator_ipca = calcular_ipca_acumulado(investimento.data_compra, taxa)
            valor_atual = valor_inicial * fator_ipca
            
        else:
            # Se não tem índice definido, retorna valor inicial
            return valor_inicial

        return valor_atual

    except Exception as e:
        print(f"Erro ao calcular RF id {investimento.id}: {e}")
        return valor_inicial