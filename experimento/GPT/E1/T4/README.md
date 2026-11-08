# T4 — Rede social com busca

Requer Python 3.12. Dependência direta Flask 3.1.3.
SQLite acompanha o Python. O pip instala as dependências do Flask.

Execute na pasta experimento/GPT/E1/T4 no PowerShell.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
~~~

Abra http://127.0.0.1:5000. No Linux/macOS, use .venv/bin/python.

Cadastre-se e entre para usar postagens, comentários e busca.
Somente o autor pode editar e excluir suas postagens.
Postagens aceitam de 1 a 5.000 caracteres e comentários de 1 a 2.000 caracteres.
Excluir uma postagem também exclui seus comentários.

O campo de busca pesquisa trechos dos nomes de usuário e do conteúdo das postagens.
A busca ignora diferenças entre maiúsculas e minúsculas, inclusive em letras acentuadas.
Acentos continuam significativos. Os caracteres % e _ são pesquisados literalmente.
O termo aceita até 200 caracteres. Uma busca vazia solicita um termo.
Os resultados separam usuários e postagens e incluem links para as postagens no mural.

O banco instance/users.sqlite3 é criado automaticamente.
Para aproveitar os dados de T3, pare as aplicações, crie T4/instance e copie
T3/instance/users.sqlite3 para T4/instance/users.sqlite3 antes da primeira execução.

As senhas são armazenadas como hashes e a sessão usa cookies assinados.
Os formulários de alteração têm proteção CSRF.
Para manter sessões válidas entre reinícios, configure uma chave secreta fixa.

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
- templates/search.html

instance/, .venv/ e __pycache__/ são gerados localmente e ignorados pelo Git.
