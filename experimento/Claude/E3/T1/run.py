"""Ponto de entrada para executar a aplicação localmente.

Uso:
    python run.py

Variáveis de ambiente opcionais:
    FLASK_SECRET_KEY  chave secreta da sessão (se ausente, é gerada e
                      guardada em instance/secret_key)
    FLASK_DEBUG=1     ativa o modo debug (apenas em desenvolvimento)
    HOST / PORT       endereço e porta (padrão 127.0.0.1:5000)
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=debug)
