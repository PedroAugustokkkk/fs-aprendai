from flask import Blueprint, request, jsonify # Importa Blueprint, request, jsonify do Flask
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # Importa create_access_token, jwt_required, get_jwt_identity do flask_jwt_extended
from app.services import user_service # Importa o user_service
from app.schemas.user_schema import user_schema # Importa o user_schema
from marshmallow import ValidationError # Importa o ValidationError do marshmallow

# --- NOVAS IMPORTAÇÕES PARA A CORREÇÃO ---
import uuid # Para gerar IDs únicos para os guests
from datetime import datetime # Para definir o timestamp de criação
from app.models import User # Importa o modelo de usuário (baseado no schema do DB)
from app.extensions import db # Importa a instância do banco de dados (SQLAlchemy)
# --- FIM DAS NOVAS IMPORTAÇÕES ---

bp = Blueprint('auth', __name__, url_prefix='/auth') # Cria um Blueprint para autenticação

# # --- ROTA DE REGISTRO COMENTADA ---
# @bp.route('/register', methods=['POST']) # Define a rota para registro com método POST
# def register(): # Define a função de registro
#     json_data = request.get_json() # Pega os dados JSON da requisição
# ... (código comentado original mantido) ...

# # --- ROTA DE LOGIN COMENTADA ---
# @bp.route('/login', methods=['POST']) # Define a rota para login com método POST
# def login(): # Define a função de login
#     json_data = request.get_json() # Pega os dados JSON da requisição
# ... (código comentado original mantido) ...

# --- ROTA DE GUEST CORRIGIDA ---
@bp.route('/guest', methods=['POST']) # Define a rota para criar convidado com método POST
def create_guest(): # Define a função para criar convidado
    """
    Cria um usuário convidado temporário e retorna um token JWT.
    """
    try: # Inicia um bloco de tratamento de exceção
        # 1. GERAR UM USERNAME ÚNICO E ALEATÓRIO
        # Isso garante que a restrição 'UNIQUE NOT NULL' do banco seja satisfeita
        guest_username = f"guest_{uuid.uuid4().hex[:16]}" # Cria um nome como "guest_a1b2c3d4e5f6a7b8"

        # 2. Criar a nova entidade User
        guest_user = User(
            username=guest_username, # Define o username único (CRÍTICO)
            is_guest=True, # Marca como convidado
            created_at=datetime.utcnow() # Define o timestamp de criação
            # O campo 'email' pode ser nulo (com base no schema), então não precisamos defini-lo
        )

        # 3. Salvar o novo usuário no banco de dados
        db.session.add(guest_user) # Adiciona o novo usuário à sessão do DB
        db.session.commit() # Comita (salva) as mudanças no DB

        # 4. Criar o token JWT para este novo usuário
        # Usamos o ID do usuário (que o Supabase gerou) como a identidade no token
        access_token = create_access_token(identity=guest_user.id) 
        
        # 5. Serializar os dados do usuário para retornar ao front-end
        guest_data = user_schema.dump(guest_user) 
 
        # 6. Retornar o token e os dados do usuário com status 200 (OK)
        return jsonify(access_token=access_token, user=guest_data), 200 
    
    except Exception as e: # Captura qualquer exceção
        db.session.rollback() # Desfaz quaisquer mudanças no DB se algo deu errado
        print(f"ERRO CRÍTICO EM /guest: {e}") # Loga o erro REAL no console do Render
        return jsonify(error=f"Erro interno ao criar convidado: {str(e)}"), 500 # Retorna erro 500

@bp.route('/me', methods=['GET']) # Define a rota para buscar dados do usuário atual com método GET
@jwt_required() # Protege a rota, exigindo um token JWT válido
def get_current_user(): # Define a função para buscar dados do usuário atual
    """ # Docstring da função
    Retorna os dados do usuário logado (baseado no token JWT). # Descrição
    """ # Fim da docstring
    current_user_id = get_jwt_identity() # Pega a ID do usuário (identity) do token JWT
    try: # Tenta buscar o usuário pelo ID
        user = user_service.get_user_by_id(current_user_id) # Chama a função get_user_by_id do user_service
        if not user: # Verifica se o usuário foi encontrado
            return jsonify(error="Usuário não encontrado"), 404 # Retorna erro 404 se o usuário não for encontrado

 
        return jsonify(user_schema.dump(user)), 200 # Serializa e retorna os dados do usuário com status 200
    except Exception as e: # Captura qualquer exceção
        print(f"ERRO /me: {e}") # Loga o erro no servidor
        return jsonify(error="Erro ao buscar dados do usuário."), 500 # Retorna erro interno com status 500

