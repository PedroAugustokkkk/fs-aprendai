# /app/services/task_service.py

from app.models.task_model import Task
from app.extensions import db
from app.schemas.task_schema import task_schema, tasks_schema
from marshmallow import ValidationError

def create_task(data, user_id):
    """
    Cria uma nova tarefa para o usuário logado.
    'data' é um dicionário já validado pelo TaskSchema.
    """
    try:
        # 1. Carrega os dados em um objeto Task
        # (O schema vai garantir que 'content' existe)
        new_task = task_schema.load(data)
        
        # 2. Associa a tarefa ao ID do usuário
        new_task.user_id = user_id

        # 3. Salva no banco de dados
        db.session.add(new_task)
        db.session.commit()
        
        # 4. Retorna a tarefa criada e serializada
        return task_schema.dump(new_task)
    
    except ValidationError as err:
        # Repassa o erro de validação
        raise err
    except Exception as e:
        db.session.rollback()
        # Retorna um erro genérico
        raise Exception(f"Erro ao criar tarefa: {str(e)}")


def get_tasks_by_user(user_id):
    """
    Busca todas as tarefas de um usuário específico.
    """
    try:
        # 1. Busca todas as tarefas filtrando pelo user_id
        tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
        
        # 2. Serializa a lista de tarefas e retorna
        return tasks_schema.dump(tasks)
    
    except Exception as e:
        raise Exception(f"Erro ao buscar tarefas: {str(e)}")

def get_task_by_id(task_id, user_id):
    """
    Busca uma tarefa específica, garantindo que ela pertence ao usuário.
    """
    try:
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        return task
    except Exception as e:
        raise Exception(f"Erro ao buscar tarefa: {str(e)}")


def update_task(task_id, data, user_id):
    """
    Atualiza uma tarefa existente (ex: marcar como concluída).
    """
    task = get_task_by_id(task_id, user_id)
    if not task:
        return None # Tarefa não encontrada ou não pertence ao usuário

    try:
        # Atualiza os campos permitidos
        if 'content' in data:
            task.content = data['content']
        if 'is_completed' in data:
            task.is_completed = data['is_completed']
        
        db.session.commit()
        return task_schema.dump(task)
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao atualizar tarefa: {str(e)}")


def delete_task(task_id, user_id):
    """
    Deleta uma tarefa.
    """
    task = get_task_by_id(task_id, user_id)
    if not task:
        return False # Tarefa não encontrada ou não pertence ao usuário

    try:
        db.session.delete(task)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Erro ao deletar tarefa: {str(e)}")