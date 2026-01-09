# services/transactions_service.py

from datetime import datetime
from flask import flash, request
from flask_login import current_user
from database import db
from models import Categoria, Transacao
from services.parcelas_service import criar_parcelas_a_partir_formulario

def adicionar_transacao_core(user_id, categoria_id, descricao, valor, data_transacao):
    """
    Função Pura (Core):
    Recebe dados brutos e salva no banco.
    Usada tanto pelo Formulário Manual quanto pela Importação de Extrato.
    """
    try:
        # Verifica categoria
        categoria = db.session.get(Categoria, categoria_id)
        if not categoria or categoria.user_id != user_id:
            return False, "Categoria inválida ou não pertence ao usuário."

        # Ajuste de sinal automático (Entrada positiva, Saída negativa)
        valor_final = valor
        if categoria.tipo != "entrada":
            valor_final = -abs(valor)
        else:
            valor_final = abs(valor)

        nova = Transacao(
            categoria_id=categoria_id,
            descricao=descricao,
            valor=valor_final,
            data_transacao=data_transacao,
            user_id=user_id,
        )

        db.session.add(nova)
        db.session.commit()
        return True, "Transação salva com sucesso."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erro interno ao salvar: {str(e)}"


def criar_transacao_a_partir_formulario(form):
    """
    Controlador (Adapter):
    Pega os dados do HTML/Form e passa para a função Core.
    """
    
    # 1. Obter 'tipo_transacao' do HTML
    tipo = request.form.get('tipo_transacao', 'unico')

    # --- FLUXO DE PARCELAMENTO/RECORRÊNCIA (Mantém lógica existente) ---
    if tipo in ['parcelado', 'recorrente']:
        valor_original = float(form.valor.data)
        dados_adaptados = {
            "descricao": form.descricao.data,
            "data_vencimento_primeira": str(form.data.data),
            "categoria_id": str(form.categoria_id.data), 
            "cartao_id": request.form.get('cartao_id', ''), 
        }

        if tipo == 'parcelado':
            dados_adaptados["valor_total"] = str(valor_original)
            dados_adaptados["num_parcelas"] = request.form.get('num_parcelas')
        else: 
            meses_str = request.form.get('meses_recorrencia')
            meses = 12 if not meses_str or int(meses_str) < 2 else int(meses_str)
            valor_total_calculado = valor_original * meses
            dados_adaptados["valor_total"] = str(valor_total_calculado)
            dados_adaptados["num_parcelas"] = str(meses)
            dados_adaptados["descricao"] += " (Recorrente)"

        return criar_parcelas_a_partir_formulario(dados_adaptados)

    # --- FLUXO PADRÃO: TRANSAÇÃO ÚNICA (Agora usa o Core) ---
    try:
        categoria_id = int(request.form.get('categoria_id'))
    except (TypeError, ValueError):
        flash("Categoria inválida.", "danger")
        return False

    descricao = form.descricao.data
    valor = form.valor.data
    data_python = form.data.data # Date object

    if valor is None or data_python is None:
        flash("Valor e Data são obrigatórios.", "danger")
        return False

    # Converte date para datetime
    data_transacao = datetime.combine(data_python, datetime.min.time())

    # CHAMA A FUNÇÃO CORE QUE CRIAMOS ACIMA
    sucesso, mensagem = adicionar_transacao_core(
        user_id=current_user.id,
        categoria_id=categoria_id,
        descricao=descricao,
        valor=valor,
        data_transacao=data_transacao
    )

    if sucesso:
        flash("Transação adicionada com sucesso!", "success")
        return True
    else:
        flash(mensagem, "danger")
        return False