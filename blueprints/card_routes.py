from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models_finance import Cartao, Parcela

cards_bp = Blueprint('cards', __name__)

@cards_bp.route("/", methods=["GET"])
@login_required
def cartoes():
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    for cartao in cartoes:
        cartao.parcelas_abertas = Parcela.query.filter_by(cartao_id=cartao.id, pago=False).count()
    return render_template("cartoes.html", cartoes=cartoes)

@cards_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_cartao():
    nome = request.form.get("nome")
    limite = float(request.form.get("limite") or 0)
    venc_str = request.form.get("vencimento_dia")
    try:
        venc = int(venc_str) if venc_str else None
        if venc is not None and (venc < 1 or venc > 31):
            flash("Dia inválido.", "danger")
            return redirect(url_for("cards.cartoes"))
        
        novo = Cartao(nome=nome, limite=limite, vencimento_dia=venc, user_id=current_user.id)
        db.session.add(novo)
        db.session.commit()
        flash(f'Cartão "{nome}" adicionado!', "success")
    except ValueError:
        flash("Limite inválido.", "danger")
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
        flash("Não pode excluir cartão com parcelas.", "danger")
        return redirect(url_for("cards.cartoes"))

    try:
        db.session.delete(cartao)
        db.session.commit()
        flash("Cartão excluído.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for("cards.cartoes"))