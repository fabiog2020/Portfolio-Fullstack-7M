# services/market_service.py

import yfinance as yf

def get_current_price(ticker): 
    """
    Busca o preço atual de um ativo usando yfinance.
    Adiciona .SA automaticamente se for padrão B3 e não tiver sufixo.
    """
    if not ticker:
        return 0.0

    ticker = ticker.strip().upper()
    
    # Tratamento simples para ações brasileiras
    if not ticker.endswith(".SA") and (len(ticker) == 5 or len(ticker) == 6) and ticker[-1].isdigit():
        ticker = f"{ticker}.SA"
    
    try:
        stock = yf.Ticker(ticker)
        # Tenta pegar o preço de mercado regular
        data = stock.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return 0.0
    except Exception as e:
        print(f"Erro ao buscar ticker {ticker}: {e}") 
        return 0.0 
  