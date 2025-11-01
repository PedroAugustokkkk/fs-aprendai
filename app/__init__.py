# Importa a classe principal do Flask e a função jsonify para criar respostas JSON
from flask import Flask, jsonify
# Importa a extensão Flask-CORS para lidar com a política de mesma origem do navegador
from flask_cors import CORS 

# Importa a classe de configuração (Config) do módulo core.config
from app.core.config import Config

# Importa as instâncias das extensões (db, migrate, etc.) e o cliente qdrant
from app.extensions import db, migrate, bcrypt, jwt, ma, qdrant 
# Importa o cliente principal do Qdrant
from qdrant_client import QdrantClient 
# Importa modelos específicos do Qdrant para configuração de vetores
from qdrant_client.http.models import VectorParams, Distance
# Importa a biblioteca do Google Gemini
import google.generativeai as genai

# Importa os Blueprints (módulos de rotas) da aplicação
from app.routers import auth
from app.routers import tasks
from app.routers import chat
from app.routers import documents

# --- A FÁBRICA DE APLICAÇÃO (Application Factory Pattern) ---
def create_app(config_class=Config):
    """
    Cria e configura uma instância da aplicação Flask.
    """
    # 1. Cria a instância principal do app Flask
    app = Flask(__name__)
    
    # --- 2. Configure o CORS ---
    # Define a lista de origens (domínios) que têm permissão para fazer requisições
    origins = [
        "http://localhost:3000", # Permite requisições do localhost na porta 3000 (para dev)
        "http://localhost:8080", # Permite requisições do localhost na porta 8080 (Vite)
        # *** CORREÇÃO AQUI ***
        # Esta é a URL correta do seu front-end na Vercel, conforme os logs de erro
        "https://aprendi-ai-explorer.vercel.app" 
    ]
    
    # Aplica a configuração do CORS ao app Flask
    CORS(app,
         # Define quais recursos (rotas, ex: "/*" para todas) usarão quais origens
         resources={r"/*": {"origins": origins}},
         # Permite que o navegador envie credenciais (como cookies ou tokens de autorização)
         supports_credentials=True
        )
    # --- Fim da configuração do CORS ---
    
    # 3. Carrega as configurações (chaves de API, URL do banco, etc.) do objeto de configuração
    app.config.from_object(config_class)

    # 4. Configura a API do Google Gemini com a chave carregada do app.config
    genai.configure(api_key=app.config['GOOGLE_API_KEY'])

    # 5. Inicializa as extensões do Flask, ligando-as à instância 'app'
    db.init_app(app) # Inicializa o SQLAlchemy (banco de dados)
    migrate.init_app(app, db) # Inicializa o Flask-Migrate (migrações do DB)
    bcrypt.init_app(app) # Inicializa o Flask-Bcrypt (hashing de senhas)
    jwt.init_app(app) # Inicializa o Flask-JWT-Extended (tokens JWT)
    ma.init_app(app) # Inicializa o Flask-Marshmallow (serialização/validação)

    # Inicializa o Cliente Qdrant global com as configurações carregadas do app.config
    global qdrant # Informa que estamos usando a variável global 'qdrant' (de extensions.py)
    try:
        # Tenta criar uma nova instância do cliente Qdrant
        qdrant = QdrantClient(
            host=app.config['QDRANT_HOST'], # Pega o host do Qdrant do config
            api_key=app.config['QDRANT_API_KEY'], # Pega a API key do Qdrant do config
            prefer_grpc=True # Usa gRPC para melhor performance, se disponível
        )
        print("Cliente Qdrant conectado.") # Log de sucesso
        
        # Tenta criar a coleção de vetores se ela ainda não existir
        qdrant.create_collection(
            collection_name=app.config['QDRANT_COLLECTION_NAME'], # Nome da coleção vindo do config
            vectors_config=VectorParams( # Define a configuração dos vetores
                size=768, # Tamanho do vetor (compatível com o modelo de embedding)
                distance=Distance.COSINE # Métrica de distância (similaridade de cosseno)
            )
        )
        print(f"Coleção '{app.config['QDRANT_COLLECTION_NAME']}' verificada/criada.") # Log
    except Exception as e:
        # Captura exceções durante a inicialização do Qdrant
        # Verifica se o erro é apenas porque a coleção já existe (o que é esperado)
        if "already exists" in str(e).lower():
            print(f"Coleção '{app.config['QDRANT_COLLECTION_NAME']}' já existe.") # Log normal
        else:
            # Se for outro erro (ex: falha de conexão, API key inválida), imprime o erro
            print(f"ERRO ao inicializar Qdrant ou criar coleção: {e}")
            # Em produção, você poderia levantar o erro aqui ou ter um fallback

    # 6. Rota de Teste (Raiz da API)
    @app.route('/')
    def read_root():
        # Retorna um JSON simples para verificar se a API está no ar
        return jsonify(
            status="ok",
            message="Bem-vindo à API Flask do Gênio Guiado, Chefe!"
        )

    # 7. Registrar os Blueprints (módulos de rotas) na aplicação
    app.register_blueprint(auth.bp) # Registra rotas de autenticação (ex: /auth/guest)
    app.register_blueprint(tasks.bp) # Registra rotas de tarefas (ex: /tasks/)
    app.register_blueprint(chat.bp) # Registra rotas de chat (ex: /chat/send)
    app.register_blueprint(documents.bp) # Registra rotas de documentos (ex: /documents/upload)
    
    # 8. Retorna a instância do app pronta para ser executada pelo Gunicorn/Render
    return app
