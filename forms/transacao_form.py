# forms/transacao_form.py
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, DateField
from wtforms.validators import DataRequired, Length, NumberRange
from .custom_fields import BrazilianFloatField


class TransacaoForm(FlaskForm):
    categoria_id = IntegerField(
        "Categoria",
        validators=[DataRequired(message="Selecione uma categoria.")]
    )

    descricao = StringField(
        "Descrição",
        validators=[
            DataRequired(message="Informe uma descrição."),
            Length(max=120, message="A descrição deve ter no máximo 120 caracteres."),
        ],
    )

    valor = BrazilianFloatField(
        "Valor (R$)",
        validators=[
            DataRequired(message="Informe um valor."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
    )

    data = DateField(
        "Data da Transação",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Informe a data da transação.")],
    )
