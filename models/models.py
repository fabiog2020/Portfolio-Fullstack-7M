# models/models.py
# Define as tabelas de Usuário e Suporte

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from database import db

# ==========================================================
# MODELO: USUÁRIO
# ==========================================================
class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # SEGURANÇA (Confirmação de E-mail)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    # PERFIL BÁSICO
    foto_perfil = db.Column(db.String(200), default="default_user.png")
    data_cadastro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    plano = db.Column(db.String(20), default='free', nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # ======================================================
    # DADOS ESTENDIDOS (RAIO-X PARA I.A. E MARKETING)
    # ======================================================
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    
    # Endereço (Geolocalização de ofertas)
    cep = db.Column(db.String(10), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True) # UF (SP, RJ, etc)
    
    # Perfil Econômico (Para recomendação de Investimentos)
    profissao = db.Column(db.String(100), nullable=True)
    renda_mensal = db.Column(db.Float, default=0.0)

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


# ==========================================================
# MODELO: SUPORTE
# ==========================================================
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