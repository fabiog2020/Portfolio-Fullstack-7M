import calendar
import uuid # <--- Importante para gerar o ID único
from datetime import date, datetime

from flask import flash
from flask_login import current_user

from database import db
from models import Categoria, Parcela, Transacao

def criar_parcelas_a_partir_formulario(form_data):
    # 1. Normalização
    def get_val(key):
        if hasattr(form_data, key): return getattr(form_data, key).data
        return form_data.get(key)

    descricao = get_val("descricao")
    valor_total_str = str(get_val("valor_total"))
    num_parcelas_str = str(get_val("num_parcelas"))
    data_primeira_str = str(get_val("data_vencimento_primeira"))
    categoria_id_str = str(get_val("categoria_id"))
    cartao_id_str = str(get_val("cartao_id")) if get_val("cartao_id") else None

    try:
        valor_total = float(valor_total_str)
        num_parcelas = int(num_parcelas_str)
        categoria_id = int(categoria_id_str)
        cartao_id = int(cartao_id_str) if cartao_id_str and cartao_id_str.isdigit() else None
        
        if isinstance(get_val("data_vencimento_primeira"), (date, datetime)):
            data_primeira = get_val("data_vencimento_primeira")
        else:
            data_primeira = date.fromisoformat(data_primeira_str)

        if valor_total <= 0 or num_parcelas <= 0:
            flash("Valores inválidos.", "danger")
            return False

    except (ValueError, TypeError):
        flash("Erro de formato nos dados.", "danger")
        return False

    # 3. Gerar GROUP_ID único para esta série
    group_id = str(uuid.uuid4()) # Ex: '550e8400-e29b-41d4-a716-446655440000'

    valor_parcela = round(valor_total / num_parcelas, 2)
    ajuste = round(valor_total - (valor_parcela * num_parcelas), 2)
    dia_vencimento_inicial = data_primeira.day
    primeira_parcela_id = None

    try:
        for i in range(1, num_parcelas + 1):
            mes_base = data_primeira.month + i - 1
            ano_vencimento = data_primeira.year + (mes_base - 1) // 12
            mes_vencimento = ((mes_base - 1) % 12) + 1
            ultimo_dia_mes = calendar.monthrange(ano_vencimento, mes_vencimento)[1]
            data_vencimento = date(ano_vencimento, mes_vencimento, min(dia_vencimento_inicial, ultimo_dia_mes))

            valor_final = valor_parcela + (ajuste if i == num_parcelas else 0)

            nova_parcela = Parcela(
                group_id=group_id, # <--- Salvando o ID do grupo
                descricao=f"{descricao} ({i}/{num_parcelas})",
                valor=valor_final,
                data_vencimento=data_vencimento,
                categoria_id=categoria_id,
                cartao_id=cartao_id,
                user_id=current_user.id,
                pago=False,
            )
            db.session.add(nova_parcela)
            
            if i == 1:
                db.session.flush()
                primeira_parcela_id = nova_parcela.id

        db.session.commit()
        
        # Auto-pagamento da 1ª se for data passada/hoje
        if primeira_parcela_id and data_primeira <= date.today():
            pagar_parcela_service(primeira_parcela_id, flash_message=False)
            flash(f"Série criada! 1ª parcela paga automaticamente.", "success")
        else:
            flash(f"{num_parcelas} parcelas agendadas.", "success")
            
        return True

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao gerar: {e}", "danger")
        return False

def pagar_parcela_service(parcela_id: int, flash_message=True):
    # ... (MANTENHA A FUNÇÃO PAGAR_PARCELA_SERVICE IGUAL AO QUE JÁ ESTAVA) ...
    # Vou resumir aqui para não ocupar espaço, mas copie do seu arquivo anterior
    # A lógica de pagamento individual não muda.
    parcela = Parcela.query.filter_by(id=parcela_id, user_id=current_user.id).first()
    if not parcela or parcela.pago: return False
    
    try:
        parcela.pago = True
        categoria = db.session.get(Categoria, parcela.categoria_id)
        valor_transacao = -abs(parcela.valor) # Simplificado para saída
        if categoria and categoria.tipo == 'entrada': valor_transacao = abs(parcela.valor)

        transacao = Transacao(
            categoria_id=parcela.categoria_id,
            descricao=f"[Pgto] {parcela.descricao}",
            valor=valor_transacao,
            data_transacao=datetime.combine(parcela.data_vencimento, datetime.min.time()),
            user_id=current_user.id
        )
        db.session.add(transacao)
        db.session.commit()
        if flash_message: flash("Parcela paga!", "success")
        return True
    except Exception:
        db.session.rollback()
        return False

# --- NOVAS FUNÇÕES PARA GERENCIAR SÉRIE ---

def excluir_serie_completa(parcela_id):
    """Exclui TODAS as parcelas que pertencem ao mesmo grupo da parcela informada."""
    parcela_alvo = Parcela.query.get(parcela_id)
    
    if not parcela_alvo or not parcela_alvo.group_id:
        flash("Série não identificada ou parcela avulsa.", "warning")
        return False

    try:
        # Deleta todas com o mesmo group_id e user_id
        num_deletadas = Parcela.query.filter_by(
            group_id=parcela_alvo.group_id, 
            user_id=current_user.id
        ).delete()
        
        db.session.commit()
        flash(f"Série completa excluída ({num_deletadas} parcelas removidas).", "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir série: {e}", "danger")
        return False

def editar_cartao_serie(parcela_id, novo_cartao_id):
    """Atualiza o cartão de crédito de TODA a série."""
    parcela_alvo = Parcela.query.get(parcela_id)
    
    if not parcela_alvo or not parcela_alvo.group_id:
        flash("Série não identificada.", "warning")
        return False

    try:
        Parcela.query.filter_by(
            group_id=parcela_alvo.group_id, 
            user_id=current_user.id
        ).update({"cartao_id": novo_cartao_id})
        
        db.session.commit()
        flash("Cartão atualizado para todas as parcelas da série.", "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao atualizar série: {e}", "danger")
        return False