# /app/services/chat_service.py

# Importa o 'genai' que foi configurado no __init__
import google.generativeai as genai

# Importa as ferramentas de banco de dados
from app.extensions import db
from app.models.chat_history_model import ChatHistory
from app.schemas.chat_history_schema import chat_history_schema

# --- O Cérebro do Tutor (O Prompt de Sistema) ---
# Esta é a personalidade que definimos, agora morando no backend
SYSTEM_INSTRUCTION = """
Você é um tutor de IA chamado Gênio Guiado. Sua especialidade é ajudar estudantes a resolverem problemas de forma eficiente e estratégica, focando no desenvolvimento do raciocínio.
Seu método NÃO é dar a resposta, mas sim co-criar o caminho para a solução com o aluno.
Siga estritamente as seguintes regras:
1.  **Apresentação Rápida**: Apresente-se brevemente e peça ao aluno para apresentar o tópico ou a questão que ele quer resolver. (Se for o início da conversa).
2.  **Crie um "Plano de Ataque"**: Ao receber a questão, sua primeira ação é apresentar um plano simples e numerado de como abordá-la.
3.  **Assuma Compreensão, Ofereça Aprofundamento**: Explique os conceitos em blocos lógicos. Ao final de um bloco, NÃO pergunte "Você entendeu?". Em vez disso, assuma que ele entendeu e convide-o para a próxima ação.
4.  **Ajuda Progressiva e Adaptativa**: Se o aluno errar ou disser que não sabe, ative um sistema de ajuda em níveis (Dica Conceitual, Exemplo Análogo, Próximo Passo Direto).
5.  **Seja Conciso e Focado**: Mantenha a linguagem direta e objetiva, mas sempre encorajadora.
6.  **Resumo Estratégico**: Ao final, quando o aluno chegar à resposta, parabenize-o e faça um resumo rápido da ESTRATÉGIA usada.
"""

def send_chat_message(prompt: str, session_id: str, user_id: int):
    """
    Processa uma mensagem de chat, consulta o Gemini e salva o histórico.
    """
    try:
        # --- 1. Salvar a Mensagem do Usuário ---
        # Primeiro, salvamos a pergunta do usuário no banco.
        user_message = ChatHistory(
            session_id=session_id,
            role="user",
            message=prompt,
            user_id=user_id
        )
        db.session.add(user_message)
        
        # --- 2. Carregar o Histórico da Conversa ---
        # Busca todas as mensagens desta sessão e deste usuário, em ordem.
        history_db = ChatHistory.query.filter_by(
            user_id=user_id, 
            session_id=session_id
        ).order_by(ChatHistory.timestamp.asc()).all()

        # Formata o histórico para o formato que a API do Gemini espera
        # (Remove a última mensagem, pois é a que estamos respondendo)
        history_for_gemini = []
        for msg in history_db:
             history_for_gemini.append({
                 "role": msg.role,
                 "parts": [msg.message]
             })

        # --- 3. Inicializar e Chamar o Modelo Gemini ---
        # Inicializa o modelo com o cérebro (system_instruction)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-latest", # Usando o modelo robusto
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Inicia a sessão de chat, passando o histórico formatado
        chat_session = model.start_chat(history=history_for_gemini[:-1]) # Pega todo o histórico, exceto a msg atual

        # Envia a nova mensagem (prompt) para o Gemini
        response = chat_session.send_message(prompt)

        # --- 4. Salvar a Resposta da IA ---
        # Salva a resposta do modelo no banco de dados.
        model_message = ChatHistory(
            session_id=session_id,
            role="model",
            message=response.text,
            user_id=user_id
        )
        db.session.add(model_message)
        
        # --- 5. Commitar tudo no Banco ---
        db.session.commit()

        # --- 6. Retornar a Resposta da IA ---
        # Serializa a resposta da IA para enviar de volta ao front-end
        return chat_history_schema.dump(model_message)

    except Exception as e:
        db.session.rollback() # Desfaz as alterações se algo der errado
        raise Exception(f"Erro no serviço de chat: {str(e)}")