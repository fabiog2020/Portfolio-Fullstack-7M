# blueprints/profile_routes.py
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models.models import User, Suporte, Notification

profile_bp = Blueprint('profile', __name__)

# --- ROTAS DE PERFIL, PLANOS E CHECKOUT (Mantidas iguais) ---
@profile_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        nova_senha = request.form.get('senha')
        
        current_user.telefone = request.form.get('telefone')
        current_user.cpf = request.form.get('cpf')
        current_user.cep = request.form.get('cep')
        current_user.endereco = request.form.get('endereco')
        current_user.numero = request.form.get('numero')
        current_user.bairro = request.form.get('bairro')
        current_user.cidade = request.form.get('cidade')
        current_user.estado = request.form.get('estado')
        current_user.profissao = request.form.get('profissao')
        
        renda_input = request.form.get('renda_mensal')
        if renda_input:
            try:
                renda_limpa = renda_input.replace('R$', '').replace('.', '').replace(',', '.')
                current_user.renda_mensal = float(renda_limpa)
            except ValueError:
                pass

        if novo_nome: current_user.nome = novo_nome
        if nova_senha: 
            current_user.set_password(nova_senha)
            flash('Senha atualizada!', 'success')
        else:
            flash('Perfil atualizado com sucesso!', 'success')
            
        db.session.commit()
        return redirect(url_for('profile.meu_perfil'))

    return render_template('perfil.html', user=current_user)

@profile_bp.route('/planos', methods=['GET', 'POST'])
@login_required
def planos():
    if request.method == 'POST':
        plano_escolhido = request.form.get('plano_selecionado')
        planos_validos = ['free', 'mensal', 'semestral', 'anual']
        if plano_escolhido == 'free':
            current_user.plano = 'free'
            db.session.commit()
            flash('Plano alterado para FREE.', 'info')
            return redirect(url_for('profile.planos'))
        if plano_escolhido in planos_validos:
            return redirect(url_for('profile.checkout', plano=plano_escolhido))
    return render_template('planos.html', plano_atual=current_user.plano)

@profile_bp.route('/checkout/<plano>', methods=['GET'])
@login_required
def checkout(plano):
    precos = {'mensal': 19.90, 'semestral': 99.90, 'anual': 189.90}
    valor = precos.get(plano, 0)
    return render_template('checkout.html', plano=plano, valor=valor)

@profile_bp.route('/confirmar_pagamento', methods=['POST'])
@login_required
def confirmar_pagamento():
    plano = request.form.get('plano')
    current_user.plano = plano
    nova_notif = Notification(
        mensagem=f"Parabéns! Seu plano {plano.upper()} foi ativado.",
        tipo='success',
        user_id=current_user.id
    )
    db.session.add(nova_notif)
    db.session.commit()
    flash(f'Pagamento confirmado! Plano {plano.upper()} ativo.', 'success')
    return redirect(url_for('profile.meu_perfil'))

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
            flash('Ticket aberto!', 'success')
            return redirect(url_for('profile.suporte'))
    tickets = Suporte.query.filter_by(user_id=current_user.id).order_by(Suporte.data_abertura.desc()).all()
    return render_template('suporte.html', tickets=tickets)

# --- NOVA ROTA INTELIGENTE DE NOTIFICAÇÃO ---
@profile_bp.route('/notificacao/ler/<int:notif_id>')
@login_required
def marcar_lida(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    
    if notif.user_id == current_user.id:
        notif.lida = True
        db.session.commit()
        
        # LÓGICA NOVA: Se tiver 'detalhes', abre a página de relatório
        if notif.detalhes:
            return render_template('notificacao_detalhe.html', notif=notif)
            
        # Se for link comum, redireciona
        if notif.link_destino:
            return redirect(notif.link_destino)
            
    return redirect(request.referrer or url_for('main.dashboard'))