from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DateField, IntegerField, StringField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from .custom_fields import BrazilianFloatField

class TransacaoForm(FlaskForm):
    # ==============================
    # ÁREA DE IMPORTAÇÃO
    # ==============================
    arquivo = FileField(
        "Importar Extrato",
        validators=[
            Optional(),
            FileAllowed(['ofx', 'csv', 'pdf'], 'Apenas arquivos OFX, CSV ou PDF são permitidos!')
        ]
    )
    
    senha_pdf = StringField(
        "Senha do PDF",
        validators=[Optional()]
    )

    # Novo Campo: Escolher Cartão para a Importação
    # (0 = Conta Corrente, >0 = ID do Cartão)
    cartao_import_id = SelectField(
        "Vincular ao Cartão (Opcional)", 
        choices=[], 
        coerce=int, 
        validate_choice=False # Validamos manualmente na rota
    )

    # ==============================
    # ÁREA MANUAL E DADOS GERAIS
    # ==============================
    
    # Categoria é obrigatória para ambos os casos
    categoria_id = IntegerField(
        "Categoria", 
        validators=[DataRequired(message="Selecione uma categoria.")]
    )

    descricao = StringField(
        "Descrição",
        validators=[
            Optional(), 
            Length(max=120, message="A descrição deve ter no máximo 120 caracteres."),
        ],
    )

    valor = BrazilianFloatField(
        "Valor (R$)",
        validators=[
            Optional(),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
    )

    data = DateField(
        "Data da Transação",
        format="%Y-%m-%d",
        validators=[Optional()],
    )
