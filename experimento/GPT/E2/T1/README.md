# T1 — Cadastro e autenticação

Aplicação local em Python 3.10+, Flask e SQLite. Possui cadastro, login,
logout por POST e página inicial com identificação do usuário autenticado.

## Estrutura

```text
T1/
├── .gitignore
├── app.py
├── README.md
├── requirements.txt
├── static/
│   └── style.css
└── templates/
    ├── auth.html
    ├── base.html
    └── index.html
```

## Instalação e execução

No terminal, a partir da raiz do repositório:

```powershell
cd experimento/GPT/E2/T1
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Linux/macOS: substitua `.venv\Scripts\python.exe` por `.venv/bin/python`.
Não é necessário ativar o ambiente virtual.

Abra http://127.0.0.1:5000 no navegador. Para encerrar, pressione Ctrl+C.
O servidor executa localmente, com o depurador desativado.

## Dependências

- Flask 3.1.2: rotas, templates e sessão assinada.
- Werkzeug 3.1.3: geração e verificação dos hashes de senha.
- SQLite: disponível pelo módulo `sqlite3` da biblioteca padrão do Python.

As dependências transitivas são instaladas automaticamente pelo pip.

## Uso e persistência

1. Clique em **Criar conta** e cadastre um nome e uma senha.
2. Use de 3 a 30 letras ASCII, números ou sublinhado no nome e de 8 a 128
   caracteres na senha. Nomes não diferenciam maiúsculas de minúsculas.
3. Entre com as credenciais. A página inicial exibirá seu nome.
4. Recarregue a página ou reabra o navegador: a sessão permanece por até sete
   dias de inatividade, se o navegador conservar o cookie.
5. Clique em **Sair** para limpar a sessão no navegador.

Na primeira execução, a aplicação cria automaticamente `instance/users.sqlite3`
e `instance/secret.key`. Preserve esses arquivos para manter usuários e a chave
de assinatura entre reinícios. A variável de ambiente `SECRET_KEY`, se definida,
substitui a chave local. Não compartilhe a chave nem versione a pasta `instance`.

As senhas são armazenadas como hashes com salt. As consultas usam parâmetros,
os templates escapam os valores e os formulários validam tokens CSRF.
O cookie contém o identificador do usuário, sem a senha; é assinado, HttpOnly
e SameSite=Lax. Esta configuração utiliza HTTP no servidor de desenvolvimento
local. Uma implantação pública requer servidor de produção, HTTPS,
`SESSION_COOKIE_SECURE=True` e controle de tentativas de login.
