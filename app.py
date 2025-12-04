# app.py

import os
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from sqlalchemy import extract, func

# ===========================
# CONFIGURAÇÃO BÁSICA
# ===========================
from config import DevConfig
from database import db
from forms.auth_forms import LoginForm, RegisterForm
from forms.categoria_form import CategoriaForm
from forms.investimento_form import InvestimentoForm
from forms.transacao_form import TransacaoForm
from services.parcelas_service import (criar_parcelas_a_partir_formulario,
                                       pagar_parcela_service)
from services.transactions_service import criar_transacao_a_partir_formulario
from tools.cli_commands import register_cli_commands
from models import User
from models_finance import Cartao, Categoria, Investimento, Parcela, Transacao

app = Flask(__name__, instance_relative_config=True)


def ensure_instance_folder(flask_app: Flask) -> None:
    """Garante que a pasta *instance* existe para armazenar configs/sessões."""

    try:
        os.makedirs(flask_app.instance_path, exist_ok=True)
    except OSError as exc:  # pragma: no cover - comportamento dependente do SO
        raise RuntimeError(
            f"Não foi possível criar a pasta de instância '{flask_app.instance_path}'."
        ) from exc


ensure_instance_folder(app)

# Carrega configuração de desenvolvimento (pode trocar para ProdConfig no futuro)
app.config.from_object(DevConfig)

# Inicializa o SQLAlchemy com o app
db.init_app(app)
# Registra comandos CLI para flask seed-db
with app.app_context():
    register_cli_commands(app)  # <--- NOVO

# =========================================================================
# IMPORTAÇÃO DOS MODELOS
# Assumimos que 'User' está em models.py e os demais em models_finance.py
# =========================================================================

# Durante execução normal da aplicação, criamos as tabelas caso ainda não existam.
if __name__ == "__main__":
    with app.app_context():
        db.create_all()



# ===========================
# FUNÇÃO LOGIN MANAGER
# ===========================
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    # Usando a sintaxe moderna do SQLAlchemy 2.0 para compatibilidade
    return db.session.get(User, int(user_id))


# ==================================================
# UTILITY: CONVERSOR HEX-TO-RGB (Para Templates)
# ==================================================
def hex_to_rgb(hex_color):
    """Converte uma cor hexadecimal (#RRGGBB) para uma tupla RGB (R, G, B)."""
    cor_padrao = (108, 117, 125)

    try:
        # 1. Pré-processamento
        hex_color = str(hex_color).lstrip("#")
        if len(hex_color) == 3:
            hex_color = hex_color[0] * 2 + hex_color[1] * 2 + hex_color[2] * 2

        # 2. Tentativa de conversão
        # Tenta converter os 6 dígitos hexadecimais para inteiros RGB
        # O [0:2] pega os dois primeiros (R), [2:4] pega (G), [4:6] pega (B)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b  # <--- Retorna a cor RGB

    # 3. Tratamento de erro (se a string for inválida)
    except (ValueError, TypeError, AttributeError) as e:
        # Captura erros de conversão de inteiro ou problemas de tipo
        print(f"Erro ao converter cor {hex_color}: {e}")
        # Retorna a cor padrão (cinza) para evitar quebrar o app
        return cor_padrao


# Torna a função 'hex_to_rgb' disponível em todos os templates Jinja
@app.context_processor
def utility_processor():
    return dict(hex_to_rgb=hex_to_rgb)


