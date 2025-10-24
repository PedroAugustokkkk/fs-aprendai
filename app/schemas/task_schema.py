# /app/schemas/task_schema.py
from app.extensions import ma
from app.models.task_model import Task

class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
        include_fk = True # Inclui a 'user_id' no schema

    id = ma.auto_field(dump_only=True)
    created_at = ma.auto_field(dump_only=True)

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)