# Rede Social — T1: Cadastro e autenticação

Aplicação web em Python + Flask + SQLite com cadastro, login, logout,
sessão persistente e página inicial mostrando o usuário autenticado.

## Estrutura

```
T1/
├── run.py                  # ponto de entrada
├── requirements.txt        # dependências
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py         # application factory, configuração e blueprints
│   ├── db.py               # conexão SQLite e criação da tabela users
│   ├── auth.py             # cadastro, login, logout, carregamento do usuário
│   ├── main.py             # página inicial (protegida)
│   ├── security.py         # CSRF, cabeçalhos de segurança, login_required
│   ├── static/style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       └── register.html
└── instance/               # criada automaticamente (banco e chave secreta)
```

## Dependências

- Python 3.9+
- Flask 3.x (inclui Werkzeug, usado para hash de senha)
- SQLite (módulo `sqlite3` da biblioteca padrão)

## Instalação

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## Execução

```bash
python run.py
```

Acesse <http://127.0.0.1:5000>. O banco `instance/rede_social.sqlite3` é criado
automaticamente na primeira execução.

Opcional: defina `SECRET_KEY` no ambiente; caso contrário, uma chave aleatória é
gerada e salva em `instance/secret_key`. Em produção com HTTPS, use
`SESSION_COOKIE_SECURE=1`.

## Rotas

| Rota             | Método     | Descrição                                   |
|------------------|------------|---------------------------------------------|
| `/`              | GET        | Página inicial (exige login)                |
| `/auth/register` | GET, POST  | Cadastro de usuário                         |
| `/auth/login`    | GET, POST  | Login                                       |
| `/auth/logout`   | POST       | Logout                                      |
