# /app/routers/auth.py

from flask import Blueprint, request, jsonify
# --- NOVA IMPORTAÇÃO ---
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services import user_service
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    json_data = request.get_json()
    if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400
    try:
        # Schema valida e carrega dados, mas NÃO cria instância aqui
        # pois precisamos setar is_guest=False explicitamente
        data = user_schema.load(json_data) 
    except ValidationError as err:
        return jsonify(errors=err.messages), 422
    try:
        # O serviço cria o User, seta a senha e is_guest
        new_user_data = user_service.create_user(data)
        return jsonify(new_user_data), 201 
    except ValidationError as err:
        return jsonify(errors=err.messages), 409
    except Exception as e:
        print(f"ERRO /register: {e}")
        return jsonify(error="Erro interno ao registrar usuário."), 500

@bp.route('/login', methods=['POST'])
def login():
    json_data = request.get_json()
    if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400
    email = json_data.get('email')
    password = json_data.get('password')
    if not email or not password: return jsonify(error="Email e senha são obrigatórios"), 400
    
    user = user_service.authenticate_user(email, password)
    if not user: return jsonify(error="Email ou senha inválidos"), 401
        
    access_token = create_access_token(identity=user.id)
    user_data = user_schema.dump(user)
    return jsonify(access_token=access_token, user=user_data), 200

@bp.route('/guest', methods=['POST'])
def create_guest():
    try:
        guest_user = user_service.create_guest_user()
        if not guest_user: return jsonify(error="Não foi possível criar a conta de convidado"), 500
            
        access_token = create_access_token(identity=guest_user.id)
        # Usa o schema para formatar os dados do convidado
        guest_data = user_schema.dump(guest_user) 
        
        return jsonify(access_token=access_token, user=guest_data), 200
    except Exception as e:
        print(f"ERRO /guest: {e}")
        return jsonify(error="Erro interno ao criar convidado."), 500

# --- NOVA ROTA ---
@bp.route('/me', methods=['GET'])
@jwt_required() # Protege a rota
def get_current_user():
    """
    Retorna os dados do usuário logado (baseado no token JWT).
    """
    current_user_id = get_jwt_identity() # Pega o ID do token
    try:
        user = user_service.get_user_by_id(current_user_id)
        if not user:
            return jsonify(error="Usuário não encontrado"), 404
        
        # Usa o schema para serializar os dados (sem senha)
        return jsonify(user_schema.dump(user)), 200
    except Exception as e:
        print(f"ERRO /me: {e}")
        return jsonify(error="Erro ao buscar dados do usuário."), 500
