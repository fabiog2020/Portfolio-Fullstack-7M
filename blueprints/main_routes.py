# blueprints/main_routes.py
from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from database import db
from models.models_finance import Transacao, Categoria
from services.ai_service import AIService 

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # ---------------------------------------------------------
    # 1. EXECUTA A INTELIGÊNCIA ARTIFICIAL (ROBÔ)
    # ---------------------------------------------------------
    try:
        AIService.executar_analise_geral(current_user)
    except Exception as e:
        print(f"Erro ao executar IA: {e}")

    # ---------------------------------------------------------
    # 2. LÓGICA PADRÃO DO DASHBOARD
    # ---------------------------------------------------------
    
    hoje = datetime.now()
    mes = hoje.month
    ano = hoje.year

    # --- TOTAIS (CARDS) ---

    # 1. Receitas
    receitas = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
        Transacao.user_id == current_user.id,
        Categoria.tipo == 'entrada',
        extract('month', Transacao.data_transacao) == mes,
        extract('year', Transacao.data_transacao) == ano
    ).scalar() or 0.0

    # 2. Despesas
    despesas_raw = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
        Transacao.user_id == current_user.id,
        Categoria.tipo == 'saída',
        extract('month', Transacao.data_transacao) == mes,
        extract('year', Transacao.data_transacao) == ano
    ).scalar() or 0.0

    # 3. Investimentos
    investido_raw = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
        Transacao.user_id == current_user.id,
        Categoria.tipo == 'investimento',
        extract('month', Transacao.data_transacao) == mes,
        extract('year', Transacao.data_transacao) == ano
    ).scalar() or 0.0

    # Saldo Real
    saldo = receitas + despesas_raw + investido_raw

    # Valores visuais (positivos para exibição)
    despesas_visual = abs(despesas_raw)
    investido_visual = abs(investido_raw)

    # --- DADOS COMPLEMENTARES ---
    
    # Últimas 5 transações
    ultimas_transacoes = Transacao.query.filter_by(user_id=current_user.id)\
        .order_by(Transacao.data_transacao.desc())\
        .limit(5).all()

    # --- DADOS PARA GRÁFICOS ---

    # A) Gráfico de DESPESAS
    qry_despesas = db.session.query(Categoria.nome, func.sum(Transacao.valor))\
        .join(Categoria)\
        .filter(
            Transacao.user_id == current_user.id,
            Categoria.tipo == 'saída', 
            extract('month', Transacao.data_transacao) == mes,
            extract('year', Transacao.data_transacao) == ano
        )\
        .group_by(Categoria.nome).all()

    labels_despesas = [c[0] for c in qry_despesas]
    valores_despesas = [abs(c[1]) for c in qry_despesas] # Positivo

    # B) Gráfico de RECEITAS (NOVO BLOCO ADICIONADO)
    qry_receitas = db.session.query(Categoria.nome, func.sum(Transacao.valor))\
        .join(Categoria)\
        .filter(
            Transacao.user_id == current_user.id,
            Categoria.tipo == 'entrada', 
            extract('month', Transacao.data_transacao) == mes,
            extract('year', Transacao.data_transacao) == ano
        )\
        .group_by(Categoria.nome).all()

    labels_receitas = [c[0] for c in qry_receitas]
    valores_receitas = [c[1] for c in qry_receitas]

    return render_template('dashboard.html',
                           nome=current_user.nome,
                           entradas_realizadas=receitas,
                           saidas_realizadas=despesas_visual,
                           saldo_realizado=saldo,
                           saldo_projetado=saldo,
                           transacoes_recentes=ultimas_transacoes,
                           
                           # Gráfico de Despesas
                           dados_despesas=dict(zip(labels_despesas, valores_despesas)),
                           
                           # Gráfico de Receitas (AGORA CORRIGIDO)
                           dados_receitas=dict(zip(labels_receitas, valores_receitas)),
                           
                           mes_atual=mes,
                           ano_atual=ano)