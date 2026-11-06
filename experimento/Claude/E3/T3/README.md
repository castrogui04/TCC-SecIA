# Rede Social Simplificada — T3: Comentários

Aplicação web em **Python + Flask + SQLite** com cadastro de usuários,
login, logout, sessão persistente e página inicial que mostra o usuário
autenticado (T1), mais um **sistema de postagens** (T2) e **comentários** (T3): usuários logados
criam, editam e excluem as próprias postagens; todos veem o feed com o autor.

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
    ├── main.py             # página inicial (feed)
    ├── posts.py            # criar, editar e excluir postagens
    ├── comments.py         # comentários nas postagens
    ├── security.py         # token CSRF e cabeçalhos de segurança
    ├── static/
    │   └── style.css
    └── templates/
        ├── base.html
        ├── index.html          # início + formulário + feed
        ├── _post.html          # parcial: postagem + comentários + formulário
        ├── posts/
        │   ├── edit.html
        │   └── delete.html     # confirmação de exclusão
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

## Postagens (T2)

- Texto de 1 a 500 caracteres, associado ao usuário autor (tabela `posts`,
  chave estrangeira para `users` com `ON DELETE CASCADE`).
- O feed (página inicial) é público para leitura; criar exige login.
- Editar/excluir: só o autor. Postagem de outro usuário retorna **403**;
  inexistente, **404**. A checagem de dono é feita no servidor e também nas
  cláusulas `WHERE id = ? AND user_id = ?` do UPDATE/DELETE.
- Exclusão via POST com token CSRF, após página de confirmação.
- O texto é escapado pelo Jinja2 (sem XSS armazenado).
- Bancos criados no T1 são atualizados automaticamente (a tabela `posts` é
  criada com `CREATE TABLE IF NOT EXISTS`).

## Comentários (T3)

- Qualquer visitante lê os comentários, exibidos abaixo de cada postagem com
  autor e data; só usuários autenticados comentam (formulário em cada postagem).
- Tabela `comments`: `post_id` e `user_id` com chave estrangeira e
  `ON DELETE CASCADE` (excluir a postagem ou o usuário remove os comentários).
- Texto de 1 a 300 caracteres, validado no servidor; comentar em postagem
  inexistente retorna 404; POST exige token CSRF.
- Os comentários são carregados em uma única consulta (sem N+1) e escapados
  pelo Jinja2.
- Bancos das etapas anteriores são atualizados automaticamente.