# ==================================================
# FUNÇÃO UTILITÁRIA (INSERÇÃO DE DADOS INICIAIS)
# ==================================================
def inserir_categorias_padrao(user_id):
    """Insere um conjunto de categorias padrão com ícones e cores para um novo usuário."""
    # Ícones Font Awesome 6
    categorias = [
        # ENTRADAS
        {
            "nome": "Salário",
            "tipo": "entrada",
            "icone": "fa-solid fa-money-bill-wave",
            "cor": "#28a745",
        },  # Verde
        {
            "nome": "Renda Extra",
            "tipo": "entrada",
            "icone": "fa-solid fa-sack-dollar",
            "cor": "#17a2b8",
        },  # Azul Ciano
        # SAÍDAS ESSENCIAIS
        {
            "nome": "Moradia (Aluguel/Parcela)",
            "tipo": "saída",
            "icone": "fa-solid fa-house",
            "cor": "#dc3545",
        },  # Vermelho
        {
            "nome": "Alimentação",
            "tipo": "saída",
            "icone": "fa-solid fa-burger",
            "cor": "#ffc107",
        },  # Amarelo
        {
            "nome": "Transporte (Combustível)",
            "tipo": "saída",
            "icone": "fa-solid fa-car-side",
            "cor": "#6f42c1",
        },  # Roxo
        {
            "nome": "Saúde (Farmácia)",
            "tipo": "saída",
            "icone": "fa-solid fa-briefcase-medical",
            "cor": "#20c997",
        },  # Verde Água
        {
            "nome": "Lazer",
            "tipo": "saída",
            "icone": "fa-solid fa-champagne-glasses",
            "cor": "#fd7e14",
        },  # Laranja
        {
            "nome": "Educação",
            "tipo": "saída",
            "icone": "fa-solid fa-graduation-cap",
            "cor": "#007bff",
        },  # Azul Padrão
        # INVESTIMENTOS
        {
            "nome": "Renda Variável (Ações)",
            "tipo": "investimento",
            "icone": "fa-solid fa-chart-line",
            "cor": "#007bff",
        },
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

        # Usando sintaxe moderna do SQLAlchemy 2.0
        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and user.check_password(senha):
            login_user(user)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha inválidos.", "danger")

    # Se for GET, ou se o form tiver erro de validação, renderiza de novo
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

        # Verifica se o e-mail já existe
        user_existente = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user_existente:
            flash("E-mail já cadastrado.", "warning")
            return render_template("register.html", form=form)

        # Cria o novo usuário
        novo = User(nome=nome, email=email)
        novo.set_password(senha)
        db.session.add(novo)
        db.session.commit()  # importante: gera novo.id

        # Insere categorias padrão para o novo usuário
        inserir_categorias_padrao(novo.id)

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    # GET ou form inválido → volta a tela de cadastro com erros
    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout efetuado com sucesso!", "info")
    return redirect(url_for("login"))


# ===========================
# DASHBOARD PRINCIPAL (DINÂMICO E ROBUSTO)
# ===========================
@app.route("/")
@login_required
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    # 1. DEFINIÇÃO DO PERÍODO (TORNANDO DINÂMICO)
    mes_param = request.args.get("mes", type=int)
    ano_param = request.args.get("ano", type=int)

    hoje = datetime.now()

    mes_atual = mes_param if mes_param and 1 <= mes_param <= 12 else hoje.month
    ano_atual = ano_param if ano_param else hoje.year

    # 2. CÁLCULO REALIZADO (TRANSAÇÕES JÁ EFETUADAS)
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

    # 2.2. SAÍDAS REALIZADAS (DESPESAS)
    # As saídas são persistidas como valores negativos para facilitar o balanço.
    # Para apresentar o total gasto no mês, usamos o valor absoluto das transações.
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

    # 3. CÁLCULO PREVISTO (CONTAS A PAGAR/RECEBER - PARCELAS NÃO PAGAS)

    # 3.1. DESPESAS PREVISTAS (SOMENTE PARCELAS A VENCER, COM DATA NO MÊS ATUAL, E NÃO PAGAS)
    despesas_previstas_parcelas = (
        db.session.query(func.sum(Parcela.valor))
        .join(Categoria)
        .filter(
            Parcela.user_id == current_user.id,
            extract("month", Parcela.data_vencimento) == mes_atual,
            extract("year", Parcela.data_vencimento) == ano_atual,
            Categoria.tipo == "saída",  # Só consideramos parcelas de despesas
           Parcela.pago.is_(False),  # Apenas as que ainda não foram pagas
        )
        .scalar()
        or 0.0
    )

    # 4. CONSOLIDAÇÃO DO DASHBOARD

    saldo_realizado = entradas_realizadas - saidas_realizadas
    saldo_projetado = saldo_realizado - despesas_previstas_parcelas

    # 5. TRANSAÇÕES RECENTES
    transacoes_recentes = (
        Transacao.query.filter(Transacao.user_id == current_user.id)
        .order_by(Transacao.data_transacao.desc())
        .limit(10)
        .all()
    )

    # =========================================================
    # 6. DADOS PARA GRÁFICOS (Adicionado para resolver o TypeError)
    # =========================================================

    # 6.1. DESPESAS POR CATEGORIA (SAÍDAS)
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

    # Converte os resultados da query para um dicionário Python simples (nome: float)
    # Isso garante que o Jinja/tojson consiga serializar o objeto para o JavaScript.
    dados_despesas = {
        nome: float(total) for nome, total in query_despesas if total is not None
    }

    # 6.2. RECEITAS POR CATEGORIA (ENTRADAS)
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

    # Converte os resultados da query para um dicionário Python simples (nome: float)
    dados_receitas = {
        nome: float(total) for nome, total in query_receitas if total is not None
    }

    # 7. RENDERIZAR O TEMPLATE (Passando os novos dados)
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
        # NOVOS DADOS PARA OS GRÁFICOS
        dados_despesas=dados_despesas,
        dados_receitas=dados_receitas,
    )


