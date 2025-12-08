# tests/conftest.py
import pytest
from factory import create_app
from database import db
from models import User

@pytest.fixture(scope="function")
def test_app():
    """
    Cria uma instância da aplicação configurada para testes.
    Usa um banco de dados em memória e desabilita CSRF para facilitar os posts.
    """
    # Cria o app usando a fábrica
    app = create_app()
    
    # Sobrescreve configurações para o ambiente de teste
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False, # Desabilita tokens CSRF nos forms de teste
        LOGIN_DISABLED=False,
    )

    # Contexto da aplicação (cria e dropa tabelas a cada teste)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(test_app):
    """Retorna o cliente de teste (navegador simulado)."""
    return test_app.test_client()

@pytest.fixture()
def usuario_padrao(test_app):
    """Cria e insere um usuário para testes que exigem login."""
    user = User(nome="Tester", email="tester@example.com")
    user.set_password("123456")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture()
def client_logado(client, usuario_padrao):
    """Retorna um cliente já autenticado."""
    # Atenção: Rota atualizada para o blueprint de auth
    client.post(
        "/auth/login", 
        data={"email": usuario_padrao.email, "senha": "123456"},
        follow_redirects=True,
    )
    return client

