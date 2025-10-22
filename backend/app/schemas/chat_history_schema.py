# /app/schemas/chat_history_schema.py
from app.extensions import ma
from app.models.chat_history_model import ChatHistory

class ChatHistorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ChatHistory
        load_instance = True
        include_fk = True

    id = ma.auto_field(dump_only=True)
    timestamp = ma.auto_field(dump_only=True)

chat_history_schema = ChatHistorySchema()
chat_histories_schema = ChatHistorySchema(many=True)