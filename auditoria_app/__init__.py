import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .extensions import mail
from .config import Config
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# Inicializa extensões globais
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    login_manager.login_view = 'auth.login'

    from .models import User, Auditoria

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main
    from .auth import auth as auth_blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint)

    @app.template_filter('getattr')
    def jinja_getattr(obj, attr):
        return getattr(obj, attr)

    return app
