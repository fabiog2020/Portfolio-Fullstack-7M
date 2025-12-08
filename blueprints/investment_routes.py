from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Investimento, Categoria
from forms.investimento_form import InvestimentoForm

investments_bp = Blueprint('investments', __name__)

@investments_bp.route("/", methods=["GET", "POST"])
@login_required
def investimentos():
    form = InvestimentoForm()
    lista = Investimento.query.filter_by(user_id=current_user.id).all()
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                cat_id = int(request.form.get("categoria_id") or 0)
                categoria = Categoria.query.get(cat_id)
                if not categoria or categoria.user_id != current_user.id:
                    raise ValueError("Categoria inválida")

                data_dt = datetime.combine(form.data_compra.data, datetime.min.time())
                novo = Investimento(
                    user_id=current_user.id,
                    tipo=form.tipo.data,
                    nome=form.nome.data,
                    quantidade=form.quantidade.data,
                    preco_compra=form.preco_compra.data,
                    data_compra=data_dt
                )
                db.session.add(novo)
                db.session.commit()
                flash("Investimento registrado!", "success")
                return redirect(url_for("investments.investimentos"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro: {e}", "danger")
        else:
            flash("Erro no formulário.", "danger")

    return render_template("investimentos.html", investimentos=lista, categorias_investimento=cats, form=form, nome=current_user.nome)

@investments_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if not inv:
        flash("Não encontrado.", "danger")
        return redirect(url_for("investments.investimentos"))

    form = InvestimentoForm(obj=inv)
    cats = Categoria.query.filter_by(user_id=current_user.id, tipo="investimento").all()

    if request.method == "POST" and form.validate_on_submit():
        try:
            inv.tipo = form.tipo.data
            inv.nome = form.nome.data
            inv.quantidade = form.quantidade.data
            inv.preco_compra = form.preco_compra.data
            if form.data_compra.data:
                inv.data_compra = datetime.combine(form.data_compra.data, datetime.min.time())
            db.session.commit()
            flash("Atualizado!", "success")
            return redirect(url_for("investments.investimentos"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")

    if request.method == "GET" and inv.data_compra:
        form.data_compra.data = inv.data_compra.date()

    return render_template("editar_investimento.html", investimento=inv, categorias_investimento=cats, form=form)

@investments_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_investimento(id):
    inv = Investimento.query.filter_by(id=id, user_id=current_user.id).first()
    if inv:
        db.session.delete(inv)
        db.session.commit()
        flash("Investimento excluído.", "success")
    return redirect(url_for("investments.investimentos"))