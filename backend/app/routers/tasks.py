# /app/routers/tasks.py

from flask import Blueprint, request, jsonify
# Importa o decorator de proteção e a função para pegar a ID do usuário
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import task_service
from app.schemas.task_schema import task_schema, tasks_schema
from marshmallow import ValidationError

# Cria o Blueprint para /tasks
bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@bp.route('/', methods=['POST'])
@jwt_required() # <--- MÁGICA AQUI: Protege este endpoint
def create_task():
    """
    Cria uma nova tarefa. Requer autenticação JWT.
    Espera JSON: { "content": "Minha nova tarefa" }
    """
    # 1. Pega a ID do usuário a partir do token JWT
    current_user_id = get_jwt_identity()
    
    # 2. Pega o JSON da requisição
    json_data = request.get_json()
    if not json_data:
        return jsonify(error="Nenhum dado de entrada fornecido"), 400

    # 3. Valida os dados com o schema
    try:
        data = task_schema.load(json_data)
    except ValidationError as err:
        return jsonify(errors=err.messages), 422

    # 4. Chama o serviço para criar a tarefa
    try:
        new_task = task_service.create_task(data, current_user_id)
        return jsonify(new_task), 201
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route('/', methods=['GET'])
@jwt_required() # <--- MÁGICA AQUI: Protege este endpoint
def get_tasks():
    """
    Busca todas as tarefas do usuário logado. Requer autenticação JWT.
    """
    # 1. Pega a ID do usuário a partir do token JWT
    current_user_id = get_jwt_identity()

    # 2. Chama o serviço para buscar as tarefas
    try:
        tasks = task_service.get_tasks_by_user(current_user_id)
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """
    Busca uma tarefa específica pelo ID.
    """
    current_user_id = get_jwt_identity()
    try:
        # O serviço já garante que a tarefa pertence ao usuário
        task = task_service.get_task_by_id(task_id, current_user_id)
        if not task:
            return jsonify(error="Tarefa não encontrada"), 404
        
        return jsonify(task_schema.dump(task)), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """
    Atualiza uma tarefa (ex: marcar como concluída).
    Espera JSON: { "content": "Novo texto", "is_completed": true }
    """
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        return jsonify(error="Nenhum dado de entrada fornecido"), 400

    # Validação simples (não precisa do schema completo para atualizar)
    valid_data = {}
    if 'content' in json_data:
        valid_data['content'] = json_data['content']
    if 'is_completed' in json_data:
        valid_data['is_completed'] = json_data['is_completed']
        
    if not valid_data:
        return jsonify(error="Nenhum campo válido para atualização"), 400

    try:
        updated_task = task_service.update_task(task_id, valid_data, current_user_id)
        if not updated_task:
            return jsonify(error="Tarefa não encontrada"), 404
            
        return jsonify(updated_task), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """
    Deleta uma tarefa.
    """
    current_user_id = get_jwt_identity()
    try:
        was_deleted = task_service.delete_task(task_id, current_user_id)
        if not was_deleted:
            return jsonify(error="Tarefa não encontrada"), 404
            
        # Retorna uma resposta vazia com status 204 (No Content)
        return '', 204
    except Exception as e:
        return jsonify(error=str(e)), 500