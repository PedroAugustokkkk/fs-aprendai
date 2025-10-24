# /app/tasks.py

import os # Necessário para lidar com caminhos de arquivos
import pypdf # Movido do rag_service
from io import BytesIO # Movido do rag_service
import google.generativeai as genai # Movido do rag_service
from qdrant_client import models # Movido do rag_service
from langchain_text_splitters import RecursiveCharacterTextSplitter # Movido do rag_service
import uuid # Movido do rag_service

from celery import Celery # Importa o Celery
from app import create_app # Importa nossa factory de app Flask
from app.extensions import qdrant # Importa o cliente Qdrant
from app.core.config import settings # Importa nossas configurações

# 1. Função para criar a instância do Celery
def make_celery(app):
    # Configura o Celery
    celery = Celery(
        app.import_name, # Usa o nome do app Flask
        # Usa nosso DATABASE_URL como broker (a fila de tarefas)
        broker=app.config['SQLALCHEMY_DATABASE_URI'],
        # Usa o DATABASE_URL também para guardar resultados (se precisarmos)
        backend=app.config['SQLALCHEMY_DATABASE_URI']
    )
    # Atualiza a configuração do Celery com a do Flask
    celery.conf.update(app.config)

    # Subclasse de Tarefa para "envolver" a execução da tarefa
    # no contexto do app Flask.
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            # Isso garante que db, qdrant, etc. estejam
            # configurados e acessíveis dentro da tarefa.
            with app.app_context():
                return self.run(*args, **kwargs)

    # Define a classe de Tarefa personalizada como base
    celery.Task = ContextTask
    return celery

# 2. Cria o app Flask "fora"
#    Isso é necessário para que o Celery possa acessar a config
flask_app = create_app()

# 3. Cria a instância do Celery
celery_app = make_celery(flask_app)

# 4. A TAREFA (O CÓDIGO DO WORKER)
#    Esta é a função que será executada em background.
#    Note o decorador @celery_app.task
@celery_app.task(name='tasks.process_document_task')
def process_document_task(file_path: str, user_id: int, original_filename: str):
    """
    Tarefa assíncrona que processa o PDF e o armazena no Qdrant.
    Esta função contém a lógica que *antes* estava no rag_service.
    """
    try:
        print(f"[CELERY WORKER] Iniciando processamento de: {original_filename} para user {user_id}")

        # --- 1. Ler o Arquivo (do caminho temporário) e Extrair o Texto ---
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        pdf_file = BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
            
        if not full_text:
            raise Exception("Não foi possível extrair texto do PDF.")

        # --- 2. "Chunking" ---
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(full_text)
        
        if not chunks:
            raise Exception("O texto era muito curto para ser processado.")

        # --- 3. "Embedding" ---
        # Note que o 'genai' está configurado no app_context
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )
        embeddings = result['embedding']

        # --- 4. Armazenar no Qdrant ---
        points_to_insert = []
        point_ids = [str(uuid.uuid4()) for _ in chunks]

        for i, chunk_text in enumerate(chunks):
            points_to_insert.append(
                models.PointStruct(
                    id=point_ids[i],
                    vector=embeddings[i],
                    payload={
                        'text': chunk_text,
                        'user_id': user_id,
                        'doc_name': original_filename # Nome do arquivo original
                    }
                )
            )
        
        # O 'qdrant' também está configurado no app_context
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_insert,
            wait=True
        )

        print(f"[CELERY WORKER] Sucesso: {original_filename} processado. {len(chunks)} chunks criados.")
        
        # --- 5. Limpar o arquivo temporário ---
        os.remove(file_path)
        print(f"[CELERY WORKER] Arquivo temporário {file_path} removido.")
        
        return f"Processado com sucesso: {original_filename}"

    except Exception as e:
        print(f"ERRO no CELERY WORKER ao processar {original_filename}: {e}")
        # Tenta remover o arquivo temporário mesmo em caso de erro
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[CELERY WORKER] Arquivo temporário {file_path} removido após erro.")
        # Podemos re-lançar o erro para o Celery registrar como 'FAILURE'
        raise e

# Define o nome da coleção (copiado do rag_service original)
COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME