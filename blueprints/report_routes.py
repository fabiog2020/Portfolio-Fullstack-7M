import calendar
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func, case
from database import db
from models import Categoria, Transacao, Investimento

reports_bp = Blueprint('reports', __name__)

def get_last_12_months_data(user_id):
    """
    Retorna dados agrupados por mês para os últimos 12 meses.
    Responsabilidade: Lógica de Negócio (Cálculo de histórico).
    """
    hoje = date.today()
    data_inicio = hoje - timedelta(days=365)
    
    # Busca transações do último ano
    query = db.session.query(
        func.strftime('%Y-%m', Transacao.data_transacao).label('mes'),
        func.sum(case((Categoria.tipo == 'entrada', Transacao.valor), else_=0)).label('total_receita'),
        func.sum(case((Categoria.tipo == 'saída', func.abs(Transacao.valor)), else_=0)).label('total_despesa')
    ).join(Categoria).filter(
        Transacao.user_id == user_id,
        Transacao.data_transacao >= data_inicio
    ).group_by('mes').order_by('mes').all()

    # Cria estrutura de dicionário para garantir que meses vazios apareçam zerados
    resultado = {}
    temp_date = data_inicio.replace(day=1)
    while temp_date <= hoje:
        key = temp_date.strftime('%Y-%m')
        resultado[key] = {'receita': 0.0, 'despesa': 0.0, 'saldo': 0.0}
        days_in_month = calendar.monthrange(temp_date.year, temp_date.month)[1]
        temp_date += timedelta(days=days_in_month)

    # Preenche com dados reais e calcula evolução patrimonial
    patrimonio_acumulado = 0 # Em um app real, buscaríamos o saldo inicial do usuário
    evolucao_patrimonial = {}

    for row in query:
        mes = row.mes
        rec = row.total_receita or 0.0
        desp = row.total_despesa or 0.0
        saldo = rec - desp
        
        if mes in resultado:
            resultado[mes]['receita'] = rec
            resultado[mes]['despesa'] = desp
            resultado[mes]['saldo'] = saldo
        
        # Lógica de negócio: Patrimônio é o acúmulo dos saldos
        patrimonio_acumulado += saldo
        evolucao_patrimonial[mes] = patrimonio_acumulado

    return resultado, evolucao_patrimonial

def get_investments_allocation(user_id):
    """Calcula alocação de ativos."""
    query = db.session.query(
        Investimento.tipo,
        func.sum(Investimento.quantidade * Investimento.preco_compra)
    ).filter(Investimento.user_id == user_id).group_by(Investimento.tipo).all()
    
    return {row[0]: row[1] for row in query}

@reports_bp.route("/relatorios", methods=["GET"])
@login_required
def relatorios():
    # 1. Busca dados processados (Regra de Negócio no Python)
    historico_mensal, evolucao_patrimonial = get_last_12_months_data(current_user.id)
    
    # Prepara listas simples para o template (View Model)
    labels_meses = sorted(historico_mensal.keys())
    data_receitas = [historico_mensal[m]['receita'] for m in labels_meses]
    data_despesas = [historico_mensal[m]['despesa'] for m in labels_meses]
    data_saldos = [historico_mensal[m]['saldo'] for m in labels_meses]
    data_patrimonio = [evolucao_patrimonial.get(m, 0) for m in labels_meses]

    # 2. Dados do Mês Atual (Pizza de Despesas)
    hoje = datetime.now()
    despesas_categoria_query = db.session.query(Categoria.nome, func.sum(func.abs(Transacao.valor)))\
        .join(Categoria)\
        .filter(Transacao.user_id == current_user.id, Categoria.tipo == 'saída',
                extract("month", Transacao.data_transacao) == hoje.month,
                extract("year", Transacao.data_transacao) == hoje.year)\
        .group_by(Categoria.nome).all()
    despesas_por_categoria = {nome: val for nome, val in despesas_categoria_query}

    # 3. Investimentos
    alocacao_ativos = get_investments_allocation(current_user.id)

    # 4. Mock de Metas (Futuramente virá do Banco)
    metas_mock = [
        {"nome": "Reserva de Emergência", "atual": 5000, "alvo": 15000, "cor": "bg-blue-500"},
        {"nome": "Viagem Férias", "atual": 2000, "alvo": 8000, "cor": "bg-green-500"},
        {"nome": "Carro Novo", "atual": 15000, "alvo": 60000, "cor": "bg-purple-500"},
    ]

    return render_template("relatorios.html",
        labels=labels_meses,
        data_receitas=data_receitas,
        data_despesas=data_despesas,
        data_saldos=data_saldos,
        data_patrimonio=data_patrimonio,
        despesas_por_categoria=despesas_por_categoria,
        alocacao_ativos=alocacao_ativos,
        metas=metas_mock
    )

@reports_bp.route("/extrato", methods=["GET"])
@login_required
def extrato():
    # Mantém a lógica correta do extrato que fizemos anteriormente
    cats = Categoria.query.filter_by(user_id=current_user.id).filter(Categoria.tipo.in_(["entrada", "saída"])).all()
    query = db.session.query(
        Transacao.id, Transacao.data_transacao.label("data"), Transacao.descricao,
        func.abs(Transacao.valor).label("valor"), Categoria.nome.label("categoria_nome"),
        Categoria.tipo.label("tipo_bd")
    ).join(Categoria).filter(Transacao.user_id == current_user.id)

    dt_ini_param = request.args.get("data_inicio")
    dt_fim_param = request.args.get("data_fim")
    cat_id = request.args.get("categoria_id")
    tipo = request.args.get("tipo")

    hoje = date.today()
    # Lógica de filtro padrão (Mês atual)
    if dt_ini_param is None:
        dt_ini = date(hoje.year, hoje.month, 1).isoformat()
    else:
        dt_ini = dt_ini_param

    if dt_fim_param is None:
        _, ultimo_dia = calendar.monthrange(hoje.year, hoje.month)
        dt_fim = date(hoje.year, hoje.month, ultimo_dia).isoformat()
    else:
        dt_fim = dt_fim_param

    if dt_ini: query = query.filter(func.date(Transacao.data_transacao) >= dt_ini)
    if dt_fim: query = query.filter(func.date(Transacao.data_transacao) <= dt_fim)
    if cat_id and cat_id.isdigit(): query = query.filter(Transacao.categoria_id == int(cat_id))
    if tipo == 'receita': query = query.filter(Categoria.tipo == 'entrada')
    elif tipo == 'despesa': query = query.filter(Categoria.tipo == 'saída')

    res = query.order_by(Transacao.data_transacao.desc()).all()
    lista = [dict(r._asdict(), tipo="receita" if r.tipo_bd == "entrada" else "despesa", conta_nome="Padrão") for r in res]

    return render_template("extrato.html", transacoes=lista, categorias=cats, 
                           data_inicio=dt_ini, data_fim=dt_fim, 
                           filtro_tipo=tipo, filtro_cat=cat_id)