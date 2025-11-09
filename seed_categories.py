# seed_categories.py

import os
import sys
from sqlalchemy import select

# O Flask app.py e models_finance.py estão no mesmo diretório
# Adicionamos o diretório atual ao path para garantir que a importação de 'app' e 'models_finance' funcione
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importamos o objeto 'app' para ter acesso à configuração do Flask
from app import app, db
from models_finance import Categoria

# Definimos os tipos de transação como strings simples (como definido no modelo Categoria)
ENTRADA = "entrada"
SAIDA = "saída"


def seed_categories():
    """Popula o banco de dados com categorias e subcategorias hierárquicas."""
    
    # 1. ENTRAR NO CONTEXTO DA APLICAÇÃO
    # Usamos o contexto para acessar o banco de dados configurado no app.py
    with app.app_context():
        
        print("--- Iniciando Seeding de Categorias ---")

        # 2. VERIFICAÇÃO DE EXISTÊNCIA (IDEMPOTÊNCIA)
        # Verifica se já existe alguma categoria para evitar duplicação
        if Categoria.query.first():
            print("Categorias já existentes no banco de dados. Pulando o Seeding.")
            return

        # 3. CRIAÇÃO DAS CATEGORIAS PAI (Root)
        # Estas categorias não têm parent_id
        categoria_saidas = Categoria(nome="Saídas", tipo=SAIDA, descricao="Todas as despesas")
        categoria_entradas = Categoria(nome="Entradas", tipo=ENTRADA, descricao="Todas as receitas")

        # Adicionar e Commitar as Categorias PAI
        # É NECESSÁRIO commitar agora para que elas recebam seu ID (primary key)
        db.session.add_all([categoria_saidas, categoria_entradas])
        db.session.commit()

        print(f"Pais criados: Saídas (ID: {categoria_saidas.id}) e Entradas (ID: {categoria_entradas.id})")

        # 4. CRIAÇÃO DAS SUBCATEGORIAS (Filhas)
        # Usamos os IDs gerados no commit anterior para ligar o parent_id
        subcategorias = [
            # SAÍDAS
            Categoria(nome="Aluguel", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Energia Elétrica", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Agua", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Internet/Streaming", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Supermercado", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Restaurante/Lanche", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Transporte Público/Uber", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Combustível", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Manutenção Veicular", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Hospital/Plano de Saúde", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Farmacia", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Educação/Cursos", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Lazer/viagens", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Manutenção Residencial", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Contabilidade", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Mei/Cnpj", tipo=SAIDA, parent_id=categoria_saidas.id),
            Categoria(nome="Investimentos", tipo=SAIDA, parent_id=categoria_saidas.id),
            
            # ENTRADAS
            Categoria(nome="Salário", tipo=ENTRADA, parent_id=categoria_entradas.id),
            Categoria(nome="Rendimentos de Investimento", tipo=ENTRADA, parent_id=categoria_entradas.id),
            Categoria(nome="Freelance/Extra", tipo=ENTRADA, parent_id=categoria_entradas.id),
        ]

        # 5. Adicionar e Commitar Subcategorias
        db.session.add_all(subcategorias)
        db.session.commit()

        print("Subcategorias criadas com sucesso!")
        print("--- Seeding Concluído ---")


if __name__ == "__main__":
    seed_categories()