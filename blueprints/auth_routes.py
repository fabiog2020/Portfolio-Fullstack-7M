# blueprints/auth_routes.py
import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database import db
from models.models import User

auth_bp = Blueprint('auth', __name__)

# --- Validação de Senha Forte ---
def is_password_strong(password):
    """
    Exige: 8 caracteres, 1 maiúscula, 1 minúscula, 1 número, 1 especial.
    """
    regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return re.match(regex, password)

# ---------------------------------------------------------
# ROTA: REGISTRO
# ---------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('password')
        senha_confirm = request.form.get('password_confirm') # Captura a confirmação

        # 1. Validação: Senhas Iguais?
        if senha != senha_confirm:
            flash('As senhas não conferem. Digite com atenção.', 'error')
            return render_template('register.html')

        # 2. Validação: Senha Forte?
        if not is_password_strong(senha):
            flash('A senha deve ter: min 8 caracteres, 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial (@$!%*?&).', 'error')
            return render_template('register.html')

        # 3. Verifica se email já existe
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este e-mail já está cadastrado.', 'error')
            return redirect(url_for('auth.register'))

        # 4. Cria o Usuário
        new_user = User(nome=nome, email=email, confirmed=False)
        new_user.set_password(senha)
        
        db.session.add(new_user)
        db.session.commit()

        # 5. SIMULAÇÃO DE ENVIO DE E-MAIL (OLHE O TERMINAL)
        token = f"fake-token-{new_user.id}" 
        link = url_for('auth.confirm_email', token=token, _external=True)
        
        # MENSAGEM NO CONSOLE (AQUI ESTÁ O LINK!)
        print("\n" + "="*50)
        print("📧 [SIMULAÇÃO] EMAIL DE CONFIRMAÇÃO PARA:", email)
        print(f"🔗 LINK CLICÁVEL: {link}")
        print("="*50 + "\n")

        flash('Conta criada! Olhe o terminal do sistema para pegar o link de confirmação (Simulação).', 'info')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ---------------------------------------------------------
# ROTA: CONFIRMAÇÃO DE EMAIL
# ---------------------------------------------------------
@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        user_id = int(token.split('-')[-1])
        user = db.session.get(User, user_id)
        
        if user and not user.confirmed:
            user.confirmed = True
            user.confirmed_on = datetime.now(timezone.utc)
            db.session.commit()
            flash('E-mail confirmado com sucesso! Faça login.', 'success')
        else:
            flash('Link inválido ou conta já confirmada.', 'warning')
            
    except:
        flash('Link de confirmação inválido.', 'error')

    return redirect(url_for('auth.login'))

# ---------------------------------------------------------
# ROTA: LOGIN
# ---------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.confirmed:
                flash('Conta não confirmada. Pegue o link no terminal (Simulação) e confirme.', 'warning')
                return render_template('login.html')

            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login inválido. Verifique e-mail e senha.', 'error')

    return render_template('login.html')

# ---------------------------------------------------------
# ROTA: LOGOUT
# ---------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))