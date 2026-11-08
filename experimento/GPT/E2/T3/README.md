# T3 — Cadastro, autenticação, postagens e comentários

## Estrutura

```text
T3/
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

## Dependências

Python 3.10 ou superior, Flask 3.1.2 e Werkzeug 3.1.3.
SQLite é fornecido pelo módulo `sqlite3` do Python.
O pip instala automaticamente as dependências transitivas.

## Instalação e execução

No Windows, a partir da raiz do repositório:

```powershell
cd experimento/GPT/E2/T3
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

No Linux/macOS:

```bash
cd experimento/GPT/E2/T3
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Não é necessário ativar o ambiente virtual.
Abra http://127.0.0.1:5000 no navegador. Encerre com Ctrl+C.

## Uso

1. Crie uma conta com nome de 3 a 30 letras ASCII, números ou sublinhado e
   senha de 8 a 128 caracteres. Nomes não diferenciam maiúsculas de minúsculas.
2. Entre para visualizar as postagens e seus comentários.
3. Publique textos de 1 a 2000 caracteres. Somente o autor pode editar ou excluir
   a postagem, com verificação de autorização no servidor.
4. Use o formulário de cada postagem para comentar. Comentários têm de 1 a
   1000 caracteres e mostram autor e data UTC, do mais antigo para o mais recente.
   Espaços nas pontas são removidos de postagens e comentários.
5. A sessão permanece por até sete dias de inatividade, se o navegador conservar
   o cookie. Clique em Sair para encerrar a sessão neste navegador.

Excluir uma postagem também exclui seus comentários na mesma transação,
por chave estrangeira com `ON DELETE CASCADE`.

## Persistência e atualização da T2

Na primeira execução, a aplicação cria `instance/users.sqlite3` e
`instance/secret.key`. Preserve esses arquivos entre reinícios.
A variável de ambiente `SECRET_KEY`, se definida, substitui a chave local.
Não versione nem compartilhe a pasta `instance`.

Para manter os usuários e as postagens da T2, encerre as aplicações e copie
a pasta `instance` da T2 para a T3 antes da primeira execução da T3.
As tabelas existentes são preservadas e a tabela `comments` é criada automaticamente.
Sem a cópia, a T3 usa um banco novo e independente.

As senhas são armazenadas como hashes com salt. As consultas usam parâmetros,
os templates escapam os textos e os formulários validam tokens CSRF.
O cookie é assinado, HttpOnly e SameSite=Lax; não contém senhas.
O servidor fornecido serve ao desenvolvimento local, sem depurador.
Uma implantação pública requer servidor de produção, HTTPS, cookie Secure
e controle de tentativas de login.
