# T2 — Postagens

Projeto completo em Python, Flask e SQLite. Preserva cadastro, login, logout, sessão persistente e identificação do usuário do T1. Acrescenta criação e visualização de postagens, com edição e exclusão restritas ao autor.

## Estrutura

```text
T2/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── test_app.py
├── test_posts.py
├── templates/
│   ├── base.html
│   ├── auth.html
│   ├── index.html
│   ├── post_form.html
│   └── error.html
└── static/
    └── style.css
```

`instance/usuarios.sqlite3` e `instance/session.key` são criados automaticamente e ignorados pelo Git. Não há preparação manual do banco.

## Dependências

Python 3.9 ou superior e Flask 3.1.2. O pip instala automaticamente Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click e Blinker (além de Colorama no Windows). SQLite, unittest e os demais módulos utilizados acompanham o Python.

## Windows (PowerShell)

Dentro da pasta do repositório:

```powershell
cd experimento/GPT/E3/T2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Linux/macOS

```sh
cd experimento/GPT/E3/T2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra http://127.0.0.1:5000. Use Ctrl+C para encerrar o servidor.

## Uso

1. Cadastre um nome de 3 a 30 letras ASCII, números ou sublinhado e uma senha de 8 a 128 caracteres. Nomes não diferenciam maiúsculas e minúsculas; senhas diferenciam. Senhas compostas apenas por espaços são rejeitadas.
2. Faça login. A sessão permanece válida por até sete dias de inatividade, inclusive após reabrir o navegador ou reiniciar o servidor com a mesma chave.
3. A página inicial mostra o usuário autenticado e todas as postagens, das mais recentes às mais antigas, com autor e data em UTC.
4. Clique em **Nova postagem**, escreva de 1 a 5000 caracteres e clique em **Publicar**. Espaços nas extremidades são removidos; texto vazio ou composto apenas por espaços é rejeitado.
5. Nas suas postagens, use **Editar** ou **Excluir postagem**. A exclusão ocorre ao clicar no botão.
6. Clique em **Sair** para encerrar a sessão neste navegador. Visitantes veem apenas a página de boas-vindas.

## Preservar os dados locais do T1

Com ambos os servidores parados, caso T2 ainda não possua dados, copie a pasta `instance/` de T1 para T2. Preserve tanto `usuarios.sqlite3` quanto `session.key`. Ao iniciar T2, a tabela de postagens será criada no banco existente, mantendo os usuários. T1 e T2 permanecem projetos independentes; não é necessário copiar código de T1.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

No Linux/macOS: `.venv/bin/python -m unittest -v`.

Os testes usam bancos temporários. Cobrem autenticação, sessão, validações, CSRF, escape HTML, SQL parametrizado, persistência, ordenação, criação, edição, exclusão e tentativas de alteração por outro usuário ou visitante.

## Implementação

Senhas com hash scrypt pelo Werkzeug; cookies assinados com HttpOnly e SameSite=Lax; renovação da sessão no login; CSRF em todos os formulários POST; SQL parametrizado; vínculo de autor com chave estrangeira; autorização conferida no servidor em cada edição e exclusão. O autor é obtido da sessão, nunca de um campo enviado pelo navegador. Textos são escapados pelo Jinja e preservam quebras de linha.

Servidor destinado à execução local, com depuração desativada. Para implantação com HTTPS, configure `SESSION_COOKIE_SECURE=True`, forneça uma `SECRET_KEY` privada por variável de ambiente e use servidor WSGI apropriado. Não publique o diretório `instance/`.
