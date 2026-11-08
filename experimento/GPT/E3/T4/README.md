# T4 — Busca

Projeto completo em Python, Flask e SQLite. Preserva cadastro, login, logout, sessão persistente, postagens com edição/exclusão restritas ao autor e comentários. Acrescenta busca por nomes de usuário e conteúdo de postagens, com resultados em seções separadas na página `/busca`.

## Estrutura

```text
T4/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── test_app.py
├── test_posts.py
├── test_comments.py
├── test_search.py
├── templates/
│   ├── base.html
│   ├── auth.html
│   ├── index.html
│   ├── post_form.html
│   ├── search.html
│   └── error.html
└── static/
    └── style.css
```

`instance/usuarios.sqlite3` e `instance/session.key` são criados automaticamente e ignorados pelo Git. Não é necessário criar o banco manualmente.

## Dependências

Python 3.9 ou superior e Flask 3.1.2. O Flask instala Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click e Blinker automaticamente (além de Colorama no Windows). SQLite, unittest e os demais módulos utilizados acompanham o Python.

## Windows (PowerShell)

Dentro do repositório:

```powershell
cd experimento/GPT/E3/T4
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Linux/macOS

```sh
cd experimento/GPT/E3/T4
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra http://127.0.0.1:5000. Use Ctrl+C para parar o servidor.

## Uso

1. Cadastre um nome de 3 a 30 letras ASCII, números ou sublinhado e uma senha de 8 a 128 caracteres. Senhas compostas apenas por espaços são rejeitadas. Nomes não diferenciam maiúsculas e minúsculas; senhas diferenciam.
2. Faça login. A sessão permanece válida por até sete dias de inatividade, inclusive ao reiniciar o servidor com a mesma chave.
3. Crie postagens de até 5000 caracteres. Use **Editar** e **Excluir postagem** nas suas publicações. A autorização é conferida no servidor.
4. Leia e adicione comentários de até 2000 caracteres sob qualquer postagem. Eles exibem autor, texto e data. Excluir uma postagem remove seus comentários; editar preserva os comentários.
5. No campo **Buscar usuários e postagens**, informe de 1 a 100 caracteres e clique em **Buscar**. A página de resultados separa usuários e postagens, mostra contagens e informa quando não há correspondências.
6. A busca encontra trechos de nomes e do conteúdo das postagens, sem diferenciar maiúsculas de minúsculas, inclusive em texto Unicode: `FÉRIAS` encontra `Férias`. Acentos são preservados: `ferias` não equivale a `férias`. `%` e `_` são caracteres literais. Espaços nas extremidades do termo são removidos. Comentários não entram na pesquisa.
7. Cada resultado de postagem mostra autor, texto e data, com um link para a publicação e seus comentários no feed. A busca consulta o banco atual, refletindo novas publicações, edições e exclusões.
8. Use **Sair** para encerrar a sessão neste navegador. A busca, as postagens e os comentários exigem autenticação.

Postagens e comentários vazios, compostos apenas por espaços ou com caracteres nulos são rejeitados. Datas são exibidas em UTC. Postagens aparecem das mais recentes às mais antigas; comentários, do mais antigo ao mais recente.

## Preservar dados das versões anteriores

Com os servidores parados, caso T4 ainda não possua dados, copie a pasta `instance/` da versão anterior para T4. Preserve `usuarios.sqlite3` e `session.key`. As tabelas ausentes são criadas ao iniciar, mantendo os dados existentes. O código de T4 é independente das demais pastas.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Linux/macOS: `.venv/bin/python -m unittest -v`.

Os testes usam bancos temporários e cobrem autenticação, sessão, autoria, postagens, comentários, persistência, exclusão em cascata, busca parcial e Unicode, caracteres literais, ausência de resultados, validação, CSRF, escape HTML e SQL parametrizado.

## Implementação

Senhas com hash scrypt pelo Werkzeug; cookies assinados HttpOnly/SameSite=Lax; renovação da sessão no login; CSRF nos formulários POST; SQL parametrizado; chaves estrangeiras com exclusão em cascata; autor obtido da sessão. O Jinja escapa textos e termos pesquisados. A busca usa `instr` e uma função SQLite `casefold` registrada em cada conexão para comparação Unicode sem distinção de caixa.

Servidor destinado à execução local, com depuração desativada. Para implantação HTTPS, configure `SESSION_COOKIE_SECURE=True`, forneça uma `SECRET_KEY` privada por variável de ambiente e use servidor WSGI apropriado. Não publique `instance/`.
