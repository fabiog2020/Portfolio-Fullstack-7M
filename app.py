# app.py

from datetime import date, datetime
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import extract, func

# ===========================
# 1. IMPORTAÇÃO DA FÁBRICA
# ===========================
from factory import create_app
from database import db, login_manager

# Importações de Models, Forms e Services
from models import User
from models_finance import Cartao, Categoria, Investimento, Parcela, Transacao
from forms.auth_forms import LoginForm, RegisterForm
from forms.categoria_form import CategoriaForm
from forms.investimento_form import InvestimentoForm
from forms.transacao_form import TransacaoForm
from services.parcelas_service import criar_parcelas_a_partir_formulario, pagar_parcela_service
from services.transactions_service import criar_transacao_a_partir_formulario

# ===========================
# 2. CRIAÇÃO DA APP (Usando a Fábrica)
# ===========================
# Aqui a mágica acontece: o app vem pronto, já com DB e CLI configurados no factory.py
app = create_app()

# ===========================
# CONFIGURAÇÃO DE LOGIN
# ===========================
@login_manager.user_loader
def load_user(user_id):
    # Usando a sintaxe moderna do SQLAlchemy 2.0
    return db.session.get(User, int(user_id))

# ==================================================
# FUNÇÃO UTILITÁRIA (Regra de Negócio de Cadastro)
# ==================================================
def inserir_categorias_padrao(user_id):
    """
    Insere categorias padrão para um NOVO usuário que acabou de se registrar.
    Isso é diferente do 'seed-db', que reseta o banco todo via terminal.
    """
    categorias = [
        {"nome": "Salário", "tipo": "entrada", "icone": "fa-solid fa-money-bill-wave", "cor": "#28a745"},
        {"nome": "Renda Extra", "tipo": "entrada", "icone": "fa-solid fa-sack-dollar", "cor": "#17a2b8"},
        {"nome": "Moradia (Aluguel/Parcela)", "tipo": "saída", "icone": "fa-solid fa-house", "cor": "#dc3545"},
        {"nome": "Alimentação", "tipo": "saída", "icone": "fa-solid fa-burger", "cor": "#ffc107"},
        {"nome": "Transporte (Combustível)", "tipo": "saída", "icone": "fa-solid fa-car-side", "cor": "#6f42c1"},
        {"nome": "Saúde (Farmácia)", "tipo": "saída", "icone": "fa-solid fa-briefcase-medical", "cor": "#20c997"},
        {"nome": "Lazer", "tipo": "saída", "icone": "fa-solid fa-champagne-glasses", "cor": "#fd7e14"},
        {"nome": "Educação", "tipo": "saída", "icone": "fa-solid fa-graduation-cap", "cor": "#007bff"},
        {"nome": "Renda Variável (Ações)", "tipo": "investimento", "icone": "fa-solid fa-chart-line", "cor": "#007bff"},
    ]

    for c in categorias:
        nova_categoria = Categoria(
            user_id=user_id,
            nome=c["nome"],
            tipo=c["tipo"],
            icone=c["icone"],
            cor=c["cor"],
        )
        db.session.add(nova_categoria)
    db.session.commit()

# ===========================
# ROTAS DE LOGIN E CADASTRO
# ===========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        senha = form.senha.data

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and user.check_password(senha):
            login_user(user)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        nome = form.nome.data
        email = form.email.data
        senha = form.senha.data

        user_existente = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user_existente:
            flash("E-mail já cadastrado.", "warning")
            return render_template("register.html", form=form)

        novo = User(nome=nome, email=email)
        novo.set_password(senha)
        db.session.add(novo)
        db.session.commit()

        # Chama a função definida acima
        inserir_categorias_padrao(novo.id)

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout efetuado com sucesso!", "info")
    return redirect(url_for("login"))


