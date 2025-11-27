from models import User
from database import db


def test_criacao_usuario(test_app):
    with test_app.app_context():
        user = User(nome="Fábio", email="fabio@test.com")
        user.set_password("senha123")
        db.session.add(user)
        db.session.commit()

        salvo = User.query.filter_by(email="fabio@test.com").first()

        assert salvo is not None
        assert salvo.nome == "Fábio"
        assert salvo.check_password("senha123")
