# tests/unit/test_models.py

from models import User
from database import db

def test_password_hashing():
    """
    Teste Unitário: Verifica a lógica de hash de senha (sem precisar do banco).
    """
    user = User(nome="Teste", email="teste@example.com")
    user.set_password("gatinho")

    # A senha não pode estar em texto plano
    assert user.password_hash != "gatinho"
    
    # Deve retornar True para a senha correta
    assert user.check_password("gatinho") is True
    
    # Deve retornar False para senha errada
    assert user.check_password("cachorro") is False

def test_user_repr():
    """
    Teste Unitário: Verifica a representação em string do objeto.
    """
    user = User(nome="Admin", email="admin@finance.app")
    # O método __repr__ deve retornar: User('Admin', 'admin@finance.app')
    assert repr(user) == "User('Admin', 'admin@finance.app')"

def test_criacao_e_persistencia_usuario(test_app):
    """
    Teste de Integração de Modelo: Verifica se o usuário é salvo no DB corretamente.
    (Este é o seu teste original, ajustado e mantido aqui)
    """
    with test_app.app_context():
        user = User(nome="Fábio", email="fabio@test.com")
        user.set_password("senha123")
        
        db.session.add(user)
        db.session.commit()

        salvo = User.query.filter_by(email="fabio@test.com").first()

        assert salvo is not None
        assert salvo.id is not None  # Garante que ganhou um ID
        assert salvo.nome == "Fábio"
        assert salvo.check_password("senha123")