# ===========================
# DASHBOARD
# ===========================
@app.route("/")
@login_required
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    mes_param = request.args.get("mes", type=int)
    ano_param = request.args.get("ano", type=int)
    hoje = datetime.now()
    mes_atual = mes_param if mes_param and 1 <= mes_param <= 12 else hoje.month
    ano_atual = ano_param if ano_param else hoje.year

    entradas_realizadas = (
        db.session.query(func.sum(Transacao.valor))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            extract("month", Transacao.data_transacao) == mes_atual,
            extract("year", Transacao.data_transacao) == ano_atual,
            Categoria.tipo == "entrada",
        )
        .scalar()
        or 0.0
    )

    saidas_realizadas = (
        db.session.query(func.sum(func.abs(Transacao.valor)))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            extract("month", Transacao.data_transacao) == mes_atual,
            extract("year", Transacao.data_transacao) == ano_atual,
            Categoria.tipo == "saída",
        )
        .scalar()
        or 0.0
    )

    despesas_previstas_parcelas = (
        db.session.query(func.sum(Parcela.valor))
        .join(Categoria)
        .filter(
            Parcela.user_id == current_user.id,
            extract("month", Parcela.data_vencimento) == mes_atual,
            extract("year", Parcela.data_vencimento) == ano_atual,
            Categoria.tipo == "saída",
           Parcela.pago.is_(False),
        )
        .scalar()
        or 0.0
    )

    saldo_realizado = entradas_realizadas - saidas_realizadas
    saldo_projetado = saldo_realizado - despesas_previstas_parcelas

    transacoes_recentes = (
        Transacao.query.filter(Transacao.user_id == current_user.id)
        .order_by(Transacao.data_transacao.desc())
        .limit(10)
        .all()
    )

    query_despesas = (
        db.session.query(Categoria.nome, func.sum(Transacao.valor).label("total"))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            extract("month", Transacao.data_transacao) == mes_atual,
            extract("year", Transacao.data_transacao) == ano_atual,
            Categoria.tipo == "saída",
        )
        .group_by(Categoria.nome)
        .order_by(func.sum(Transacao.valor).desc())
        .all()
    )
    dados_despesas = {nome: float(total) for nome, total in query_despesas if total is not None}

    query_receitas = (
        db.session.query(Categoria.nome, func.sum(Transacao.valor).label("total"))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            extract("month", Transacao.data_transacao) == mes_atual,
            extract("year", Transacao.data_transacao) == ano_atual,
            Categoria.tipo == "entrada",
        )
        .group_by(Categoria.nome)
        .order_by(func.sum(Transacao.valor).desc())
        .all()
    )
    dados_receitas = {nome: float(total) for nome, total in query_receitas if total is not None}

    return render_template(
        "dashboard.html",
        nome=current_user.nome,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        entradas_realizadas=entradas_realizadas,
        saidas_realizadas=saidas_realizadas,
        saldo_realizado=saldo_realizado,
        despesas_previstas_parcelas=despesas_previstas_parcelas,
        saldo_projetado=saldo_projetado,
        transacoes_recentes=transacoes_recentes,
        dados_despesas=dados_despesas,
        dados_receitas=dados_receitas,
    )


# ===========================
# ROTAS DE TRANSAÇÕES
# ===========================
@app.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    form = TransacaoForm()
    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .order_by(Categoria.nome.asc())
        .all()
    )
    categorias_transacao = [c for c in categorias if c.tipo in ["entrada", "saída"]]
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "adicionar.html",
        form=form,
        categorias=categorias_transacao,
        cartoes=cartoes,
    )


@app.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    form = TransacaoForm()
    if not form.validate_on_submit():
        for field_name, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{field_name}': {error}", "danger")
        return redirect(url_for("formulario_adicionar_transacao"))

    sucesso = criar_transacao_a_partir_formulario(form)
    if not sucesso:
        return redirect(url_for("formulario_adicionar_transacao"))

    return redirect(url_for("dashboard"))


