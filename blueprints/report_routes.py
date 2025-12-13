import calendar
from datetime import date, datetime
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func
from database import db
from models import Categoria, Transacao

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

    # 1. Obter Parâmetros da URL
    dt_ini_param = request.args.get("data_inicio")
    dt_fim_param = request.args.get("data_fim")
    cat_id = request.args.get("categoria_id")
    tipo = request.args.get("tipo")

    # 2. Lógica de Data Padrão (Mês Atual)
    hoje = date.today()
    
    # Se dt_ini_param for None, significa que é o primeiro carregamento da página.
    # Se for uma string vazia "", significa que o usuário limpou o filtro intencionalmente.
    if dt_ini_param is None:
        dt_ini = date(hoje.year, hoje.month, 1).isoformat()
    else:
        dt_ini = dt_ini_param

    if dt_fim_param is None:
        # Pega o último dia do mês atual
        _, ultimo_dia = calendar.monthrange(hoje.year, hoje.month)
        dt_fim = date(hoje.year, hoje.month, ultimo_dia).isoformat()
    else:
        dt_fim = dt_fim_param

    # 3. Aplicação dos Filtros
    if dt_ini: 
        query = query.filter(func.date(Transacao.data_transacao) >= dt_ini)
    
    if dt_fim: 
        query = query.filter(func.date(Transacao.data_transacao) <= dt_fim)
    
    if cat_id and cat_id.isdigit(): 
        query = query.filter(Transacao.categoria_id == int(cat_id))
    
    if tipo == 'receita': 
        query = query.filter(Categoria.tipo == 'entrada')
    elif tipo == 'despesa': 
        query = query.filter(Categoria.tipo == 'saída')

    res = query.order_by(Transacao.data_transacao.desc()).all()
    lista = [dict(r._asdict(), tipo="receita" if r.tipo_bd == "entrada" else "despesa", conta_nome="Padrão") for r in res]

    # Retornamos as datas para o template preencher os inputs
    return render_template("extrato.html", transacoes=lista, categorias=cats, 
                           data_inicio=dt_ini, data_fim=dt_fim, 
                           filtro_tipo=tipo, filtro_cat=cat_id)