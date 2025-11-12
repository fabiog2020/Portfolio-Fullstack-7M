# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, date
import os
from sqlalchemy import func, extract
import re 
import calendar # Usado para o cálculo robusto de parcelas

# ===========================
# CONFIGURAÇÃO BÁSICA
# ===========================
app = Flask(__name__)
app.secret_key = "chave-super-secreta"

# ===========================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ===========================
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(base_dir, "finance.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Importa o objeto 'db'
from database import db
db.init_app(app)

# =========================================================================
# IMPORTAÇÃO DOS MODELOS
# Assumimos que 'User' está em models.py e os demais em models_finance.py
# =========================================================================
from models import User
from models_finance import Transacao, Categoria, Cartao, Parcela, Investimento

# Cria o banco de dados e as tabelas
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
    # Remove # se presente
    hex_color = hex_color.lstrip('#')
    # Se for hex de 3 dígitos (ex: #F00), expande para 6 (ex: #FF0000)
    if len(hex_color) == 3:
        hex_color = hex_color[0]*2 + hex_color[1]*2 + hex_color[2]*2
    
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b
    except:
        # Fallback para cinza (#6c757d) se a conversão falhar
        return 108, 117, 125 

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
        {'nome': 'Salário', 'tipo': 'entrada', 'icone': 'fa-solid fa-money-bill-wave', 'cor': '#28a745'}, # Verde
        {'nome': 'Renda Extra', 'tipo': 'entrada', 'icone': 'fa-solid fa-sack-dollar', 'cor': '#17a2b8'}, # Azul Ciano
        # SAÍDAS ESSENCIAIS
        {'nome': 'Moradia (Aluguel/Parcela)', 'tipo': 'saída', 'icone': 'fa-solid fa-house', 'cor': '#dc3545'}, # Vermelho
        {'nome': 'Alimentação', 'tipo': 'saída', 'icone': 'fa-solid fa-burger', 'cor': '#ffc107'}, # Amarelo
        {'nome': 'Transporte (Combustível)', 'tipo': 'saída', 'icone': 'fa-solid fa-car-side', 'cor': '#6f42c1'}, # Roxo
        {'nome': 'Saúde (Farmácia)', 'tipo': 'saída', 'icone': 'fa-solid fa-briefcase-medical', 'cor': '#20c997'}, # Verde Água
        {'nome': 'Lazer', 'tipo': 'saída', 'icone': 'fa-solid fa-champagne-glasses', 'cor': '#fd7e14'}, # Laranja
        {'nome': 'Educação', 'tipo': 'saída', 'icone': 'fa-solid fa-graduation-cap', 'cor': '#007bff'}, # Azul Padrão
        # INVESTIMENTOS
        {'nome': 'Renda Variável (Ações)', 'tipo': 'investimento', 'icone': 'fa-solid fa-chart-line', 'cor': '#007bff'},
    ]

    for c in categorias:
        nova_categoria = Categoria(
            user_id=user_id,
            nome=c['nome'],
            tipo=c['tipo'],
            icone=c['icone'],
            cor=c['cor']
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
        
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        # Usando sintaxe moderna do SQLAlchemy 2.0
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        
        if user and user.check_password(senha):
            login_user(user)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        # Validação de E-mail usando Regex
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        if not re.match(email_regex, email):
            flash("Formato de e-mail inválido. Por favor, corrija.", "warning")
            return render_template("register.html")
            
        # Usando sintaxe moderna do SQLAlchemy 2.0
        if db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none():
            flash("E-mail já cadastrado.", "warning")
        else:
            # 1. Cria o novo usuário
            novo = User(nome=nome, email=email)
            novo.set_password(senha)
            db.session.add(novo)
            db.session.commit() # CRÍTICO: Comita o usuário para gerar o novo.id
            
            # 2. Insere as categorias padrão APÓS O CADASTRO
            inserir_categorias_padrao(novo.id)
            
            flash("Cadastro realizado com sucesso! Faça login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


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
    mes_param = request.args.get('mes', type=int)
    ano_param = request.args.get('ano', type=int)

    hoje = datetime.now()
    
    mes_atual = mes_param if mes_param and 1 <= mes_param <= 12 else hoje.month
    ano_atual = ano_param if ano_param else hoje.year

    # 2. CÁLCULO REALIZADO (TRANSAÇÕES JÁ EFETUADAS)
    entradas_realizadas = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
        Transacao.user_id == current_user.id,
        extract('month', Transacao.data_transacao) == mes_atual,
        extract('year', Transacao.data_transacao) == ano_atual,
        Categoria.tipo == 'entrada'
    ).scalar() or 0.0

    # 2.2. SAÍDAS REALIZADAS (DESPESAS)
    saidas_realizadas = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
        Transacao.user_id == current_user.id,
        extract('month', Transacao.data_transacao) == mes_atual,
        extract('year', Transacao.data_transacao) == ano_atual,
        Categoria.tipo == 'saída'
    ).scalar() or 0.0

    # 3. CÁLCULO PREVISTO (CONTAS A PAGAR/RECEBER - PARCELAS NÃO PAGAS)
    
    # 3.1. DESPESAS PREVISTAS (SOMENTE PARCELAS A VENCER, COM DATA NO MÊS ATUAL, E NÃO PAGAS)
    despesas_previstas_parcelas = db.session.query(func.sum(Parcela.valor)).join(Categoria).filter(
        Parcela.user_id == current_user.id,
        extract('month', Parcela.data_vencimento) == mes_atual,
        extract('year', Parcela.data_vencimento) == ano_atual,
        Categoria.tipo == 'saída', # Só consideramos parcelas de despesas
        Parcela.pago == False       # Apenas as que ainda não foram pagas
    ).scalar() or 0.0

    # 4. CONSOLIDAÇÃO DO DASHBOARD

    saldo_realizado = entradas_realizadas - saidas_realizadas
    saldo_projetado = saldo_realizado - despesas_previstas_parcelas
    
    # 5. TRANSAÇÕES RECENTES
    # Nota: O uso de .all() sem .join() pode ser ineficiente. 
    # Idealmente, faríamos .options(joinedload(Transacao.categoria)).all() se estivéssemos fora do Flask-SQLAlchemy.
    transacoes_recentes = Transacao.query.filter(
        Transacao.user_id == current_user.id
    ).order_by(Transacao.data_transacao.desc()).limit(10).all()

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
        transacoes_recentes=transacoes_recentes
    )

