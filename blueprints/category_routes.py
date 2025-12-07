from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models_finance import Categoria, Transacao, Parcela
from forms.categoria_form import CategoriaForm

categories_bp = Blueprint('categories', __name__)

@categories_bp.route("/", methods=["GET", "POST"])
@login_required
def gerenciar_categorias():
    form = CategoriaForm()
    if form.validate_on_submit():
        nome = form.nome.data.strip()
        tipo = form.tipo.data
        icone = form.icone.data or "fa-solid fa-list"
        cor = form.cor.data or "#007bff"

        existente = Categoria.query.filter_by(user_id=current_user.id, nome=nome).first()
        if existente:
            flash(f"A categoria '{nome}' já existe.", "warning")
            return redirect(url_for("categories.gerenciar_categorias"))

        nova = Categoria(user_id=current_user.id, nome=nome, tipo=tipo, icone=icone, cor=cor)
        try:
            db.session.add(nova)
            db.session.commit()
            flash(f"Categoria '{nome}' adicionada!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")
        return redirect(url_for("categories.gerenciar_categorias"))

    categorias = Categoria.query.filter_by(user_id=current_user.id).order_by(Categoria.nome.asc()).all()
    return render_template("categorias.html", categorias=categorias, form=form)

@categories_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()
    if not categoria:
        flash("Categoria não encontrada.", "danger")
        return redirect(url_for("categories.gerenciar_categorias"))

    form = CategoriaForm(obj=categoria)
    if request.method == "POST":
        if not form.validate():
            flash("Erros no formulário.", "danger")
            return render_template("editar_categoria.html", categoria=categoria, form=form)

        novo_nome = form.nome.data.strip()
        if novo_nome != categoria.nome:
            existente = Categoria.query.filter(Categoria.user_id == current_user.id, Categoria.nome == novo_nome, Categoria.id != id).first()
            if existente:
                flash(f"Nome '{novo_nome}' já existe.", "warning")
                return render_template("editar_categoria.html", categoria=categoria, form=form)

        categoria.nome = novo_nome
        categoria.tipo = form.tipo.data
        categoria.icone = form.icone.data or categoria.icone
        categoria.cor = form.cor.data or categoria.cor
        
        try:
            db.session.commit()
            flash("Categoria atualizada!", "success")
            return redirect(url_for("categories.gerenciar_categorias"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")

    return render_template("editar_categoria.html", categoria=categoria, form=form)

@categories_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_categoria(id):
    categoria = Categoria.query.filter_by(id=id, user_id=current_user.id).first()
    if not categoria:
        flash("Categoria não encontrada.", "danger")
        return redirect(url_for("categories.gerenciar_categorias"))

    vinculos = Transacao.query.filter_by(categoria_id=id).count() + Parcela.query.filter_by(categoria_id=id).count()
    if vinculos > 0:
        flash(f"Impossível excluir. Possui {vinculos} vínculos.", "danger")
        return redirect(url_for("categories.gerenciar_categorias"))

    try:
        db.session.delete(categoria)
        db.session.commit()
        flash("Categoria excluída.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for("categories.gerenciar_categorias"))