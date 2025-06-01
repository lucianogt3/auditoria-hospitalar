from auditoria_app import create_app, db
from auditoria_app.models import User, Prestador, CID, Auditoria

app = create_app()

with app.app_context():
    db.create_all()
    print("Banco de dados e tabelas criados com sucesso.")
