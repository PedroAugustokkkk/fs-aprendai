# /app/services/user_service.py
from app.models.user_model import User # Importa o modelo User
from app.extensions import db # Importa a instância do banco de dados
from app.schemas.user_schema import user_schema # Importa o user_schema
from marshmallow import ValidationError # Importa o ValidationError do marshmallow

# # --- FUNÇÃO create_user COMENTADA ---
# def create_user(data): # Define a função para criar um usuário registrado
#     # Verifica se o nome de usuário já existe
#     if User.query.filter_by(username=data['username']).first(): 
#         raise ValidationError('Nome de usuário já existe.', field_name='username') # Lança erro se já existir
#     # Verifica se o email já existe
#     if User.query.filter_by(email=data['email']).first(): 
#         raise ValidationError('E-mail já cadastrado.', field_name='email') # Lança erro se já existir
#     
#     # Cria a instância do usuário não-convidado
#     new_user = User( 
#         username=data['username'], # Define o username
#         email=data['email'], # Define o email
#         is_guest=False # Define como não convidado
#     ) 
#     # Define a senha usando o método set_password do modelo
#     new_user.set_password(data['password']) 

#     try: # Tenta adicionar e salvar o novo usuário no banco
#         db.session.add(new_user) # Adiciona o novo usuário à sessão
#         db.session.commit() # Salva as alterações no banco
#     except Exception as e: # Captura qualquer exceção durante o salvamento
#         db.session.rollback() # Desfaz as alterações na sessão
#         raise Exception(f"Erro ao salvar no banco: {str(e)}") # Lança uma exceção com a mensagem de erro

#     # Retorna os dados do usuário serializados (sem senha)
#     return user_schema.dump(new_user) 

# # --- FUNÇÃO authenticate_user COMENTADA ---
# def authenticate_user(email, password): # Define a função para autenticar um usuário registrado
#     user = User.query.filter_by(email=email).first() # Busca o usuário pelo email
#     # Verifica se o usuário existe, não é convidado e a senha está correta
#     if user and not user.is_guest and user.check_password(password): 
#         return user # Retorna o objeto usuário se a autenticação for bem-sucedida
#     return None # Retorna None se a autenticação falhar

def create_guest_user(): # Define a função para criar um usuário convidado
    # Esta função continua essencial
    try: # Tenta criar e salvar o usuário convidado
        guest_user = User.create_guest_user() # Cria a instância do usuário convidado usando o método estático do modelo
        db.session.add(guest_user) # Adiciona o convidado à sessão
        db.session.commit() # Salva o convidado no banco
        return guest_user # Retorna o objeto do usuário convidado criado
    except Exception as e: # Captura qualquer exceção
        db.session.rollback() # Desfaz as alterações na sessão
        raise Exception(f"Erro ao criar conta de convidado: {str(e)}") # Lança uma exceção com a mensagem de erro

def get_user_by_id(user_id: int): # Define a função para buscar um usuário pelo ID
    # Esta função continua essencial (usada pela rota /me)
    """ # Docstring da função
    Busca um usuário pelo seu ID. # Descrição
    """ # Fim da docstring
    try: # Tenta buscar o usuário pelo ID
        user = User.query.get(user_id) # Usa o método .get() que busca pela chave primária
        return user # Retorna o objeto usuário encontrado (ou None se não encontrado)
    except Exception as e: # Captura qualquer exceção
        print(f"Erro ao buscar usuário por ID: {e}") # Loga o erro no servidor
        raise Exception(f"Falha ao buscar dados do usuário: {str(e)}") # Lança uma exceção com a mensagem de erro
