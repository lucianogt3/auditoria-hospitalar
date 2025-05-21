from auditoria_app import create_app
import os
print("DATABASE_URL:", os.getenv("DATABASE_URL"))

app = create_app()
print("SECRET_KEY:", app.config.get("SECRET_KEY"))

if __name__ == '__main__':
    app.run(debug=True)
''''''