@app.route("/transacoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        flash("Transação não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("dashboard"))

    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .filter(Categoria.tipo.in_(["entrada", "saída"]))
        .order_by(Categoria.nome.asc())
        .all()
    )

    if request.method == "POST":
        categoria_id = int(request.form.get("categoria_id"))
        descricao = request.form.get("descricao")
        valor_str = request.form.get("valor")
        data_str = request.form.get("data")

        try:
            valor = float(valor_str)
            data_transacao = date.fromisoformat(data_str)
            nova_categoria = Categoria.query.get(categoria_id)

            if not nova_categoria or nova_categoria.user_id != current_user.id:
                flash("Nova categoria inválida.", "danger")
                return render_template("editar.html", transacao=transacao, categorias=categorias)

            valor_final = valor if nova_categoria.tipo == "entrada" else -abs(valor)

            transacao.categoria_id = categoria_id
            transacao.descricao = descricao
            transacao.valor = valor_final
            transacao.data_transacao = data_transacao

            db.session.commit()
            flash("Transação atualizada com sucesso!", "success")
            return redirect(url_for("dashboard"))

        except (ValueError, TypeError) as e:
            flash(f"Erro no formato dos dados: {e}", "danger")

    return render_template("editar.html", transacao=transacao, categorias=categorias)


@app.route("/transacoes/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_transacao(id):
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        flash("Transação não encontrada ou sem permissão.", "danger")
        return redirect(url_for("dashboard"))

    try:
        db.session.delete(transacao)
        db.session.commit()
        flash("Transação excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir a transação: {e}", "danger")

    return redirect(url_for("dashboard"))


# ===============================================
# ROTAS: CATEGORIAS
# ===============================================
@app.route("/categorias", methods=["GET", "POST"])
@login_required
def gerenciar_categorias():
    form = CategoriaForm()

    if form.validate_on_submit():
        nome = form.nome.data.strip()
        tipo = form.tipo.data
        icone = form.icone.data or "fa-solid fa-list"
        cor = form.cor.data or "#007bff"

        if not nome or not tipo:
            flash("Nome e Tipo da categoria são obrigatórios.", "danger")
            return redirect(url_for("gerenciar_categorias"))

        existente = Categoria.query.filter_by(user_id=current_user.id, nome=nome).first()
        if existente:
            flash(f"A categoria '{nome}' já existe.", "warning")
            return redirect(url_for("gerenciar_categorias"))

        nova = Categoria(user_id=current_user.id, nome=nome, tipo=tipo, icone=icone, cor=cor)
        try:
            db.session.add(nova)
            db.session.commit()
            flash(f"Categoria '{nome}' ({tipo}) adicionada com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar a categoria: {e}", "danger")

        return redirect(url_for("gerenciar_categorias"))

    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .order_by(Categoria.nome.asc())
        .all()
    )
    return render_template("categorias.html", categorias=categorias, form=form)


