# factory.py
import os
from flask import Flask
from config import DevConfig
from database import db, login_manager
from tools.cli_commands import register_cli_commands

# Importa TODOS os Blueprints
from blueprints.auth_routes import auth_bp
from blueprints.main_routes import main_bp
from blueprints.transaction_routes import transactions_bp
from blueprints.category_routes import categories_bp
from blueprints.card_routes import cards_bp
from blueprints.installment_routes import installments_bp
from blueprints.investment_routes import investments_bp
from blueprints.report_routes import reports_bp

def hex_to_rgb(hex_color):
    """Converte #RRGGBB para (R, G, B)."""
    cor_padrao = (108, 117, 125)
    try:
        hex_color = str(hex_color).lstrip("#")
        if len(hex_color) == 3: hex_color = "".join([c*2 for c in hex_color])
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    except Exception:
        return cor_padrao

def create_app(config_class=DevConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    try: os.makedirs(app.instance_path, exist_ok=True)
    except OSError: pass

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        register_cli_commands(app)

    # REGISTRO DOS BLUEPRINTS
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) # Sem prefixo (home/dashboard)
    app.register_blueprint(transactions_bp, url_prefix='/transacoes') # /transacoes/adicionar
    app.register_blueprint(categories_bp, url_prefix='/categorias')
    app.register_blueprint(cards_bp, url_prefix='/cartoes')
    app.register_blueprint(installments_bp, url_prefix='/parcelas')
    app.register_blueprint(investments_bp, url_prefix='/investimentos')
    app.register_blueprint(reports_bp) # Sem prefixo ou /relatorios se preferir

    @app.context_processor
    def utility_processor():
        return dict(hex_to_rgb=hex_to_rgb)

    return app