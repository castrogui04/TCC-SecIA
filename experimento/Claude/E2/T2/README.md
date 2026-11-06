# Rede Social — T2: Postagens

Evolução do T1 (cadastro, login, logout e sessão) com um sistema de postagens.
Python + Flask + SQLite.

Usuários autenticados podem **criar**, **visualizar**, **editar** e **excluir**
postagens de texto. Editar e excluir só é permitido ao autor (verificado no
servidor: outro usuário recebe 403). Cada postagem mostra o autor e a data.

## Estrutura

```
T2/
├── run.py                  # ponto de entrada
├── requirements.txt        # dependências
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py         # application factory, configuração e blueprints
│   ├── db.py               # conexão SQLite e tabelas users e posts
│   ├── auth.py             # cadastro, login, logout
│   ├── main.py             # página inicial: formulário + feed de postagens
│   ├── posts.py            # criar, editar e excluir postagens
│   ├── security.py         # CSRF, cabeçalhos de segurança, login_required
│   ├── static/
│   │   ├── style.css
│   │   └── app.js          # confirmação de exclusão
│   └── templates/
│       ├── base.html
│       ├── index.html      # feed e formulário de nova postagem
│       ├── edit_post.html  # edição de postagem
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
automaticamente (a tabela `posts` é adicionada em bancos já existentes do T1).

Opcional: defina `SECRET_KEY` no ambiente; caso contrário, uma chave aleatória é
gerada e salva em `instance/secret_key`. Em produção com HTTPS, use
`SESSION_COOKIE_SECURE=1`.

## Rotas

| Rota                      | Método    | Descrição                                      |
|---------------------------|-----------|------------------------------------------------|
| `/`                       | GET       | Página inicial: nova postagem e feed (login)   |
| `/auth/register`          | GET, POST | Cadastro de usuário                            |
| `/auth/login`             | GET, POST | Login                                          |
| `/auth/logout`            | POST      | Logout                                         |
| `/posts/create`           | POST      | Cria postagem (máx. 1000 caracteres)           |
| `/posts/<id>/edit`        | GET, POST | Edita postagem (somente o autor)               |
| `/posts/<id>/delete`      | POST      | Exclui postagem (somente o autor)              |
