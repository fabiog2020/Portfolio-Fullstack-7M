from datetime import datetime
from flask import flash, request
from flask_login import current_user
from database import db
from models import Categoria, Transacao
# Importa o serviço de parcelas para delegar se for o caso
from services.parcelas_service import criar_parcelas_a_partir_formulario

def criar_transacao_a_partir_formulario(form):
    """
    Controlador mestre de criação.
    Lê dados híbridos: alguns do objeto form (WTForms) e outros do request.form (HTML manual).
    """
    
    # 1. Obter 'tipo_transacao'
    # Como esse campo é um hidden input manual no HTML, ele não está no objeto 'form' do WTForms.
    # Precisamos pegar direto do request do Flask.
    tipo = request.form.get('tipo_transacao', 'unico')

    # --- DESVIO DE FLUXO: PARCELADO OU RECORRENTE ---
    if tipo in ['parcelado', 'recorrente']:
        
        # Pega o valor original digitado pelo usuário
        valor_original = float(form.valor.data)

        # Montamos um dicionário base
        dados_adaptados = {
            "descricao": form.descricao.data,
            "data_vencimento_primeira": str(form.data.data),
            "categoria_id": str(form.categoria_id.data), 
            "cartao_id": request.form.get('cartao_id', ''), 
        }

        if tipo == 'parcelado':
            # Parcelado: O valor digitado É o valor total
            dados_adaptados["valor_total"] = str(valor_original)
            dados_adaptados["num_parcelas"] = request.form.get('num_parcelas')
        
        else: # Recorrente
            # Recorrente: O valor digitado é o valor MENSAL.
            # O serviço de parcelas vai dividir o total pela quantidade.
            # Então, multiplicamos agora para que a divisão resulte no valor mensal correto.
            
            meses_str = request.form.get('meses_recorrencia')
            # Se vier vazio ou 0, assumimos 12 meses por segurança
            if not meses_str or int(meses_str) < 2:
                meses = 12
            else:
                meses = int(meses_str)

            valor_total_calculado = valor_original * meses
            
            dados_adaptados["valor_total"] = str(valor_total_calculado)
            dados_adaptados["num_parcelas"] = str(meses)
            dados_adaptados["descricao"] += " (Recorrente)"

        # Chama o serviço de parcelas com o dicionário ajustado
        return criar_parcelas_a_partir_formulario(dados_adaptados)

    # --- FLUXO PADRÃO: TRANSAÇÃO ÚNICA ---
    
    # Validação dos dados do Form
    try:
        categoria_id = int(request.form.get('categoria_id'))
    except (TypeError, ValueError):
        flash("Categoria inválida.", "danger")
        return False

    descricao = form.descricao.data
    valor = form.valor.data
    data_python = form.data.data

    if valor is None or data_python is None:
        flash("Valor e Data são obrigatórios.", "danger")
        return False

    # Verifica categoria
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria or categoria.user_id != current_user.id:
        flash("Categoria não encontrada.", "danger")
        return False

    # Converte data
    data_transacao = datetime.combine(data_python, datetime.min.time())

    nova = Transacao(
        categoria_id=categoria_id,
        descricao=descricao,
        # Se for saída/investimento é negativo, entrada é positivo
        valor=valor if categoria.tipo == "entrada" else -abs(valor),
        data_transacao=data_transacao,
        user_id=current_user.id,
    )

    try:
        db.session.add(nova)
        db.session.commit()
        flash("Transação adicionada com sucesso!", "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao salvar: {e}", "danger")
        return False