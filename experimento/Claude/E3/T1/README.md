# Rede Social Simplificada — T1: Cadastro e autenticação

Aplicação web em **Python + Flask + SQLite** com cadastro de usuários,
login, logout, sessão persistente e página inicial que mostra o usuário
autenticado.

## Estrutura

```
T1/
├── run.py                  # ponto de entrada
├── requirements.txt        # dependências
├── .gitignore
├── README.md
└── app/
    ├── __init__.py         # fábrica da aplicação e configuração
    ├── db.py               # conexão SQLite e criação das tabelas
    ├── schema.sql          # esquema do banco
    ├── auth.py             # cadastro, login, logout, sessão
    ├── main.py             # página inicial
    ├── security.py         # token CSRF e cabeçalhos de segurança
    ├── static/
    │   └── style.css
    └── templates/
        ├── base.html
        ├── index.html
        └── auth/
            ├── login.html
            └── register.html
```

O banco (`instance/rede_social.sqlite3`) e a chave secreta
(`instance/secret_key`) são criados automaticamente na primeira execução.

## Dependências

- Python 3.10 ou superior
- Flask 3.x (traz Werkzeug, Jinja2, itsdangerous, click e blinker)
- `sqlite3` (já incluído na biblioteca padrão do Python)

## Instalação

```bash
cd experimento/Claude/E3/T1
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Execução

```bash
python run.py
```

Acesse <http://127.0.0.1:5000>.

Alternativa com a CLI do Flask:

```bash
flask --app run run
```

Variáveis de ambiente opcionais:

| Variável                | Efeito                                                     |
|-------------------------|------------------------------------------------------------|
| `FLASK_SECRET_KEY`      | Chave da sessão (senão é gerada em `instance/secret_key`)  |
| `FLASK_DEBUG=1`         | Modo debug (somente em desenvolvimento)                    |
| `SESSION_COOKIE_SECURE=1` | Cookie de sessão só via HTTPS (use em produção)          |
| `HOST` / `PORT`         | Endereço e porta (padrão `127.0.0.1:5000`)                 |

Para recriar as tabelas manualmente: `flask --app run init-db`.

## Medidas de segurança adotadas

- Senhas armazenadas com hash (`werkzeug.security`, scrypt/pbkdf2 com salt).
- Consultas SQL parametrizadas (sem concatenação de strings).
- Token CSRF em todos os formulários POST; logout apenas via POST.
- Sessão limpa ao fazer login (evita fixação de sessão).
- Cookie de sessão `HttpOnly` e `SameSite=Lax`; `Secure` configurável.
- Mensagem de erro genérica no login e verificação de hash mesmo quando o
  usuário não existe (dificulta enumeração de usuários).
- Validação do nome de usuário (regex) e da senha (tamanho mínimo/máximo).
- Redirecionamento pós-login (`next`) restrito a caminhos internos.
- Escape automático do Jinja2 e cabeçalhos CSP, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy` e `Cache-Control: no-store`.
- Chave secreta aleatória (não fixa no código) e debug desligado por padrão.
