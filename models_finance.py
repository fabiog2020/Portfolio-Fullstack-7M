# models_finance.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean
from database import db

# ==========================================================
# 1. MODELO USUARIO (Tabela: users)
# ==========================================================
# UserMixin adiciona propriedades necessárias ao Flask-Login
class Usuario(UserMixin, db.Model):
    # __tablename__ é 'users' para corresponder aos ForeignKeys nos outros modelos
    __tablename__ = 'users' 

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relações: facilita o acesso a todos os objetos do usuário
    categorias = relationship('Categoria', backref='user', lazy=True)
    transacoes = relationship('Transacao', backref='user', lazy=True)
    cartoes = relationship('Cartao', backref='user', lazy=True)
    parcelas = relationship('Parcela', backref='user', lazy=True)
    investimentos = relationship('Investimento', backref='user', lazy=True)
    
    # Métodos de segurança (Hashing de Senha)
    def set_senha(self, senha):
        """Gera o hash seguro da senha."""
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        """Verifica se a senha fornecida corresponde ao hash."""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario {self.email}>'

# ==========================================================
# 2. MODELO CATEGORIA (Tabela: categorias)
# ==========================================================
class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False) # 'entrada', 'saída', 'investimento'
    
    # Campos Visuais
    icone: Mapped[str] = mapped_column(String(50), default='fa-tag') 
    cor: Mapped[str] = mapped_column(String(7), default='#007bff') 
    
    # Relações
    transacoes = relationship('Transacao', backref='categoria', lazy=True)
    parcelas = relationship('Parcela', backref='categoria', lazy=True) # Ligação com parcelas
    
    def __repr__(self):
        return f"Categoria('{self.nome}', Tipo='{self.tipo}')"

# ==========================================================
# 3. MODELO TRANSAÇÃO (Tabela: transacoes)
# ==========================================================
class Transacao(db.Model):
    __tablename__ = 'transacoes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Chaves Estrangeiras
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey('categorias.id'), nullable=False)
    
    descricao: Mapped[str] = mapped_column(String(200), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    # Mudado para DateTime para registrar a hora, não apenas o dia
    data_transacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow) 
    
    def __repr__(self):
        return f"Transacao('{self.descricao}', Valor={self.valor})"

# ==========================================================
# 4. MODELO CARTAO (Tabela: cartoes)
# ==========================================================
class Cartao(db.Model):
    __tablename__ = 'cartoes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    limite: Mapped[float] = mapped_column(Float, default=0.0)
    vencimento_dia: Mapped[int] = mapped_column(Integer, nullable=True) # Dia do mês de vencimento
    
    # Relações
    parcelas = relationship('Parcela', backref='cartao', lazy=True) # Ligação com parcelas
    
    def __repr__(self):
        return f"Cartao('{self.nome}', Limite={self.limite})"

# ==========================================================
# 5. MODELO PARCELA (Tabela: parcelas)
# ==========================================================
class Parcela(db.Model):
    __tablename__ = 'parcelas'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Chaves Estrangeiras
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    cartao_id: Mapped[int] = mapped_column(Integer, ForeignKey('cartoes.id'), nullable=True) 
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey('categorias.id'), nullable=False)
    
    descricao: Mapped[str] = mapped_column(String(200), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False) 
    data_vencimento: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pago: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def __repr__(self):
        return f"Parcela('{self.descricao}', Vencimento={self.data_vencimento})"

# ==========================================================
# 6. MODELO INVESTIMENTO (Tabela: investimentos)
# ==========================================================
class Investimento(db.Model):
    __tablename__ = 'investimentos'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    tipo: Mapped[str] = mapped_column(String(50), nullable=False) 
    nome: Mapped[str] = mapped_column(String(100), nullable=False) 
    quantidade: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Dados de Compra
    preco_compra: Mapped[float] = mapped_column(Float, default=0.0)
    # Mudado para usar default=datetime.utcnow, que é executado no momento da inserção
    data_compra: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) 
    
    def __repr__(self):
        return f"Investimento('{self.nome}', Qtde={self.quantidade})"