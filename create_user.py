from auditoria_app import create_app, db
from auditoria_app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()  # Garante que as tabelas existem
    username = 'admin'
    password = '123456'
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    if not User.query.filter_by(username=username).first():
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print("Usuário criado com sucesso!")
    else:
        print("Usuário já existe.")
