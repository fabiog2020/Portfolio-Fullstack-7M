from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from models import Parcela, Categoria, Cartao
from services.parcelas_service import (
    criar_parcelas_a_partir_formulario, 
    pagar_parcela_service, 
    excluir_serie_completa,  # <--- Nova
    editar_cartao_serie      # <--- Nova
)

installments_bp = Blueprint('installments', __name__)

# ... (rotas listar_parcelas e adicionar_parcela mantêm iguais) ...
@installments_bp.route("/", methods=["GET"])
@login_required
def listar_parcelas():
    parcelas = Parcela.query.filter_by(user_id=current_user.id).order_by(Parcela.data_vencimento.asc()).all()
    categorias_saida = Categoria.query.filter_by(user_id=current_user.id, tipo="saída").order_by(Categoria.nome.asc()).all()
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    return render_template("parcelas.html", parcelas=parcelas, categorias_saida=categorias_saida, cartoes=cartoes)

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

# --- NOVAS ROTAS ---

@installments_bp.route("/excluir_serie/<int:id>", methods=["POST"])
@login_required
def excluir_serie(id):
    """Exclui todas as parcelas vinculadas a este ID."""
    excluir_serie_completa(id)
    return redirect(url_for("installments.listar_parcelas"))

@installments_bp.route("/editar_cartao_serie/<int:id>", methods=["POST"])
@login_required
def editar_cartao(id):
    """Altera o cartão da série."""
    novo_cartao_id = request.form.get("novo_cartao_id")
    if not novo_cartao_id:
        # Se for vazio, remove o cartão (None)
        novo_cartao_id = None 
    
    editar_cartao_serie(id, novo_cartao_id)
    return redirect(url_for("installments.listar_parcelas"))