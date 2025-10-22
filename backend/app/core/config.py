# /app/core/config.py

import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# __file__ se refere a este arquivo (config.py)
# .parent.parent se refere à pasta raiz (g_guiado_backend)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '..', '.env'))

# Define uma classe de Configuração
class Config:
    """Carrega as configurações do app a partir de variáveis de ambiente."""

    # --- Configurações Gerais do Flask ---
    # Carrega a chave secreta do .env
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # --- Configurações do Banco de Dados (Flask-SQLAlchemy) ---
    # Carrega a URL do banco do .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Desativa um recurso do SQLAlchemy que não usaremos (reduz overhead)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configurações da IA ---
    # Carrega a chave do Gemini do .env
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

    # --- Configurações de Segurança (Flask-JWT-Extended) ---
    # Usa a mesma SECRET_KEY para assinar os tokens JWT
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY')
    # Você pode adicionar outras configs JWT aqui, como tempo de expiração
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30) 

# Exporta uma instância da classe para ser usada no app
settings = Config()