# /app/routers/chat.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import chat_service
from marshmallow import ValidationError

# Cria o Blueprint para /chat
bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/send', methods=['POST'])
@jwt_required() # Protege o endpoint de chat
def send_message():
    """
    Recebe uma mensagem do usuário, processa com o Gemini e retorna a resposta.
    Requer autenticação JWT.
    Espera JSON: { "prompt": "Minha pergunta...", "session_id": "uuid-da-sessao" }
    """
    # 1. Pega a ID do usuário a partir do token
    current_user_id = get_jwt_identity()
    
    # 2. Pega o JSON da requisição
    json_data = request.get_json()
    if not json_data:
        return jsonify(error="Nenhum dado de entrada fornecido"), 400

    prompt = json_data.get('prompt')
    session_id = json_data.get('session_id')

    # 3. Validação de entrada
    if not prompt:
        return jsonify(error="O campo 'prompt' é obrigatório"), 400
    if not session_id:
        return jsonify(error="O campo 'session_id' é obrigatório"), 400
        
    # 4. Chama o serviço de chat
    try:
        ai_response = chat_service.send_chat_message(
            prompt=prompt,
            session_id=session_id,
            user_id=current_user_id
        )
        # Retorna a resposta da IA (que já é um objeto serializado)
        return jsonify(ai_response), 200
    
    except Exception as e:
        return jsonify(error=str(e)), 500