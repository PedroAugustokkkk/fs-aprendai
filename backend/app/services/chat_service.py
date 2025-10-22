# /app/services/chat_service.py

def get_chat_response(prompt, user_id):
    # Lógica de IA (gemini) e RAG virá aqui
    print(f"Processando chat para usuário {user_id}...")
    
    # Por agora, vamos apenas simular uma resposta
    response_text = f"Recebi sua mensagem: '{prompt}'. Em breve, falarei com o Gemini."
    
    # Salvar no histórico (lógica futura)
    
    return response_text