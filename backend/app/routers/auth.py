# /app/routers/auth.py

# Importa as classes do Flask para criar o Blueprint e lidar com requisições
from flask import Blueprint, request, jsonify

# Importa o gerenciador de token JWT
from flask_jwt_extended import create_access_token

# Importa nosso serviço de usuário
from app.services import user_service

# Importa o schema para validação e o erro de validação
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

# Cria um "Blueprint". Pense nisso como um "mini-app"
# focado apenas em autenticação.
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint para registrar um novo usuário.
    Espera um JSON com: username, email, password
    """
    # 1. Pega o JSON enviado na requisição
    json_data = request.get_json()
    if not json_data:
        return jsonify(error="Nenhum dado de entrada fornecido"), 400

    # 2. Valida os dados usando o Marshmallow schema
    try:
        # 'load()' valida e levanta ValidationError se falhar
        data = user_schema.load(json_data)
    except ValidationError as err:
        # Retorna os erros de validação
        return jsonify(errors=err.messages), 422 # 422 Unprocessable Entity

    # 3. Chama o serviço para criar o usuário
    try:
        new_user = user_service.create_user(data)
    except ValidationError as err:
        # Captura erros de "usuário já existe" do serviço
        return jsonify(errors=err.messages), 409 # 409 Conflict
    except Exception as e:
        return jsonify(error=str(e)), 500 # Erro interno do servidor

    # 4. Retorna o usuário criado (sem a senha)
    return jsonify(user_schema.dump(new_user)), 201 # 201 Created

@bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para logar um usuário.
    Espera um JSON com: email, password
    """
    # 1. Pega o JSON da requisição
    json_data = request.get_json()
    if not json_data:
        return jsonify(error="Nenhum dado de entrada fornecido"), 400

    email = json_data.get('email')
    password = json_data.get('password')

    if not email or not password:
        return jsonify(error="Email e senha são obrigatórios"), 400

    # 2. Chama o serviço de autenticação
    user = user_service.authenticate_user(email, password)

    # 3. Se a autenticação falhar
    if not user:
        return jsonify(error="Email ou senha inválidos"), 401 # 401 Unauthorized

    # 4. Se for sucesso, cria o token JWT
    # O 'identity' pode ser qualquer coisa que identifique o usuário
    # Usar o ID do usuário é o padrão
    access_token = create_access_token(identity=user.id)
    
    # 5. Retorna o token para o cliente
    return jsonify(access_token=access_token), 200 # 200 OK

@bp.route('/guest', methods=['POST'])
def create_guest():
    """
    Cria uma conta de convidado temporária e retorna um token de acesso.
    Não recebe JSON.
    """

    try:
        guest_user = user_service.create_guest_user()
    
        if not guest_user: 
            return jsonify(error="Não foi possível criar a conta de convidado"), 500
        
        acess_token = create_acess_token(identify=guest_user.id)
        guest_data = user_schema.dump(guest_user)

        return jsonify(
            acess_token=acess_token,
            user=guest_data
        ), 200
    
    except Exception as e: 
        return jsonify(error=str(e)), 500