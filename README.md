# 💰 FinanceApp - Gerenciador Financeiro Pessoal

Este é um aplicativo de finanças pessoais robusto e modular desenvolvido com **Flask**. O projeto segue padrões modernos de Engenharia de Software, incluindo **Application Factory Pattern**, **Blueprints** e arquitetura em camadas (MVC/Services).

---

## 🚀 Funcionalidades Principais

- **Autenticação Segura**: Login, Registro e Logout com `Flask-Login`.
- **Dashboard Interativo**: Visão geral de receitas, despesas, saldo projetado e gráficos.
- **Gestão de Transações**: CRUD completo de entradas e saídas.
- **Controle de Cartões de Crédito**: Gestão de limites e dias de vencimento.
- **Parcelamentos**: Lógica avançada para parcelas recorrentes e pagamentos parciais.
- **Investimentos**: Controle de Renda Fixa, Variável e outros ativos.
- **Categorias Hierárquicas**: Organização visual com ícones e cores personalizáveis.
- **Relatórios**: Extratos detalhados e gráficos de distribuição por categoria.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+, Flask 3.x
- **Banco de Dados**: SQLite (via SQLAlchemy e Alembic)
- **Frontend**: HTML5, Jinja2, TailwindCSS (CDN), FontAwesome
- **Formulários**: Flask-WTF
- **Testes**: Pytest

---

## 📂 Estrutura do Projeto

O projeto foi refatorado para garantir escalabilidade e testabilidade:

```text
finance-app/
├── app.py                 # Ponto de entrada da aplicação (Entry Point)
├── factory.py             # Application Factory (Configuração e Inicialização)
├── database.py            # Instâncias do SQLAlchemy e LoginManager
├── config.py              # Configurações de Ambiente (Dev/Prod)
│
├── blueprints/            # Rotas Modularizadas (Controllers)
│   ├── auth_routes.py     # Login/Registro
│   ├── main_routes.py     # Dashboard
│   ├── transaction_routes.py
│   └── ... (card, category, installment, investment, report)
│
├── models/                # Modelos do Banco de Dados
│   ├── models.py          # Modelo User
│   └── models_finance.py  # Transacao, Categoria, etc.
│
├── services/              # Regras de Negócio (Business Logic)
│   ├── parcelas_service.py
│   └── transactions_service.py
│
├── tools/                 # Ferramentas de Linha de Comando (CLI)
├── forms/                 # Validações de Formulário (WTForms)
├── templates/             # Arquivos HTML (Jinja2)
└── static/                # CSS e Imagens
⚙️ Configuração e Instalação
1. Pré-requisitos
Python 3.10 ou superior.
Git.
2. Clonar e Configurar
code
Bash
# Clone o repositório
git clone https://github.com/fabiog2020/Portfolio-Fullstack-7M.git
cd Portfolio-Fullstack-7M/finance-app

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
3. Variáveis de Ambiente
Crie um arquivo .env na raiz (baseado no config.py) se desejar configurações específicas, ou use os padrões de desenvolvimento já configurados.
💾 Banco de Dados
O projeto utiliza SQLite e já vem com comandos CLI personalizados para facilitar a configuração inicial.
Inicializar e Popular o Banco (Seed)
Para criar as tabelas e inserir o usuário administrador e categorias padrão (Renda Fixa, Variável, Moradia, etc.):
code
Bash
flask seed-db
Isso criará:
Usuário Admin: admin@finance.app / Senha: 123456
Categorias Padrão: Receitas, Despesas, Investimentos e suas subcategorias.
▶️ Executando a Aplicação
Para rodar o servidor de desenvolvimento:
code
Bash
python app.py
Acesse no navegador: http://127.0.0.1:5000
## 🧪 Testes e Qualidade de Código

O projeto utiliza **Pytest** para testes unitários e de integração. A arquitetura de *Application Factory* permite que cada teste rode em uma instância isolada com banco de dados em memória, garantindo velocidade e segurança (sem afetar dados reais).

### Pré-requisitos de Teste
Certifique-se de que as dependências de desenvolvimento estão instaladas:
```bash
pip install -r requirements_dev.txt

# Execute os testes
pytest
🤝 Contribuição
Contribuições são bem-vindas!
Faça um Fork do projeto.
Crie uma Branch para sua Feature (git checkout -b feature/NovaFeature).
Commit suas mudanças (git commit -m 'Add: Nova Feature').
Faça o Push (git push origin feature/NovaFeature).
Abra um Pull Request.
📄 Licença
Este projeto está sob a licença MIT.
Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
