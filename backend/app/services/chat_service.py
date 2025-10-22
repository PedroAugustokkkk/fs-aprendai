# /app/services/chat_service.py

import google.generativeai as genai
from app.extensions import db
from app.models.chat_history_model import ChatHistory
# --- NOVA IMPORTAÇÃO ---
from app.schemas.chat_history_schema import chat_history_schema, chat_histories_schema
from app.services import rag_service

SYSTEM_INSTRUCTION = """
Você é um tutor de IA chamado Gênio Guiado.
REGRA DE OURO: Você deve basear suas respostas no "CONTEXTO FORNECIDO" abaixo.
Sua especialidade é ajudar estudantes a entenderem o material de estudo deles.
Siga estritamente as seguintes regras:
1.  **Priorize o Contexto**: Se o "CONTEXTO FORNECIDO" não estiver vazio, sua resposta DEVE ser baseada *exclusivamente* nele. Não use seu conhecimento geral, a menos que o contexto não seja suficiente.
2.  **Seja Honesto**: Se a resposta para a pergunta do aluno não estiver no "CONTEXTO FORNECIDO", diga "Essa informação não parece estar no material de estudo que você enviou. Posso tentar responder com meu conhecimento geral?".
3.  **Não Dê Respostas Prontas**: Mesmo usando o contexto, seu objetivo é guiar. Se o contexto é um parágrafo que define 'Mitocôndria', não o recite. Use-o para criar um "Plano de Ataque" (Regra 4).
4.  **Crie um "Plano de Ataque"**: Ao receber uma questão, apresente um plano de como abordá-la usando o contexto.
5.  **Seja Conciso e Focado**: Mantenha a linguagem direta e objetiva, mas sempre encorajadora.
"""

def send_chat_message(prompt: str, session_id: str, user_id: int):
    try:
        # --- 1. Salvar Mensagem do Usuário ---
        user_message = ChatHistory(session_id=session_id, role="user", message=prompt, user_id=user_id)
        db.session.add(user_message)
        # Commit inicial para que a mensagem do user apareça no histórico carregado abaixo
        db.session.flush() 

        # --- 2. Carregar Histórico ---
        history_db = ChatHistory.query.filter_by(user_id=user_id, session_id=session_id).order_by(ChatHistory.timestamp.asc()).all()
        history_for_gemini = [{"role": msg.role, "parts": [msg.message]} for msg in history_db]

        # --- 3. Buscar Contexto RAG ---
        contexts = rag_service.search_relevant_chunks(query=prompt, user_id=user_id)
        context_string = "\n\n".join(contexts) if contexts else "Nenhum contexto encontrado no material de estudo."
        
        # --- 4. Prompt Aumentado ---
        augmented_prompt = f"---\nCONTEXTO FORNECIDO:\n{context_string}\n---\n\nPERGUNTA DO ALUNO:\n{prompt}"

        # --- 5. Chamar Gemini ---
        model = genai.GenerativeModel(model_name="gemini-pro", system_instruction=SYSTEM_INSTRUCTION)
        # Passa o histórico COMPLETO (incluindo a última msg do user) para start_chat
        chat_session = model.start_chat(history=history_for_gemini) 
        # Envia SÓ o prompt aumentado (pois o histórico já está na sessão)
        response = chat_session.send_message(augmented_prompt) 

        # --- 6. Salvar Resposta da IA ---
        model_message = ChatHistory(session_id=session_id, role="model", message=response.text, user_id=user_id)
        db.session.add(model_message)
        
        # --- 7. Commitar ---
        db.session.commit()

        # --- 8. Retornar Resposta ---
        return chat_history_schema.dump(model_message)

    except Exception as e:
        db.session.rollback()
        # Log detalhado do erro real
        print(f"ERRO DETALHADO em send_chat_message: {type(e).__name__} - {e}")
        # Retorna uma mensagem de erro genérica para o usuário
        raise Exception(f"Erro ao processar mensagem: {str(e)}")


# --- NOVA FUNÇÃO ---
def get_chat_history(session_id: str, user_id: int):
    """
    Busca todas as mensagens de uma sessão de chat específica para o usuário logado.
    """
    try:
        # Busca todas as mensagens da sessão e usuário, ordenadas pela mais antiga primeiro
        messages = ChatHistory.query.filter_by(
            user_id=user_id, 
            session_id=session_id
        ).order_by(ChatHistory.timestamp.asc()).all()
        
        # Serializa a lista de mensagens usando o schema apropriado
        return chat_histories_schema.dump(messages)

    except Exception as e:
        print(f"Erro ao buscar histórico do chat: {e}")
        raise Exception(f"Falha ao buscar histórico: {str(e)}")
