# app.py

from factory import create_app
from database import db, login_manager # Importamos o login_manager aqui
from models import User

# Cria a aplicação usando a fábrica
app = create_app()

# ==========================================================
# CONFIGURAÇÃO OBRIGATÓRIA DO FLASK-LOGIN
# ==========================================================
# Esta função diz ao Flask-Login como encontrar um usuário pelo ID
@login_manager.user_loader
def load_user(user_id):
    # Usa o Session.get (sintaxe moderna do SQLAlchemy)
    return db.session.get(User, int(user_id))

# ==========================================================
# EXECUÇÃO DA APLICAÇÃO
# ==========================================================
if __name__ == "__main__":
    # Garante que as tabelas existam ao rodar localmente
    with app.app_context():
        db.create_all()
    app.run(debug=True)