# ===========================
# ROTAS DE TRANSAÇÕES (CRIAÇÃO, EDIÇÃO, EXCLUSÃO)
# ===========================
@app.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    """Rota GET para exibir o formulário e passar a lista de categorias e cartões."""

    form = TransacaoForm()

    # Traz as categorias do usuário logado
    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .order_by(Categoria.nome.asc())
        .all()
    )

    # Filtra as categorias de Investimento para não aparecerem em Transações Comuns (Entrada/Saída)
    categorias_transacao = [c for c in categorias if c.tipo in ["entrada", "saída"]]
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()  # cartões

    return render_template(
        "adicionar.html",
        form=form,
        categorias=categorias_transacao,
        cartoes=cartoes,
    )


@app.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    """Processa o envio do formulário de nova transação usando WTForms."""
    form = TransacaoForm()

    # 1. Validação básica do formulário (tipos / campos obrigatórios)
    if not form.validate_on_submit():
        # Mostra as mensagens de erro campo a campo
        for field_name, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{field_name}': {error}", "danger")
        return redirect(url_for("formulario_adicionar_transacao"))

    # 2. Delega validações de negócio e criação à camada de serviço
    sucesso = criar_transacao_a_partir_formulario(form)

    if not sucesso:
        # O próprio service já mostrou mensagens via flash
        return redirect(url_for("formulario_adicionar_transacao"))

    # 3. Tudo certo → volta para o dashboard
    return redirect(url_for("dashboard"))


