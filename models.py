# models.py corrigido

# Importa o objeto 'db' central e o UserMixin do Flask-Login
from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# Modelo de usuário — AGORA HERDA DE UserMixin E db.Model!
class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)

    # grava senha criptografada
    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    # valida senha ao logar
    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<User {self.email}>"