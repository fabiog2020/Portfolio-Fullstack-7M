# blueprints/investment_routes.py

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Investimento, Categoria
from forms.investimento_form import InvestimentoForm

# Importação dos Serviços de Cálculo
from services.market_service import get_current_price
from services.fixed_income_service import calcular_renda_fixa

investments_bp = Blueprint('investments', __name__)

@investments_bp.route("/", methods=["GET", "POST"])
@login_required
def investimentos():
    form = InvestimentoForm()
    
    # 1. Busca investimentos ATIVOS do usuário
    investimentos_ativos = Investimento.query.filter_by(
        user_id=current_user.id, 
        status="Ativo"
    ).all()
    
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    # 2. Motor de Cálculo e Processamento de Dados
    total_investido = 0
    total_atual = 0
    dados_investimentos = []
    
    for inv in investimentos_ativos:
        # Valores iniciais baseados na compra
        valor_comprado_posicao = inv.preco_compra * inv.quantidade
        valor_atual_posicao = valor_comprado_posicao # Fallback (valor padrão caso falhe o cálculo)
        preco_unitario_atual = inv.preco_compra

        # --- LÓGICA DE DECISÃO EXPLÍCITA ---
        
        # CASO 1: RENDA FIXA (CDB, Tesouro, LCI)
        if inv.classe == 'Fixa':
            # Usa o motor matemático (BCB/Juros)
            valor_calculado = calcular_renda_fixa(inv)
            
            if valor_calculado > 0:
                valor_atual_posicao = valor_calculado
                # Calcula o "preço unitário virtual" para exibir na tabela
                if inv.quantidade > 0:
                    preco_unitario_atual = valor_atual_posicao / inv.quantidade

        # CASO 2: RENDA VARIÁVEL (Ações, FIIs, Crypto)
        elif inv.classe == 'Variavel':
            # Usa o motor de mercado (Yahoo Finance)
            if inv.ticker:
                cotacao = get_current_price(inv.ticker)
                if cotacao > 0:
                    preco_unitario_atual = cotacao
                    valor_atual_posicao = cotacao * inv.quantidade
        
        # -----------------------------------

        # Cálculo de Rentabilidade
        rentabilidade = 0
        lucro_reais = valor_atual_posicao - valor_comprado_posicao
        
        if valor_comprado_posicao > 0:
            rentabilidade = (lucro_reais / valor_comprado_posicao) * 100

        # Atualiza Totais
        total_investido += valor_comprado_posicao
        total_atual += valor_atual_posicao
        
        # Prepara objeto para o Front-end
        dados_investimentos.append({
            "obj": inv,
            "preco_atual": preco_unitario_atual,
            "valor_total_atual": valor_atual_posicao,
            "rentabilidade": rentabilidade,
            "lucro_reais": lucro_reais
        })

    # 3. Processamento do Formulário (Salvar Novo)
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                # Sanitização de Dados
                classe_selecionada = form.classe.data
                
                # Prepara dados específicos baseados na classe
                ticker_final = None
                indice_final = None
                taxa_final = None
                vencimento_final = None

                if classe_selecionada == 'Variavel':
                    if form.ticker.data:
                        ticker_final = form.ticker.data.strip().upper()
                
                elif classe_selecionada == 'Fixa':
                    indice_final = form.indice.data
                    taxa_final = form.taxa_contratada.data
                    vencimento_final = form.data_vencimento.data

                # Criação do Objeto
                novo = Investimento(
                    user_id=current_user.id,
                    classe=classe_selecionada, # Salva a decisão explícita
                    tipo=form.tipo.data,
                    nome=form.nome.data,
                    
                    # Dados Específicos limpos
                    ticker=ticker_final,
                    indice=indice_final,
                    taxa_contratada=taxa_final,
                    data_vencimento=vencimento_final,
                    
                    # Dados Financeiros Comuns
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
            flash("Erro no formulário. Verifique os campos.", "danger")

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
        
        # Cálculos de Saída
        valor_venda_total = preco_venda_unitario * inv.quantidade
        valor_compra_total = inv.preco_compra * inv.quantidade
        lucro = valor_venda_total - valor_compra_total
        
        # Atualiza Banco
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
    form = InvestimentoForm() # Evita erro no template base
    
    # Filtros
    ano = request.args.get('ano')
    nome = request.args.get('nome')
    
    query = Investimento.query.filter_by(user_id=current_user.id, status="Vendido")
    
    if ano:
        query = query.filter(db.extract('year', Investimento.data_venda) == int(ano))
    if nome:
        query = query.filter(Investimento.nome.ilike(f"%{nome}%"))
        
    vendidos = query.order_by(Investimento.data_venda.desc()).all()
    
    # Renderiza com totais zerados (modo histórico)
    return render_template(
        "investimentos.html", 
        dados=[], 
        historico=vendidos, 
        form=form, 
        total_investido=0, 
        total_atual=0, 
        modo="historico"
    )

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
            # Atualiza campos básicos
            inv.classe = form.classe.data
            inv.tipo = form.tipo.data
            inv.nome = form.nome.data
            
            # Atualiza dados baseados na classe escolhida
            if inv.classe == 'Variavel':
                inv.ticker = form.ticker.data.strip().upper() if form.ticker.data else None
                # Limpa dados de RF
                inv.indice = None
                inv.taxa_contratada = None
                inv.data_vencimento = None
                
            elif inv.classe == 'Fixa':
                inv.indice = form.indice.data
                inv.taxa_contratada = form.taxa_contratada.data
                inv.data_vencimento = form.data_vencimento.data
                # Limpa Ticker
                inv.ticker = None

            # Atualiza Financeiro
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

    # Preenche datas no formulário (GET)
    if request.method == "GET":
        if inv.data_compra: 
            form.data_compra.data = inv.data_compra.date()
        if inv.data_vencimento: 
            form.data_vencimento.data = inv.data_vencimento.date()

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