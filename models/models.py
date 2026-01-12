# models/models.py
# Define as tabelas de Usuário e Suporte

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from database import db

class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # PERFIL
    foto_perfil = db.Column(db.String(200), default="default_user.png")
    data_cadastro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # PLANOS
    plano = db.Column(db.String(20), default='free', nullable=False)

    # ADMIN (Novo Campo)
    # Se for True, tem acesso total. Se for False, é usuário comum.
    is_admin = db.Column(db.Boolean, default=False)

    # RELAÇÕES
    transacoes = db.relationship("Transacao", backref="usuario", lazy=True)
    categorias = db.relationship("Categoria", backref="usuario", lazy=True)
    tickets = db.relationship("Suporte", backref="usuario", lazy=True)

    def set_password(self, senha):
        self.password_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.password_hash, senha)

    def __repr__(self):
        return f"User('{self.nome}', '{self.email}', Admin: {self.is_admin})"

class Suporte(db.Model):
    __tablename__ = "suporte"
    
    id = db.Column(db.Integer, primary_key=True)
    assunto = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='aberto')
    data_abertura = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Ticket('{self.assunto}', '{self.status}')"