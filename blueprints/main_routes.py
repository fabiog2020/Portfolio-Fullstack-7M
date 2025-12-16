# blueprints/main_routes.py

from datetime import datetime
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import extract, func
from database import db
from models import Transacao, Categoria, Parcela

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """
    Página Inicial (Landing Page).
    Se logado -> Dashboard.
    Se não logado -> Apresentação do App (Landing).
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    return render_template("landing.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Obtém mês e ano da URL ou usa a data atual
    mes = request.args.get("mes", type=int) or datetime.now().month
    ano = request.args.get("ano", type=int) or datetime.now().year

    # Função auxiliar para somar valores
    def get_total(tipo, model=Transacao, campo_data=Transacao.data_transacao, extra_filter=None):
        query = db.session.query(func.sum(func.abs(model.valor) if tipo == 'saída' else model.valor))\
            .join(Categoria).filter(model.user_id == current_user.id,
                                    extract("month", campo_data) == mes,
                                    extract("year", campo_data) == ano,
                                    Categoria.tipo == tipo)
        
        if extra_filter is not None: 
            query = query.filter(extra_filter)
        
        return query.scalar() or 0.0

    # Cálculos usando a função auxiliar
    entradas = get_total("entrada")
    saidas = get_total("saída")
    # Filtro: Parcelas de saída que NÃO foram pagas
    previsto = get_total("saída", Parcela, Parcela.data_vencimento, Parcela.pago.is_(False))
    
    # Transações Recentes
    recentes = Transacao.query.filter_by(user_id=current_user.id).order_by(Transacao.data_transacao.desc()).limit(10).all()
    
    # Dados para os Gráficos
    def get_chart_data(tipo):
        q = db.session.query(Categoria.nome, func.sum(Transacao.valor)).join(Categoria)\
            .filter(Transacao.user_id == current_user.id, Categoria.tipo == tipo,
                    extract("month", Transacao.data_transacao) == mes, extract("year", Transacao.data_transacao) == ano)\
            .group_by(Categoria.nome).all()
        return {n: float(v) for n, v in q if v}

    return render_template("dashboard.html", nome=current_user.nome, mes_atual=mes, ano_atual=ano,
                           entradas_realizadas=entradas, saidas_realizadas=saidas,
                           saldo_realizado=entradas - saidas, despesas_previstas_parcelas=previsto,
                           saldo_projetado=(entradas - saidas) - previsto, transacoes_recentes=recentes,
                           dados_despesas=get_chart_data("saída"), dados_receitas=get_chart_data("entrada"))