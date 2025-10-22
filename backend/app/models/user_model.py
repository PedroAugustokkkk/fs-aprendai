# /app/models/user_model.py

# Importa o 'db' (nosso banco) e 'bcrypt' (para senhas) de extensions
from app.extensions import db, bcrypt
import datetime

class User(db.Model):
    # Define o nome da tabela no banco
    __tablename__ = "users"

    # Define as colunas
    id = db.Column(db.Integer, primary_key=True) # Chave primária
    username = db.Column(db.String(80), unique=True, nullable=False) # Nome de usuário
    email = db.Column(db.String(120), unique=True, nullable=False) # Email
    password_hash = db.Column(db.String(128), nullable=False) # Senha criptografada
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow) # Data de criação

    # --- Relacionamentos ---
    # Define a relação "um-para-muitos" com Tarefas e Histórico
    # O 'backref' cria uma propriedade virtual 'author' no modelo Task
    tasks = db.relationship('Task', backref='author', lazy=True, cascade="all, delete-orphan")
    # 'cascade' garante que, se um usuário for deletado, suas tarefas também sejam.
    chat_histories = db.relationship('ChatHistory', backref='user', lazy=True, cascade="all, delete-orphan")

    # --- Métodos de Senha ---
    def set_password(self, password):
        # Gera o hash da senha usando bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # Verifica se a senha fornecida bate com o hash salvo
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        # Representação em string do objeto (útil para debug)
        return f'<User {self.username}>'