@app.route("/categorias/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()
    if not categoria:
        flash("Categoria não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("gerenciar_categorias"))

    form = CategoriaForm(obj=categoria)

    if request.method == "POST":
        if not form.validate():
            flash("Há erros no formulário.", "danger")
            return render_template("editar_categoria.html", categoria=categoria, form=form)

        novo_nome = form.nome.data.strip()
        novo_tipo = form.tipo.data
        novo_icone = form.icone.data or categoria.icone
        novo_cor = form.cor.data or categoria.cor

        if novo_nome != categoria.nome:
            existente = Categoria.query.filter(
                Categoria.user_id == current_user.id,
                Categoria.nome == novo_nome,
                Categoria.id != id,
            ).first()
            if existente:
                flash(f"Já existe outra categoria chamada '{novo_nome}'.", "warning")
                return render_template("editar_categoria.html", categoria=categoria, form=form)

        categoria.nome = novo_nome
        categoria.tipo = novo_tipo
        categoria.icone = novo_icone
        categoria.cor = novo_cor

        try:
            db.session.commit()
            flash(f"Categoria '{categoria.nome}' atualizada com sucesso!", "success")
            return redirect(url_for("gerenciar_categorias"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar a categoria: {e}", "danger")
            return render_template("editar_categoria.html", categoria=categoria, form=form)

    return render_template("editar_categoria.html", categoria=categoria, form=form)


@app.route("/categorias/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()
    if not categoria:
        flash("Categoria não encontrada.", "danger")
        return redirect(url_for("gerenciar_categorias"))

    transacoes_vinculadas = Transacao.query.filter_by(categoria_id=id).count()
    parcelas_vinculadas = Parcela.query.filter_by(categoria_id=id).count()
    total_vinculos = transacoes_vinculadas + parcelas_vinculadas

    if total_vinculos > 0:
        flash(f"Não é possível excluir a categoria '{categoria.nome}'. Ela possui {total_vinculos} vínculos.", "danger")
        return redirect(url_for("gerenciar_categorias"))

    try:
        db.session.delete(categoria)
        db.session.commit()
        flash(f"Categoria '{categoria.nome}' excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir a categoria: {e}", "danger")

    return redirect(url_for("gerenciar_categorias"))


# ===========================
# ROTAS: CARTÕES
# ===========================
@app.route("/cartoes", methods=["GET"])
@login_required
def cartoes():
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    for cartao in cartoes:
        cartao.parcelas_abertas = Parcela.query.filter_by(cartao_id=cartao.id, pago=False).count()
    return render_template("cartoes.html", cartoes=cartoes)


@app.route("/cartoes/adicionar", methods=["POST"])
@login_required
def adicionar_cartao():
    nome = request.form.get("nome")
    limite = float(request.form.get("limite") or 0)
    venc_str = request.form.get("vencimento_dia")

    try:
        venc = int(venc_str) if venc_str else None
        if venc is not None and (venc < 1 or venc > 31):
            flash("Dia de vencimento inválido.", "danger")
            return redirect(url_for("cartoes"))

        novo = Cartao(nome=nome, limite=limite, vencimento_dia=venc, user_id=current_user.id)
        db.session.add(novo)
        db.session.commit()
        flash(f'Cartão "{nome}" adicionado com sucesso!', "success")
    except ValueError:
        flash("Limite deve ser um número válido.", "danger")

    return redirect(url_for("cartoes"))


@app.route("/cartoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cartao(id):
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()
    if not cartao:
        flash("Cartão não encontrado.", "danger")
        return redirect(url_for("cartoes"))

    if request.method == "POST":
        novo_nome = request.form.get("nome")
        novo_limite_str = request.form.get("limite")
        novo_venc_str = request.form.get("vencimento_dia")

        try:
            novo_limite = float(novo_limite_str or 0)
            novo_venc = int(novo_venc_str) if novo_venc_str else None

            if novo_venc is not None and (novo_venc < 1 or novo_venc > 31):
                flash("Dia de vencimento inválido.", "danger")
                return render_template("editar_cartao.html", cartao=cartao)

            cartao.nome = novo_nome
            cartao.limite = novo_limite
            cartao.vencimento_dia = novo_venc
            db.session.commit()
            flash(f"Cartão '{cartao.nome}' atualizado com sucesso!", "success")
            return redirect(url_for("cartoes"))

        except ValueError:
            flash("Erro: Limite ou dia de vencimento inválido.", "danger")

    return render_template("editar_cartao.html", cartao=cartao)


@app.route("/cartoes/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_cartao(id):
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()
    if not cartao:
        flash("Cartão não encontrado.", "danger")
        return redirect(url_for("cartoes"))

    parcelas_vinculadas = Parcela.query.filter_by(cartao_id=id).count()
    if parcelas_vinculadas > 0:
        flash(f"Não é possível excluir o cartão '{cartao.nome}'. Possui {parcelas_vinculadas} parcelas vinculadas.", "danger")
        return redirect(url_for("cartoes"))

    try:
        db.session.delete(cartao)
        db.session.commit()
        flash(f"Cartão '{cartao.nome}' excluído com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir o cartão: {e}", "danger")

    return redirect(url_for("cartoes"))


# ===========================
# ROTAS: PARCELAS
# ===========================
@app.route("/parcelas", methods=["GET"])
@login_required
def listar_parcelas():
    parcelas = (
        Parcela.query.filter_by(user_id=current_user.id)
        .order_by(Parcela.data_vencimento.asc())
        .all()
    )
    categorias_saida = (
        Categoria.query.filter_by(user_id=current_user.id, tipo="saída")
        .order_by(Categoria.nome.asc())
        .all()
    )
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "parcelas.html",
        parcelas=parcelas,
        categorias_saida=categorias_saida,
        cartoes=cartoes,
    )


@app.route("/parcelas/adicionar", methods=["POST"])
@login_required
def adicionar_parcela():
    criar_parcelas_a_partir_formulario(request.form)
    return redirect(url_for("listar_parcelas"))


@app.route("/parcelas/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_parcela(id):
    pagar_parcela_service(id)
    return redirect(url_for("listar_parcelas"))


# ===========================
# ROTAS: INVESTIMENTOS
# ===========================
@app.route("/investimentos", methods=["GET", "POST"])
@login_required
def investimentos():
    form = InvestimentoForm()
    investimentos = Investimento.query.filter_by(user_id=current_user.id).all()
    categorias_investimento = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    if request.method == "POST":
        if form.validate_on_submit():
            tipo = form.tipo.data.strip()
            nome = form.nome.data.strip()
            quantidade = form.quantidade.data
            preco_compra = form.preco_compra.data
            data_compra_date = form.data_compra.data
            categoria_id_str = (request.form.get("categoria_id") or "").strip()

            if not categoria_id_str:
                flash("Selecione uma categoria de investimento.", "danger")
                return redirect(url_for("investimentos"))

            try:
                categoria_id = int(categoria_id_str)
            except ValueError:
                flash("Categoria de investimento inválida.", "danger")
                return redirect(url_for("investimentos"))

            categoria = Categoria.query.get(categoria_id)
            if not categoria or categoria.user_id != current_user.id or categoria.tipo != "investimento":
                flash("Categoria de investimento inválida.", "danger")
                return redirect(url_for("investimentos"))

            data_compra_dt = datetime.combine(data_compra_date, datetime.min.time())

            try:
                novo = Investimento(
                    user_id=current_user.id,
                    tipo=tipo,
                    nome=nome,
                    quantidade=quantidade,
                    preco_compra=preco_compra,
                    data_compra=data_compra_dt,
                )
                db.session.add(novo)
                db.session.commit()
                flash(f'Investimento em "{nome}" registrado!', "success")
                return redirect(url_for("investimentos"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar o investimento: {e}", "danger")
        else:
            flash("Erro no formulário de investimento.", "danger")

    return render_template(
        "investimentos.html",
        nome=current_user.nome,
        investimentos=investimentos,
        categorias_investimento=categorias_investimento,
        form=form,
    )


@app.route("/investimentos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_investimento(id):
    investimento = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not investimento:
        flash("Investimento não encontrado.", "danger")
        return redirect(url_for("investimentos"))

    form = InvestimentoForm(obj=investimento)
    categorias_investimento = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                investimento.tipo = form.tipo.data.strip()
                investimento.nome = form.nome.data.strip()
                investimento.quantidade = form.quantidade.data
                investimento.preco_compra = form.preco_compra.data
                data_compra_date = form.data_compra.data
                if data_compra_date:
                    investimento.data_compra = datetime.combine(data_compra_date, datetime.min.time())

                db.session.commit()
                flash(f"Investimento '{investimento.nome}' atualizado!", "success")
                return redirect(url_for("investimentos"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao atualizar: {e}", "danger")
        else:
            flash("Erro no formulário de edição.", "danger")

    if request.method == "GET" and investimento.data_compra:
        form.data_compra.data = investimento.data_compra.date()

    return render_template(
        "editar_investimento.html",
        investimento=investimento,
        categorias_investimento=categorias_investimento,
        form=form,
    )


@app.route("/investimentos/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_investimento(id):
    investimento = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not investimento:
        flash("Investimento não encontrado.", "danger")
        return redirect(url_for("investimentos"))

    try:
        db.session.delete(investimento)
        db.session.commit()
        flash(f"Investimento '{investimento.nome}' excluído.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir: {e}", "danger")

    return redirect(url_for("investimentos"))


# ===========================
# ROTAS: RELATÓRIOS
# ===========================
@app.route("/relatorios", methods=["GET"])
@login_required
def relatorios():
    periodo_selecionado = request.args.get("periodo")
    hoje = datetime.now()

    if periodo_selecionado:
        try:
            ano = int(periodo_selecionado.split("-")[0])
            mes = int(periodo_selecionado.split("-")[1])
        except (ValueError, IndexError):
            mes = hoje.month
            ano = hoje.year
            periodo_selecionado = hoje.strftime("%Y-%m")
    else:
        mes = hoje.month
        ano = hoje.year
        periodo_selecionado = hoje.strftime("%Y-%m")

    despesas_por_categoria = (
        db.session.query(Categoria.nome, func.sum(Transacao.valor))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            Categoria.tipo == "saída",
            extract("month", Transacao.data_transacao) == mes,
            extract("year", Transacao.data_transacao) == ano,
        )
        .group_by(Categoria.nome)
        .all()
    )
    dados_despesas = {nome: abs(valor) for nome, valor in despesas_por_categoria if valor is not None}

    receitas_por_categoria = (
        db.session.query(Categoria.nome, func.sum(Transacao.valor))
        .join(Categoria)
        .filter(
            Transacao.user_id == current_user.id,
            Categoria.tipo == "entrada",
            extract("month", Transacao.data_transacao) == mes,
            extract("year", Transacao.data_transacao) == ano,
        )
        .group_by(Categoria.nome)
        .all()
    )
    dados_receitas = {nome: valor for nome, valor in receitas_por_categoria if valor is not None}

    return render_template(
        "relatorios.html",
        periodo_selecionado=periodo_selecionado,
        dados_despesas=dados_despesas,
        dados_receitas=dados_receitas,
    )


# ===========================
# ROTAS: EXTRATO
# ===========================
@app.route("/extrato", methods=["GET"])
@login_required
def extrato():
    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .filter(Categoria.tipo.in_(["entrada", "saída"]))
        .order_by(Categoria.nome.asc())
        .all()
    )

    selecao = (
        db.session.query(
            Transacao.id,
            Transacao.data_transacao.label("data"),
            Transacao.descricao,
            func.abs(Transacao.valor).label("valor"),
            Categoria.nome.label("categoria_nome"),
            Categoria.tipo.label("tipo_bd"),
        )
        .join(Categoria)
        .filter(Transacao.user_id == current_user.id)
    )

    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    categoria_id_str = request.args.get("categoria_id")
    tipo_str = request.args.get("tipo")

    try:
        if data_inicio_str:
            data_inicio = date.fromisoformat(data_inicio_str)
            selecao = selecao.filter(Transacao.data_transacao >= data_inicio)
        if data_fim_str:
            data_fim = date.fromisoformat(data_fim_str)
            selecao = selecao.filter(Transacao.data_transacao <= data_fim)
    except ValueError:
        flash("Formato de data inválido.", "warning")

    if categoria_id_str and categoria_id_str.isdigit():
        categoria_id = int(categoria_id_str)
        if categoria_id > 0:
            selecao = selecao.filter(Transacao.categoria_id == categoria_id)

    if tipo_str:
        if tipo_str == "receita":
            selecao = selecao.filter(Categoria.tipo == "entrada")
        elif tipo_str == "despesa":
            selecao = selecao.filter(Categoria.tipo == "saída")

    selecao = selecao.order_by(Transacao.data_transacao.desc())
    resultados_db = selecao.all()

    transacoes_formatadas = []
    for r in resultados_db:
        d = r._asdict()
        d["tipo"] = "receita" if d["tipo_bd"] == "entrada" else "despesa"
        d["conta_nome"] = "Conta Padrão"
        d["cartao_nome"] = None
        transacoes_formatadas.append(d)

    return render_template(
        "extrato.html", transacoes=transacoes_formatadas, categorias=categorias
    )


# ===========================
# EXECUÇÃO DA APLICAÇÃO
# ===========================
if __name__ == "__main__":
    # Garante a criação do banco de dados ao executar localmente
    with app.app_context():
        db.create_all()
    app.run(debug=True)