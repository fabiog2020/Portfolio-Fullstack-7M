# tests/test_auth.py
from models import User

def test_registro_usuario_sucesso(client, test_app):
    """Testa se é possível registrar um novo usuário."""
    response = client.post("/auth/register", data={
        "nome": "Novo Usuario",
        "email": "novo@teste.com",
        "senha": "senha_segura"
    }, follow_redirects=True)

    # Verifica redirecionamento ou mensagem de sucesso
    assert response.status_code == 200
    # Verifica se o usuário foi salvo no banco
    with test_app.app_context():
        user = User.query.filter_by(email="novo@teste.com").first()
        assert user is not None
        assert user.nome == "Novo Usuario"

def test_login_sucesso(client, usuario_padrao):
    """Testa o login com credenciais corretas."""
    response = client.post("/auth/login", data={
        "email": usuario_padrao.email,
        "senha": "123456"
    }, follow_redirects=True)

    assert response.status_code == 200
    # Verifica se apareceu o link de logout (indicando que está logado)
    # Ou verifica se estamos no dashboard
    assert b"Dashboard" in response.data or b"Sair" in response.data

def test_login_senha_errada(client, usuario_padrao):
    """Testa o login com senha incorreta."""
    response = client.post("/auth/login", data={
        "email": usuario_padrao.email,
        "senha": "senha_errada"
    }, follow_redirects=True)

    assert response.status_code == 200
    # Deve conter mensagem de erro (ajuste conforme sua flash message)
    assert b"inv" in response.data.lower()  # Procura por "inválidos" ou similar

def test_logout(client_logado):
    """Testa o logout."""
    response = client_logado.get("/auth/logout", follow_redirects=True)
    
    assert response.status_code == 200
    # Deve redirecionar para login e mostrar o formulário de login novamente
    assert b"Entrar" in response.data