# T5 — Rede social com foto de perfil

## Estrutura

```text
T5/
├── .gitignore
├── app.py
├── README.md
├── requirements.txt
├── static/
│   └── style.css
├── templates/
│   ├── auth.html
│   ├── base.html
│   ├── edit_post.html
│   ├── error.html
│   ├── index.html
│   ├── profile.html
│   └── search.html
└── instance/                 # criada automaticamente
    ├── secret.key
    ├── users.sqlite3
    └── uploads/              # fotos normalizadas em PNG
```

## Dependências

Python 3.10 ou superior, Flask 3.1.2, Werkzeug 3.1.3 e Pillow 12.2.0.
SQLite faz parte da biblioteca padrão do Python.
O pip instala as dependências transitivas automaticamente.

## Instalar e executar

No Windows, a partir da raiz do repositório:

```powershell
cd experimento/GPT/E2/T5
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

No Linux/macOS:

```bash
cd experimento/GPT/E2/T5
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Não é necessário ativar o ambiente virtual.
Abra http://127.0.0.1:5000. Encerre com Ctrl+C.

## Funcionalidades

- Cadastro com nome de 3 a 30 letras ASCII, números ou sublinhado e senha de
  8 a 128 caracteres. Nomes não diferenciam maiúsculas de minúsculas.
- Login, logout por POST e sessão por até sete dias de inatividade, se o navegador
  conservar o cookie.
- Postagens de 1 a 2000 caracteres, da mais recente para a mais antiga.
  Somente o autor pode editar e excluir, com autorização verificada no servidor.
- Comentários de 1 a 1000 caracteres, com autor e data UTC, do mais antigo
  para o mais recente. Excluir uma postagem exclui seus comentários em cascata.
  Espaços nas pontas de postagens e comentários são removidos.
- Busca por trechos de nomes e conteúdos de postagens, com resultados separados.
  Aceita até 100 caracteres e ignora diferenças entre maiúsculas e minúsculas
  usando Unicode casefold. Acentos são significativos e `%`, `_` e aspas são
  literais. Comentários não fazem parte da busca.
- Foto de perfil: entre, abra **Meu perfil**, selecione um arquivo e envie.
  A foto aparece no perfil e no topo das páginas autenticadas. Repita o envio
  para substituí-la. O usuário alterado é sempre o da sessão autenticada.

## Imagens

São aceitos arquivos JPEG, PNG e WebP válidos, com até 5 MiB, 16 megapixels
e 8192 pixels por lado. O conteúdo é validado com Pillow, independentemente
do nome e do tipo declarado pelo navegador. SVG e outros formatos são recusados.
A imagem é regravada em PNG RGB sem metadados, preservando a proporção e com
até 256 × 256 pixels. Em imagens animadas é utilizado o primeiro quadro.
A requisição completa tem limite de 6 MiB para acomodar o formulário.

As imagens ficam em `instance/uploads`, com nomes aleatórios gerados pelo servidor.
O banco armazena o nome do arquivo em `users.profile_photo`.
A foto anterior é removida após a atualização do banco. Se a atualização falhar,
o arquivo novo é removido e a foto anterior permanece associada ao usuário.
As fotos são servidas por uma rota que exige autenticação; não ficam em `static`.

## Persistência e migração

O banco, a chave da sessão e a pasta de fotos são criados automaticamente.
Preserve a pasta `instance` inteira entre reinícios e nos backups.
A variável de ambiente `SECRET_KEY`, quando definida, substitui a chave local.
Não compartilhe nem versione a pasta `instance`.

Para continuar com dados da T4 ou de uma etapa anterior, encerre as aplicações
e copie a pasta `instance` da versão anterior para a T5 antes da primeira execução.
As tabelas existentes são preservadas, tabelas ausentes são criadas e a coluna
`profile_photo` é acrescentada automaticamente à tabela `users`.
Sem a cópia, esta versão usa um banco novo e independente.

Senhas usam hashes com salt; consultas usam parâmetros; templates escapam textos;
formulários POST validam tokens CSRF. Cookies são assinados, HttpOnly e
SameSite=Lax, sem senhas. O servidor fornecido é para desenvolvimento local,
com debug desativado. Uma implantação pública requer servidor de produção,
HTTPS, cookie Secure e controle de tentativas de login.
