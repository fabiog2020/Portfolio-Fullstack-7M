# blueprints/investment_routes.py

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Investimento, Categoria
from forms.investimento_form import InvestimentoForm

from services.market_service import get_current_price
from services.fixed_income_service import calcular_renda_fixa

investments_bp = Blueprint('investments', __name__)

# --- FUNÇÃO AUXILIAR DE INTELIGÊNCIA ---
def determinar_classe_automaticamente(categoria_nome):
    """
    Deduz a classe do ativo baseado no nome da categoria.
    Retorna: 'Fixa' ou 'Variavel'
    """
    if not categoria_nome:
        return 'Variavel'
    
    nome_upper = categoria_nome.upper()
    
    # Palavras-chave que indicam Renda Fixa
    termos_fixa = ['FIXA', 'TESOURO', 'CDB', 'LCI', 'LCA', 'POUPANÇA', 'CONSORCIO', 'CONSÓRCIO']
    
    for termo in termos_fixa:
        if termo in nome_upper:
            return 'Fixa'
            
    return 'Variavel' # Padrão para Ações, FIIs, Crypto, etc.

@investments_bp.route("/", methods=["GET", "POST"])
@login_required
def investimentos():
    form = InvestimentoForm()
    
    # Popula o Select de Categorias no Form (Necessário para o WTForms)
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()
    form.categoria_id.choices = [(c.id, c.nome) for c in cats]

    # 1. Busca investimentos
    investimentos_ativos = Investimento.query.filter_by(user_id=current_user.id, status="Ativo").all()
    
    # 2. Cálculos
    total_investido = 0
    total_atual = 0
    dados_investimentos = []
    
    for inv in investimentos_ativos:
        valor_comprado_posicao = inv.preco_compra * inv.quantidade
        valor_atual_posicao = valor_comprado_posicao
        preco_unitario_atual = inv.preco_compra

        # Lógica de Cálculo baseada na classe salva no banco
        if inv.classe == 'Fixa':
            valor_calculado = calcular_renda_fixa(inv)
            if valor_calculado > 0:
                valor_atual_posicao = valor_calculado
                if inv.quantidade > 0:
                    preco_unitario_atual = valor_atual_posicao / inv.quantidade

        elif inv.classe == 'Variavel':
            if inv.ticker:
                cotacao = get_current_price(inv.ticker)
                if cotacao > 0:
                    preco_unitario_atual = cotacao
                    valor_atual_posicao = cotacao * inv.quantidade
        
        rentabilidade = 0
        lucro_reais = valor_atual_posicao - valor_comprado_posicao
        if valor_comprado_posicao > 0:
            rentabilidade = (lucro_reais / valor_comprado_posicao) * 100

        total_investido += valor_comprado_posicao
        total_atual += valor_atual_posicao
        
        dados_investimentos.append({
            "obj": inv,
            "preco_atual": preco_unitario_atual,
            "valor_total_atual": valor_atual_posicao,
            "rentabilidade": rentabilidade,
            "lucro_reais": lucro_reais
        })

    # 3. Salvar (POST)
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                # Busca a categoria real para decidir a classe
                cat_selecionada = Categoria.query.get(form.categoria_id.data)
                classe_auto = determinar_classe_automaticamente(cat_selecionada.nome)
                
                # Prepara dados
                ticker_final = None
                indice_final = None
                taxa_final = None
                vencimento_final = None

                if classe_auto == 'Variavel':
                    if form.ticker.data:
                        ticker_final = form.ticker.data.strip().upper()
                
                elif classe_auto == 'Fixa':
                    indice_final = form.indice.data
                    taxa_final = form.taxa_contratada.data
                    vencimento_final = form.data_vencimento.data

                novo = Investimento(
                    user_id=current_user.id,
                    # Não vem mais do form, vem da lógica automática
                    classe=classe_auto, 
                    # categoria_id não salva direto no modelo Investimento (se não tiver relação direta), 
                    # mas usaremos o nome/tipo para salvar ou criar relação se necessário.
                    # NOTA: Seu modelo Investimento não tem categoria_id ligado, mas vamos salvar
                    # o "tipo" como string visual por enquanto (como estava antes).
                    tipo=cat_selecionada.nome, 
                    nome=form.nome.data,
                    ticker=ticker_final,
                    indice=indice_final,
                    taxa_contratada=taxa_final,
                    data_vencimento=vencimento_final,
                    quantidade=form.quantidade.data,
                    preco_compra=form.preco_compra.data,
                    data_compra=datetime.combine(form.data_compra.data, datetime.min.time()),
                    status="Ativo"
                )
                
                db.session.add(novo)
                db.session.commit()
                flash(f"Investimento registrado como {classe_auto}!", "success")
                return redirect(url_for("investments.investimentos"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar: {e}", "danger")
        else:
            flash("Erro no formulário.", "danger")

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
        preco_venda_unitario = float(request.form.get("preco_venda"))
        data_venda_str = request.form.get("data_venda")
        data_venda = datetime.strptime(data_venda_str, "%Y-%m-%d")
        
        valor_venda_total = preco_venda_unitario * inv.quantidade
        valor_compra_total = inv.preco_compra * inv.quantidade
        lucro = valor_venda_total - valor_compra_total
        
        inv.status = "Vendido"
        inv.preco_venda = preco_venda_unitario
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
    form = InvestimentoForm()
    # Popula choices vazio para evitar erro de validação visual
    form.categoria_id.choices = [] 
    
    ano = request.args.get('ano')
    nome = request.args.get('nome')
    query = Investimento.query.filter_by(user_id=current_user.id, status="Vendido")
    if ano:
        query = query.filter(db.extract('year', Investimento.data_venda) == int(ano))
    if nome:
        query = query.filter(Investimento.nome.ilike(f"%{nome}%"))
    vendidos = query.order_by(Investimento.data_venda.desc()).all()
    
    return render_template("investimentos.html", dados=[], historico=vendidos, form=form, total_investido=0, total_atual=0, modo="historico")

@investments_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not inv:
        flash("Investimento não encontrado.", "danger")
        return redirect(url_for("investments.investimentos"))

    form = InvestimentoForm(obj=inv)
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()
    form.categoria_id.choices = [(c.id, c.nome) for c in cats]

    # Tenta pré-selecionar a categoria baseada no nome salvo em 'tipo'
    # (Isso é uma adaptação pois não temos categoria_id no model Investimento ainda)
    cat_atual = Categoria.query.filter_by(user_id=current_user.id, nome=inv.tipo).first()
    if cat_atual and request.method == "GET":
        form.categoria_id.data = cat_atual.id

    if request.method == "POST" and form.validate_on_submit():
        try:
            # Recalcula a classe caso o usuário tenha mudado a categoria
            cat_selecionada = Categoria.query.get(form.categoria_id.data)
            inv.classe = determinar_classe_automaticamente(cat_selecionada.nome)
            inv.tipo = cat_selecionada.nome # Atualiza o texto visual
            inv.nome = form.nome.data
            
            if inv.classe == 'Variavel':
                inv.ticker = form.ticker.data.strip().upper() if form.ticker.data else None
                inv.indice = None
                inv.taxa_contratada = None
                inv.data_vencimento = None
                
            elif inv.classe == 'Fixa':
                inv.indice = form.indice.data
                inv.taxa_contratada = form.taxa_contratada.data
                inv.data_vencimento = form.data_vencimento.data
                inv.ticker = None

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

    if request.method == "GET":
        if inv.data_compra: form.data_compra.data = inv.data_compra.date()
        if inv.data_vencimento: form.data_vencimento.data = inv.data_vencimento.date()

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