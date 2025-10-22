# /app/extensions.py

# Importa as classes das extensões que vamos usar
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
# Cria instâncias vazias das extensões
# Elas não estão ligadas a nenhum app Flask... ainda.
# Elas serão "ligadas" na nossa fábrica de app.
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
ma = Marshmallow()