# ===========================
# ROTAS DE TRANSAÇÕES (CRIAÇÃO, EDIÇÃO, EXCLUSÃO)
# ===========================
@app.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    """Rota GET para exibir o formulário e passar a lista de categorias e cartões."""
    
    # Traz as categorias do usuário logado
    categorias = Categoria.query.filter_by(user_id=current_user.id).order_by(Categoria.nome.asc()).all()
    
    # Filtra as categorias de Investimento para não aparecerem em Transações Comuns (Entrada/Saída)
    categorias_transacao = [c for c in categorias if c.tipo in ['entrada', 'saída']]
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all() # Adiciona cartões para futuras integrações
    
    return render_template(
        "adicionar.html",
        categorias=categorias_transacao,
        cartoes=cartoes
    )

@app.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    # 1. Obter dados do formulário
    categoria_id_str = request.form.get("categoria_id")
    descricao = request.form.get("descricao")
    valor_str = request.form.get("valor")
    data_str = request.form.get("data") # Ex: "2025-11-09"

    try:
        # 2. VALIDAÇÃO E CONVERSÃO
        categoria_id = int(categoria_id_str)
        # Verifica se o ID da categoria existe antes de prosseguir
        categoria = Categoria.query.get(categoria_id)
        if not categoria or categoria.user_id != current_user.id:
            flash("Categoria inválida ou não encontrada.", "danger")
            return redirect(url_for("formulario_adicionar_transacao"))
            
        valor = float(valor_str)
        # Permite datas no passado, presente e futuro
        data_transacao = date.fromisoformat(data_str) 

    except (ValueError, TypeError) as e:
        flash(f"Erro de formato nos dados. Verifique a categoria, valor e data: {e}", "danger")
        return redirect(url_for("formulario_adicionar_transacao"))

    # 3. CRIAÇÃO E SALVAMENTO
    nova = Transacao(
        categoria_id=categoria_id, 
        descricao=descricao,
        # Se a categoria for de 'saída', o valor deve ser negativo no banco para cálculos corretos
        valor=valor if categoria.tipo == 'entrada' else -abs(valor),
        data_transacao=data_transacao, 
        user_id=current_user.id
    )
    db.session.add(nova)
    db.session.commit()
    flash("Transação adicionada com sucesso!", "success")
    return redirect(url_for("dashboard"))


