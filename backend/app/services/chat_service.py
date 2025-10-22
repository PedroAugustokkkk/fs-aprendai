# /app/services/chat_service.py

# Importa o 'genai' que foi configurado no __init__
import google.generativeai as genai

# Importa as ferramentas de banco de dados
from app.extensions import db
from app.models.chat_history_model import ChatHistory
from app.schemas.chat_history_schema import chat_history_schema

# --- NOVA IMPORTAÇÃO ---
# Importa nosso serviço de RAG para fazer a busca
from app.services import rag_service

# --- O NOVO CÉREBRO (RAG-AWARE) ---
# Esta instrução é CRÍTICA. Ela ensina a IA a priorizar o contexto.
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
    """
    Processa uma mensagem de chat, consulta o RAG,
    injeta o contexto no Gemini e salva o histórico.
    """
    try:
        # --- 1. Salvar a Mensagem do Usuário (igual a antes) ---
        user_message = ChatHistory(
            session_id=session_id,
            role="user",
            message=prompt,
            user_id=user_id
        )
        db.session.add(user_message)
        
        # --- 2. Carregar o Histórico da Conversa (igual a antes) ---
        history_db = ChatHistory.query.filter_by(
            user_id=user_id, 
            session_id=session_id
        ).order_by(ChatHistory.timestamp.asc()).all()

        history_for_gemini = []
        for msg in history_db:
             history_for_gemini.append({
                 "role": msg.role,
                 "parts": [msg.message]
             })

        # --- 3. NOVO PASSO: Buscar Contexto no RAG (Qdrant) ---
        # Usa o prompt do usuário para buscar chunks relevantes no Qdrant
        contexts = rag_service.search_relevant_chunks(
            query=prompt, 
            user_id=user_id
        )
        
        # --- 4. NOVO PASSO: Criar o "Prompt Aumentado" ---
        # Prepara o contexto para ser injetado no prompt
        context_string = "Nenhum contexto encontrado no material de estudo."
        if contexts:
            # Concatena os chunks de texto encontrados
            context_string = "\n\n".join(contexts)

        # Monta o prompt final que será enviado ao Gemini
        # Isso "aumenta" o prompt do usuário com o contexto do RAG
        augmented_prompt = f"""
        --- CONTEXTO FORNECIDO ---
        {context_string}
        --- FIM DO CONTEXTO ---

        PERGUNTA DO ALUNO:
        {prompt}
        """

        # --- 5. Inicializar e Chamar o Modelo Gemini ---
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            system_instruction=SYSTEM_INSTRUCTION # A nova instrução RAG-aware
        )
        
        chat_session = model.start_chat(history=history_for_gemini[:-1])

        # Envia o PROMPT AUMENTADO (RAG) para o Gemini
        response = chat_session.send_message(augmented_prompt)

        # --- 6. Salvar a Resposta da IA (igual a antes) ---
        model_message = ChatHistory(
            session_id=session_id,
            role="model",
            message=response.text,
            user_id=user_id
        )
        db.session.add(model_message)
        
        # --- 7. Commitar tudo (igual a antes) ---
        db.session.commit()

        # --- 8. Retornar a Resposta da IA (igual a antes) ---
        return chat_history_schema.dump(model_message)

    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro no serviço de chat: {str(e)}")