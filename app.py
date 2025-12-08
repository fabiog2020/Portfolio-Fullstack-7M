# app.py
from factory import create_app
from database import db

# Cria a aplicação usando a fábrica (que já configura o user_loader)
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)