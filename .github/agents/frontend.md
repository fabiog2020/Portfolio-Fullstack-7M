## Agente Frontend — responsabilidades

- Verificar templates Jinja em `templates/` por:
  - Uso correto de `{{ url_for('static', filename='...') }}` para assets.
  - Presença do bloco de mensagens de flash em `templates/base.html`.
  - Formulários com campos `name` consistentes com rotas (ex.: `nome`, `email`, `senha`, `valor`, `categoria`).

- Verificar `static/css/style.css` por regras básicas de layout e responsividade.

## Checks automáticos sugeridos
- Detectar formulários que não possuem `method="post"` quando esperam envio.
- Verificar se templates que exibem listas usam `for` com `|length` para mensagens vazias.

## Exemplos no repo
- `templates/base.html` — flash messages e inclusão do CSS.
- `templates/dashboard.html` — exemplo de listagem de `transacoes`.

Use este arquivo para orientar revisões front-end e tarefas automatizadas que chequem templates e CSS.
