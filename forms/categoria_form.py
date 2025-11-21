# forms/categoria_form.py
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, Length


class CategoriaForm(FlaskForm):
    nome = StringField(
        "Nome da Categoria",
        validators=[
            DataRequired(message="Informe o nome da categoria."),
            Length(max=100, message="O nome deve ter no máximo 100 caracteres."),
        ],
    )

    tipo = SelectField(
        "Tipo",
        choices=[
            ("entrada", "Entrada(Receita)"),
            ("saída", "Saída(Despesa)"),
            ("investimento", "Investimento"),
        ],
        validators=[DataRequired(message="Selecione o tipo da categoria.")],
    )

    icone = StringField(
        "Ícone (Font Awesome)",
        validators=[
            Length(max=50, message="O ícone deve ter no máximo 50 caracteres."),
        ],
    )

    cor = StringField(
        "Cor (hex)",
        validators=[
            Length(max=7, message="A cor deve ter no máximo 7 caracteres."),
        ],
    )
