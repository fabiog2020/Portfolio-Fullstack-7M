from models_finance import Categoria, Transacao

def test_criar_categoria_e_transacao(client, client_logado):
    """
    Teste de Integração:
    1. Cria uma categoria via POST.
    2. Cria uma transação usando essa categoria.
    3. Verifica se ambas foram realmente salvas no banco em memória.
    """

    # =============================
    # PARTE A — Criar Categoria
    # =============================
    resp_cat = client_logado.post(
        "/categorias",
        data={
            "nome": "Mercado Teste",
            "tipo": "saída",
            "icone": "fa-cart",
            "cor": "#000000",
        },
        follow_redirects=True,
    )

    # Valida a resposta
    assert resp_cat.status_code == 200
    assert b"sucesso" in resp_cat.data.lower()

    # Busca a categoria no banco
    with client.application.app_context():
        cat = Categoria.query.filter_by(nome="Mercado Teste").first()
        assert cat is not None
        cat_id = cat.id

    # =============================
    # PARTE B — Criar Transação
    # =============================
    resp_trans = client_logado.post(
        "/adicionar",
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

    # Confirma se salvou no banco
    with client.application.app_context():
        transacao = Transacao.query.filter_by(descricao="Compra Semanal").first()
        assert transacao is not None
        assert transacao.valor == -150.50  # saída deve ser negativa

