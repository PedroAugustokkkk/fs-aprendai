# /app/routers/documents.py

from flask import Blueprint, request, jsonify
from markupsafe import escape
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import rag_service
# --- NOVA IMPORTAÇÃO ---
from app.schemas.document_schema import documents_schema 
import os

bp = Blueprint('documents', __name__, url_prefix='/documents')

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    current_user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify(error="Nenhum arquivo enviado"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="Nenhum arquivo selecionado"), 400
    if not file or not allowed_file(file.filename):
        return jsonify(error="Formato de arquivo não permitido. Envie apenas .pdf"), 400
    try:
        result_message = rag_service.process_and_store_document(
            file_storage=file,
            user_id=current_user_id
        )
        return jsonify(message=result_message), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

# --- NOVA ROTA ---
@bp.route('/', methods=['GET'])
@jwt_required()
def list_documents():
    """
    Lista os documentos enviados pelo usuário logado.
    """
    current_user_id = get_jwt_identity()
    try:
        docs = rag_service.list_documents(current_user_id)
        # Serializa usando o schema de documentos
        return jsonify(documents_schema.dump(docs)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

# --- NOVA ROTA ---
@bp.route('/<string:doc_name>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_name):
    """
    Deleta um documento (e todos os seus chunks) pelo nome.
    O nome do documento vem da URL.
    """
    current_user_id = get_jwt_identity()
    # Simples sanitização do nome do arquivo (importante!)
    safe_doc_name = escape(doc_name) 
    
    try:
        was_deleted = rag_service.delete_document_by_name(safe_doc_name, current_user_id)
        if not was_deleted:
             # Pode significar que não encontrou ou erro no serviço
             # O serviço já loga o erro, retornamos 404 por segurança
            return jsonify(error="Documento não encontrado ou falha ao deletar"), 404
            
        return '', 204 # No Content
    except Exception as e:
        return jsonify(error=str(e)), 500
