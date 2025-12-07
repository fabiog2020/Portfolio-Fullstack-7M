# blueprints/auth_routes.py

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from database import db
from forms.auth_forms import LoginForm, RegisterForm
from models import User
from models_finance import Categoria

# Define o Blueprint
auth_bp = Blueprint('auth', __name__)

# ==================================================
# FUNÇÃO AUXILIAR (Usada no Registro)
# ==================================================
def inserir_categorias_padrao(user_id):
    """Insere categorias padrão para um NOVO usuário."""
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
# ROTAS DE AUTENTICAÇÃO
# ===========================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

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
            return redirect(url_for('dashboard'))
        else:
            flash("E-mail ou senha inválidos.", "danger")

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

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
            return render_template('register.html', form=form)

        novo = User(nome=nome, email=email)
        novo.set_password(senha)
        db.session.add(novo)
        db.session.commit()

        # Insere categorias padrão
        inserir_categorias_padrao(novo.id)

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        # Redireciona para o login do blueprint auth
        return redirect(url_for('auth.login')) 

    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout efetuado com sucesso!", "info")
    return redirect(url_for('auth.login'))