from datetime import datetime

from flask import flash
from flask_login import current_user

from database import db
from models_finance import Categoria, Transacao

# Opcional: só para tipo de anotação, não é obrigatório
# from forms.transacao_form import TransacaoForm


def criar_transacao_a_partir_formulario(form):
    """
    Recebe um TransacaoForm já validado (WTForms),
    faz validações de negócio e cria a transação no banco.

    Retorna:
        True  -> se deu tudo certo
        False -> se houve algum erro de validação de negócio
    """

    # 1. Lê os dados já convertidos/validados pelo WTForms
    categoria_id = form.categoria_id.data
    descricao = form.descricao.data
    valor = form.valor.data
    data_python = form.data.data  # objeto date do Python

    # 1.1. Validações defensivas adicionais (evitam erros silenciosos caso o form mude)
    if categoria_id is None:
        flash("Categoria não informada.", "danger")
        return False

    if valor is None:
        flash("Valor da transação é obrigatório.", "danger")
        return False

    if data_python is None:
        flash("Data da transação é obrigatória.", "danger")
        return False

    # 2. Verifica se a categoria existe e pertence ao usuário logado
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria or categoria.user_id != current_user.id:
        flash("Categoria inválida ou não encontrada.", "danger")
        return False

    # 3. Converte a data (date) para datetime (modelo Transacao usa DateTime)
    data_transacao = datetime.combine(data_python, datetime.min.time())

    # 4. Cria a transação
    nova = Transacao(
        categoria_id=categoria_id,
        descricao=descricao,
        # Se a categoria for de 'saída', o valor fica negativo
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
        flash(f"Erro ao salvar a transação: {e}", "danger")
        return False
