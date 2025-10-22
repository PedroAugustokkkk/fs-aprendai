# /app/__init__.py

# Importa a classe principal do Flask
from flask import Flask, jsonify
from flask_cors import CORS # <--- 1. Importe o CORS aqui

# Importa nossa classe de configuração
from app.core.config import Config

# Importa as instâncias das extensões que criamos
# (Adicionei a importação do qdrant aqui também)
from app.extensions import db, migrate, bcrypt, jwt, ma, qdrant 
from qdrant_client import QdrantClient # <--- Importe o QdrantClient

# Importa a biblioteca do Gemini
import google.generativeai as genai

# Importa os Blueprints (Routers)
from app.routers import auth
from app.routers import tasks
from app.routers import chat
from app.routers import documents

# --- A FÁBRICA DE APLICAÇÃO ---
def create_app(config_class=Config):
    """
    Cria e configura uma instância da aplicação Flask.
    """
    # 1. Cria a instância do app Flask
    app = Flask(__name__)
    
    # --- 2. Configure o CORS ---
    # Aplica o CORS à sua aplicação Flask
    # Permite requisições de qualquer origem (ideal para dev)
    # Em produção, troque "*" pela URL da Vercel
    CORS(app, resources={r"/*": {"origins": "*"}})
    # --- Fim da configuração do CORS ---
    
    # 3. Carrega a configuração a partir da classe Config
    app.config.from_object(config_class)

    # 4. Configura a API do Gemini (usando a config carregada)
    genai.configure(api_key=app.config['GOOGLE_API_KEY'])

    # 5. Inicializa as extensões, ligando-as ao 'app'
    db.init_app(app)
    migrate.init_app(app, db) # Flask-Migrate precisa do app e do db
    bcrypt.init_app(app)
    jwt.init_app(app)
    ma.init_app(app) # Inicializa o Marshmallow

    # Inicializa o Cliente Qdrant com as configurações carregadas
    # (Usando a instância global importada de extensions, mas reconfigurando-a)
    global qdrant
    try:
        qdrant = QdrantClient(
            host=app.config['QDRANT_HOST'],
            api_key=app.config['QDRANT_API_KEY'],
            prefer_grpc=True # gRPC geralmente é mais rápido
        )
        print("Cliente Qdrant conectado.")
        # Lógica para criar a coleção no Qdrant se ela não existir
        # (Usamos 'create_collection' em vez de 'recreate_collection' para evitar apagar dados)
        qdrant.create_collection(
            collection_name=app.config['QDRANT_COLLECTION_NAME'],
            vectors_config={
                "size": 768, # Tamanho do vetor do 'text-embedding-004'
                "distance": "Cosine"
            }
        )
        print(f"Coleção '{app.config['QDRANT_COLLECTION_NAME']}' verificada/criada.")
    except Exception as e:
        # Se a coleção já existir, um erro específico é lançado, podemos ignorá-lo
        # Outros erros (conexão, API key) devem ser logados
        if "already exists" in str(e).lower():
             print(f"Coleção '{app.config['QDRANT_COLLECTION_NAME']}' já existe.")
        else:
             print(f"ERRO ao inicializar Qdrant ou criar coleção: {e}")
             # Em produção, você poderia levantar o erro aqui ou ter um fallback

    # 6. Rota de Teste (o "Hello World")
    @app.route('/')
    def read_root():
        return jsonify(
            status="ok",
            message="Bem-vindo à API Flask do Gênio Guiado, Chefe!"
        )

    # 7. Registrar os Blueprints (Routers)
    app.register_blueprint(auth.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(documents.bp)
    
    # Retorna a aplicação configurada
    return app
