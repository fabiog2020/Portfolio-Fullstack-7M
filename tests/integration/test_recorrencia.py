from datetime import date
from models import Categoria, Parcela

def test_criar_despesa_recorrente_valor_correto(client_logado, usuario_padrao, test_app):
    """
    Cenário: Usuário lança uma despesa recorrente de R$ 100,00 por 12 meses.
    Expectativa: O sistema deve criar 12 parcelas, e CADA UMA deve ser de R$ 100,00.
    """
    
    # 1. Preparação
    with test_app.app_context():
        # Cria a categoria no banco de teste
        cat = Categoria(nome="Teste Recorrente", tipo="saída", user_id=usuario_padrao.id)
        from database import db
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

    # 2. Ação
    # URL CORRIGIDA conforme factory.py (/transacoes e não /transactions)
    url_post = "/transacoes/adicionar"

    dados_formulario = {
        "valor": "100.00",
        "descricao": "Internet Fixa",
        "data": date.today().isoformat(),
        "categoria_id": cat_id,          
        "tipo_transacao": "recorrente",  
        "meses_recorrencia": "12",       
        "cartao_id": ""                  
    }

    # O client_logado envia a requisição POST
    response = client_logado.post(url_post, data=dados_formulario, follow_redirects=True)

    # 3. Verificação
    assert response.status_code == 200, f"Erro na requisição. Recebido: {response.status_code}"
    
    with test_app.app_context():
        # Busca parcelas criadas
        parcelas = Parcela.query.filter(Parcela.descricao.like("Internet Fixa%")).all()
        
        # Verifica se criou as 12
        assert len(parcelas) == 12, f"Erro na quantidade: Esperado 12, encontrou {len(parcelas)}"
        
        # Verifica se o valor NÃO foi dividido (R$ 100.00)
        # Se a lógica estivesse errada, o valor seria ~8.33
        parcela_amostra = parcelas[0]
        assert abs(parcela_amostra.valor - 100.00) < 0.01, f"Erro no valor: Esperado 100.00, encontrou {parcela_amostra.valor}"