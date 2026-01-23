# blueprints/auth_routes.py

import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from models.models import User
# Importamos Categoria para poder criar os dados
from models.models_finance import Categoria 

auth_bp = Blueprint('auth', __name__)

# ==========================================================
# 1. CONSTANTES E LISTA COMPLETA DE CATEGORIAS
# ==========================================================
ENTRADA = "entrada"
SAIDA = "saída"
INVESTIMENTO = "investimento"

CATEGORIAS_PADRAO = [
    # --- GERAL (Pais) ---
    {
        "nome": "Receitas (Geral)",
        "tipo": ENTRADA,
        "icone": "fa-solid fa-sack-dollar",
        "cor": "#4CAF50",
        "parent_ref": None,
    },
    {
        "nome": "Despesas (Geral)",
        "tipo": SAIDA,
        "icone": "fa-solid fa-wallet",
        "cor": "#F44336",
        "parent_ref": None,
    },
    {   
        "nome": "Carteira de Ativos",
        "tipo": INVESTIMENTO,
        "icone": "fa-solid fa-chart-pie",
        "cor": "#2196F3",
        "parent_ref": None,
    },

    # --- FILHAS (SAIDAS) ---
    {
        "nome": "Aluguel",
        "tipo": SAIDA,
        "icone": "fa-solid fa-house",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Energia Elétrica",
        "tipo": SAIDA,
        "icone": "fa-solid fa-bolt",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Água",
        "tipo": SAIDA,
        "icone": "fa-solid fa-droplet",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Internet/Streaming",
        "tipo": SAIDA,
        "icone": "fa-solid fa-video",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Supermercado",
        "tipo": SAIDA,
        "icone": "fa-solid fa-cart-shopping",
        "cor": "#FF9800",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Restaurante/Lanche",
        "tipo": SAIDA,
        "icone": "fa-solid fa-burger",
        "cor": "#FF9800",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Transporte Público/Uber",
        "tipo": SAIDA,
        "icone": "fa-solid fa-train",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Combustível",
        "tipo": SAIDA,
        "icone": "fa-solid fa-gas-pump",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Manutenção Veicular",
        "tipo": SAIDA,
        "icone": "fa-solid fa-car-wrench",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Hospital/Plano de Saúde",
        "tipo": SAIDA,
        "icone": "fa-solid fa-suitcase-medical",
        "cor": "#00BCD4",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Farmácia",
        "tipo": SAIDA,
        "icone": "fa-solid fa-pills",
        "cor": "#00BCD4",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Educação/Cursos",
        "tipo": SAIDA,
        "icone": "fa-solid fa-graduation-cap",
        "cor": "#673AB7",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Lazer/Viagens",
        "tipo": SAIDA,
        "icone": "fa-solid fa-plane",
        "cor": "#E91E63",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Manutenção Residencial",
        "tipo": SAIDA,
        "icone": "fa-solid fa-screwdriver-wrench",
        "cor": "#9E9E9E",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Contabilidade",
        "tipo": SAIDA,
        "icone": "fa-solid fa-calculator",
        "cor": "#9C27B0",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "MEI/CNPJ",
        "tipo": SAIDA,
        "icone": "fa-solid fa-building",
        "cor": "#9C27B0",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Aporte/Investimento",
        "tipo": SAIDA,
        "icone": "fa-solid fa-money-bill-transfer",
        "cor": "#009688",
        "parent_ref": "Despesas (Geral)",
    },

    # --- FILHAS (ENTRADAS) ---
    {
        "nome": "Salário",
        "tipo": ENTRADA,
        "icone": "fa-solid fa-wallet",
        "cor": "#4CAF50",
        "parent_ref": "Receitas (Geral)",
    },
    {
        "nome": "Rendimentos de Investimento",
        "tipo": ENTRADA,
        "icone": "fa-solid fa-money-bill-trend-up",
        "cor": "#009688",
        "parent_ref": "Receitas (Geral)",
    },
    {
        "nome": "Freelance/Extra",
        "tipo": ENTRADA,
        "icone": "fa-solid fa-briefcase",
        "cor": "#8BC34A",
        "parent_ref": "Receitas (Geral)",
    },

    # --- FILHAS (INVESTIMENTOS/ATIVOS) ---
    {
        "nome": "Renda Fixa",
        "tipo": INVESTIMENTO,
        "icone": "fa-solid fa-piggy-bank",
        "cor": "#2196F3",
        "parent_ref": "Carteira de Ativos",
    },
    {
        "nome": "Renda Variável",
        "tipo": INVESTIMENTO,
        "icone": "fa-solid fa-chart-line",
        "cor": "#FFC107",
        "parent_ref": "Carteira de Ativos",
    },
    {
        "nome": "Consórcio",
        "tipo": INVESTIMENTO,
        "icone": "fa-solid fa-car",
        "cor": "#9C27B0",
        "parent_ref": "Carteira de Ativos",
    },
]

