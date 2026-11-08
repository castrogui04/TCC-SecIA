# T1 — Cadastro e autenticação

Rede social simplificada com cadastro, login, logout e identificação do usuário na página inicial.

## Estrutura

```text
T1/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── test_app.py
├── templates/
│   ├── base.html
│   ├── auth.html
│   └── index.html
└── static/
    └── style.css
```

`instance/usuarios.sqlite3` e `instance/session.key` são criados automaticamente na primeira execução e ignorados pelo Git. Não é necessário criar o banco manualmente. A chave local persiste entre reinicializações; preserve-a para manter as sessões existentes.

## Dependências

Python 3.9 ou superior e Flask 3.1.2. O Flask instala Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click e Blinker automaticamente (além de Colorama no Windows). SQLite, unittest e os demais módulos utilizados acompanham o Python.

## Instalação e execução no Windows (PowerShell)

Dentro da pasta do repositório:

```powershell
cd experimento/GPT/E3/T1
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Instalação e execução no Linux/macOS

```sh
cd experimento/GPT/E3/T1
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Acesse http://127.0.0.1:5000 no navegador. Para encerrar o servidor, pressione Ctrl+C.

## Uso

1. Clique em **Criar conta**. Use de 3 a 30 letras ASCII, números ou sublinhado no nome e de 8 a 128 caracteres na senha. Senhas compostas apenas por espaços são rejeitadas.
2. Após o cadastro, faça login. Nomes de usuário não diferenciam maiúsculas e minúsculas; senhas diferenciam.
3. A página inicial mostra o usuário autenticado. A sessão usa cookie assinado e permanece válida por até 7 dias de inatividade, inclusive após fechar e reabrir o navegador.
4. Clique em **Sair** para encerrar a sessão neste navegador.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

No Linux/macOS, use `.venv/bin/python -m unittest -v`. Os testes usam um banco temporário e verificam cadastro, hash de senha, duplicidade, validações, login, persistência, logout, CSRF, escape HTML e tentativas de injeção SQL.

## Implementação

Consultas SQL parametrizadas, senhas com hash scrypt pelo Werkzeug, formulários com token CSRF, logout via POST, renovação da sessão no login e cookies HttpOnly/SameSite=Lax. A sessão contém o identificador do usuário, nunca sua senha. O banco usa unicidade para impedir nomes duplicados.

O servidor fornecido é destinado à execução local, com depuração desativada. Para implantação com HTTPS, configure `SESSION_COOKIE_SECURE=True`, forneça uma `SECRET_KEY` privada por variável de ambiente e use um servidor WSGI apropriado. Não publique o diretório `instance/`.

Referências: [Flask — instalação](https://flask.palletsprojects.com/en/stable/installation/) e [Flask — guia inicial](https://flask.palletsprojects.com/en/stable/quickstart/).
