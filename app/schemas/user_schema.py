from app.extensions import ma 
from app.models.user_model import User 
from marshmallow import fields 

class UserSchema(ma.SQLAlchemyAutoSchema):
    password = fields.String(load_only=True, required=False, allow_none=True) 

    class Meta:
        model = User
        load_instance = False 
        exclude = ("password_hash", "tasks", "chat_histories")

    id = ma.auto_field(dump_only=True)
    created_at = ma.auto_field(dump_only=True)

    email = fields.Email(required=False, allow_none=True)

    username = fields.String(required=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
