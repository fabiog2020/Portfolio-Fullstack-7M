# factory.py

import os
from flask import Flask
from config import DevConfig
from database import db, login_manager
from tools.cli_commands import register_cli_commands

# Importa o Blueprint
from blueprints.auth_routes import auth_bp

def hex_to_rgb(hex_color):
    """Converte uma cor hexadecimal (#RRGGBB) para uma tupla RGB (R, G, B)."""
    cor_padrao = (108, 117, 125)
    try:
        hex_color = str(hex_color).lstrip("#")
        if len(hex_color) == 3:
            hex_color = hex_color[0] * 2 + hex_color[1] * 2 + hex_color[2] * 2
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Erro ao converter cor {hex_color}: {e}")
        return cor_padrao

def create_app(config_class=DevConfig):
    """Fábrica de Aplicação: Inicializa e configura a instância do Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        register_cli_commands(app)

    # ==========================
    # REGISTRO DE BLUEPRINTS
    # ==========================
    # Define que todas as rotas de auth começam com /auth
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.context_processor
    def utility_processor():
        return dict(hex_to_rgb=hex_to_rgb)

    return app