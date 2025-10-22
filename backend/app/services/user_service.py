# /app/services/user_service.py

from app.models.user_model import User
from app.extensions import db
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

def create_user(data):
    """
    Cria um novo usuário no banco de dados.
    'data' é um dicionário já validado pelo UserSchema.
    """
    
    # 1. Verifica se o usuário ou e-mail já existem
    if User.query.filter_by(username=data['username']).first():
        raise ValidationError('Nome de usuário já existe.', field_name='username')
    if User.query.filter_by(email=data['email']).first():
        raise ValidationError('E-mail já cadastrado.', field_name='email')

    # 2. Deserializa os dados validados para um objeto User
    # 'load_instance=True' no schema faz isso funcionar
    new_user = user_schema.load(data)

    # 3. Seta a senha (o 'password_hash' foi carregado pelo schema)
    # O modelo User tem o método set_password para hashear
    # Vamos ajustar o schema e o modelo para trabalhar com a senha pura
    
    # --- Vamos simplificar a lógica de senha ---
    # (Vamos ajustar o modelo e schema depois, por agora vamos assumir
    # que o schema nos deu um objeto User sem a senha)
    
    # Criando o usuário com os dados
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    # Seta a senha, que será hasheada pelo método do modelo
    new_user.set_password(data['password'])

    # 4. Adiciona ao banco e commita
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Retorna um erro genérico de banco
        raise Exception(f"Erro ao salvar no banco: {str(e)}")

    # 5. Retorna o usuário criado (sem a senha)
    return user_schema.dump(new_user)

def authenticate_user(email, password):
    """
    Autentica um usuário, retornando o objeto User se for válido.
    """
    # 1. Encontra o usuário pelo e-mail
    user = User.query.filter_by(email=email).first()

    # 2. Verifica se o usuário existe E se a senha está correta
    if user and user.check_password(password):
        return user
    
    # Se falhar, retorna None
    return None

def create_guest_user():
    """
    Cria uma nova conta de convidado e a salva no banco.
    """
    try:
        guest_user = User.create_guest_user()

        db.session.add(guest_user)
        db.session.commit()
        
        return guest_user
    
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao criar conta de convidado: {str(e)}")