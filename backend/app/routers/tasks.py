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

# (Vamos adicionar as rotas de Update e Delete em breve,
# mas POST e GET são o essencial para começar)