# tests/integration/test_fluxo_transacao.py
from models import Categoria, Transacao

def test_criar_categoria_e_transacao(client, client_logado):
    """
    Teste de Integração: Cria Categoria -> Cria Transação.
    Rotas atualizadas para os Blueprints.
    """

    # 1. Criar Categoria (Rota: /categorias/)
    resp_cat = client_logado.post(
        "/categorias/",
        data={
            "nome": "Mercado Teste",
            "tipo": "saída",
            "icone": "fa-cart",
            "cor": "#000000",
        },
        follow_redirects=True,
    )
    assert resp_cat.status_code == 200

    # Busca o ID da categoria criada
    with client.application.app_context():
        cat = Categoria.query.filter_by(nome="Mercado Teste").first()
        assert cat is not None
        cat_id = cat.id

    # 2. Criar Transação (Rota: /transacoes/adicionar)
    resp_trans = client_logado.post(
        "/transacoes/adicionar",
        data={
            "categoria_id": cat_id,
            "descricao": "Compra Semanal",
            "valor": "150.50",
            "data": "2023-10-01",
        },
        follow_redirects=True,
    )

    assert resp_trans.status_code == 200
    assert b"sucesso" in resp_trans.data.lower()

    # Confirma persistência
    with client.application.app_context():
        transacao = Transacao.query.filter_by(descricao="Compra Semanal").first()
        assert transacao is not None
        assert transacao.valor == -150.50