import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-segura')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///auditoria.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações de envio de e-mail via Gmail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'jeizadasilvasantos@gmail.com'
    MAIL_PASSWORD = 'qizqngkkmsvrjpxb'  # senha de app gerada no Gmail
    MAIL_DEFAULT_SENDER = 'jeizadasilvasantos@gmail.com'
