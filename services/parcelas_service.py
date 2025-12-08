import calendar
from datetime import date, datetime

from flask import flash
from flask_login import current_user

from database import db
from models import Categoria, Parcela, Transacao


def criar_parcelas_a_partir_formulario(form):
    """
    Lê os dados do formulário de parcelas, valida e cria as parcelas no banco.

    Retorna:
        True  -> se deu tudo certo
        False -> se houve algum erro
    """
    # 1. Obter dados do formulário
    descricao = form.get("descricao")
    valor_total_str = form.get("valor_total")
    num_parcelas_str = form.get("num_parcelas")
    data_primeira_str = form.get("data_vencimento_primeira")
    categoria_id_str = form.get("categoria_id")
    cartao_id_str = form.get("cartao_id")

    # 2. Conversão e validação básica
    try:
        valor_total = float(valor_total_str)
        num_parcelas = int(num_parcelas_str)
        categoria_id = int(categoria_id_str)
        cartao_id = int(cartao_id_str) if cartao_id_str else None
        data_primeira = date.fromisoformat(data_primeira_str)

        if valor_total <= 0 or num_parcelas <= 0 or num_parcelas > 60:
            flash(
                "Verifique o valor total e o número de parcelas (máx. 60).",
                "danger",
            )
            return False

    except (ValueError, TypeError):
        flash(
            "Erro de formato nos dados (Valor Total, Parcelas, Categoria ou Data).",
            "danger",
        )
        return False

    # 3. Verificar se categoria é válida e de saída
    categoria = Categoria.query.filter_by(
        id=categoria_id, user_id=current_user.id
    ).first()
    if not categoria or categoria.tipo != "saída":
        flash(
            "Categoria inválida ou não é uma categoria de Despesa.",
            "danger",
        )
        return False

    # 4. Cálculo das parcelas
    valor_parcela = round(valor_total / num_parcelas, 2)
    ajuste = round(valor_total - (valor_parcela * num_parcelas), 2)
    dia_vencimento_inicial = data_primeira.day

    try:
        for i in range(1, num_parcelas + 1):
            # Calcula mês e ano da parcela i
            mes_base = data_primeira.month + i - 1
            ano_vencimento = data_primeira.year

            while mes_base > 12:
                mes_base -= 12
                ano_vencimento += 1
            mes_vencimento = mes_base

            # Tenta criar a data, ajustando se o dia não existir (31/02 etc.)
            try:
                data_vencimento = date(
                    ano_vencimento, mes_vencimento, dia_vencimento_inicial
                )
            except ValueError:
                ultimo_dia_mes = calendar.monthrange(ano_vencimento, mes_vencimento)[1]
                data_vencimento = date(ano_vencimento, mes_vencimento, ultimo_dia_mes)

            # Ajuste da última parcela para fechar o total
            valor_final_parcela = valor_parcela
            if i == num_parcelas:
                valor_final_parcela += ajuste

            nova_parcela = Parcela(
                descricao=f"{descricao} ({i}/{num_parcelas})",
                valor=valor_final_parcela,
                data_vencimento=data_vencimento,
                categoria_id=categoria_id,
                cartao_id=cartao_id,
                user_id=current_user.id,
                pago=False,
            )
            db.session.add(nova_parcela)

        db.session.commit()
        flash(
            f"{num_parcelas} parcelas adicionadas com sucesso para '{descricao}'!",
            "success",
        )
        return True

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao gerar as parcelas: {e}", "danger")
        return False


def pagar_parcela_service(parcela_id: int):
    """
    Marca uma parcela como paga e gera a Transacao correspondente.

    Retorna:
        True  -> se deu tudo certo
        False -> se houve algum erro
    """
    parcela = Parcela.query.filter_by(id=parcela_id, user_id=current_user.id).first()

    if not parcela:
        flash(
            "Parcela não encontrada ou você não tem permissão.",
            "danger",
        )
        return False

    if parcela.pago:
        flash("Esta parcela já estava marcada como paga.", "warning")
        return False

    try:
        # Marca como paga
        parcela.pago = True

        # Recupera a categoria para validar
        categoria = Categoria.query.get(parcela.categoria_id)
        if not categoria:
            flash(
                "Erro: Categoria da parcela não encontrada. "
                "A Transação Realizada não pôde ser criada.",
                "danger",
            )
            parcela.pago = False
            db.session.rollback()
            return False

        # Cria a transação de saída (valor negativo)
        transacao_realizada = Transacao(
            categoria_id=parcela.categoria_id,
            descricao=f"[PAGO] {parcela.descricao}",
            valor=-abs(parcela.valor),  # garante valor negativo
            # aqui usamos datetime (modelo Transacao usa DateTime)
            data_transacao=datetime.now(),
            user_id=current_user.id,
        )

        db.session.add(transacao_realizada)
        db.session.commit()

        flash(
            f"Parcela '{parcela.descricao}' marcada como paga e "
            "Transação de Saída gerada!",
            "success",
        )
        return True

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao processar o pagamento da parcela: {e}", "danger")
        return False
