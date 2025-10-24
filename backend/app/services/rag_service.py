# /app/services/rag_service.py

# Importa a tarefa que acabamos de criar
from app.tasks import process_document_task
# Importa 'os' para lidar com caminhos
import os
import uuid
# Importa o app Flask para pegar o caminho da pasta de uploads
from flask import current_app

# Remova estas importações, pois elas foram movidas para app/tasks.py:
# import google.generativeai as genai (MANTENHA ESTE, é usado no search_relevant_chunks)
# import pypdf
# from io import BytesIO
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# import uuid (MANTENHA ESTE)
# from qdrant_client import models (MANTENHA ESTE, é usado em outras funções)

import google.generativeai as genai # <-- MANTENHA
from app.extensions import qdrant
from app.core.config import settings
from qdrant_client import models # <-- MANTENHA

# Define o nome da coleção que usaremos no Qdrant
COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME

# --- FUNÇÃO ATUALIZADA ---
def process_and_store_document(file_storage, user_id: int):
    """
    Salva o documento temporariamente e enfileira uma tarefa
    assíncrona para processá-lo.
    'file_storage' é o objeto de arquivo do Flask (request.files['file']).
    """
    
    try:
        # --- 1. Salvar o arquivo temporariamente ---
        
        # Garante que o nome do arquivo seja seguro (embora não o usemos para Qdrant)
        # Vamos gerar um nome de arquivo único para evitar conflitos
        temp_filename = f"{uuid.uuid4()}.pdf"
        
        # Define o caminho completo para salvar o arquivo
        # current_app.root_path é a pasta 'backend'
        upload_folder = os.path.join(current_app.root_path, 'uploads')
        file_path = os.path.join(upload_folder, temp_filename)
        
        # Salva o arquivo no disco
        file_storage.save(file_path)

        # --- 2. Chamar a Tarefa Assíncrona ---
        # Pega o nome original do arquivo para salvar no Qdrant
        original_filename = file_storage.filename
        
        # Envia a tarefa para a fila do Celery
        # .delay() é o comando para executar em background
        process_document_task.delay(
            file_path=file_path,
            user_id=user_id,
            original_filename=original_filename
        )
        
        # --- 3. Retornar Resposta Imediata ---
        return f"O documento '{original_filename}' foi recebido e está sendo processado em segundo plano."

    except Exception as e:
        print(f"Erro no rag_service (enfileiramento): {e}")
        # Se falhar aqui, o arquivo pode ter sido salvo.
        # Uma lógica mais robusta poderia tentar removê-lo.
        raise Exception(f"Falha ao enfileirar o processamento do documento: {str(e)}")


def search_relevant_chunks(query: str, user_id: int):
    """
    Busca no Qdrant os chunks mais relevantes para uma pergunta,
    filtrando pelo usuário logado.
    (Esta função não muda)
    """
    try:
        # 1. Gera o embedding para a pergunta (query)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="RETRIEVAL_QUERY"
        )
        query_vector = result['embedding']

        # 2. Busca no Qdrant
        search_result = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )
        )
        
        # 3. Formata os resultados (apenas o texto)
        contexts = [hit.payload['text'] for hit in search_result]
        return contexts

    except Exception as e:
        print(f"Erro ao buscar no Qdrant: {e}")
        return [] 

# --- NOVA FUNÇÃO ---
def list_documents(user_id: int):
    # (Esta função não muda)
    try:
        scroll_response, _ = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=100,
            with_payload=['doc_name']
        )
        doc_names = set(hit.payload['doc_name'] for hit in scroll_response if hit.payload and 'doc_name' in hit.payload)
        return [{"doc_name": name} for name in sorted(list(doc_names))]
    except Exception as e:
        print(f"Erro ao listar documentos do Qdrant: {e}")
        raise Exception(f"Falha ao listar documentos: {str(e)}")

# --- NOVA FUNÇÃO ---
def delete_document_by_name(doc_name: str, user_id: int):
    # (Esta função não muda)
    try:
        delete_result = qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        ),
                        models.FieldCondition(
                            key="doc_name",
                            match=models.MatchValue(value=doc_name)
                        )
                    ]
                )
            ),
            wait=True
        )
        print(f"Resultado da deleção para '{doc_name}' do user {user_id}: {delete_result}")
        if delete_result.status == models.UpdateStatus.COMPLETED:
             return True
        else:
             return True 
    except Exception as e:
        print(f"Erro ao deletar documento '{doc_name}' do Qdrant: {e}")
        raise Exception(f"Falha ao deletar documento: {str(e)}")