from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Meta
from forms.meta_form import MetaForm

metas_bp = Blueprint('metas', __name__)

@metas_bp.route("/", methods=["GET"])
@login_required
def listar_metas():
    metas = Meta.query.filter_by(user_id=current_user.id).order_by(Meta.data_limite.asc()).all()
    form = MetaForm() # Instância vazia para o modal de criação
    return render_template("metas.html", metas=metas, form=form)

@metas_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_meta():
    form = MetaForm()
    if form.validate_on_submit():
        nova_meta = Meta(
            user_id=current_user.id,
            nome=form.nome.data,
            valor_alvo=form.valor_alvo.data,
            data_limite=form.data_limite.data,
            cor=form.cor.data,
            valor_atual=0.0 # Começa zerada
        )
        db.session.add(nova_meta)
        db.session.commit()
        flash(f"Meta '{nova_meta.nome}' criada com sucesso!", "success")
    else:
        flash("Erro ao criar meta. Verifique os dados.", "danger")
    
    return redirect(url_for("metas.listar_metas"))

@metas_bp.route("/aportar/<int:id>", methods=["POST"])
@login_required
def aportar_meta(id):
    """Adiciona um valor ao saldo atual da meta."""
    meta = db.session.get(Meta, id)
    if not meta or meta.user_id != current_user.id:
        flash("Meta não encontrada.", "danger")
        return redirect(url_for("metas.listar_metas"))

    valor = request.form.get("valor_aporte")
    try:
        valor_float = float(valor)
        if valor_float <= 0:
            raise ValueError
        
        meta.valor_atual += valor_float
        
        # Verifica se concluiu
        if meta.valor_atual >= meta.valor_alvo and not meta.concluida:
            meta.concluida = True
            flash(f"Parabéns! Você atingiu a meta '{meta.nome}'! 🎉", "success")
        else:
            flash(f"Aporte de R$ {valor} realizado!", "success")
            
        db.session.commit()
    except (ValueError, TypeError):
        flash("Valor inválido.", "danger")

    return redirect(url_for("metas.listar_metas"))

@metas_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_meta(id):
    meta = db.session.get(Meta, id)
    if meta and meta.user_id == current_user.id:
        db.session.delete(meta)
        db.session.commit()
        flash("Meta excluída.", "success")
    return redirect(url_for("metas.listar_metas"))