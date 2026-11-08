# T3 — Rede social com comentários

Requer Python 3.12. Dependência direta Flask 3.1.3.
SQLite acompanha o Python. As dependências do Flask são instaladas pelo pip.

Execute na pasta experimento/GPT/E1/T3 no PowerShell.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
~~~

Abra http://127.0.0.1:5000. No Linux/macOS, use .venv/bin/python.

Cadastre-se e entre para criar, visualizar, editar e excluir suas postagens.
Cada postagem aceita comentários de qualquer usuário autenticado.
O mural mostra o autor de cada postagem e de cada comentário.
Postagens aceitam de 1 a 5.000 caracteres e comentários de 1 a 2.000 caracteres.
Ao excluir uma postagem, seus comentários são excluídos junto com ela.

O banco instance/users.sqlite3 é criado automaticamente.
Para aproveitar os dados de T2, pare as aplicações, crie T3/instance e copie
T2/instance/users.sqlite3 para T3/instance/users.sqlite3 antes da primeira execução.
A tabela de comentários será criada preservando usuários e postagens.

A sessão usa cookie assinado, e as senhas são armazenadas como hashes.
Há proteção CSRF nos formulários e verificação de autoria no servidor.
Para manter sessões válidas entre reinícios, configure uma chave secreta fixa
antes de executar a aplicação.

~~~powershell
$env:SECRET_KEY = 'substitua-por-um-valor-aleatorio-longo-e-secreto'
~~~

Sem essa variável, uma chave é gerada a cada inicialização.
app.py inicia o servidor local de desenvolvimento.

Arquivos do projeto

- app.py
- requirements.txt
- .gitignore
- README.md
- templates/index.html
- templates/post.html

instance/, .venv/ e __pycache__/ são gerados localmente e ignorados pelo Git.
