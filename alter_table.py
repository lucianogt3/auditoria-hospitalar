from sqlalchemy import create_engine, text

# Substitua com sua string de conexão
db_url = "postgresql+psycopg2://auditor:CMV27p8dL9qgz4DpY3Tmf3ykahM8VQ2E@dpg-d0mp6immcj7s739gtdj0-a.oregon-postgres.render.com/auditoria_1dna?sslmode=require"
engine = create_engine(db_url)

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(512);'))
    print("Alteração aplicada com sucesso.")
