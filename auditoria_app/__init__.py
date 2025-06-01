import os
import platform
import pdfkit
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

# 📌 Detecta o caminho do wkhtmltopdf para Windows ou Render (Linux)
if os.environ.get("RENDER"):
    path_wkhtmltopdf = os.path.join(os.getcwd(), 'bin', 'wkhtmltopdf')
elif platform.system() == "Windows":
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
else:
    path_wkhtmltopdf = '/usr/bin/wkhtmltopdf'

# Configuração do pdfkit
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Opções de formatação
options = {
    'enable-local-file-access': '',
    'page-size': 'A4',
    'margin-top': '10mm',
    'margin-right': '5mm',
    'margin-bottom': '10mm',
    'margin-left': '5mm',
    'encoding': 'UTF-8',
}

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
