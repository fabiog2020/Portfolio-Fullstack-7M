from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

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
# DASHBOARD PRINCIPAL
# ===========================
@app.route("/")
@login_required
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    transacoes = Transacao.query.filter_by(user_id=current_user.id).order_by(Transacao.data.desc()).all()
    entradas = sum(t.valor for t in transacoes if t.tipo == 'entrada')
    saidas = sum(t.valor for t in transacoes if t.tipo == 'saida')
    saldo = entradas - saidas
    return render_template("dashboard.html", nome=current_user.nome, transacoes=transacoes, saldo=saldo)


# ===========================
# ADICIONAR TRANSAÇÃO
# ===========================
@app.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    tipo = request.form.get("tipo")
    categoria = request.form.get("categoria")
    descricao = request.form.get("descricao")
    valor = float(request.form.get("valor"))

    nova = Transacao(tipo=tipo, categoria=categoria, descricao=descricao, valor=valor, user_id=current_user.id)
    db.session.add(nova)
    db.session.commit()
    flash("Transação adicionada com sucesso!", "success")
    return redirect(url_for("dashboard"))


# ===========================
# EDITAR TRANSAÇÃO
# ===========================
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    if transacao.user_id != current_user.id:
        flash("Você não tem permissão para editar esta transação.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        transacao.tipo = request.form.get("tipo")
        transacao.categoria = request.form.get("categoria")
        transacao.descricao = request.form.get("descricao")
        transacao.valor = float(request.form.get("valor"))
        db.session.commit()
        flash("Transação atualizada com sucesso!", "success")
        return redirect(url_for("dashboard"))

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
