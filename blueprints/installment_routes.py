from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from models_finance import Parcela, Categoria, Cartao
from services.parcelas_service import criar_parcelas_a_partir_formulario, pagar_parcela_service

installments_bp = Blueprint('installments', __name__)

@installments_bp.route("/", methods=["GET"])
@login_required
def listar_parcelas():
    parcelas = Parcela.query.filter_by(user_id=current_user.id).order_by(Parcela.data_vencimento.asc()).all()
    categorias = Categoria.query.filter_by(user_id=current_user.id, tipo="saída").order_by(Categoria.nome.asc()).all()
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    return render_template("parcelas.html", parcelas=parcelas, categorias_saida=categorias, cartoes=cartoes)

@installments_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_parcela():
    criar_parcelas_a_partir_formulario(request.form)
    return redirect(url_for("installments.listar_parcelas"))

@installments_bp.route("/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_parcela(id):
    pagar_parcela_service(id)
    return redirect(url_for("installments.listar_parcelas"))