# app.py

import logging
import sys
from factory import create_app
from database import db

# ==========================================================
# CONFIGURAÇÃO DE LOGS (Boas Práticas)
# ==========================================================
# Configura logs para sair no console (stdout).
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==========================================================
# INICIALIZAÇÃO
# ==========================================================
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Cria as tabelas se não existirem (ideal para dev rápido)
        # Em produção, confie nas migrações do Alembic.
        db.create_all()
        logger.info("Sistema inicializado. Banco de dados verificado.")

    logger.info("Iniciando servidor Flask na porta 5000...")
    app.run(debug=True)