# models_finance.py

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import TEXT 
from database import db


# ==========================================================
# 2. MODELO CATEGORIA (Tabela: categorias)
# ==========================================================
class Categoria(db.Model):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'entrada', 'saída', 'investimento'

    # Campos Visuais
    icone: Mapped[str] = mapped_column(String(50), default="fa-tag")
    cor: Mapped[str] = mapped_column(String(7), default="#007bff")

    # 4. Hierarquia (Para subcategorias) <--- NOVO: Coluna que guarda o ID do Pai
    parent_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)

    # 5. Relacionamento de Subcategorias (SELF-REFERENCE) <--- NOVO: Relação Python
    # Essa linha permite que você acesse as subcategorias com categoria_pai.subcategorias
    subcategorias = db.relationship(
        "Categoria",
        backref=db.backref("pai", remote_side=[id]),
        lazy="dynamic",
        foreign_keys=[parent_id],
    )

    # Relações
    transacoes = relationship("Transacao", backref="categoria", lazy=True)
    parcelas = relationship(
        "Parcela", backref="categoria", lazy=True
    )  # Ligação com parcelas

    def __repr__(self):
        return f"Categoria('{self.nome}', Tipo='{self.tipo}')"


# ==========================================================
# 3. MODELO TRANSAÇÃO (Tabela: transacoes)
# ==========================================================
class Transacao(db.Model):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Chaves Estrangeiras
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    categoria_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categorias.id"), nullable=False
    )

    descricao: Mapped[str] = mapped_column(String(200), nullable=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    # Mudado para DateTime para registrar a hora, não apenas o dia
    data_transacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    def __repr__(self):
        return f"Transacao('{self.descricao}', Valor={self.valor})"


# ==========================================================
# 4. MODELO CARTAO (Tabela: cartoes)
# ==========================================================
class Cartao(db.Model):
    __tablename__ = "cartoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    limite: Mapped[float] = mapped_column(Float, default=0.0)
    vencimento_dia: Mapped[int] = mapped_column(
        Integer, nullable=True
    )  # Dia do mês de vencimento

    # Relações
    parcelas = relationship(
        "Parcela", backref="cartao", lazy=True
    )  # Ligação com parcelas

    def __repr__(self):
        return f"Cartao('{self.nome}', Limite={self.limite})"


# ==========================================================
# 5. MODELO PARCELA (Tabela: parcelas)
# ==========================================================
class Parcela(db.Model):
    __tablename__ = "parcelas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # --- NOVO CAMPO: Identificador do Grupo de Parcelas ---
    # Permite agrupar parcelas de uma mesma compra
    group_id: Mapped[str] = mapped_column(String(36), nullable=True) 
    # ------------------------------------------------------

    # Chaves Estrangeiras
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

    # Chave Estrangeira
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, default=0.0)

    # Dados de Compra
    preco_compra: Mapped[float] = mapped_column(Float, default=0.0)
    # Mudado para usar default=datetime.utcnow, que é executado no momento da inserção
    data_compra: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Investimento('{self.nome}', Qtde={self.quantidade})"
