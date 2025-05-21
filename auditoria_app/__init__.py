import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .extensions import mail
from .config import Config  # Importa as configurações do seu config.py
from dotenv import load_dotenv
load_dotenv()


# Inicializa extensões
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Carrega configurações diretamente do config.py

    # Inicializa extensões no app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # Define rota padrão de login
    login_manager.login_view = 'auth.login'

    # Importa o modelo de usuário
    from .models import User
    from .models import Auditoria


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registra os Blueprints
    from .routes import main
    from .auth import auth as auth_blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint)

    # Filtro adicional para usar getattr no Jinja
    @app.template_filter('getattr')
    def jinja_getattr(obj, attr):
        return getattr(obj, attr)

    return app
