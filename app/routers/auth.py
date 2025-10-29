# /app/routers/auth.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services import user_service
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

bp = Blueprint('auth', __name__, url_prefix='/auth')

# // # --- ROTA DE REGISTRO COMENTADA ---
# // # @bp.route('/register', methods=['POST'])
# // # def register():
# // #     json_data = request.get_json()
# // #     if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400
# // #     try:
# // #         data = user_schema.load(json_data) 
# // #     except ValidationError as err:
# // #         return jsonify(errors=err.messages), 422
# // #     try:
# // #         new_user_data = user_service.create_user(data) # // Chama a função create_user que será comentada
# // #         return jsonify(new_user_data), 201 
# // #     except ValidationError as err:
# // #         return jsonify(errors=err.messages), 409
# // #     except Exception as e:
# // #         print(f"ERRO /register: {e}")
# // #         return jsonify(error="Erro interno ao registrar usuário."), 500

# // # --- ROTA DE LOGIN COMENTADA ---
# // # @bp.route('/login', methods=['POST'])
# // # def login():
# // #     json_data = request.get_json()
# // #     if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400
# // #     email = json_data.get('email')
# // #     password = json_data.get('password')
# // #     if not email or not password: return jsonify(error="Email e senha são obrigatórios"), 400
# // #     
# // #     user = user_service.authenticate_user(email, password) # // Chama a função authenticate_user que será comentada
# // #     if not user: return jsonify(error="Email ou senha inválidos"), 401
# // #         
# // #     access_token = create_access_token(identity=user.id)
# // #     user_data = user_schema.dump(user)
# // #     return jsonify(access_token=access_token, user=user_data), 200

@bp.route('/guest', methods=['POST'])
def create_guest():
    try:
        # // Esta rota continua funcionando para criar o convidado
        guest_user = user_service.create_guest_user()
        if not guest_user: return jsonify(error="Não foi possível criar a conta de convidado"), 500
            
        access_token = create_access_token(identity=guest_user.id)
        guest_data = user_schema.dump(guest_user) 
        
        return jsonify(access_token=access_token, user=guest_data), 200
    except Exception as e:
        print(f"ERRO /guest: {e}")
        return jsonify(error="Erro interno ao criar convidado."), 500

@bp.route('/me', methods=['GET'])
@jwt_required() # // Esta rota continua útil para o frontend buscar dados do guest/usuário logado
def get_current_user():
    current_user_id = get_jwt_identity() 
    try:
        user = user_service.get_user_by_id(current_user_id)
        if not user:
            return jsonify(error="Usuário não encontrado"), 404
        
        return jsonify(user_schema.dump(user)), 200
    except Exception as e:
        print(f"ERRO /me: {e}")
        return jsonify(error="Erro ao buscar dados do usuário."), 500
