# T4 — Rede social com busca

## Estrutura

```text
T4/
├── .gitignore
├── app.py
├── README.md
├── requirements.txt
├── static/
│   └── style.css
└── templates/
    ├── auth.html
    ├── base.html
    ├── edit_post.html
    ├── index.html
    └── search.html
```

## Dependências

Python 3.10 ou superior, Flask 3.1.2 e Werkzeug 3.1.3.
SQLite é fornecido pelo módulo `sqlite3` do Python.
O pip instala automaticamente as dependências transitivas.

## Instalação e execução

No Windows, a partir da raiz do repositório:

```powershell
cd experimento/GPT/E2/T4
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

No Linux/macOS:

```bash
cd experimento/GPT/E2/T4
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Não é necessário ativar o ambiente virtual.
Abra http://127.0.0.1:5000 no navegador. Encerre com Ctrl+C.

## Funcionalidades

- Cadastro com nome de 3 a 30 letras ASCII, números ou sublinhado e senha de
  8 a 128 caracteres. Nomes não diferenciam maiúsculas de minúsculas.
- Login, logout por POST e sessão persistente por até sete dias de inatividade,
  se o navegador conservar o cookie.
- Postagens de 1 a 2000 caracteres, exibidas da mais recente para a mais antiga.
  Somente o autor pode editar ou excluir sua postagem, com autorização no servidor.
- Comentários de 1 a 1000 caracteres em cada postagem, exibidos do mais antigo
  para o mais recente. Postagens e comentários exibem autor e data UTC.
  Espaços nas pontas dos textos são removidos. Excluir uma postagem remove
  também seus comentários por chave estrangeira com `ON DELETE CASCADE`.
- Busca disponível após o login, pelo campo no topo das páginas. Procura o termo
  em qualquer parte do nome de usuário e do conteúdo das postagens armazenadas.
  Os resultados aparecem em `/busca?q=termo`, separados em usuários e postagens.
  Cada postagem encontrada tem um link para sua posição no início e comentários.

## Regras da busca

A busca aceita até 100 caracteres, remove espaços nas pontas e ignora diferenças
entre maiúsculas e minúsculas, inclusive letras acentuadas, usando `str.casefold`
como função SQLite. Acentos continuam significativos: `cafe` não encontra `café`.
Aspas, `%` e `_` são tratados literalmente. Consultas vazias pedem um termo;
consultas sem correspondências mostram mensagens em cada seção.
Comentários não fazem parte da pesquisa. Nenhuma pesquisa modifica o banco.

## Banco e atualização das etapas anteriores

Na primeira execução são criados `instance/users.sqlite3` e `instance/secret.key`.
Preserve esses arquivos para manter dados e assinatura da sessão entre reinícios.
A variável de ambiente `SECRET_KEY`, se definida, substitui a chave local.
Não versione nem compartilhe a pasta `instance`.

Para manter dados da T3 (ou da T1/T2), encerre as aplicações e copie a pasta
`instance` da etapa anterior para a T4 antes da primeira execução da T4.
As tabelas existentes são preservadas e as tabelas ausentes são criadas.
Sem a cópia, a T4 utiliza um banco novo e independente.

Senhas usam hashes com salt; consultas usam parâmetros; templates escapam os
textos; formulários POST validam tokens CSRF. O cookie de sessão é assinado,
HttpOnly e SameSite=Lax, sem senhas. O servidor fornecido destina-se ao uso local,
com debug desativado. Uma implantação pública requer servidor de produção,
HTTPS, cookie Secure e controle de tentativas de login.
