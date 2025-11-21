# forms/investimento_form.py
from flask_wtf import FlaskForm
from wtforms import DateField, StringField
from wtforms.validators import DataRequired, Length, NumberRange

from .custom_fields import BrazilianFloatField


class InvestimentoForm(FlaskForm):
    tipo = StringField(
        "Tipo de Ativo",
        validators=[
            DataRequired(
                message="Informe o tipo do investimento (ex: Ação, FII, CDB)."
            ),
            Length(max=50, message="O tipo deve ter no máximo 50 caracteres."),
        ],
    )

    nome = StringField(
        "Nome do Ativo",
        validators=[
            DataRequired(message="Informe o nome do ativo (ex: PETR4, HGLG11)."),
            Length(max=100, message="O nome deve ter no máximo 100 caracteres."),
        ],
    )

    quantidade = BrazilianFloatField(
        "Quantidade",
        validators=[
            DataRequired(message="Informe a quantidade."),
            NumberRange(min=0.0001, message="A quantidade deve ser maior que zero."),
        ],
    )

    preco_compra = BrazilianFloatField(
        "Preço de compra (R$)",
        validators=[
            DataRequired(message="Informe o preço de compra."),
            NumberRange(min=0.0, message="O preço não pode ser negativo."),
        ],
    )

    data_compra = DateField(
        "Data da compra",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Informe a data da compra.")],
    )