@app.route("/transacoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    """Rota para carregar o formulário de edição ou processar a atualização."""
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()

    if not transacao:
        flash("Transação não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("dashboard"))

    categorias = Categoria.query.filter_by(user_id=current_user.id).filter(Categoria.tipo.in_(['entrada', 'saída'])).order_by(Categoria.nome.asc()).all()
    
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
                return render_template("editar.html", transacao=transacao, categorias=categorias)

            # Ajusta o valor para ser negativo se for uma despesa
            valor_final = valor if nova_categoria.tipo == 'entrada' else -abs(valor)
            
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
        flash("Transação não encontrada ou você não tem permissão para excluí-la.", "danger")
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
    if request.method == "POST":
        nome = request.form.get("nome").strip()
        tipo = request.form.get("tipo")
        icone = request.form.get("icone", "fa-solid fa-list") # Padrão
        cor = request.form.get("cor", "#6c757d") # Padrão

        if not nome or not tipo:
            flash("Nome e Tipo da categoria são obrigatórios.", "danger")
            return redirect(url_for("gerenciar_categorias"))

        # 1. Checa se já existe uma categoria com este nome para este usuário
        existente = Categoria.query.filter_by(user_id=current_user.id, nome=nome).first()
        if existente:
            flash(f"A categoria '{nome}' já existe.", "warning")
            return redirect(url_for("gerenciar_categorias"))

        # 2. Cria e Salva a nova categoria
        nova = Categoria(
            user_id=current_user.id, 
            nome=nome, 
            tipo=tipo, 
            icone=icone, 
            cor=cor
        )
        db.session.add(nova)
        db.session.commit()
        flash(f"Categoria '{nome}' ({tipo}) adicionada com sucesso!", "success")
        return redirect(url_for("gerenciar_categorias"))
    
    # Rota GET: Listar Categorias
    categorias = Categoria.query.filter_by(user_id=current_user.id).order_by(Categoria.nome.asc()).all()
    return render_template("categorias.html", categorias=categorias)


@app.route("/categorias/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_categoria(id):
    """Rota para editar uma categoria existente."""
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()
    
    if not categoria:
        flash("Categoria não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("gerenciar_categorias"))
        
    if request.method == "POST":
        novo_nome = request.form.get("nome").strip()
        novo_tipo = request.form.get("tipo")
        novo_icone = request.form.get("icone", categoria.icone)
        novo_cor = request.form.get("cor", categoria.cor)
        
        # 1. Checa por duplicação (se o nome mudou e já existe outro igual)
        if novo_nome != categoria.nome:
            existente = Categoria.query.filter(
                Categoria.user_id == current_user.id, 
                Categoria.nome == novo_nome,
                Categoria.id != id
            ).first()
            if existente:
                flash(f"A categoria '{novo_nome}' já existe.", "warning")
                return render_template("editar_categoria.html", categoria=categoria)
        
        # 2. Atualiza e Salva
        categoria.nome = novo_nome
        categoria.tipo = novo_tipo
        categoria.icone = novo_icone
        categoria.cor = novo_cor
        
        db.session.commit()
        flash(f"Categoria '{categoria.nome}' atualizada com sucesso!", "success")
        return redirect(url_for("gerenciar_categorias"))
        
    return render_template("editar_categoria.html", categoria=categoria)


@app.route("/categorias/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()

    if not categoria:
        flash("Categoria não encontrada ou você não tem permissão para excluí-la.", "danger")
        return redirect(url_for("gerenciar_categorias"))
    
    # VERIFICAÇÃO DE SEGURANÇA: Checa se há transações ou parcelas vinculadas
    transacoes_vinculadas = Transacao.query.filter_by(categoria_id=id).count()
    parcelas_vinculadas = Parcela.query.filter_by(categoria_id=id).count()
    total_vinculos = transacoes_vinculadas + parcelas_vinculadas

    if total_vinculos > 0:
        flash(f"Não é possível excluir a categoria '{categoria.nome}'. Ela possui {total_vinculos} vinculos com transações e/ou parcelas.", "danger")
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
@app.route('/cartoes', methods=['GET'])
@login_required
def cartoes():
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    # Adicionando a contagem de parcelas não pagas por cartão (para o template)
    for cartao in cartoes:
        cartao.parcelas_abertas = Parcela.query.filter_by(cartao_id=cartao.id, pago=False).count()
    return render_template('cartoes.html', cartoes=cartoes)


@app.route('/cartoes/adicionar', methods=['POST'])
@login_required
def adicionar_cartao():
    nome = request.form.get('nome')
    limite = float(request.form.get('limite') or 0)
    venc_str = request.form.get('vencimento_dia')
    
    try:
        venc = int(venc_str) if venc_str else None
        
        # Validação simples para dia de vencimento (1 a 31)
        if venc is not None and (venc < 1 or venc > 31):
            flash('Dia de vencimento inválido. Use um número entre 1 e 31.', 'danger')
            return redirect(url_for('cartoes'))

        novo = Cartao(nome=nome, limite=limite, vencimento_dia=venc, user_id=current_user.id)
        db.session.add(novo)
        db.session.commit()
        flash(f'Cartão "{nome}" adicionado com sucesso!', 'success')
        
    except ValueError:
        flash('Limite deve ser um número válido.', 'danger')
        
    return redirect(url_for('cartoes'))


@app.route("/cartoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cartao(id):
    """Rota para editar um cartão existente."""
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()
    
    if not cartao:
        flash("Cartão não encontrado ou você não tem permissão.", "danger")
        return redirect(url_for("cartoes"))
        
    if request.method == "POST":
        novo_nome = request.form.get('nome')
        novo_limite_str = request.form.get('limite')
        novo_venc_str = request.form.get('vencimento_dia')
        
        try:
            novo_limite = float(novo_limite_str or 0)
            novo_venc = int(novo_venc_str) if novo_venc_str else None
            
            if novo_venc is not None and (novo_venc < 1 or novo_venc > 31):
                flash('Dia de vencimento inválido.', 'danger')
                return render_template("editar_cartao.html", cartao=cartao)
            
            cartao.nome = novo_nome
            cartao.limite = novo_limite
            cartao.vencimento_dia = novo_venc
            
            db.session.commit()
            flash(f"Cartão '{cartao.nome}' atualizado com sucesso!", "success")
            return redirect(url_for("cartoes"))
            
        except ValueError:
            flash('Erro: Limite ou dia de vencimento inválido.', 'danger')

    return render_template("editar_cartao.html", cartao=cartao)


@app.route("/cartoes/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_cartao(id):
    """Rota para excluir um cartão, verificando vínculos com parcelas."""
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()

    if not cartao:
        flash("Cartão não encontrado ou você não tem permissão para excluí-lo.", "danger")
        return redirect(url_for("cartoes"))
    
    # VERIFICAÇÃO DE SEGURANÇA: Checa se há parcelas vinculadas (mesmo as pagas)
    parcelas_vinculadas = Parcela.query.filter_by(cartao_id=id).count()

    if parcelas_vinculadas > 0:
        flash(f"Não é possível excluir o cartão '{cartao.nome}'. Ele possui {parcelas_vinculadas} parcelas vinculadas. Exclua as parcelas primeiro ou desvincule-as.", "danger")
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
@app.route('/parcelas', methods=['GET'])
@login_required
def listar_parcelas():
    # Trazendo todas as parcelas (pagas e não pagas)
    parcelas = Parcela.query.filter_by(user_id=current_user.id).order_by(Parcela.data_vencimento.asc()).all()
    
    # Trazendo categorias (para o formulário)
    categorias_saida = Categoria.query.filter_by(user_id=current_user.id, tipo='saída').order_by(Categoria.nome.asc()).all()
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    
    return render_template('parcelas.html', 
        parcelas=parcelas, 
        categorias_saida=categorias_saida,
        cartoes=cartoes
    )


@app.route('/parcelas/adicionar', methods=['POST'])
@login_required
def adicionar_parcela():
    """Rota para adicionar um conjunto de parcelas de uma só vez."""

    # 1. Obter dados do formulário (agora com valor total e num_parcelas)
    descricao = request.form.get('descricao')
    valor_total_str = request.form.get('valor_total')
    num_parcelas_str = request.form.get('num_parcelas')
    data_primeira_str = request.form.get('data_vencimento_primeira')
    categoria_id_str = request.form.get('categoria_id')
    cartao_id_str = request.form.get('cartao_id')
    
    try:
        valor_total = float(valor_total_str)
        num_parcelas = int(num_parcelas_str)
        categoria_id = int(categoria_id_str)
        cartao_id = int(cartao_id_str) if cartao_id_str else None
        data_primeira = date.fromisoformat(data_primeira_str)
        
        if valor_total <= 0 or num_parcelas <= 0 or num_parcelas > 60: 
             flash('Verifique o valor total e o número de parcelas (máx. 60).', 'danger')
             return redirect(url_for('listar_parcelas'))
             
    except (ValueError, TypeError):
        flash('Erro de formato nos dados (Valor Total, Parcelas, Categoria ou Data).', 'danger')
        return redirect(url_for('listar_parcelas'))
        
    # Verifica se a categoria é válida e de saída (parcelas geralmente são despesas)
    categoria = Categoria.query.filter_by(id=categoria_id, user_id=current_user.id).first()
    if not categoria or categoria.tipo != 'saída':
        flash('Categoria inválida ou não é uma categoria de Despesa.', 'danger')
        return redirect(url_for('listar_parcelas'))

    # Calcula o valor da parcela (arredondado para duas casas decimais)
    valor_parcela = round(valor_total / num_parcelas, 2)
    
    # Ajusta a última parcela para que a soma seja exatamente o valor_total (evita erro de arredondamento)
    ajuste = round(valor_total - (valor_parcela * num_parcelas), 2)
    
    dia_vencimento_inicial = data_primeira.day

    try:
        for i in range(1, num_parcelas + 1):
            
            # Cálculo da data de vencimento: Mês atual + i - 1
            mes_base = data_primeira.month + i - 1
            ano_vencimento = data_primeira.year
            
            # Ajusta ano e mês
            while mes_base > 12:
                mes_base -= 12
                ano_vencimento += 1
            mes_vencimento = mes_base
            
            # Tenta criar a data. O dia pode ser inválido (ex: 31/02), então ajustamos.
            try:
                data_vencimento = date(ano_vencimento, mes_vencimento, dia_vencimento_inicial)
            except ValueError:
                # Se o dia for inválido para o mês (ex: dia 31 em fev/abr/jun/set/nov), usa o último dia do mês
                ultimo_dia_mes = calendar.monthrange(ano_vencimento, mes_vencimento)[1]
                data_vencimento = date(ano_vencimento, mes_vencimento, ultimo_dia_mes)
                
            
            valor_final_parcela = valor_parcela
            if i == num_parcelas:
                # Adiciona o ajuste à última parcela
                valor_final_parcela += ajuste
            
            # Cria a Parcela
            nova_parcela = Parcela(
                descricao=f"{descricao} ({i}/{num_parcelas})", 
                valor=valor_final_parcela, 
                data_vencimento=data_vencimento,
                categoria_id=categoria_id,
                cartao_id=cartao_id,
                user_id=current_user.id,
                pago=False
            )
            db.session.add(nova_parcela)
            
        db.session.commit()
        flash(f'{num_parcelas} parcelas adicionadas com sucesso para "{descricao}"!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerar as parcelas: {e}', 'danger')
        
    return redirect(url_for('listar_parcelas'))


@app.route("/parcelas/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_parcela(id):
    """Rota para marcar uma parcela como paga."""
    parcela = Parcela.query.filter_by(id=id, user_id=current_user.id).first()
    
    if not parcela:
        flash("Parcela não encontrada ou você não tem permissão.", "danger")
        return redirect(url_for("listar_parcelas"))
        
    if parcela.pago:
        flash("Esta parcela já estava marcada como paga.", "warning")
        return redirect(url_for("listar_parcelas"))
        
    try:
        # Marca como paga
        parcela.pago = True
        
        # 🔔 Ação CRÍTICA: Geração da Transação Realizada
        # Quando a parcela é paga, ela DEVE gerar uma Transação no banco de dados
        # para que o dashboard reflita o débito no SALDO REALIZADO.
        categoria = Categoria.query.get(parcela.categoria_id)
        if not categoria:
             flash("Erro: Categoria da parcela não encontrada. A Transação Realizada não pôde ser criada.", "danger")
             parcela.pago = False # Reverte o pago se a transação falhar
             db.session.rollback()
             return redirect(url_for("listar_parcelas"))

        # Cria a transação (o valor deve ser negativo, já que é uma despesa)
        transacao_realizada = Transacao(
            categoria_id=parcela.categoria_id,
            descricao=f"[PAGO] {parcela.descricao}",
            # O valor já é positivo no modelo Parcela, precisamos garantir que seja negativo na Transação (Saída)
            valor=-abs(parcela.valor), 
            data_transacao=datetime.now().date(), # Data de pagamento
            user_id=current_user.id
        )
        db.session.add(transacao_realizada)
        db.session.commit()
        
        flash(f"Parcela '{parcela.descricao}' marcada como paga e Transação de Saída gerada!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao processar o pagamento da parcela: {e}", "danger")
        
    return redirect(url_for('listar_parcelas'))


# ===========================
# ROTAS: INVESTIMENTOS (CRUD COMPLETO)
# ===========================
@app.route("/investimentos")
@login_required
def investimentos():
    investimentos = Investimento.query.filter_by(user_id=current_user.id).all()
    # Trazendo categorias de investimento para o formulário
    categorias_investimento = Categoria.query.filter_by(user_id=current_user.id, tipo='investimento').all()
    
    return render_template("investimentos.html", 
        nome=current_user.nome, 
        investimentos=investimentos,
        categorias_investimento=categorias_investimento
    )


@app.route('/investimentos/adicionar', methods=['POST'])
@login_required
def adicionar_investimento():
    tipo = request.form.get('tipo')
    nome = request.form.get('nome')
    categoria_id_str = request.form.get('categoria_id')
    quantidade = float(request.form.get('quantidade') or 0)
    preco_compra = float(request.form.get('preco_compra') or 0)
    data_compra_str = request.form.get('data_compra')
    
    try:
        categoria_id = int(categoria_id_str)
        data_compra_dt = date.fromisoformat(data_compra_str)
        
        # 1. Validação de Categoria (deve ser tipo 'investimento')
        categoria = Categoria.query.get(categoria_id)
        if not categoria or categoria.user_id != current_user.id or categoria.tipo != 'investimento':
            flash("Categoria inválida ou não é uma categoria de Investimento.", "danger")
            return redirect(url_for('investimentos'))
            
        # 2. Cria e Salva
        novo = Investimento(
            tipo=tipo, 
            nome=nome, 
            quantidade=quantidade, 
            preco_compra=preco_compra,
            data_compra=data_compra_dt, 
            user_id=current_user.id,
            # Vinculação com categoria (necessária se quisermos rastrear o "custo" do investimento)
            # Nota: O modelo Investimento não tem categoria_id no seu código anterior. 
            # Assumindo que você irá adicionar se precisar vincular uma transação inicial.
            # Por enquanto, vou salvar apenas os dados do investimento em si.
        )
        db.session.add(novo)
        db.session.commit()
        flash(f'Investimento em "{nome}" registrado!', 'success')
        
    except (ValueError, TypeError) as e:
        flash(f'Erro de formato nos dados do investimento: {e}', 'danger')
        db.session.rollback()
        
    return redirect(url_for('investimentos'))


@app.route("/investimentos/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_investimento(id):
    """Rota para editar um investimento existente."""
    investimento = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    
    if not investimento:
        flash("Investimento não encontrado ou você não tem permissão.", "danger")
        return redirect(url_for("investimentos"))

    categorias_investimento = Categoria.query.filter_by(user_id=current_user.id, tipo='investimento').all()
        
    if request.method == "POST":
        novo_tipo = request.form.get('tipo')
        novo_nome = request.form.get('nome')
        nova_quantidade = float(request.form.get('quantidade') or 0)
        novo_preco_compra = float(request.form.get('preco_compra') or 0)
        nova_data_compra_str = request.form.get('data_compra')
        
        try:
            nova_data_compra = date.fromisoformat(nova_data_compra_str)

            investimento.tipo = novo_tipo
            investimento.nome = novo_nome
            investimento.quantidade = nova_quantidade
            investimento.preco_compra = novo_preco_compra
            investimento.data_compra = nova_data_compra
            
            db.session.commit()
            flash(f"Investimento '{investimento.nome}' atualizado com sucesso!", "success")
            return redirect(url_for("investimentos"))
            
        except (ValueError, TypeError):
            flash('Erro: Verifique os formatos de quantidade, preço e data.', 'danger')

    return render_template("editar_investimento.html", investimento=investimento, categorias_investimento=categorias_investimento)


@app.route("/investimentos/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_investimento(id):
    """Rota para excluir um investimento."""
    investimento = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    
    if not investimento:
        flash("Investimento não encontrado ou você não tem permissão para excluí-lo.", "danger")
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
# EXECUÇÃO DA APLICAÇÃO
# ===========================
if __name__ == "__main__":
    app.run(debug=True)