# ==========================================================
# 2. FUNÇÃO AUXILIAR: Criar Categorias para o Usuário
# ==========================================================
def criar_categorias_completas(user):
    """
    Replica a lógica do CLI Seed para criar as 26 categorias
    para qualquer novo usuário que se cadastrar.
    """
    mapa_pais = {} # Para guardar o ID dos pais criados agora
    
    # FASE A: Cria as Categorias Pais (parent_ref é None)
    for cat_data in CATEGORIAS_PADRAO:
        if cat_data.get("parent_ref") is None:
            nova_categoria = Categoria(
                nome=cat_data["nome"],
                tipo=cat_data["tipo"],
                icone=cat_data["icone"],
                cor=cat_data["cor"],
                user_id=user.id,
                parent_id=None
            )
            db.session.add(nova_categoria)
            db.session.flush()  # Gera o ID
            mapa_pais[cat_data["nome"]] = nova_categoria.id

    # FASE B: Cria as Categorias Filhas (parent_ref tem o nome do Pai)
    for cat_data in CATEGORIAS_PADRAO:
        if cat_data.get("parent_ref") is not None:
            parent_name = cat_data.get("parent_ref")
            parent_id = mapa_pais.get(parent_name) # Busca ID gerado na Fase A

            if parent_id:
                nova_categoria = Categoria(
                    nome=cat_data["nome"],
                    tipo=cat_data["tipo"],
                    icone=cat_data["icone"],
                    cor=cat_data["cor"],
                    user_id=user.id,
                    parent_id=parent_id
                )
                db.session.add(nova_categoria)
    
    db.session.commit()
    print(f"✅ Categorias criadas com sucesso para o usuário {user.email}")


# ==========================================================
# 3. VALIDAÇÃO DE SENHA
# ==========================================================
def is_password_strong(password):
    regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return re.match(regex, password)


# ==========================================================
# 4. ROTAS DE AUTENTICAÇÃO
# ==========================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('password')
        senha_confirm = request.form.get('password_confirm')

        # 1. Validação: Senhas Iguais
        if senha != senha_confirm:
            flash('As senhas não conferem. Digite com atenção.', 'error')
            return render_template('register.html')

        # 2. Validação: Senha Forte
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
        db.session.commit() # Commit inicial para gerar o ID do usuário

        # 5. CRIA AS CATEGORIAS PADRÃO (AQUI ESTÁ A MÁGICA)
        try:
            criar_categorias_completas(new_user)
        except Exception as e:
            print(f"Erro crítico ao criar categorias: {e}")
            # Em produção, deveríamos reverter o usuário ou logar o erro crítico

        # 6. Simulação de Email
        token = f"fake-token-{new_user.id}" 
        link = url_for('auth.confirm_email', token=token, _external=True)
        
        print("\n" + "="*50)
        print("📧 [SIMULAÇÃO] EMAIL DE CONFIRMAÇÃO PARA:", email)
        print(f"🔗 LINK CLICÁVEL: {link}")
        print("="*50 + "\n")

        flash('Conta criada! Olhe o terminal para confirmar a conta.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


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


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))