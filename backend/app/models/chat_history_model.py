# /app/models/chat_history_model.py
from app.extensions import db
import datetime

class ChatHistory(db.Model):
    __tablename__ = "chat_histories"

    id = db.Column(db.Integer, primary_key=True)
    # session_id permite agrupar mensagens da mesma conversa
    session_id = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False) # 'user' ou 'model'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Chave Estrangeira
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<ChatHistory {self.role} @ {self.session_id}>'