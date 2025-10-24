# /app/models/task_model.py
from app.extensions import db
import datetime

class Task(db.Model):
    __tablename__ = "tasks"
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # --- Chave Estrangeira ---
    # Define que a coluna 'user_id' é uma chave estrangeira
    # que aponta para a coluna 'id' da tabela 'users'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}>'