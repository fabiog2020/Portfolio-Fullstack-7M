# tools/cli_commands.py

import click
from flask.cli import with_appcontext

from database import db
from models import User, Categoria

# ==========================================================
# 1. CONSTANTES
# ==========================================================
ENTRADA = "entrada"
SAIDA = "saída"
INVESTIMENTO = "investimento"  # <--- NOVO

# ==========================================================
# 2. DADOS DE SEED
# ==========================================================
CATEGORIAS_A_SEMEAR = [
    # --- GERAL (Pais) ---
    {
        "nome": "Receitas (Geral)",
        "tipo": ENTRADA,
        "icone": "fa-sack-dollar",
        "cor": "#4CAF50",
        "parent_ref": None,
    },
    {
        "nome": "Despesas (Geral)",
        "tipo": SAIDA,
        "icone": "fa-minus",
        "cor": "#F44336",
        "parent_ref": None,
    },
    {   # <--- NOVO PAI PARA INVESTIMENTOS
        "nome": "Carteira de Ativos",
        "tipo": INVESTIMENTO,
        "icone": "fa-chart-pie",
        "cor": "#2196F3",
        "parent_ref": None,
    },

    # --- FILHAS (SAIDAS) ---
    {
        "nome": "Aluguel",
        "tipo": SAIDA,
        "icone": "fa-house",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Energia Elétrica",
        "tipo": SAIDA,
        "icone": "fa-bolt",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Água",
        "tipo": SAIDA,
        "icone": "fa-droplet",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Internet/Streaming",
        "tipo": SAIDA,
        "icone": "fa-video",
        "cor": "#F44336",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Supermercado",
        "tipo": SAIDA,
        "icone": "fa-cart-shopping",
        "cor": "#FF9800",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Restaurante/Lanche",
        "tipo": SAIDA,
        "icone": "fa-burger",
        "cor": "#FF9800",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Transporte Público/Uber",
        "tipo": SAIDA,
        "icone": "fa-train",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Combustível",
        "tipo": SAIDA,
        "icone": "fa-gas-pump",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Manutenção Veicular",
        "tipo": SAIDA,
        "icone": "fa-car-wrench",
        "cor": "#2196F3",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Hospital/Plano de Saúde",
        "tipo": SAIDA,
        "icone": "fa-suitcase-medical",
        "cor": "#00BCD4",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Farmácia",
        "tipo": SAIDA,
        "icone": "fa-pills",
        "cor": "#00BCD4",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Educação/Cursos",
        "tipo": SAIDA,
        "icone": "fa-graduation-cap",
        "cor": "#673AB7",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Lazer/Viagens",
        "tipo": SAIDA,
        "icone": "fa-plane",
        "cor": "#E91E63",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Manutenção Residencial",
        "tipo": SAIDA,
        "icone": "fa-screwdriver-wrench",
        "cor": "#9E9E9E",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "Contabilidade",
        "tipo": SAIDA,
        "icone": "fa-calculator",
        "cor": "#9C27B0",
        "parent_ref": "Despesas (Geral)",
    },
    {
        "nome": "MEI/CNPJ",
        "tipo": SAIDA,
        "icone": "fa-building",
        "cor": "#9C27B0",
        "parent_ref": "Despesas (Geral)",
    },
    {
        # Categoria de SAÍDA para representar o dinheiro saindo para investir
        "nome": "Aporte/Investimento",
        "tipo": SAIDA,
        "icone": "fa-money-bill-transfer",
        "cor": "#009688",
        "parent_ref": "Despesas (Geral)",
    },

    # --- FILHAS (ENTRADAS) ---
    {
        "nome": "Salário",
        "tipo": ENTRADA,
        "icone": "fa-wallet",
        "cor": "#4CAF50",
        "parent_ref": "Receitas (Geral)",
    },
    {
        "nome": "Rendimentos de Investimento",
        "tipo": ENTRADA,
        "icone": "fa-money-bill-trend-up",
        "cor": "#009688",
        "parent_ref": "Receitas (Geral)",
    },
    {
        "nome": "Freelance/Extra",
        "tipo": ENTRADA,
        "icone": "fa-briefcase",
        "cor": "#8BC34A",
        "parent_ref": "Receitas (Geral)",
    },

    # --- FILHAS (INVESTIMENTOS/ATIVOS) --- <--- NOVAS CATEGORIAS AQUI
    {
        "nome": "Renda Fixa",
        "tipo": INVESTIMENTO,
        "icone": "fa-piggy-bank",
        "cor": "#2196F3",
        "parent_ref": "Carteira de Ativos",
    },
    {
        "nome": "Renda Variável",
        "tipo": INVESTIMENTO,
        "icone": "fa-chart-line",
        "cor": "#FFC107",
        "parent_ref": "Carteira de Ativos",
    },
    {
        "nome": "Consórcio",
        "tipo": INVESTIMENTO,
        "icone": "fa-car",
        "cor": "#9C27B0",
        "parent_ref": "Carteira de Ativos",
    },
]


# ==========================================================
# 3. COMANDO CLI: flask seed-db
# ==========================================================
@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """Popula o banco de dados com dados iniciais (usuário e categorias)."""

    db.drop_all()
    db.create_all()

    admin_user = User(nome="Admin", email="admin@finance.app")
    admin_user.set_password("123456")
    db.session.add(admin_user)
    db.session.flush()

    click.echo(f"✅ Usuário '{admin_user.email}' criado com sucesso! (Senha: 123456)")

    parent_map = {}
    user_id = admin_user.id

    # FASE A: Pais
    for cat_data in CATEGORIAS_A_SEMEAR:
        if cat_data.get("parent_ref") is None:
            nova_categoria = Categoria(
                nome=cat_data["nome"],
                tipo=cat_data["tipo"],
                icone=cat_data["icone"],
                cor=cat_data["cor"],
                user_id=user_id,
            )
            db.session.add(nova_categoria)
            db.session.flush()
            parent_map[cat_data["nome"]] = nova_categoria.id

    # FASE B: Filhas
    for cat_data in CATEGORIAS_A_SEMEAR:
        if cat_data.get("parent_ref") is not None:
            parent_name = cat_data.get("parent_ref")
            parent_id = parent_map.get(parent_name)

            if parent_id:
                nova_categoria = Categoria(
                    nome=cat_data["nome"],
                    tipo=cat_data["tipo"],
                    icone=cat_data["icone"],
                    cor=cat_data["cor"],
                    user_id=user_id,
                    parent_id=parent_id,
                )
                db.session.add(nova_categoria)

    db.session.commit()
    click.echo(f"✅ {len(CATEGORIAS_A_SEMEAR)} categorias adicionadas.")
    click.echo("✨ Banco de dados inicializado e populado com sucesso!")


def register_cli_commands(app):
    """Registra todos os comandos CLI no aplicativo Flask."""
    app.cli.add_command(seed_db_command)
