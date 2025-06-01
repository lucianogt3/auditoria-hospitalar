from auditoria_app import create_app, db
from sqlalchemy import text

# Cria o app e inicia o contexto
app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS _alembic_tmp_user"))
        print("Tabela _alembic_tmp_user excluída com sucesso.")
