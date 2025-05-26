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
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    app.config.from_object(Config)

    # Inicializa extensões com a instância do app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # Define a rota de login padrão para @login_required
    login_manager.login_view = 'auth.login'

    # Importa modelos necessários (evita import circular)
    from .models import User, Auditoria

    # Carregador de usuário para o Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registra os blueprints da aplicação
    from .routes import main
    from .auth import auth as auth_blueprint
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint)

    # Filtro personalizado para acessar atributos dinamicamente no Jinja
    @app.template_filter('getattr')
    def jinja_getattr(obj, attr):
        return getattr(obj, attr)

    return app
