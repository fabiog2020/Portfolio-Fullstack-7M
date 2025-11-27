import pytest
from app import app, db
from models import User


# ============================================================
# FIXTURE PRINCIPAL: cria o app de teste e o banco em memória
# ============================================================
@pytest.fixture(scope="function")
def test_app():
    """
    Cria uma instância da aplicação configurada para testes.
    Tudo que usar 'test_app' estará no banco sqlite:///:memory:
    """
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ============================================================
# CLIENTE DE TESTE
# ============================================================
@pytest.fixture()
def client(test_app):
    """
    Retorna um client limpo para cada teste.
    """
    return test_app.test_client()


# ============================================================
# USUÁRIO PADRÃO
# ============================================================
@pytest.fixture()
def usuario_padrao(test_app):
    """
    Insere um usuário padrão no banco antes de cada teste que usar login.
    """
    user = User(nome="Tester", email="tester@example.com")
    user.set_password("123456")
    db.session.add(user)
    db.session.commit()
    return user


# ============================================================
# CLIENTE LOGADO
# ============================================================
@pytest.fixture()
def client_logado(client, usuario_padrao):
    """
    Retorna um client autenticado automaticamente.
    """
    client.post(
        "/login",
        data={"email": usuario_padrao.email, "senha": "123456"},
        follow_redirects=True,
    )
    return client