@app.route("/transacoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    """Rota para carregar o formulário de edição ou processar a atualização."""
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
        # Processamento da Edição
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
                return render_template(
                    "editar.html", transacao=transacao, categorias=categorias
                )

            # Ajusta o valor para ser negativo se for uma despesa
            valor_final = valor if nova_categoria.tipo == "entrada" else -abs(valor)

            # Atualiza o objeto
            transacao.categoria_id = categoria_id
            transacao.descricao = descricao
            transacao.valor = valor_final
            transacao.data_transacao = data_transacao

            db.session.commit()
            flash("Transação atualizada com sucesso!", "success")
            return redirect(url_for("dashboard"))

        except (ValueError, TypeError) as e:
            flash(f"Erro no formato dos dados: {e}", "danger")

    # Rota GET: Exibe o formulário de edição
    return render_template("editar.html", transacao=transacao, categorias=categorias)


@app.route("/transacoes/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_transacao(id):
    """Rota para excluir uma transação."""
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()

    if not transacao:
        flash(
            "Transação não encontrada ou você não tem permissão para excluí-la.",
            "danger",
        )
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
# ROTAS: CATEGORIAS (Adicionar, Listar, Excluir, EDITAR!)
# ===============================================


@app.route("/categorias", methods=["GET", "POST"])
@login_required
def gerenciar_categorias():
    form = CategoriaForm()

    if form.validate_on_submit():
        nome = form.nome.data.strip()
        tipo = form.tipo.data
        icone = form.icone.data or "fa-solid fa-list"  # Padrão
        cor = form.cor.data or "#007bff"

        if not nome or not tipo:
            flash("Nome e Tipo da categoria são obrigatórios.", "danger")
            return redirect(url_for("gerenciar_categorias"))

        # Checa se já existe categoria com esse nome para o usuário
        existente = Categoria.query.filter_by(
            user_id=current_user.id, nome=nome
        ).first()
        if existente:
            flash(f"A categoria '{nome}' já existe.", "warning")
            return redirect(url_for("gerenciar_categorias"))

        nova = Categoria(
            user_id=current_user.id,
            nome=nome,
            tipo=tipo,
            icone=icone,
            cor=cor,
        )

        try:
            db.session.add(nova)
            db.session.commit()
            flash(f"Categoria '{nome}' ({tipo}) adicionada com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar a categoria: {e}", "danger")

        return redirect(url_for("gerenciar_categorias"))

    # GET → listar categorias e mostrar formulário
    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .order_by(Categoria.nome.asc())
        .all()
    )

    return render_template(
        "categorias.html",
        categorias=categorias,
        form=form,
    )


@app.route("/categorias/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_categoria(id):
    """Rota para editar uma categoria existente."""
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()

    if not categoria:
        flash("Categoria não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("gerenciar_categorias"))

    # form ligado ao objeto categoria
    form = CategoriaForm(obj=categoria)

    # Se for POST, tentamos validar e salvar
    if request.method == "POST":
        # Atualiza o form com o POST
        if not form.validate():
            flash("Há erros no formulário. Verifique os campos em vermelho.", "danger")
            # Aqui o form já carrega os erros e os valores digitados
            return render_template(
                "editar_categoria.html",
                categoria=categoria,
                form=form,
            )

        novo_nome = form.nome.data.strip()
        novo_tipo = form.tipo.data
        novo_icone = form.icone.data or categoria.icone
        novo_cor = form.cor.data or categoria.cor

        # Checa por duplicação se o nome mudou
        if novo_nome != categoria.nome:
            existente = Categoria.query.filter(
                Categoria.user_id == current_user.id,
                Categoria.nome == novo_nome,
                Categoria.id != id,
            ).first()
            if existente:
                flash(f"Já existe outra categoria chamada '{novo_nome}'.", "warning")
                return render_template(
                    "editar_categoria.html",
                    categoria=categoria,
                    form=form,
                )

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
            return render_template(
                "editar_categoria.html",
                categoria=categoria,
                form=form,
            )

    # GET → exibe formulário com dados atuais
    return render_template(
        "editar_categoria.html",
        categoria=categoria,
        form=form,
    )


@app.route("/categorias/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()

    if not categoria:
        flash(
            "Categoria não encontrada ou você não tem permissão para excluí-la.",
            "danger",
        )
        return redirect(url_for("gerenciar_categorias"))

    # VERIFICAÇÃO DE SEGURANÇA: Checa se há transações ou parcelas vinculadas
    transacoes_vinculadas = Transacao.query.filter_by(categoria_id=id).count()
    parcelas_vinculadas = Parcela.query.filter_by(categoria_id=id).count()
    total_vinculos = transacoes_vinculadas + parcelas_vinculadas

    if total_vinculos > 0:
        flash(
            f"Não é possível excluir a categoria '{categoria.nome}'. Ela possui {total_vinculos} vinculos com transações e/ou parcelas.",
            "danger",
        )
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
# ROTAS: CARTÕES (CRUD COMPLETO)
# ===========================
@app.route("/cartoes", methods=["GET"])
@login_required
def cartoes():
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    # Adicionando a contagem de parcelas não pagas por cartão (para o template)
    for cartao in cartoes:
        cartao.parcelas_abertas = Parcela.query.filter_by(
            cartao_id=cartao.id, pago=False
        ).count()
    return render_template("cartoes.html", cartoes=cartoes)


@app.route("/cartoes/adicionar", methods=["POST"])
@login_required
def adicionar_cartao():
    nome = request.form.get("nome")
    limite = float(request.form.get("limite") or 0)
    venc_str = request.form.get("vencimento_dia")

    try:
        venc = int(venc_str) if venc_str else None

        # Validação simples para dia de vencimento (1 a 31)
        if venc is not None and (venc < 1 or venc > 31):
            flash("Dia de vencimento inválido. Use um número entre 1 e 31.", "danger")
            return redirect(url_for("cartoes"))

        novo = Cartao(
            nome=nome, limite=limite, vencimento_dia=venc, user_id=current_user.id
        )
        db.session.add(novo)
        db.session.commit()
        flash(f'Cartão "{nome}" adicionado com sucesso!', "success")

    except ValueError:
        flash("Limite deve ser um número válido.", "danger")

    return redirect(url_for("cartoes"))


@app.route("/cartoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cartao(id):
    """Rota para editar um cartão existente."""
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()

    if not cartao:
        flash("Cartão não encontrado ou você não tem permissão.", "danger")
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
    """Rota para excluir um cartão, verificando vínculos com parcelas."""
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()

    if not cartao:
        flash(
            "Cartão não encontrado ou você não tem permissão para excluí-lo.", "danger"
        )
        return redirect(url_for("cartoes"))

    # VERIFICAÇÃO DE SEGURANÇA: Checa se há parcelas vinculadas (mesmo as pagas)
    parcelas_vinculadas = Parcela.query.filter_by(cartao_id=id).count()

    if parcelas_vinculadas > 0:
        flash(
            f"Não é possível excluir o cartão '{cartao.nome}'. Ele possui {parcelas_vinculadas} parcelas vinculadas. Exclua as parcelas primeiro ou desvincule-as.",
            "danger",
        )
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
# ROTAS: PARCELAS (Lógica Avançada e Ações)
# ===========================
@app.route("/parcelas", methods=["GET"])
@login_required
def listar_parcelas():
    # Trazendo todas as parcelas (pagas e não pagas)
    parcelas = (
        Parcela.query.filter_by(user_id=current_user.id)
        .order_by(Parcela.data_vencimento.asc())
        .all()
    )

    # Trazendo categorias (para o formulário)
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
    """Rota para adicionar um conjunto de parcelas de uma só vez."""
    sucesso = criar_parcelas_a_partir_formulario(request.form)

    # Independente de sucesso ou erro, voltamos para a lista.
    # O próprio service já mostra as mensagens (flash).
    return redirect(url_for("listar_parcelas"))


@app.route("/parcelas/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_parcela(id):
    """Rota para marcar uma parcela como paga."""
    pagar_parcela_service(id)
    # O service já cuida de tudo e mostra mensagens
    return redirect(url_for("listar_parcelas"))


# ===========================
# ROTAS: INVESTIMENTOS (CRUD COMPLETO)
# ===========================
@app.route("/investimentos", methods=["GET", "POST"])
@login_required
def investimentos():
    """
    Lista investimentos do usuário e permite cadastrar novos usando WTForms.
    """
    form = InvestimentoForm()

    # Lista de investimentos já cadastrados
    investimentos = Investimento.query.filter_by(user_id=current_user.id).all()

    # Categorias do tipo 'investimento' (para o select no template)
    categorias_investimento = Categoria.query.filter_by(
        user_id=current_user.id,
        tipo="investimento",
    ).all()

    # Se veio um POST (envio do formulário de novo investimento)
    if request.method == "POST":
        if form.validate_on_submit():
            # Campos validados pelo WTForms
            tipo = form.tipo.data.strip()
            nome = form.nome.data.strip()
            quantidade = form.quantidade.data
            preco_compra = form.preco_compra.data
            data_compra_date = form.data_compra.data  # é um date

            # Campo de categoria vem direto do formulário HTML (select)
            categoria_id_str = (request.form.get("categoria_id") or "").strip()

            # ==> AQUI categoria é OBRIGATÓRIA <==
            if not categoria_id_str:
                flash(
                    "Selecione uma categoria de investimento (ex: Renda_fixa ou Renda_variavel).",
                    "danger",
                )
                return redirect(url_for("investimentos"))

            # Converte e valida categoria
            try:
                categoria_id = int(categoria_id_str)
            except ValueError:
                flash("Categoria de investimento inválida.", "danger")
                return redirect(url_for("investimentos"))

            categoria = Categoria.query.get(categoria_id)

            if (
                not categoria
                or categoria.user_id != current_user.id
                or categoria.tipo != "investimento"
            ):
                flash("Categoria de investimento inválida.", "danger")
                return redirect(url_for("investimentos"))

            # Converter date → datetime para salvar no modelo
            data_compra_dt = datetime.combine(
                data_compra_date,
                datetime.min.time(),
            )

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
            # Form não validou
            flash(
                "Erro no formulário de investimento. Verifique os campos e tente novamente.",
                "danger",
            )

    # GET ou POST com erro → renderiza página
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
    """
    Edita um investimento existente usando WTForms.
    """
    investimento = Investimento.query.filter_by(
        id=id,
        user_id=current_user.id,
    ).first()

    if not investimento:
        flash("Investimento não encontrado ou você não tem permissão.", "danger")
        return redirect(url_for("investimentos"))

    form = InvestimentoForm(obj=investimento)

    # Categorias do tipo 'investimento' (caso queira mostrar na tela)
    categorias_investimento = Categoria.query.filter_by(
        user_id=current_user.id,
        tipo="investimento",
    ).all()

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                investimento.tipo = form.tipo.data.strip()
                investimento.nome = form.nome.data.strip()
                investimento.quantidade = form.quantidade.data
                investimento.preco_compra = form.preco_compra.data

                data_compra_date = form.data_compra.data
                if data_compra_date:
                    investimento.data_compra = datetime.combine(
                        data_compra_date,
                        datetime.min.time(),
                    )

                db.session.commit()
                flash(
                    f"Investimento '{investimento.nome}' atualizado com sucesso!",
                    "success",
                )
                return redirect(url_for("investimentos"))

            except (ValueError, TypeError) as e:
                db.session.rollback()
                flash(f"Erro ao atualizar o investimento: {e}", "danger")
        else:
            flash(
                "Erro no formulário de edição. Verifique os campos e tente novamente.",
                "danger",
            )

    # GET → garantir que o campo data_compra do form está preenchido com a data atual salva
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
    """
    Exclui um investimento do usuário logado.
    """
    investimento = Investimento.query.filter_by(
        id=id,
        user_id=current_user.id,
    ).first()

    if not investimento:
        flash(
            "Investimento não encontrado ou você não tem permissão para excluí-lo.",
            "danger",
        )
        return redirect(url_for("investimentos"))

    try:
        db.session.delete(investimento)
        db.session.commit()
        flash(f"Investimento '{investimento.nome}' excluído com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir o investimento: {e}", "danger")

    return redirect(url_for("investimentos"))


# ===========================
# ROTAS: RELATÓRIOS E ANÁLISES
# ===========================
@app.route("/relatorios", methods=["GET"])
@login_required
def relatorios():
    """
    Gera dados de Despesas e Receitas agrupados por Categoria para
    renderizar os gráficos de pizza (doughnut charts).
    """
    # 1. DEFINIÇÃO DO PERÍODO
    periodo_selecionado = request.args.get("periodo")
    hoje = datetime.now()

    # Se um período foi selecionado no formulário, usa esse período
    if periodo_selecionado:
        try:
            # O input 'month' do HTML retorna 'YYYY-MM'
            ano = int(periodo_selecionado.split("-")[0])
            mes = int(periodo_selecionado.split("-")[1])
        except (ValueError, IndexError):
            # Fallback em caso de formato inválido
            mes = hoje.month
            ano = hoje.year
            periodo_selecionado = hoje.strftime("%Y-%m")  # Volta para o formato padrão
    else:
        # Padrão: Mês e Ano atuais
        mes = hoje.month
        ano = hoje.year
        periodo_selecionado = hoje.strftime("%Y-%m")

    # 2. CONSULTA DE DESPESAS (Saídas) por Categoria
    # Nota: Transacao.valor é armazenado como negativo para saídas.
    # Usaremos ABS(func.sum) para que o gráfico mostre valores positivos.
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

    # Formata para o dict: {nome_categoria: valor_positivo}
    dados_despesas = {
        nome: abs(valor) for nome, valor in despesas_por_categoria if valor is not None
    }

    # 3. CONSULTA DE RECEITAS (Entradas) por Categoria
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

    # Formata para o dict: {nome_categoria: valor}
    dados_receitas = {
        nome: valor for nome, valor in receitas_por_categoria if valor is not None
    }

    # 4. Renderiza o template. Os dicionários são passados para o Jinja,
    # que os converterá para JSON para o JavaScript usar.
    return render_template(
        "relatorios.html",
        periodo_selecionado=periodo_selecionado,
        dados_despesas=dados_despesas,
        dados_receitas=dados_receitas,
    )


# ===========================
# ROTAS: EXTRATO (LISTAGEM E FILTRO)
# ===========================
@app.route("/extrato", methods=["GET"])
@login_required
def extrato():
    """
    Lista e filtra todas as transações do usuário, permitindo filtros por
    data, categoria e tipo (receita/despesa).
    """
    # 1. Obter Categorias para o filtro dropdown
    # Inclui apenas entradas e saídas, já que extratos geralmente não incluem Investimentos brutos.
    categorias = (
        Categoria.query.filter_by(user_id=current_user.id)
        .filter(Categoria.tipo.in_(["entrada", "saída"]))
        .order_by(Categoria.nome.asc())
        .all()
    )

    # 2. Iniciar a Query de Transações e aplicar o JOIN
    # Selecionamos as colunas essenciais, incluindo nome e tipo da categoria.
    # Usamos func.abs para garantir que o valor seja sempre positivo no extrato (o sinal é dado pelo 'tipo').
    selecao = (
        db.session.query(
            Transacao.id,
            Transacao.data_transacao.label("data"),
            Transacao.descricao,
            func.abs(Transacao.valor).label("valor"),
            Categoria.nome.label("categoria_nome"),
            Categoria.tipo.label("tipo_bd"),  # 'entrada' ou 'saída'
        )
        .join(Categoria)
        .filter(Transacao.user_id == current_user.id)
    )

    # 3. Processar e Aplicar Filtros (vindo do formulário GET)
    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    categoria_id_str = request.args.get("categoria_id")
    tipo_str = request.args.get("tipo")  # 'receita' ou 'despesa'

    # 3.1. Filtro por Data
    try:
        if data_inicio_str:
            data_inicio = date.fromisoformat(data_inicio_str)
            selecao = selecao.filter(Transacao.data_transacao >= data_inicio)
        if data_fim_str:
            data_fim = date.fromisoformat(data_fim_str)
            selecao = selecao.filter(Transacao.data_transacao <= data_fim)
    except ValueError:
        flash("Formato de data inválido. Ignorando filtro de data.", "warning")

    # 3.2. Filtro por Categoria
    if categoria_id_str and categoria_id_str.isdigit():
        categoria_id = int(categoria_id_str)
        if categoria_id > 0:
            selecao = selecao.filter(Transacao.categoria_id == categoria_id)

    # 3.3. Filtro por Tipo (Mapeando o valor do formulário para o banco)
    if tipo_str:
        tipo_bd = None
        if tipo_str == "receita":
            tipo_bd = "entrada"
        elif tipo_str == "despesa":
            tipo_bd = "saída"

        if tipo_bd:
            selecao = selecao.filter(Categoria.tipo == tipo_bd)

    # 4. Finalizar Query: Ordenar e Executar
    selecao = selecao.order_by(Transacao.data_transacao.desc())
    resultados_db = selecao.all()

    # 5. Formatar Transações (Mapear resultados da query para dicionários)
    transacoes_formatadas = []
    for r in resultados_db:
        # Cria um dicionário a partir do objeto Row
        d = r._asdict()
        # Converte o tipo do BD ('entrada'/'saída') para o tipo do Template ('receita'/'despesa')
        d["tipo"] = "receita" if d["tipo_bd"] == "entrada" else "despesa"

        # Adiciona placeholders para campos que o template espera (e seu modelo Transacao não tem)
        # Se você tiver um modelo 'Conta', precisará fazer JOINs adicionais.
        d["conta_nome"] = "Conta Padrão"
        d["cartao_nome"] = None

        transacoes_formatadas.append(d)

    # 6. Renderizar
    return render_template(
        "extrato.html", transacoes=transacoes_formatadas, categorias=categorias
    )


# ===========================
# EXECUÇÃO DA APLICAÇÃO
# ===========================
if __name__ == "__main__":
    app.run(debug=True)
