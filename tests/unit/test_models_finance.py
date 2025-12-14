from models import Cartao

def test_criar_cartao_com_digitos(test_app, usuario_padrao):
    """
    Testa se o modelo Cartao aceita e salva o novo campo 'digitos_finais'.
    """
    with test_app.app_context():
        # 1. Criação
        novo_cartao = Cartao(
            nome="Nubank Platinum",
            limite=5000.00,
            vencimento_dia=15,
            digitos_finais="8829", # O campo novo
            user_id=usuario_padrao.id
        )
        
        from database import db
        db.session.add(novo_cartao)
        db.session.commit()

        # 2. Recuperação
        cartao_banco = db.session.get(Cartao, novo_cartao.id)

        # 3. Verificações
        assert cartao_banco is not None
        assert cartao_banco.nome == "Nubank Platinum"
        assert cartao_banco.digitos_finais == "8829"
        assert cartao_banco.limite == 5000.00
        
        print("\n✅ Teste de Modelo Cartão: SUCESSO! Campos salvos corretamente.")