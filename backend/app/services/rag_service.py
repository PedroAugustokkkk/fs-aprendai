# /app/services/rag_service.py

import google.generativeai as genai
from app.extensions import qdrant # Nosso cliente Qdrant
from app.core.config import settings # Nossas configurações
import pypdf
from io import BytesIO
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
# Importa models necessários para delete
from qdrant_client import models

# Define o nome da coleção que usaremos no Qdrant
COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME

def process_and_store_document(file_storage, user_id: int):
    """
    Processa um arquivo PDF, o vetoriza e armazena no Qdrant.
    'file_storage' é o objeto de arquivo do Flask (request.files['file']).
    """
    
    try:
        # --- 1. Ler o PDF e Extrair o Texto ---
        pdf_bytes = file_storage.read()
        pdf_file = BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or "" # Garante que é string
            
        if not full_text:
            raise Exception("Não foi possível extrair texto do PDF.")

        # --- 2. "Chunking" (Quebrar o texto em pedaços) ---
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(full_text)
        
        if not chunks:
            raise Exception("O texto era muito curto para ser processado.")

        # --- 3. "Embedding" (Gerar vetores para os chunks) ---
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings = result['embedding']

        # --- 4. Armazenar no Qdrant ---
        points_to_insert = []
        # Gera IDs únicos para os pontos a serem inseridos
        point_ids = [str(uuid.uuid4()) for _ in chunks]

        for i, chunk_text in enumerate(chunks):
            points_to_insert.append(
                models.PointStruct( # Usa a classe PointStruct
                    id=point_ids[i],
                    vector=embeddings[i],
                    payload={
                        'text': chunk_text,
                        'user_id': user_id,
                        'doc_name': file_storage.filename # Nome do arquivo original
                    }
                )
            )

        # Envia os pontos para o Qdrant em lote
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_insert,
            wait=True
        )

        return f"Documento '{file_storage.filename}' processado e armazenado com sucesso. {len(chunks)} chunks criados."

    except Exception as e:
        print(f"Erro no rag_service (process): {e}")
        raise Exception(f"Falha ao processar o documento: {str(e)}")

def search_relevant_chunks(query: str, user_id: int):
    """
    Busca no Qdrant os chunks mais relevantes para uma pergunta,
    filtrando pelo usuário logado.
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
            query_filter=models.Filter( # Usa a classe Filter
                must=[
                    models.FieldCondition( # Usa FieldCondition
                        key="user_id",
                        match=models.MatchValue(value=user_id) # Usa MatchValue
                    )
                ]
            )
        )
        
        # 3. Formata os resultados (apenas o texto)
        contexts = [hit.payload['text'] for hit in search_result]
        return contexts

    except Exception as e:
        print(f"Erro ao buscar no Qdrant: {e}")
        # Retorna lista vazia em caso de erro na busca para não quebrar o chat
        return [] 

# --- NOVA FUNÇÃO ---
def list_documents(user_id: int):
    """
    Lista os nomes de documentos únicos para um usuário consultando o Qdrant.
    """
    try:
        # Usa a busca com scroll para pegar alguns pontos do usuário
        # Limitamos a busca, pois só precisamos dos nomes distintos
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
            limit=100, # Pega até 100 chunks (ajuste se necessário)
            with_payload=['doc_name'] # Só precisamos do nome do documento
        )
        
        # Extrai os nomes únicos
        doc_names = set(hit.payload['doc_name'] for hit in scroll_response if hit.payload and 'doc_name' in hit.payload)
        
        # Retorna como uma lista de dicionários para o schema
        return [{"doc_name": name} for name in sorted(list(doc_names))]

    except Exception as e:
        print(f"Erro ao listar documentos do Qdrant: {e}")
        raise Exception(f"Falha ao listar documentos: {str(e)}")

# --- NOVA FUNÇÃO ---
def delete_document_by_name(doc_name: str, user_id: int):
    """
    Deleta todos os chunks associados a um doc_name e user_id do Qdrant.
    """
    try:
        # Deleta pontos usando um filtro
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
            wait=True # Espera a conclusão
        )
        
        print(f"Resultado da deleção para '{doc_name}' do user {user_id}: {delete_result}")
        # Verifica se algum ponto foi afetado (opcional, mas bom para feedback)
        if delete_result.status == models.UpdateStatus.COMPLETED:
             # Poderíamos retornar quantos pontos foram deletados se a API do Qdrant fornecer
             return True
        else:
             # Pode ter completado mas não deletado nada se o filtro não bateu
             return True # Retorna True mesmo se 0 pontos foram deletados
             
    except Exception as e:
        print(f"Erro ao deletar documento '{doc_name}' do Qdrant: {e}")
        raise Exception(f"Falha ao deletar documento: {str(e)}")
