# models_finance.py

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db

# ==========================================================
# 2. MODELO CATEGORIA (Tabela: categorias)
# ==========================================================
class Categoria(db.Model):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # 'entrada', 'saída', 'investimento'

    # Campos Visuais
    icone: Mapped[str] = mapped_column(String(50), default="fa-tag")
    cor: Mapped[str] = mapped_column(String(7), default="#007bff")

    # Hierarquia
    parent_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)

    subcategorias = db.relationship(
        "Categoria",
        backref=db.backref("pai", remote_side=[id]),
        lazy="dynamic",
        foreign_keys=[parent_id],
    )

    # Relações
    transacoes = relationship("Transacao", backref="categoria", lazy=True)
    parcelas = relationship("Parcela", backref="categoria", lazy=True)

    def __repr__(self):
        return f"Categoria('{self.nome}', Tipo='{self.tipo}')"


# ==========================================================
# 3. MODELO TRANSAÇÃO (Tabela: transacoes)
# ==========================================================
class Transacao(db.Model):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey("categorias.id"), nullable=False)

    descricao: Mapped[str] = mapped_column(String(200), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data_transacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Transacao('{self.descricao}', Valor={self.valor})"


# ==========================================================
# 4. MODELO CARTAO (Tabela: cartoes)
# ==========================================================
class Cartao(db.Model):
    __tablename__ = "cartoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # --- NOVO CAMPO: ÚLTIMOS 4 DÍGITOS ---
    digitos_finais: Mapped[str] = mapped_column(String(4), nullable=True)
    # -------------------------------------

    limite: Mapped[float] = mapped_column(Float, default=0.0)
    vencimento_dia: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relações
    parcelas = relationship("Parcela", backref="cartao", lazy=True)

    def __repr__(self):
        return f"Cartao('{self.nome}', Limite={self.limite})"


# ==========================================================
# 5. MODELO PARCELA (Tabela: parcelas)
# ==========================================================
class Parcela(db.Model):
    __tablename__ = "parcelas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), nullable=True) 

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    cartao_id: Mapped[int] = mapped_column(Integer, ForeignKey("cartoes.id"), nullable=True)
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey("categorias.id"), nullable=False)

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
    __tablename__ = "investimentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Dados Básicos
    tipo: Mapped[str] = mapped_column(String(50), nullable=False) # Ação, FII, Crypto
    nome: Mapped[str] = mapped_column(String(100), nullable=False) # Nome descritivo
    ticker: Mapped[str] = mapped_column(String(20), nullable=True) # Código (Ex: PETR4.SA)
    
    # Dados de Compra
    quantidade: Mapped[float] = mapped_column(Float, default=0.0)
    preco_compra: Mapped[float] = mapped_column(Float, default=0.0)
    data_compra: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Dados de Venda / Situação
    status: Mapped[str] = mapped_column(String(20), default="Ativo") # 'Ativo', 'Vendido'
    preco_venda: Mapped[float] = mapped_column(Float, nullable=True)
    data_venda: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Cache de Performance (Opcional, mas útil para histórico)
    lucro_final: Mapped[float] = mapped_column(Float, nullable=True) # Valor em R$

    def __repr__(self):
        return f"Investimento('{self.ticker or self.nome}', Status='{self.status}')"


# ==========================================================
# 7. MODELO META (Tabela: metas) <--- NOVO
# ==========================================================
class Meta(db.Model):
    __tablename__ = "metas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Valores Financeiros
    valor_alvo: Mapped[float] = mapped_column(Float, nullable=False)
    valor_atual: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Configuração
    data_limite: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    cor: Mapped[str] = mapped_column(String(20), default="bg-blue-500") # Guarda a classe Tailwind ou Hex
    concluida: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"Meta('{self.nome}', Alvo={self.valor_alvo})"