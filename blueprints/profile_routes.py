# blueprints/profile_routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models.models import User, Suporte # Importando da pasta models

# Definindo o Blueprint 'profile'
profile_bp = Blueprint('profile', __name__)

# -------------------------------------------------------------------------
# 1. PERFIL: Alterar Dados e Senha
# -------------------------------------------------------------------------
@profile_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        nova_senha = request.form.get('senha')
        
        # Atualização de Nome
        if novo_nome:
            current_user.nome = novo_nome
        
        # Atualização de Senha
        if nova_senha:
            current_user.set_password(nova_senha)
            flash('Senha atualizada com segurança!', 'success')
            
        db.session.commit()
        flash('Dados do perfil atualizados.', 'success')
        return redirect(url_for('profile.meu_perfil'))

    return render_template('perfil.html', user=current_user)

# -------------------------------------------------------------------------
# 2. PLANOS: Escolher Assinatura
# -------------------------------------------------------------------------
@profile_bp.route('/planos', methods=['GET', 'POST'])
@login_required
def planos():
    if request.method == 'POST':
        plano_escolhido = request.form.get('plano_selecionado')
        
        # Validamos se o plano existe para evitar erros
        planos_validos = ['free', 'mensal', 'semestral', 'anual']
        
        if plano_escolhido in planos_validos:
            current_user.plano = plano_escolhido
            db.session.commit()
            flash(f'Sucesso! Seu plano agora é {plano_escolhido.upper()}.', 'success')
        else:
            flash('Erro: Plano inválido selecionado.', 'error')
            
        return redirect(url_for('profile.planos'))

    return render_template('planos.html', plano_atual=current_user.plano)

# -------------------------------------------------------------------------
# 3. SUPORTE: Abrir Chamados
# -------------------------------------------------------------------------
@profile_bp.route('/suporte', methods=['GET', 'POST'])
@login_required
def suporte():
    if request.method == 'POST':
        assunto = request.form.get('assunto')
        mensagem = request.form.get('mensagem')
        
        if assunto and mensagem:
            novo_ticket = Suporte(assunto=assunto, mensagem=mensagem, usuario=current_user)
            db.session.add(novo_ticket)
            db.session.commit()
            flash('Solicitação enviada! Nossa equipe responderá em breve.', 'success')
            return redirect(url_for('profile.suporte'))
        else:
            flash('Por favor, preencha o assunto e a mensagem.', 'warning')

    # Busca o histórico de tickets desse usuário
    tickets = Suporte.query.filter_by(user_id=current_user.id).order_by(Suporte.data_abertura.desc()).all()
    
    return render_template('suporte.html', tickets=tickets)