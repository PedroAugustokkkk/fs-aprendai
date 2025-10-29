# /app/routers/auth.py

from flask import Blueprint, request, jsonify # Importa Blueprint, request, jsonify do Flask
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # Importa create_access_token, jwt_required, get_jwt_identity do flask_jwt_extended
from app.services import user_service # Importa o user_service
from app.schemas.user_schema import user_schema # Importa o user_schema
from marshmallow import ValidationError # Importa o ValidationError do marshmallow

bp = Blueprint('auth', __name__, url_prefix='/auth') # Cria um Blueprint para autenticação

# # --- ROTA DE REGISTRO COMENTADA ---
# @bp.route('/register', methods=['POST']) # Define a rota para registro com método POST
# def register(): # Define a função de registro
#     json_data = request.get_json() # Pega os dados JSON da requisição
#     if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400 # Retorna erro se não houver dados
#     try: # Tenta carregar os dados com o schema
#         data = user_schema.load(json_data) # Carrega os dados usando o user_schema
#     except ValidationError as err: # Captura erro de validação
#         return jsonify(errors=err.messages), 422 # Retorna os erros de validação
#     try: # Tenta criar o usuário
#         new_user_data = user_service.create_user(data) # Chama a função create_user do user_service
#         return jsonify(new_user_data), 201 # Retorna os dados do novo usuário com status 201
#     except ValidationError as err: # Captura erro de validação (ex: email já existe)
#         return jsonify(errors=err.messages), 409 # Retorna os erros de validação com status 409
#     except Exception as e: # Captura qualquer outra exceção
#         print(f"ERRO /register: {e}") # Loga o erro no servidor
#         return jsonify(error="Erro interno ao registrar usuário."), 500 # Retorna erro interno com status 500

# # --- ROTA DE LOGIN COMENTADA ---
# @bp.route('/login', methods=['POST']) # Define a rota para login com método POST
# def login(): # Define a função de login
#     json_data = request.get_json() # Pega os dados JSON da requisição
#     if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400 # Retorna erro se não houver dados
#     email = json_data.get('email') # Pega o email dos dados JSON
#     password = json_data.get('password') # Pega a senha dos dados JSON
#     if not email or not password: return jsonify(error="Email e senha são obrigatórios"), 400 # Retorna erro se email ou senha estiverem faltando
#     
#     user = user_service.authenticate_user(email, password) # Chama a função authenticate_user do user_service
#     if not user: return jsonify(error="Email ou senha inválidos"), 401 # Retorna erro se a autenticação falhar
#         
#     access_token = create_access_token(identity=user.id) # Cria um token de acesso JWT com a ID do usuário
#     user_data = user_schema.dump(user) # Serializa os dados do usuário usando o user_schema
#     return jsonify(access_token=access_token, user=user_data), 200 # Retorna o token de acesso e os dados do usuário com status 200

@bp.route('/guest', methods=['POST']) # Define a rota para criar convidado com método POST
def create_guest(): # Define a função para criar convidado
    try: # Tenta criar o usuário convidado
        # Esta rota continua funcionando para criar o convidado
        guest_user = user_service.create_guest_user() # Chama a função create_guest_user do user_service
        if not guest_user: return jsonify(error="Não foi possível criar a conta de convidado"), 500 # Retorna erro se não foi possível criar o convidado
            
        access_token = create_access_token(identity=guest_user.id) # Cria um token de acesso JWT com a ID do convidado
        guest_data = user_schema.dump(guest_user) # Serializa os dados do convidado usando o user_schema
        
        return jsonify(access_token=access_token, user=guest_data), 200 # Retorna o token de acesso e os dados do convidado com status 200
    except Exception as e: # Captura qualquer exceção
        print(f"ERRO /guest: {e}") # Loga o erro no servidor
        return jsonify(error="Erro interno ao criar convidado."), 500 # Retorna erro interno com status 500

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
        
        # Usa o schema para serializar os dados (sem senha)
        return jsonify(user_schema.dump(user)), 200 # Serializa e retorna os dados do usuário com status 200
    except Exception as e: # Captura qualquer exceção
        print(f"ERRO /me: {e}") # Loga o erro no servidor
        return jsonify(error="Erro ao buscar dados do usuário."), 500 # Retorna erro interno com status 500
