from datetime import date, datetime
from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func
from database import db
from models_finance import Categoria, Transacao

reports_bp = Blueprint('reports', __name__)

@reports_bp.route("/relatorios", methods=["GET"])
@login_required
def relatorios():
    periodo = request.args.get("periodo")
    hoje = datetime.now()
    if periodo:
        try:
            ano, mes = map(int, periodo.split("-"))
        except ValueError:
            mes, ano = hoje.month, hoje.year
            periodo = hoje.strftime("%Y-%m")
    else:
        mes, ano = hoje.month, hoje.year
        periodo = hoje.strftime("%Y-%m")

    def get_data(tipo):
        query = db.session.query(Categoria.nome, func.sum(Transacao.valor)).join(Categoria)\
            .filter(Transacao.user_id == current_user.id, Categoria.tipo == tipo,
                    extract("month", Transacao.data_transacao) == mes,
                    extract("year", Transacao.data_transacao) == ano)\
            .group_by(Categoria.nome).all()
        return {nome: abs(val) if tipo == 'saída' else val for nome, val in query if val}

    return render_template("relatorios.html", periodo_selecionado=periodo,
                           dados_despesas=get_data("saída"), dados_receitas=get_data("entrada"))

@reports_bp.route("/extrato", methods=["GET"])
@login_required
def extrato():
    cats = Categoria.query.filter_by(user_id=current_user.id).filter(Categoria.tipo.in_(["entrada", "saída"])).all()
    query = db.session.query(
        Transacao.id, Transacao.data_transacao.label("data"), Transacao.descricao,
        func.abs(Transacao.valor).label("valor"), Categoria.nome.label("categoria_nome"),
        Categoria.tipo.label("tipo_bd")
    ).join(Categoria).filter(Transacao.user_id == current_user.id)

    dt_ini = request.args.get("data_inicio")
    dt_fim = request.args.get("data_fim")
    cat_id = request.args.get("categoria_id")
    tipo = request.args.get("tipo")

    if dt_ini: query = query.filter(Transacao.data_transacao >= date.fromisoformat(dt_ini))
    if dt_fim: query = query.filter(Transacao.data_transacao <= date.fromisoformat(dt_fim))
    if cat_id and cat_id.isdigit(): query = query.filter(Transacao.categoria_id == int(cat_id))
    if tipo == 'receita': query = query.filter(Categoria.tipo == 'entrada')
    elif tipo == 'despesa': query = query.filter(Categoria.tipo == 'saída')

    res = query.order_by(Transacao.data_transacao.desc()).all()
    lista = [dict(r._asdict(), tipo="receita" if r.tipo_bd == "entrada" else "despesa", conta_nome="Padrão") for r in res]

    return render_template("extrato.html", transacoes=lista, categorias=cats)