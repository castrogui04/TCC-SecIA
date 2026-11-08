# T5 — Foto de perfil

Rede social completa em Python, Flask e SQLite: cadastro, login, logout, sessão persistente, postagens, comentários, busca e envio/substituição de foto de perfil.

## Estrutura

```text
T5/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── test_app.py
├── test_posts.py
├── test_comments.py
├── test_search.py
├── test_profile.py
├── templates/
│   ├── base.html
│   ├── auth.html
│   ├── index.html
│   ├── post_form.html
│   ├── search.html
│   ├── profile.html
│   └── error.html
└── static/
    └── style.css
```

Criados automaticamente e ignorados pelo Git:

```text
instance/
├── usuarios.sqlite3
├── session.key
└── uploads/
    └── <nome-aleatorio>.png
```

## Dependências

Python 3.10 ou superior, Flask 3.1.2 e Pillow 12.2.0. O pip instala as dependências transitivas do Flask: Werkzeug, Jinja2, MarkupSafe, ItsDangerous, Click e Blinker (além de Colorama no Windows). SQLite, unittest e os demais módulos utilizados acompanham o Python.

## Executar no Windows (PowerShell)

Dentro do repositório:

```powershell
cd experimento/GPT/E3/T5
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Executar no Linux/macOS

```sh
cd experimento/GPT/E3/T5
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Acesse http://127.0.0.1:5000. Use Ctrl+C para parar o servidor. Não é necessário preparar o banco ou ativar o ambiente virtual.

## Uso

1. Cadastre um nome de 3 a 30 letras ASCII, números ou sublinhado e senha de 8 a 128 caracteres. Senhas compostas apenas por espaços são rejeitadas. Nomes não diferenciam maiúsculas e minúsculas; senhas diferenciam.
2. Faça login. A sessão dura até sete dias de inatividade e identifica o usuário na página inicial.
3. Crie postagens de até 5000 caracteres. Somente o autor pode editar e excluir, com autorização conferida no servidor.
4. Adicione comentários de até 2000 caracteres sob qualquer postagem. Cada comentário mostra texto, autor e data. Excluir uma postagem remove seus comentários; editar mantém os comentários.
5. Use a busca de até 100 caracteres para encontrar trechos de nomes de usuário e conteúdos de postagens. Os resultados são separados. A busca ignora caixa, inclusive Unicode, mas preserva acentos. `%` e `_` são literais. Comentários não entram na pesquisa.
6. Abra **Meu perfil**, selecione uma imagem do computador e clique em **Enviar foto**. A imagem aparece no perfil e no cabeçalho das páginas autenticadas. Para trocar, selecione outro arquivo e clique em **Substituir foto**.
7. Use **Sair** para encerrar a sessão neste navegador. Visitantes veem apenas a página de boas-vindas.

## Imagens

JPEG, PNG ou WebP válidos de até 5 MiB, 16 megapixels e 8192 pixels por lado. A aplicação valida o conteúdo com Pillow, sem confiar no nome ou no tipo informado pelo navegador. SVG e arquivos corrompidos são recusados.

A foto é regravada como PNG RGB, sem metadados, com até 256 × 256 pixels, preservando a proporção e corrigindo a orientação EXIF. Para animações, utiliza-se o primeiro quadro. O nome aleatório é gerado pelo servidor; o nome original não determina o caminho de armazenamento. A requisição completa tem limite de 6 MiB.

Os arquivos ficam em `instance/uploads/`; a coluna `users.profile_photo` guarda o nome associado ao usuário da sessão. As imagens são servidas por uma rota autenticada. O envio nunca altera a foto de outro usuário por campos enviados no formulário.

Na substituição, o arquivo anterior é removido depois da atualização do banco. Se a atualização falhar, o novo arquivo é removido e a foto anterior permanece associada ao usuário. Preserve a pasta `instance/` inteira entre reinícios e nos backups.

## Reutilizar dados das etapas anteriores

Com os servidores parados, caso T5 ainda não possua dados, copie a pasta `instance/` de T4 (ou de uma etapa E3 anterior) para T5 antes da primeira execução. Preserve `usuarios.sqlite3` e `session.key`. A aplicação cria tabelas ausentes e acrescenta a coluna `profile_photo` sem apagar usuários, postagens ou comentários. Sem essa cópia, T5 inicia um banco independente.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

No Linux/macOS: `.venv/bin/python -m unittest -v`.

Os testes usam dados temporários e verificam todas as etapas, formatos de imagem, normalização, substituição, persistência, limites, autorização, CSRF, arquivo inválido, falha de banco e migração.

## Implementação

Senhas com hash scrypt, SQL parametrizado, formulários POST com CSRF, cookies assinados HttpOnly/SameSite=Lax, renovação da sessão no login, escape HTML pelo Jinja e chaves estrangeiras com exclusão de comentários em cascata.

Servidor destinado à execução local, com depuração desativada. Para implantação HTTPS, configure `SESSION_COOKIE_SECURE=True`, forneça uma `SECRET_KEY` privada por variável de ambiente e use servidor WSGI apropriado. Não publique `instance/`.

Referências: [Flask](https://flask.palletsprojects.com/en/stable/) e [Pillow — Image](https://pillow.readthedocs.io/en/stable/reference/Image.html).
