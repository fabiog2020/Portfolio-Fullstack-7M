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
        # Montamos um dicionário com os dados misturados para o serviço de parcelas
        dados_adaptados = {
            "descricao": form.descricao.data,
            "valor_total": str(form.valor.data), # Convertendo para string pois o serviço espera string ou float
            "data_vencimento_primeira": str(form.data.data),
            "categoria_id": str(form.categoria_id.data), # Pega o ID selecionado no select manual
            "cartao_id": request.form.get('cartao_id', ''), # Campo manual
        }

        if tipo == 'parcelado':
            dados_adaptados["num_parcelas"] = request.form.get('num_parcelas')
        else:
            # Recorrente: usa o input de meses ou define 12 como padrão
            meses = request.form.get('meses_recorrencia') or '12'
            dados_adaptados["num_parcelas"] = meses
            dados_adaptados["descricao"] += " (Recorrente)"

        # Chama o serviço de parcelas com o dicionário
        return criar_parcelas_a_partir_formulario(dados_adaptados)

    # --- FLUXO PADRÃO: TRANSAÇÃO ÚNICA ---
    
    # Validação dos dados do Form
    # O campo categoria_id é um select manual no HTML, então form.categoria_id.data pode vir vazio se o WTForms não validar.
    # Vamos garantir pegando do request se necessário.
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