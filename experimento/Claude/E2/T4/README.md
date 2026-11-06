# Rede Social — T4: Busca

Evolução do T3 (cadastro, autenticação, postagens e comentários) com busca.
Python + Flask + SQLite.

Usuários autenticados podem **criar**, **visualizar**, **editar** e **excluir**
postagens de texto e **comentar** em qualquer postagem. Cada comentário mostra
autor e data, e é exibido dentro da postagem correspondente (máx. 500 caracteres).
Ao excluir uma postagem, seus comentários são excluídos junto.

**Busca:** o campo na barra superior procura, em página própria (`/search`),
**usuários** cujo nome contém o termo e **postagens** cujo conteúdo contém o
termo, em seções separadas. Não diferencia maiúsculas/minúsculas (inclusive
letras acentuadas), trata `%` e `_` como texto comum e limita a 50 resultados
por categoria. Editar e excluir só é permitido ao autor (verificado no
servidor: outro usuário recebe 403). Cada postagem mostra o autor e a data.

## Estrutura

```
T4/
├── run.py                  # ponto de entrada
├── requirements.txt        # dependências
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py         # application factory, configuração e blueprints
│   ├── db.py               # conexão SQLite e tabelas users, posts e comments
│   ├── auth.py             # cadastro, login, logout
│   ├── main.py             # página inicial: formulário + feed com comentários
│   ├── posts.py            # criar, editar e excluir postagens
│   ├── comments.py         # adicionar comentários às postagens
│   ├── search.py           # busca de usuários e postagens
│   ├── security.py         # CSRF, cabeçalhos de segurança, login_required
│   ├── static/
│   │   ├── style.css
│   │   └── app.js          # confirmação de exclusão
│   └── templates/
│       ├── base.html
│       ├── index.html      # feed e formulário de nova postagem
│       ├── edit_post.html  # edição de postagem
│       ├── search.html     # resultados da busca
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
automaticamente (bancos do T3 continuam compatíveis: a busca não altera o esquema).

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
| `/posts/<id>/comments`    | POST      | Adiciona comentário à postagem (login)         |
| `/search?q=termo`         | GET       | Busca usuários e postagens (login)             |
