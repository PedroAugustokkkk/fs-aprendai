# /app/__init__.py

# Importa a classe principal do Flask
from flask import Flask, jsonify

# Importa nossa classe de configuração
from app.core.config import Config

# Importa as instâncias das extensões que criamos
from app.extensions import db, migrate, bcrypt, jwt, ma

# Importa a biblioteca do Gemini
import google.generativeai as genai

# --- A FÁBRICA DE APLICAÇÃO ---
def create_app(config_class=Config):
    """
    Cria e configura uma instância da aplicação Flask.
    """
    # 1. Cria a instância do app Flask
    app = Flask(__name__)
    
    # 2. Carrega a configuração a partir da classe Config
    app.config.from_object(config_class)

    # 3. Configura a API do Gemini (usando a config carregada)
    genai.configure(api_key=app.config['GOOGLE_API_KEY'])

    # 4. Inicializa as extensões, ligando-as ao 'app'
    db.init_app(app)
    migrate.init_app(app, db) # Flask-Migrate precisa do app e do db
    bcrypt.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    
    # 5. Rota de Teste (o "Hello World")
    # Nós vamos mover isso para um "Blueprint" (router) depois,
    # mas por agora, deixamos aqui para testar.
    @app.route('/')
    def read_root():
        return jsonify(
            status="ok",
            message="Bem-vindo à API Flask do Gênio Guiado, Chefe!"
        )

    # 6. Registrar os Blueprints (Routers) - Próximo passo
    # from app.routers import auth, chat
    # app.register_blueprint(auth.bp, url_prefix='/auth')
    # app.register_blueprint(chat.bp, url_prefix='/chat')

    # Retorna a aplicação configurada
    return app