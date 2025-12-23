# forms/investimento_form.py
from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from .custom_fields import BrazilianFloatField

class InvestimentoForm(FlaskForm):
    # --- CAMPO DECISOR ---
    classe = SelectField(
        "Classe do Ativo",
        choices=[('Variavel', 'Renda Variável (Ações, FIIs, Crypto)'), ('Fixa', 'Renda Fixa (CDB, LCI, Tesouro)')],
        validators=[DataRequired()],
        default='Variavel'
    )
    
    # Campos Gerais
    tipo = StringField("Tipo (Ex: Ação, CDB)", validators=[DataRequired(), Length(max=50)])
    nome = StringField("Nome/Descrição", validators=[DataRequired(), Length(max=100)])
    
    # Renda Variável
    ticker = StringField("Ticker (Ex: PETR4)", validators=[Optional(), Length(max=20)])

    # Renda Fixa
    indice = SelectField(
        "Índice",
        choices=[('', 'Selecione...'), ('PRE', 'Pré-fixado'), ('CDI', 'CDI'), ('IPCA', 'IPCA')],
        validators=[Optional()]
    )
    taxa_contratada = BrazilianFloatField("Taxa (%)", validators=[Optional()])
    data_vencimento = DateField("Vencimento", format="%Y-%m-%d", validators=[Optional()])

    # Valores
    quantidade = BrazilianFloatField("Quantidade", validators=[DataRequired()])
    preco_compra = BrazilianFloatField("Valor Investido / Preço Compra", validators=[DataRequired()])
    data_compra = DateField("Data da Aplicação", format="%Y-%m-%d", validators=[DataRequired()])