# blueprints/admin_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from database import db
from models.models import User, Suporte

admin_bp = Blueprint('admin', __name__)

# --- PROTEÇÃO: Decorador para garantir que só Admin entra ---
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403) # Erro 403 = Proibido

@admin_bp.before_request
def restrict_access():
    # Executa antes de qualquer rota desse arquivo
    check_admin()

# -----------------------------------------------------------
# 1. DASHBOARD GERAL (Visão de Tickets)
# -----------------------------------------------------------
@admin_bp.route('/painel')
def dashboard():
    # Pega todos os tickets de todo mundo
    tickets = Suporte.query.order_by(Suporte.data_abertura.desc()).all()
    # Pega contagem de usuários
    total_users = User.query.count()
    return render_template('admin_dashboard.html', tickets=tickets, total_users=total_users)

# -----------------------------------------------------------
# 2. LISTA DE USUÁRIOS
# -----------------------------------------------------------
@admin_bp.route('/usuarios')
def listar_usuarios():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# -----------------------------------------------------------
# 3. EDITAR USUÁRIO (Onde você salva quem perdeu a conta)
# -----------------------------------------------------------
@admin_bp.route('/usuario/<int:user_id>', methods=['GET', 'POST'])
def gerenciar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'mudar_senha':
            nova_senha = request.form.get('nova_senha')
            if nova_senha:
                user.set_password(nova_senha)
                flash(f'Senha de {user.nome} alterada com sucesso!', 'success')
        
        elif acao == 'mudar_plano':
            novo_plano = request.form.get('novo_plano')
            user.plano = novo_plano
            flash(f'Plano de {user.nome} alterado para {novo_plano}', 'success')

        db.session.commit()
        return redirect(url_for('admin.gerenciar_usuario', user_id=user.id))

    return render_template('admin_user_detail.html', user=user)

# -----------------------------------------------------------
# 4. RESPONDER TICKET (Simples alteração de status)
# -----------------------------------------------------------
@admin_bp.route('/ticket/<int:ticket_id>/fechar')
def fechar_ticket(ticket_id):
    ticket = Suporte.query.get_or_404(ticket_id)
    ticket.status = 'fechado'
    db.session.commit()
    flash('Ticket fechado.', 'success')
    return redirect(url_for('admin.dashboard'))