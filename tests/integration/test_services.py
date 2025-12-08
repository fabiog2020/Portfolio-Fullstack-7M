# tests/integration/test_services.py

from datetime import date
from unittest.mock import patch
from flask_login import login_user
from services.transactions_service import criar_transacao_a_partir_formulario
from services.parcelas_service import criar_parcelas_a_partir_formulario, pagar_parcela_service
from models import Categoria, Transacao, User, Parcela, Cartao
from database import db

# --- CLASSES AUXILIARES PARA MOCK ---
class MockField:
    def __init__(self, data):
        self.data = data

class MockTransacaoForm:
    def __init__(self, categoria_id=None, descricao=None, valor=None, data_transacao=None):
        self.categoria_id = MockField(categoria_id)
        self.descricao = MockField(descricao)
        self.valor = MockField(valor)
        self.data = MockField(data_transacao)

# =================================================================
# TESTES DE TRANSAÇÕES
# =================================================================

def test_criar_transacao_fluxo_completo(test_app, usuario_padrao):
    """Caminho feliz de transação."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Mercado", tipo="saída")
        db.session.add(cat); db.session.commit()

        form = MockTransacaoForm(cat.id, "Compras", 500.00, date(2023, 12, 25))
        assert criar_transacao_a_partir_formulario(form) is True

def test_criar_transacao_validacoes(test_app, usuario_padrao):
    """Erros de input."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        assert criar_transacao_a_partir_formulario(MockTransacaoForm(None, "X", 10, date.today())) is False
        assert criar_transacao_a_partir_formulario(MockTransacaoForm(1, "X", None, date.today())) is False
        assert criar_transacao_a_partir_formulario(MockTransacaoForm(1, "X", 10, None)) is False
        assert criar_transacao_a_partir_formulario(MockTransacaoForm(999, "X", 10, date.today())) is False

def test_criar_transacao_permissao_e_rollback(test_app, usuario_padrao):
    """Erro de usuário e erro de banco."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        outro = User(nome="B", email="b@b.com"); outro.set_password("1"); db.session.add(outro); db.session.commit()
        cat_alheia = Categoria(user_id=outro.id, nome="Priv", tipo="saída"); db.session.add(cat_alheia); db.session.commit()
        assert criar_transacao_a_partir_formulario(MockTransacaoForm(cat_alheia.id, "Hack", 10, date.today())) is False

        cat_propria = Categoria(user_id=usuario_padrao.id, nome="Ok", tipo="saída"); db.session.add(cat_propria); db.session.commit()
        with patch('database.db.session.commit', side_effect=Exception("DB Crash")):
            assert criar_transacao_a_partir_formulario(MockTransacaoForm(cat_propria.id, "Rollback", 10, date.today())) is False

# =================================================================
# TESTES DE PARCELAS (COBERTURA TOTAL)
# =================================================================

def test_criar_parcelas_sucesso_com_cartao(test_app, usuario_padrao):
    """
    Cobre o fluxo normal E a conversão correta de cartao_id válido.
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Geral", tipo="saída")
        cartao = Cartao(user_id=usuario_padrao.id, nome="Visa", limite=1000)
        db.session.add_all([cat, cartao]); db.session.commit()

        form_data = {
            "descricao": "TV", "valor_total": "1000", "num_parcelas": "2",
            "data_vencimento_primeira": "2024-01-01", "categoria_id": str(cat.id),
            "cartao_id": str(cartao.id) # ID válido
        }
        assert criar_parcelas_a_partir_formulario(form_data) is True
        assert Parcela.query.count() == 2

def test_criar_parcelas_erro_inputs(test_app, usuario_padrao):
    """
    Cobre o bloco 'except (ValueError, TypeError)' inicial (Linhas 36-40).
    Força erro passando string no lugar de número.
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Geral", tipo="saída")
        db.session.add(cat); db.session.commit()

        # Caso 1: Cartão ID inválido (texto)
        form_cartao_errado = {
            "descricao": "Erro", "valor_total": "100", "num_parcelas": "2",
            "data_vencimento_primeira": "2024-01-01", "categoria_id": str(cat.id),
            "cartao_id": "texto" # Força ValueError no int()
        }
        assert criar_parcelas_a_partir_formulario(form_cartao_errado) is False

        # Caso 2: Valor Total inválido
        form_valor_errado = form_cartao_errado.copy()
        form_valor_errado['cartao_id'] = ""
        form_valor_errado['valor_total'] = "abc"
        assert criar_parcelas_a_partir_formulario(form_valor_errado) is False

def test_criar_parcelas_erros_logicos(test_app, usuario_padrao):
    """
    Cobre validações de negócio (valor zero, categoria errada).
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat_entrada = Categoria(user_id=usuario_padrao.id, nome="Salário", tipo="entrada")
        db.session.add(cat_entrada); db.session.commit()

        # Categoria de tipo errado
        form_cat = {
            "descricao": "X", "valor_total": "100", "num_parcelas": "1",
            "data_vencimento_primeira": "2024-01-01", "categoria_id": str(cat_entrada.id), "cartao_id": ""
        }
        assert criar_parcelas_a_partir_formulario(form_cat) is False

        # Valor Zero
        form_zero = form_cat.copy()
        form_zero['valor_total'] = "0"
        assert criar_parcelas_a_partir_formulario(form_zero) is False

