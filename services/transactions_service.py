from datetime import datetime
from flask import flash
from flask_login import current_user

from database import db
from models_finance import Transacao, Categoria


def criar_transacao_a_partir_formulario(form):
    """
    Lê os dados do formulário, valida e cria uma nova transação no banco.

    Retorna:
        True  -> se deu tudo certo
        False -> se houve algum erro de validação
    """
    # 1. Obter dados do formulário
    categoria_id_str = form.get("categoria_id")
    descricao = form.get("descricao")
    valor_str = form.get("valor")
    data_str = form.get("data")  # Exemplo: "2025-11-09"

    try:
        # 2. VALIDAÇÃO E CONVERSÃO
        categoria_id = int(categoria_id_str)

        # Verifica se a categoria existe e pertence ao usuário logado
        categoria = Categoria.query.get(categoria_id)
        if not categoria or categoria.user_id != current_user.id:
            flash("Categoria inválida ou não encontrada.", "danger")
            return False

        # Converte o valor para float
        valor = float(valor_str)

        # Converte a data. Aqui aceitamos datas no passado/presente/futuro
        data_transacao = datetime.fromisoformat(data_str)

    except (ValueError, TypeError) as e:
        flash(
            f"Erro de formato nos dados. Verifique a categoria, valor e data: {e}",
            "danger",
        )
        return False

    # 3. CRIAÇÃO E SALVAMENTO DA TRANSAÇÃO
    nova = Transacao(
        categoria_id=categoria_id,
        descricao=descricao,
        # Se a categoria for de 'saída', o valor fica negativo
        valor=valor if categoria.tipo == "entrada" else -abs(valor),
        data_transacao=data_transacao,
        user_id=current_user.id,
    )

    db.session.add(nova)
    db.session.commit()

    flash("Transação adicionada com sucesso!", "success")
    return True
