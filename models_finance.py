# models_finance.py (Versão 2.0 - Robusta)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date # Importando date para usar em fromisoformat
import os

# IMPORTS NECESSÁRIOS PARA CÁLCULOS ROBUSTOS
from sqlalchemy import func, extract # func para SUM(), extract para MONTH(), YEAR()

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
# Usar o objeto `db` modular definido em database.py
from database import db
db.init_app(app)

# ===========================
# CONFIGURAÇÃO LOGIN MANAGER
# ===========================
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# Models moved to modular files to avoid duplication
from models import User
from models_finance import Transacao, Categoria, Cartao, Parcela, Investimento

# Cria o banco de dados e as tabelas na ordem correta
with app.app_context():
    db.create_all()


# ===========================
# FUNÇÃO LOGIN MANAGER
# ===========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===========================
# ROTAS DE LOGIN E CADASTRO
# ===========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(senha):
            login_user(user)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "warning")
        else:
            novo = User(nome=nome, email=email)
            novo.set_password(senha)
            db.session.add(novo)
            db.session.commit()
            flash("Cadastro realizado com sucesso!", "success")
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
    # Tenta pegar 'mes' e 'ano' da URL: /dashboard?mes=10&ano=2025
    mes_param = request.args.get('mes', type=int)
    ano_param = request.args.get('ano', type=int)

    hoje = datetime.now()
    
    # Usa o parâmetro da URL se existir, senão usa o mês e ano atuais
    mes_atual = mes_param if mes_param and 1 <= mes_param <= 12 else hoje.month
    ano_atual = ano_param if ano_param else hoje.year

    # 2. CÁLCULO REALIZADO (TRANSAÇÕES JÁ EFETUADAS)

    # 2.1. ENTRADAS REALIZADAS (RECEITAS)
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
# ROTAS DE TRANSAÇÕES (CRIAÇÃO)
# ===========================
@app.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    """Rota GET para exibir o formulário e passar a lista de categorias."""
    
    # Traz todas as categorias em ordem alfabética para preencher o campo SELECT
    categorias = Categoria.query.order_by(Categoria.nome.asc()).all()
    
    return render_template(
        "adicionar.html",
        categorias=categorias
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
        valor = float(valor_str)
        # Converte a String de Data para o objeto date
        data_transacao = date.fromisoformat(data_str) 

    except (ValueError, TypeError) as e:
        flash(f"Erro de formato nos dados. Verifique a categoria, valor e data: {e}", "danger")
        return redirect(url_for("formulario_adicionar_transacao"))

    # 3. CRIAÇÃO E SALVAMENTO
    nova = Transacao(
        categoria_id=categoria_id, 
        descricao=descricao,
        valor=valor,
        data_transacao=data_transacao, 
        user_id=current_user.id
    )
    db.session.add(nova)
    db.session.commit()
    flash("Transação adicionada com sucesso!", "success")
    return redirect(url_for("dashboard"))


# ===========================
# EDITAR TRANSAÇÃO (ATUALIZADA)
# ===========================
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    if transacao.user_id != current_user.id:
        flash("Você não tem permissão para editar esta transação.", "danger")
        return redirect(url_for("dashboard"))

    # Rota GET: Exibe o formulário e passa as categorias
    if request.method == "GET":
        categorias = Categoria.query.order_by(Categoria.nome.asc()).all()
        return render_template("editar.html", transacao=transacao, categorias=categorias)

    # Rota POST: Recebe e salva os novos dados
    if request.method == "POST":
        categoria_id_str = request.form.get("categoria_id")
        valor_str = request.form.get("valor")
        data_str = request.form.get("data")
        
        try:
            # 1. Conversão e Atualização dos Campos
            transacao.categoria_id = int(categoria_id_str)
            transacao.descricao = request.form.get("descricao")
            transacao.valor = float(valor_str)
            transacao.data_transacao = date.fromisoformat(data_str) 
            
            db.session.commit()
            flash("Transação atualizada com sucesso!", "success")
            return redirect(url_for("dashboard"))

        except (ValueError, TypeError) as e:
            flash(f"Erro de formato nos dados. Verifique a categoria, valor e data: {e}", "danger")
            return redirect(url_for("editar_transacao", id=id)) 

    # Esta linha é um fallback, mas o código acima já direciona o fluxo corretamente.
    return render_template("editar.html", transacao=transacao) 


# ===========================
# EXCLUIR TRANSAÇÃO
# ===========================
@app.route("/excluir/<int:id>")
@login_required
def excluir_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    if transacao.user_id != current_user.id:
        flash("Você não tem permissão para excluir esta transação.", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(transacao)
    db.session.commit()
    flash("Transação excluída com sucesso!", "info")
    return redirect(url_for("dashboard"))


# ===========================
# PÁGINA DE INVESTIMENTOS
# ===========================
@app.route("/investimentos")
@login_required
def investimentos():
    investimentos = []
    try:
        investimentos = Investimento.query.filter_by(user_id=current_user.id).all()
    except Exception:
        investimentos = []
    return render_template("investimentos.html", nome=current_user.nome, investimentos=investimentos)


# ===========================
# ROTAS: CARTÕES
# ===========================
@app.route('/cartoes', methods=['GET'])
@login_required
def cartoes():
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    return render_template('cartoes.html', cartoes=cartoes)


@app.route('/cartoes/adicionar', methods=['POST'])
@login_required
def adicionar_cartao():
    nome = request.form.get('nome')
    limite = float(request.form.get('limite') or 0)
    venc = request.form.get('vencimento_dia')
    venc = int(venc) if venc else None
    novo = Cartao(nome=nome, limite=limite, vencimento_dia=venc, user_id=current_user.id)
    db.session.add(novo)
    db.session.commit()
    flash('Cartão adicionado com sucesso!', 'success')
    return redirect(url_for('cartoes'))


# ===========================
# ROTAS: PARCELAS
# ===========================
@app.route('/parcelas', methods=['GET'])
@login_required
def listar_parcelas():
    parcelas = Parcela.query.filter_by(user_id=current_user.id).all()
    return render_template('parcelas.html', parcelas=parcelas)


@app.route('/parcelas/adicionar', methods=['POST'])
@login_required
def adicionar_parcela():
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor') or 0)
    venc = request.form.get('vencimento')
    from datetime import datetime as _dt
    try:
        # Nota: Idealmente, usaríamos date.fromisoformat, mas mantivemos a sua implementação original para esta rota.
        venc_dt = _dt.fromisoformat(venc)
    except Exception:
        venc_dt = _dt.utcnow()
    nova = Parcela(descricao=descricao, valor=valor, vencimento=venc_dt, user_id=current_user.id)
    db.session.add(nova)
    db.session.commit()
    flash('Parcela adicionada com sucesso!', 'success')
    return redirect(url_for('listar_parcelas'))


# ===========================
# ROTAS: INVESTIMENTOS
# ===========================
@app.route('/investimentos/adicionar', methods=['POST'])
@login_required
def adicionar_investimento():
    tipo = request.form.get('tipo')
    nome = request.form.get('nome')
    quantidade = float(request.form.get('quantidade') or 0)
    valor_unitario = float(request.form.get('valor_unitario') or 0)
    novo = Investimento(tipo=tipo, nome=nome, quantidade=quantidade, valor_unitario=valor_unitario, user_id=current_user.id)
    db.session.add(novo)
    db.session.commit()
    flash('Investimento registrado!', 'success')
    return redirect(url_for('investimentos'))


# ===========================
# EXECUÇÃO DA APLICAÇÃO
# ===========================
if __name__ == "__main__":
    app.run(debug=True)