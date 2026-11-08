# T3 — Comentários

Projeto completo em Python, Flask e SQLite. Preserva cadastro, login, logout, sessão persistente e postagens com edição/exclusão restritas ao autor. Permite comentar diretamente em qualquer postagem, exibindo texto, autor e data junto à postagem correspondente.

## Estrutura

```text
T3/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── test_app.py
├── test_posts.py
├── test_comments.py
├── templates/
│   ├── base.html
│   ├── auth.html
│   ├── index.html
│   ├── post_form.html
│   └── error.html
└── static/
    └── style.css
```

O banco `instance/usuarios.sqlite3` e a chave `instance/session.key` são criados automaticamente. Não há preparação manual do banco. A pasta `instance/` é ignorada pelo Git.

## Dependências

Python 3.9 ou superior e Flask 3.1.2. Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click e Blinker são instalados pelo Flask (além de Colorama no Windows). SQLite, unittest e os demais módulos utilizados acompanham o Python.

## Windows (PowerShell)

Dentro do repositório:

```powershell
cd experimento/GPT/E3/T3
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Linux/macOS

```sh
cd experimento/GPT/E3/T3
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra http://127.0.0.1:5000. Pressione Ctrl+C para parar o servidor.

## Uso

1. Cadastre um nome com 3 a 30 letras ASCII, números ou sublinhado e uma senha de 8 a 128 caracteres. Nomes não diferenciam maiúsculas e minúsculas; senhas diferenciam. Senhas compostas apenas por espaços são rejeitadas.
2. Faça login. A sessão dura até sete dias de inatividade e identifica o usuário na página inicial.
3. Use **Nova postagem** para publicar texto de até 5000 caracteres. O feed mostra autor, conteúdo e data em UTC, das postagens mais recentes às mais antigas.
4. Use **Editar** ou **Excluir postagem** nas suas publicações. A autorização é conferida no servidor.
5. Sob cada postagem, leia os comentários, escreva no campo **Adicionar comentário** e clique em **Comentar**. Qualquer usuário autenticado pode comentar em qualquer postagem.
6. Comentários aceitam de 1 a 2000 caracteres. Espaços nas extremidades são removidos. Texto vazio, apenas espaços ou caracteres nulos são rejeitados. Os comentários aparecem do mais antigo ao mais recente, com autor e data em UTC.
7. Ao excluir uma postagem, seus comentários são excluídos automaticamente. A edição da postagem preserva seus comentários.
8. Use **Sair** para encerrar a sessão neste navegador. Visitantes veem apenas a página de boas-vindas.

## Preservar dados de T1 ou T2

Com os servidores parados, caso T3 ainda não possua dados, copie a pasta `instance/` da versão anterior para T3. Preserve `usuarios.sqlite3` e `session.key`. Ao iniciar, as tabelas ausentes são criadas automaticamente, mantendo usuários e postagens existentes. O código de T3 é independente das demais pastas.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Linux/macOS: `.venv/bin/python -m unittest -v`.

Os testes usam bancos temporários e verificam autenticação, sessão, postagens, autoria, comentários, vínculo com a postagem correta, persistência, validações, CSRF, escape HTML, SQL parametrizado e exclusão em cascata.

## Implementação

Senhas armazenadas como hash scrypt; cookies assinados HttpOnly/SameSite=Lax; renovação da sessão no login; CSRF em todos os formulários POST; SQL parametrizado; chaves estrangeiras com exclusão em cascata; autor obtido exclusivamente da sessão. O feed carrega os comentários em uma consulta adicional e os agrupa por postagem. O Jinja escapa o texto, e o CSS preserva quebras de linha.

Servidor destinado à execução local, com depuração desativada. Para implantação HTTPS, configure `SESSION_COOKIE_SECURE=True`, forneça uma `SECRET_KEY` privada por variável de ambiente e utilize servidor WSGI apropriado. Não publique `instance/`.
