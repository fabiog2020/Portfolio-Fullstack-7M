# blueprints/investment_routes.py

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Investimento, Categoria
from forms.investimento_form import InvestimentoForm
from services.market_service import get_current_price

investments_bp = Blueprint('investments', __name__)

@investments_bp.route("/", methods=["GET", "POST"])
@login_required
def investimentos():
    form = InvestimentoForm()
    
    # Busca investimentos ATIVOS
    investimentos_ativos = Investimento.query.filter_by(
        user_id=current_user.id, 
        status="Ativo"
    ).all()
    
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    # Processamento de Dados (Cálculos)
    total_investido = 0
    total_atual = 0
    dados_investimentos = []
    
    for inv in investimentos_ativos:
        preco_atual = inv.preco_compra # Valor padrão (se falhar a API)
        
        # Tenta pegar preço atualizado (se tiver ticker)
        if inv.ticker:
            cotacao = get_current_price(inv.ticker)
            if cotacao > 0:
                preco_atual = cotacao
        
        valor_atual_posicao = preco_atual * inv.quantidade
        valor_comprado_posicao = inv.preco_compra * inv.quantidade
        
        rentabilidade = 0
        if valor_comprado_posicao > 0:
            rentabilidade = ((valor_atual_posicao - valor_comprado_posicao) / valor_comprado_posicao) * 100

        total_investido += valor_comprado_posicao
        total_atual += valor_atual_posicao
        
        dados_investimentos.append({
            "obj": inv,
            "preco_atual": preco_atual,
            "valor_total_atual": valor_atual_posicao,
            "rentabilidade": rentabilidade,
            "lucro_reais": valor_atual_posicao - valor_comprado_posicao
        })

    # Lógica de Salvar Novo Investimento
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                # Extrai ticker (ex: "PETR4 - Petrobras" vira "PETR4")
                ticker_raw = form.nome.data.split(" ")[0].upper()
                
                novo = Investimento(
                    user_id=current_user.id,
                    tipo=form.tipo.data,
                    nome=form.nome.data,
                    ticker=ticker_raw,
                    quantidade=form.quantidade.data,
                    preco_compra=form.preco_compra.data,
                    data_compra=datetime.combine(form.data_compra.data, datetime.min.time()),
                    status="Ativo"
                )
                db.session.add(novo)
                db.session.commit()
                flash("Investimento adicionado à carteira!", "success")
                return redirect(url_for("investments.investimentos"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar: {e}", "danger")
        else:
            flash("Verifique os dados do formulário.", "danger")

    return render_template(
        "investimentos.html", 
        dados=dados_investimentos, 
        total_investido=total_investido,
        total_atual=total_atual,
        categorias_investimento=cats, 
        form=form,
        modo="carteira"
    )

@investments_bp.route("/vender/<int:id>", methods=["POST"])
@login_required
def vender_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not inv:
        flash("Investimento não encontrado.", "danger")
        return redirect(url_for("investments.investimentos"))
    
    try:
        preco_venda = float(request.form.get("preco_venda"))
        data_venda = datetime.strptime(request.form.get("data_venda"), "%Y-%m-%d")
        
        # Cálculos de Saída
        valor_venda_total = preco_venda * inv.quantidade
        valor_compra_total = inv.preco_compra * inv.quantidade
        lucro = valor_venda_total - valor_compra_total
        
        # Atualiza Banco
        inv.status = "Vendido"
        inv.preco_venda = preco_venda
        inv.data_venda = data_venda
        inv.lucro_final = lucro
        
        db.session.commit()
        flash(f"Venda registrada! Resultado: R$ {lucro:.2f}", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro na venda: {e}", "danger")
        
    return redirect(url_for("investments.investimentos"))

@investments_bp.route("/historico", methods=["GET"])
@login_required
def historico_investimentos():
    form = InvestimentoForm() # Necessário para o template base não quebrar
    
    # Filtros
    ano = request.args.get('ano')
    nome = request.args.get('nome')
    
    query = Investimento.query.filter_by(user_id=current_user.id, status="Vendido")
    
    if ano:
        # Filtra pelo ano da venda
        query = query.filter(db.extract('year', Investimento.data_venda) == int(ano))
    
    if nome:
        query = query.filter(Investimento.nome.ilike(f"%{nome}%"))
        
    vendidos = query.order_by(Investimento.data_venda.desc()).all()
    
    return render_template(
        "investimentos.html", 
        dados=[], 
        historico=vendidos, 
        form=form,
        total_investido=0, 
        total_atual=0,
        modo="historico"
    )

# Rota de Editar e Excluir permanecem iguais (já corrigidas anteriormente)
@investments_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not inv:
        flash("Investimento não encontrado.", "danger")
        return redirect(url_for("investments.investimentos"))

    form = InvestimentoForm(obj=inv)
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    if request.method == "POST" and form.validate_on_submit():
        try:
            inv.tipo = form.tipo.data
            inv.nome = form.nome.data
            inv.ticker = form.nome.data.split(" ")[0].upper()
            inv.quantidade = form.quantidade.data
            inv.preco_compra = form.preco_compra.data
            if form.data_compra.data:
                inv.data_compra = datetime.combine(form.data_compra.data, datetime.min.time())
            
            db.session.commit()
            flash("Atualizado com sucesso!", "success")
            return redirect(url_for("investments.investimentos"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")

    if request.method == "GET" and inv.data_compra:
        form.data_compra.data = inv.data_compra.date()

    return render_template("editar_investimento.html", investimento=inv, categorias_investimento=cats, form=form)

@investments_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if inv:
        db.session.delete(inv)
        db.session.commit()
        flash("Excluído permanentemente.", "success")
    return redirect(url_for("investments.investimentos"))