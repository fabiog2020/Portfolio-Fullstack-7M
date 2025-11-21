# forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="E-mail inválido."),
        ],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe sua senha."),
            Length(min=6, max=128, message="A senha deve ter pelo menos 6 caracteres."),
        ],
    )
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[DataRequired(message="Informe seu nome.")],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="E-mail inválido."),
        ],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe uma senha."),
            Length(min=6, max=128, message="A senha deve ter pelo menos 6 caracteres."),
        ],
    )
    submit = SubmitField("Cadastrar")
