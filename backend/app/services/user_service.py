# /app/services/user_service.py

from app.models.user_model import User
from app.extensions import db
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

def create_user(data):
    if User.query.filter_by(username=data['username']).first():
        raise ValidationError('Nome de usuário já existe.', field_name='username')
    if User.query.filter_by(email=data['email']).first():
        raise ValidationError('E-mail já cadastrado.', field_name='email')
    
    # Cria o usuário não-convidado
    new_user = User(
        username=data['username'],
        email=data['email'],
        is_guest=False # Garante que é um usuário registrado
    )
    # Define a senha (o campo 'password' vem do schema, hasheado aqui)
    new_user.set_password(data['password']) 

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao salvar no banco: {str(e)}")

    # Retorna usando o schema para NÃO incluir a senha
    return user_schema.dump(new_user) 


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    # Verifica se é um usuário registrado (não convidado) e se a senha bate
    if user and not user.is_guest and user.check_password(password):
        return user
    return None

def create_guest_user():
    try:
        guest_user = User.create_guest_user()
        db.session.add(guest_user)
        db.session.commit()
        return guest_user
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao criar conta de convidado: {str(e)}")

# --- NOVA FUNÇÃO ---
def get_user_by_id(user_id: int):
    """
    Busca um usuário pelo seu ID.
    """
    try:
        user = User.query.get(user_id) # .get() busca pela chave primária
        return user # Retorna o objeto SQLAlchemy
    except Exception as e:
        print(f"Erro ao buscar usuário por ID: {e}")
        raise Exception(f"Falha ao buscar dados do usuário: {str(e)}")
