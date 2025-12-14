import pytest
from datetime import date
from models import Categoria, Parcela, Transacao
from database import db
from services.transactions_service import criar_transacao_a_partir_formulario

# Mock simples para simular o comportamento do WTForms
class MockForm:
    def __init__(self, descricao, valor, data_obj, categoria_id):
        self.descricao = type('obj', (object,), {'data': descricao})
        self.valor = type('obj', (object,), {'data': valor})
        self.data = type('obj', (object,), {'data': data_obj})
        # Simula o campo do WTForms, embora a gente use o request.form também
        self.categoria_id = type('obj', (object,), {'data': categoria_id})

def test_criar_transacao_fluxo_padrao(test_app, usuario_padrao):
    """
    Testa a criação de uma transação única simples (fluxo padrão).
    Simula o envio dos dados manuais via request context.
    """
    with test_app.app_context():
        # Cria categoria necessária
        cat = Categoria(user_id=usuario_padrao.id, nome="Mercado", tipo="saída")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

        # Simula os dados que viriam do HTML (Selects manuais)
        dados_html_manual = {
            'tipo_transacao': 'unico',
            'categoria_id': str(cat_id),
            'cartao_id': ''
        }

        # Cria o contexto da requisição simulando um POST
        with test_app.test_request_context('/adicionar', method='POST', data=dados_html_manual):
            # Loga o usuário no contexto para o current_user funcionar
            from flask_login import login_user
            login_user(usuario_padrao)

            # Prepara o Form simulado (WTForms)
            form = MockForm("Compras Teste", 500.00, date(2023, 12, 25), cat_id)
            
            # Executa o serviço
            resultado = criar_transacao_a_partir_formulario(form)
            
            # Verificações
            assert resultado is True
            
            t = Transacao.query.filter_by(descricao="Compras Teste").first()
            assert t is not None
            assert t.valor == -500.00  # Deve ser negativo pois é saída

def test_criar_parcelas_erro_inputs(test_app, usuario_padrao):
    """
    Testa se o sistema lida bem com dados inválidos (ex: texto no lugar de ID).
    """
    with test_app.app_context():
        # Dados ruins (categoria_id inválido)
        dados_ruins = {
            'tipo_transacao': 'parcelado',
            'categoria_id': 'texto_invalido', 
            'num_parcelas': '12',
            'cartao_id': ''
        }
        
        with test_app.test_request_context('/adicionar', method='POST', data=dados_ruins):
            from flask_login import login_user
            login_user(usuario_padrao)
            
            form = MockForm("Erro", 100.00, date.today(), "texto")
            
            # Deve retornar False (erro tratado) e não crashar o sistema
            resultado = criar_transacao_a_partir_formulario(form)
            assert resultado is False