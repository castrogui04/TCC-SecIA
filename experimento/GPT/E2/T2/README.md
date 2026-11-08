# T2 — Cadastro, autenticação e postagens

Requer Python 3.10+. Dependências: Flask 3.1.2 e Werkzeug 3.1.3.
SQLite é fornecido pelo módulo `sqlite3` do Python. As dependências transitivas
são instaladas automaticamente pelo pip.

## Estrutura

```text
T2/
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
    └── index.html
```

## Executar no Windows

Na raiz do repositório:

```powershell
cd experimento/GPT/E2/T2
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Linux/macOS: substitua `.venv\Scripts\python.exe` por `.venv/bin/python`.
Não é necessário ativar o ambiente virtual.
Abra http://127.0.0.1:5000. Encerre com Ctrl+C.

## Funcionalidades

- Cadastro: nome com 3 a 30 letras ASCII, números ou sublinhado; senha de 8 a
  128 caracteres. Nomes não diferenciam maiúsculas de minúsculas.
- Login, logout e sessão persistente por até sete dias de inatividade.
- Usuários autenticados visualizam todas as postagens, com autor e data UTC,
  da mais recente para a mais antiga.
- Postagens têm de 1 a 2000 caracteres, desconsiderando espaços nas pontas.
- Somente o autor pode editar e excluir sua postagem. A autorização também é
  verificada no servidor. Edição e exclusão não aceitam autor enviado pelo cliente.

## Banco e sessão

Na primeira execução são criados `instance/users.sqlite3` e `instance/secret.key`.
Preserve esses arquivos para manter os dados e a chave entre reinícios.
A variável de ambiente `SECRET_KEY` pode substituir a chave local.
Não versione nem compartilhe a pasta `instance`.

Para continuar com os usuários da T1, encerre as duas aplicações e copie a pasta
`instance` da T1 para a T2 antes de iniciar a T2 pela primeira vez. A tabela
`posts` será criada automaticamente, mantendo a tabela `users` existente.
Sem essa cópia, a T2 utiliza um banco próprio e independente.

Senhas usam hashes com salt; consultas usam parâmetros; templates escapam os
textos; formulários possuem proteção CSRF. A sessão assinada armazena somente
o identificador do usuário e dados de controle, sem senha.
O servidor é destinado ao desenvolvimento local, com debug desativado.
Uma implantação pública requer servidor de produção, HTTPS, cookie Secure
e controle de tentativas de login.
