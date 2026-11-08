# T2 — Cadastro, autenticação e postagens

Requer Python 3.12. Execute os comandos na pasta experimento/GPT/E1/T2.

## Instalação e execução no Windows

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
~~~

Abra http://127.0.0.1:5000 no navegador.

No Linux/macOS, use .venv/bin/python em lugar de .\.venv\Scripts\python.exe.

O Flask instala suas dependências automaticamente. SQLite faz parte da biblioteca padrão do Python.

## Utilização

Cadastre um usuário com nome de 1 a 50 caracteres e senha de 8 a 128 caracteres.
Após entrar, publique textos de 1 a 5.000 caracteres e veja o mural com o nome de cada autor.
Os controles de edição e exclusão aparecem nas próprias postagens.
O servidor também verifica a autoria em todas as operações.
Sair encerra a sessão.

O banco instance/users.sqlite3 é criado automaticamente.
Para preservar os usuários de T1, pare os servidores e copie T1/instance/users.sqlite3
para T2/instance/users.sqlite3 antes de executar T2 pela primeira vez.
A nova tabela de postagens será criada preservando os usuários existentes.

A chave de sessão é gerada a cada início do servidor.
Para preservar sessões entre reinícios, defina SECRET_KEY com um valor secreto fixo.
No PowerShell, antes de iniciar a aplicação:

~~~powershell
$env:SECRET_KEY = 'substitua-por-um-valor-aleatorio-longo-e-secreto'
~~~

As sessões usam cookies assinados. As senhas são armazenadas como hashes.
Os formulários incluem proteção CSRF e consultas SQL usam parâmetros.
O comando app.py inicia o servidor local de desenvolvimento.

## Arquivos

- app.py
- requirements.txt
- .gitignore
- templates/index.html
- templates/post.html
- README.md

instance/, .venv/ e __pycache__/ são gerados localmente e ignorados pelo Git.
