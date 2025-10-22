# /app/services/rag_service.py

def process_and_store_document(file, user_id):
    # Lógica de ler PDF, "chunkar", gerar embeddings e salvar no Qdrant
    print(f"Processando documento para usuário {user_id}...")
    
    # Simulação
    filename = file.filename
    
    return f"Documento '{filename}' processado e vetorizado com sucesso."