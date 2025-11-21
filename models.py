# models.py
# Este arquivo define o modelo User, a primeira tabela do seu banco.

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from database import db


# ==========================================================
# MODELO: USUÁRIO (Obrigatório para autenticação)
# ==========================================================
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # NOVOS CAMPOS PARA O PERFIL (Passo 1.2)
    foto_perfil = db.Column(db.String(200), default="default_user.png")

    # CAMPO ADICIONADO: Data de registro
    data_cadastro = db.Column(db.DateTime, default=datetime.now(UTC))

    # Relações: Opcional, mas útil para debug e acesso reverso
    # 'Transacao' e 'Categoria' são classes definidas em 'models_finance.py'
    transacoes = db.relationship("Transacao", backref="usuario", lazy=True)
    categorias = db.relationship("Categoria", backref="usuario", lazy=True)

    def set_password(self, senha):
        """Cria o hash da senha para armazenamento seguro."""
        self.password_hash = generate_password_hash(senha)

    def check_password(self, senha):
        """Verifica se a senha fornecida corresponde ao hash."""
        return check_password_hash(self.password_hash, senha)

    def __repr__(self):
        return f"User('{self.nome}', '{self.email}')"
