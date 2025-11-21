from models_finance import Categoria, Transacao


def test_criar_categoria_e_transacao(test_client, logado):
    """
    Teste de Integração:
    1. Tenta criar uma categoria 'Mercado'.
    2. Tenta criar uma transação usando essa categoria.
    3. Verifica se salvou no 'banco de memória'.
    """

    # PARTE A: Criar Categoria via POST (simulando o formulário)
    resp_cat = logado.post(
        "/categorias",
        data={
            "nome": "Mercado Teste",
            "tipo": "saída",
            "icone": "fa-cart",
            "cor": "#000000",
        },
        follow_redirects=True,
    )

    # Verifica se deu certo (status 200 OK) e se apareceu mensagem de sucesso
    assert resp_cat.status_code == 200
    assert b"sucesso" in resp_cat.data.lower()

    # Verifica no banco se a categoria existe
    with test_client.application.app_context():
        cat = Categoria.query.filter_by(nome="Mercado Teste").first()
        assert cat is not None
        cat_id = cat.id

    # PARTE B: Criar Transação usando a categoria criada
    resp_trans = logado.post(
        "/adicionar",
        data={
            "categoria_id": cat_id,
            "descricao": "Compra Semanal",
            "valor": "150.50",
            "data": "2023-10-01",  # Formato YYYY-MM-DD
        },
        follow_redirects=True,
    )

    assert resp_trans.status_code == 200
    assert b"sucesso" in resp_trans.data.lower()

    # Verifica se a transação foi salva e se o valor ficou negativo (pois é saída)
    with test_client.application.app_context():
        transacao = Transacao.query.filter_by(descricao="Compra Semanal").first()
        assert transacao is not None
        assert transacao.valor == -150.50  # Deve ser negativo!
