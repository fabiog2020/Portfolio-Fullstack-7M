from datetime import date, datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Transacao, Categoria, Cartao
from forms.transacao_form import TransacaoForm
from services.transactions_service import criar_transacao_a_partir_formulario

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    form = TransacaoForm()
    categorias = Categoria.query.filter_by(user_id=current_user.id).order_by(Categoria.nome.asc()).all()
    categorias_transacao = [c for c in categorias if c.tipo in ["entrada", "saída"]]
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    return render_template("adicionar.html", form=form, categorias=categorias_transacao, cartoes=cartoes)

@transactions_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    form = TransacaoForm()
    if not form.validate_on_submit():
        for field_name, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{field_name}': {error}", "danger")
        return redirect(url_for("transactions.formulario_adicionar_transacao"))

    sucesso = criar_transacao_a_partir_formulario(form)
    if not sucesso:
        return redirect(url_for("transactions.formulario_adicionar_transacao"))
    
    # Redireciona para o dashboard (main.dashboard)
    return redirect(url_for("main.dashboard"))

@transactions_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        flash("Transação não encontrada.", "danger")
        return redirect(url_for("main.dashboard"))

    categorias = Categoria.query.filter_by(user_id=current_user.id).filter(Categoria.tipo.in_(["entrada", "saída"])).order_by(Categoria.nome.asc()).all()

    if request.method == "POST":
        categoria_id = int(request.form.get("categoria_id"))
        descricao = request.form.get("descricao")
        valor_str = request.form.get("valor")
        data_str = request.form.get("data")
        try:
            valor = float(valor_str)
            data_transacao = date.fromisoformat(data_str)
            nova_categoria = Categoria.query.get(categoria_id)
            
            if not nova_categoria or nova_categoria.user_id != current_user.id:
                flash("Categoria inválida.", "danger")
                return render_template("editar.html", transacao=transacao, categorias=categorias)

            valor_final = valor if nova_categoria.tipo == "entrada" else -abs(valor)
            transacao.categoria_id = categoria_id
            transacao.descricao = descricao
            transacao.valor = valor_final
            transacao.data_transacao = data_transacao
            
            db.session.commit()
            flash("Transação atualizada!", "success")
            return redirect(url_for("main.dashboard"))
        except (ValueError, TypeError) as e:
            flash(f"Erro no formato: {e}", "danger")

    return render_template("editar.html", transacao=transacao, categorias=categorias)

@transactions_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_transacao(id):
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        flash("Erro ao excluir.", "danger")
        return redirect(url_for("main.dashboard"))
    try:
        db.session.delete(transacao)
        db.session.commit()
        flash("Transação excluída.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for("main.dashboard"))