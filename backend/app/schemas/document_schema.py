# /app/schemas/document_schema.py
# Importa a instância do Marshmallow das extensões
from app.extensions import ma
# Importa a classe fields do Marshmallow para definir os campos
from marshmallow import fields

# Schema simples para representar um documento listado.
# Ele não está ligado a um modelo SQLAlchemy, pois os dados vêm do Qdrant.
class DocumentSchema(ma.Schema):
    # Definimos os campos que queremos na resposta da API.
    # Usamos 'attribute' para mapear o nome do campo interno ('doc_name')
    # para o nome que queremos na API ('id', 'name').
    # 'dump_only=True' significa que este campo só aparecerá na resposta (GET),
    # não será esperado em requisições (POST/PUT).
    
    # Usamos o nome do documento como ID por simplicidade
    id = fields.Str(attribute="doc_name", dump_only=True) 
    name = fields.Str(attribute="doc_name", dump_only=True)
    # Poderíamos adicionar 'uploaded_at' se tivéssemos essa informação
    # salva no payload do Qdrant durante o upload.
    # uploaded_at = fields.Str(dump_only=True) 

# Instancia os schemas para serem usados nos routers.
# 'document_schema' para um único objeto
document_schema = DocumentSchema()
# 'documents_schema' para uma lista de objetos
documents_schema = DocumentSchema(many=True)

