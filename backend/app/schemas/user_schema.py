# /app/schemas/user_schema.py
from app.extensions import ma
from app.models.user_model import User
from marshmallow import fields

class UserSchema(ma.SQLAlchemyAutoSchema):
    # SQLAlchemyAutoSchema magicamente cria campos do schema
    # baseados no modelo SQLAlchemy.
    
    class Meta:
        model = User        # Liga este schema ao modelo User
        load_instance = True # Permite carregar dados direto para um objeto User
        # Exclui o 'tasks' e 'chat_histories' do dump principal
        # para não poluir a resposta de usuário (teremos endpoints para eles)
        exclude = ("tasks", "chat_histories", "password_hash")

    # --- Validação e Segurança ---
    # Define regras extras para os campos
    
    # 'load_only=True' significa que este campo é ACEITO
    # ao criar um usuário, mas NUNCA é ENVIADO de volta
    # em uma resposta. Isso protege o hash da senha.
    password_hash = ma.auto_field(load_only=True, required=True)
    
    # 'dump_only=True' significa que este campo é ENVIADO
    # na resposta, mas não é esperado na criação (é gerado auto)
    id = ma.auto_field(dump_only=True)
    created_at = ma.auto_field(dump_only=True)
    
    # Adiciona validação de e-mail
    email = fields.Email(required=True)
    username = fields.String(required=True)

# Instancia os schemas para uso fácil
user_schema = UserSchema()              # Para um único usuário
users_schema = UserSchema(many=True)    # Para uma lista de usuários