def test_criar_parcelas_datas_ajuste_fevereiro(test_app, usuario_padrao):
    """
    Cobre o ajuste de datas (Linhas 72-73 - except ValueError).
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Datas", tipo="saída")
        db.session.add(cat); db.session.commit()

        # 31/01 -> Próximo mês (Fev) não tem 31, deve cair no except
        form_data = {
            "descricao": "Data", "valor_total": "200", "num_parcelas": "2",
            "data_vencimento_primeira": "2023-01-31", 
            "categoria_id": str(cat.id), "cartao_id": ""
        }
        assert criar_parcelas_a_partir_formulario(form_data) is True
        
        p2 = Parcela.query.filter_by(descricao="Data (2/2)").first()
        assert p2.data_vencimento.month == 2
        # Verifica se ajustou (28 em 2023)
        assert p2.data_vencimento.day == 28 

def test_criar_parcelas_erro_banco(test_app, usuario_padrao):
    """Cobre o rollback ao criar parcelas (Linhas 108-111)."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Ok", tipo="saída")
        db.session.add(cat); db.session.commit()
        
        form_data = {
            "descricao": "Rollback", "valor_total": "100", "num_parcelas": "1",
            "data_vencimento_primeira": "2024-01-01", "categoria_id": str(cat.id), "cartao_id": ""
        }
        
        with patch('database.db.session.commit', side_effect=Exception("DB Error")):
            assert criar_parcelas_a_partir_formulario(form_data) is False

def test_pagar_parcela_fluxo_normal(test_app, usuario_padrao):
    """Caminho feliz do pagamento."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="C", tipo="saída")
        db.session.add(cat); db.session.commit()
        p = Parcela(user_id=usuario_padrao.id, categoria_id=cat.id, valor=10, data_vencimento=date.today(), pago=False)
        db.session.add(p); db.session.commit()
        
        assert pagar_parcela_service(p.id) is True
        assert Parcela.query.get(p.id).pago is True

def test_pagar_parcela_validacoes_iniciais(test_app, usuario_padrao):
    """Cobre validações iniciais (não existe ou já paga)."""
    with test_app.test_request_context():
        login_user(usuario_padrao)
        
        # Não existe
        assert pagar_parcela_service(9999) is False
        
        # Já paga
        cat = Categoria(user_id=usuario_padrao.id, nome="C", tipo="saída")
        db.session.add(cat); db.session.commit()
        p = Parcela(user_id=usuario_padrao.id, categoria_id=cat.id, valor=10, data_vencimento=date.today(), pago=True)
        db.session.add(p); db.session.commit()
        assert pagar_parcela_service(p.id) is False

def test_pagar_parcela_sem_categoria(test_app, usuario_padrao):
    """
    Cobre 'if not categoria' (Linhas 142-149).
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="Temp", tipo="saída")
        db.session.add(cat); db.session.commit()
        
        p = Parcela(user_id=usuario_padrao.id, categoria_id=cat.id, valor=50, data_vencimento=date.today(), pago=False)
        db.session.add(p); db.session.commit()
        
        # Deleta a categoria forçadamente
        Categoria.query.filter_by(id=cat.id).delete()
        db.session.commit()
        
        assert pagar_parcela_service(p.id) is False
        db.session.expire_all()
        assert Parcela.query.get(p.id).pago is False

def test_pagar_parcela_erro_rollback(test_app, usuario_padrao):
    """
    Cobre 'except Exception' no pagamento (Linhas 164-169).
    """
    with test_app.test_request_context():
        login_user(usuario_padrao)
        cat = Categoria(user_id=usuario_padrao.id, nome="T", tipo="saída")
        db.session.add(cat); db.session.commit()
        p = Parcela(user_id=usuario_padrao.id, categoria_id=cat.id, valor=50, data_vencimento=date.today(), pago=False)
        db.session.add(p); db.session.commit()

        with patch('database.db.session.commit', side_effect=Exception("Critical")):
            assert pagar_parcela_service(p.id) is False