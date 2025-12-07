# database.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Cria o objeto SQLAlchemy. Ele será inicializado em app.py
db = SQLAlchemy()

# Instancia o LoginManager (Movido do app.py para evitar ciclos)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"