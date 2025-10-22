# /app/routers/chat.py

from flask import Blueprint, request, jsonify, escape
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import chat_service
from marshmallow import ValidationError

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data: return jsonify(error="Nenhum dado de entrada fornecido"), 400
    prompt = json_data.get('prompt')
    session_id = json_data.get('session_id')
    if not prompt: return jsonify(error="O campo 'prompt' é obrigatório"), 400
    if not session_id: return jsonify(error="O campo 'session_id' é obrigatório"), 400
    try:
        ai_response = chat_service.send_chat_message(
            prompt=prompt,
            session_id=escape(session_id), # Sanitiza session_id
            user_id=current_user_id
        )
        return jsonify(ai_response), 200
    except Exception as e:
        # Log do erro real no servidor para debug
        print(f"ERRO no endpoint /chat/send: {e}") 
        # Mensagem genérica para o cliente
        return jsonify(error="Ocorreu um erro ao processar sua mensagem."), 500


# --- NOVA ROTA ---
@bp.route('/<string:session_id>', methods=['GET'])
@jwt_required()
def get_history(session_id):
    """
    Busca o histórico de mensagens para uma sessão de chat específica.
    """
    current_user_id = get_jwt_identity()
    # Sanitiza o session_id vindo da URL
    safe_session_id = escape(session_id)
    
    try:
        history = chat_service.get_chat_history(safe_session_id, current_user_id)
        # O serviço já retorna os dados serializados
        return jsonify(history), 200
    except Exception as e:
        print(f"ERRO no endpoint GET /chat/{safe_session_id}: {e}")
        return jsonify(error="Ocorreu um erro ao buscar o histórico."), 500
