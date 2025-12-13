from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from database import db
from models import Cartao, Parcela

cards_bp = Blueprint('cards', __name__)

@cards_bp.route("/", methods=["GET"])
@login_required
def cartoes():
    # Busca os cartões do usuário
    meus_cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    
    # Lógica para calcular a barra de progresso de cada cartão
    for c in meus_cartoes:
        # Soma todas as parcelas DESTE cartão que NÃO foram pagas (saldo devedor)
        saldo_usado = db.session.query(func.sum(Parcela.valor))\
            .filter_by(cartao_id=c.id, pago=False)\
            .scalar() or 0.0
        
        # Anexa atributos temporários ao objeto para usar no template
        c.saldo_usado = saldo_usado
        c.saldo_disponivel = c.limite - saldo_usado
        
        # Calcula porcentagem e evita divisão por zero
        if c.limite > 0:
            c.porcentagem_uso = (saldo_usado / c.limite) * 100
        else:
            c.porcentagem_uso = 0

        # Trava a porcentagem em 100% visualmente se estourar o limite
        c.porcentagem_uso_visual = min(c.porcentagem_uso, 100)

    return render_template("cartoes.html", cartoes=meus_cartoes)

@cards_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_cartao():
    nome = request.form.get("nome")
    limite = float(request.form.get("limite") or 0)
    venc_str = request.form.get("vencimento_dia")
    digitos = request.form.get("digitos_finais") # Novo campo

    try:
        venc = int(venc_str) if venc_str else None
        if venc is not None and (venc < 1 or venc > 31):
            flash("Dia inválido.", "danger")
            return redirect(url_for("cards.cartoes"))
        
        # Limita visualmente a 4 dígitos
        if digitos and len(digitos) > 4:
            digitos = digitos[-4:]

        novo = Cartao(
            nome=nome, 
            limite=limite, 
            vencimento_dia=venc, 
            digitos_finais=digitos, # Salvando
            user_id=current_user.id
        )
        db.session.add(novo)
        db.session.commit()
        flash(f'Cartão "{nome}" adicionado!', "success")
    except ValueError:
        flash("Dados inválidos.", "danger")
    return redirect(url_for("cards.cartoes"))

@cards_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cartao(id):
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()
    if not cartao:
        flash("Cartão não encontrado.", "danger")
        return redirect(url_for("cards.cartoes"))

    if request.method == "POST":
        try:
            cartao.nome = request.form.get("nome")
            cartao.limite = float(request.form.get("limite") or 0)
            
            venc_str = request.form.get("vencimento_dia")
            cartao.vencimento_dia = int(venc_str) if venc_str else None
            
            digitos = request.form.get("digitos_finais")
            if digitos and len(digitos) > 4:
                digitos = digitos[-4:]
            cartao.digitos_finais = digitos

            db.session.commit()
            flash("Cartão atualizado!", "success")
            return redirect(url_for("cards.cartoes"))
        except ValueError:
            flash("Dados inválidos.", "danger")
            
    return render_template("editar_cartao.html", cartao=cartao)

@cards_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_cartao(id):
    cartao = Cartao.query.filter_by(id=id, user_id=current_user.id).first()
    if not cartao:
        flash("Erro ao excluir.", "danger")
        return redirect(url_for("cards.cartoes"))
    
    if Parcela.query.filter_by(cartao_id=id).count() > 0:
        flash("Não pode excluir cartão com parcelas vinculadas.", "danger")
        return redirect(url_for("cards.cartoes"))

    try:
        db.session.delete(cartao)
        db.session.commit()
        flash("Cartão excluído.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for("cards.cartoes"))