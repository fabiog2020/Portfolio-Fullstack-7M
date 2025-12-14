from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class MetaForm(FlaskForm):
    nome = StringField("Nome da Meta", validators=[DataRequired(), Length(max=100)])
    valor_alvo = FloatField("Valor Alvo (R$)", validators=[DataRequired(), NumberRange(min=0.01)])
    # Data limite é opcional, pois a meta pode ser "para a vida toda"
    data_limite = DateField("Data Limite", validators=[Optional()])
    
    # Cores baseadas nas classes do Tailwind que usamos no Dashboard
    cor = SelectField("Cor do Card", choices=[
        ('bg-blue-500', 'Azul'),
        ('bg-green-500', 'Verde'),
        ('bg-purple-500', 'Roxo'),
        ('bg-red-500', 'Vermelho'),
        ('bg-yellow-500', 'Amarelo'),
        ('bg-pink-500', 'Rosa'),
        ('bg-indigo-500', 'Índigo'),
        ('bg-orange-500', 'Laranja'),
        ('bg-teal-500', 'Verde Água')
    ], default='bg-blue-500')