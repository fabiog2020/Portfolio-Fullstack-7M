import pytest

from app import app, db
from models import User


# ==================================================
# FIXTURE: O CENÁRIO DO TESTE
# ==================================================
@pytest.fixture(scope="module")
def test_client():
    # 1. Configura o Flask para modo de TESTE (Banco na memória RAM)
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Banco volátil
            "WTF_CSRF_ENABLED": False,  # Desliga proteção de form p/ facilitar automação
            "LOGIN_DISABLED": False,
        }
    )

    # 2. Cria o gerenciador de testes do Flask
    testing_client = app.test_client()

    # 3. Cria as tabelas e um usuário padrão para testar
    with app.app_context():
        db.create_all()

        # Cria usuário de teste
        usuario = User(nome="Tester", email="teste@demo.com")
        usuario.set_password("123456")  # Senha simples p/ teste
        db.session.add(usuario)
        db.session.commit()

        yield testing_client  # <-- O teste acontece AQUI

        # 4. Limpeza (tira tudo da memória quando acabar)
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="module")
def logado(test_client):
    """Fixture auxiliar que já entrega o sistema com usuário logado"""
    test_client.post(
        "/login",
        data={"email": "teste@demo.com", "senha": "123456"},
        follow_redirects=True,
    )

    return test_client
