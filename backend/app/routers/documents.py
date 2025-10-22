# /app/routers/documents.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import rag_service
import os

# Cria o Blueprint para /documents
bp = Blueprint('documents', __name__, url_prefix='/documents')

# Define as extensões de arquivo permitidas
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@jwt_required() # Protege o endpoint
def upload_document():
    """
    Recebe um arquivo (PDF) do usuário, processa e armazena para RAG.
    Requer autenticação JWT e o arquivo deve ser enviado como 'multipart/form-data'.
    """
    # 1. Pega a ID do usuário do token
    current_user_id = get_jwt_identity()
    
    # 2. Verifica se o arquivo está na requisição
    if 'file' not in request.files:
        return jsonify(error="Nenhum arquivo enviado"), 400
    
    file = request.files['file']
    
    # 3. Verifica se o nome do arquivo é válido
    if file.filename == '':
        return jsonify(error="Nenhum arquivo selecionado"), 400

    # 4. Verifica se a extensão é permitida (PDF)
    if not file or not allowed_file(file.filename):
        return jsonify(error="Formato de arquivo não permitido. Envie apenas .pdf"), 400
        
    # 5. Chama o serviço de RAG para fazer o trabalho pesado
    try:
        result_message = rag_service.process_and_store_document(
            file_storage=file,
            user_id=current_user_id
        )
        return jsonify(message=result_message), 201 # 201 Created
    
    except Exception as e:
        return jsonify(error=str(e)), 500