# T5 — Rede social com foto de perfil

Requer Python 3.12. Dependências diretas Flask 3.1.3 e Pillow 13.0.0.
SQLite acompanha o Python. O pip instala as demais dependências.

Execute na pasta experimento/GPT/E1/T5 no PowerShell.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
~~~

Abra http://127.0.0.1:5000. No Linux/macOS, use .venv/bin/python.

Cadastre-se e entre para acessar postagens, comentários, busca e foto de perfil.
Na página inicial, selecione uma imagem e clique em Enviar foto.
Para trocar a imagem, selecione outra e clique em Substituir foto.

São aceitas imagens JPEG, PNG e WebP de até 5 MB e 4 milhões de pixels.
A aplicação valida o conteúdo, aplica a orientação e converte para PNG
com tamanho máximo de 512 por 512 pixels, preservando a proporção.
Os bytes do arquivo convertido são armazenados no SQLite na tabela profile_photos,
associados ao usuário autenticado. A substituição ocorre em uma transação.
O arquivo original é representado pela versão PNG normalizada armazenada.
As fotos são exibidas na página inicial do próprio usuário.

Somente o autor pode editar e excluir suas postagens.
Postagens aceitam de 1 a 5.000 caracteres e comentários de 1 a 2.000 caracteres.
Excluir uma postagem também exclui seus comentários.
A busca pesquisa trechos de nomes e postagens, ignorando maiúsculas e minúsculas.
O termo aceita até 200 caracteres. Acentos são significativos.

O banco instance/users.sqlite3 é criado automaticamente.
Para aproveitar os dados de T4, pare as aplicações, crie T5/instance e copie
T4/instance/users.sqlite3 para T5/instance/users.sqlite3 antes da primeira execução.
A nova tabela será criada sem apagar os dados existentes.

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
