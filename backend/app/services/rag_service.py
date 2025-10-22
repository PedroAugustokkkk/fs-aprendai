# /app/services/rag_service.py

import google.generativeai as genai
from app.extensions import qdrant # Nosso cliente Qdrant
from app.core.config import settings # Nossas configurações
import pypdf
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid

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
            full_text += page.extract_text()
            
        if not full_text:
            raise Exception("Não foi possível extrair texto do PDF.")

        # --- 2. "Chunking" (Quebrar o texto em pedaços) ---
        # Usamos um divisor de texto da Langchain para isso
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, # Pedaços de ~1000 caracteres
            chunk_overlap=100, # Com 100 caracteres de sobreposição
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(full_text)
        
        if not chunks:
            raise Exception("O texto era muito curto para ser processado.")

        # --- 3. "Embedding" (Gerar vetores para os chunks) ---
        # Chamamos a API do Google para gerar embeddings para todos os chunks de uma vez
        # Usamos o modelo 'text-embedding-004' (ou similar)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT" # Importante: diz que é para RAG
        )
        embeddings = result['embedding']

        # --- 4. Armazenar no Qdrant ---
        # Prepara os "pontos" (vetores + metadados) para o Qdrant
        points = []
        for i, chunk_text in enumerate(chunks):
            points.append(
                {
                    'id': str(uuid.uuid4()), # ID único para cada chunk
                    'vector': embeddings[i], # O vetor numérico
                    'payload': {
                        'text': chunk_text, # O texto original do chunk
                        'user_id': user_id, # **CRUCIAL: Associa o chunk ao usuário**
                        'doc_name': file_storage.filename # Nome do arquivo original
                    }
                }
            )

        # Envia os pontos para o Qdrant em lote
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True # Espera a operação ser concluída
        )

        return f"Documento '{file_storage.filename}' processado e armazenado com sucesso. {len(chunks)} chunks criados."

    except Exception as e:
        # Log do erro (em um app real)
        print(f"Erro no rag_service: {e}")
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
            task_type="RETRIEVAL_QUERY" # Importante: diz que é para busca
        )
        query_vector = result['embedding']

        # 2. Busca no Qdrant
        hits = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3, # Retorna os 3 chunks mais relevantes
            query_filter={
                "must": [
                    {
                        "key": "user_id", # Filtra o payload
                        "match": {
                            "value": user_id # **CRUCIAL: Só busca nos docs deste usuário**
                        }
                    }
                ]
            }
        )
        
        # 3. Formata os resultados (apenas o texto)
        contexts = [hit.payload['text'] for hit in hits]
        return contexts

    except Exception as e:
        print(f"Erro ao buscar no Qdrant: {e}")
        raise Exception(f"Falha ao buscar contexto: {str(e)}")