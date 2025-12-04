# Portfolio-Fullstack-7M

## Sobre o Projeto
Este é um aplicativo de finanças pessoais desenvolvido com Flask. Ele permite gerenciar transações financeiras, categorias, investimentos e muito mais. O projeto utiliza SQLite como banco de dados e Flask-Login para autenticação.

---

## Funcionalidades Principais
- **Autenticação de Usuários**: Registro e login com segurança.
- **Gerenciamento de Transações**: Adicionar, editar e excluir transações financeiras.
- **Categorias**: Organização de transações por categorias.
- **Investimentos**: Controle de investimentos e parcelas.
- **Relatórios**: Visualização de relatórios financeiros.

---

## Configuração do Ambiente

### Pré-requisitos
- Python 3.10 ou superior
- Pip (gerenciador de pacotes do Python)
- Ambiente virtual (recomendado)

### Passo a Passo
1. **Clone o repositório**:
   ```bash
   git clone https://github.com/fabiog2020/Portfolio-Fullstack-7M.git
   cd Portfolio-Fullstack-7M/finance-app
   ```

2. **Crie e ative um ambiente virtual**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Para Windows
   source .venv/bin/activate       # Para Linux/Mac
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_dev.txt
   ```

4. **Configure o banco de dados**:
   - O banco de dados SQLite será criado automaticamente ao rodar o projeto.
   - Para popular categorias iniciais, execute:
     ```bash
     flask seed-db
     ```

---

## Executando o Projeto
1. **Inicie o servidor Flask**:
   ```bash
   python app.py
   ```

2. **Acesse a aplicação**:
   - Abra o navegador e vá para: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Estrutura do Projeto
- **`app.py`**: Arquivo principal da aplicação.
- **`templates/`**: Templates HTML renderizados pelo Flask.
- **`static/`**: Arquivos estáticos (CSS, imagens).
- **`forms/`**: Formulários para validação de dados.
- **`services/`**: Lógica de negócios e serviços auxiliares.
- **`migrations/`**: Scripts de migração do banco de dados.
- **`database.py`**: Configuração do banco de dados.

---

## Notas Importantes
- **Backup do Banco de Dados**: Um backup automático é gerado periodicamente (ex.: `finance_backup_YYYYMMDD.db`).
- **Migrações**: Utilize Alembic para gerenciar alterações no esquema do banco de dados.

---

## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

---

## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
