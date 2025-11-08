# models_finance.py (Importação Corrigida)

from database import db # Garante que está usando o db central
from datetime import datetime

class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # OK!

    def __repr__(self):
        return f"<Transacao {self.tipo} - {self.valor}>"

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Categoria {self.nome} ({self.tipo})>"


class Cartao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    limite = db.Column(db.Float, default=0.0)
    vencimento_dia = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # OK!

    def __repr__(self):
        return f"<Cartao {self.nome} - limite {self.limite}>"


class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.DateTime, nullable=False)
    pago = db.Column(db.Boolean, default=False)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacao.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # OK!

    def __repr__(self):
        return f"<Parcela {self.descricao} - {self.valor}>"


class Investimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50))
    nome = db.Column(db.String(200))
    quantidade = db.Column(db.Float, default=0.0)
    valor_unitario = db.Column(db.Float, default=0.0)
    data_compra = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # OK!

    def __repr__(self):
        return f"<Investimento {self.nome} ({self.tipo}) - qtd {self.quantidade}>"