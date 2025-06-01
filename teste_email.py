from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Configuração do Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jeizadasilvasantos@gmail.com'
app.config['MAIL_PASSWORD'] = 'qizqngkkmsvrjpxb'  # senha de aplicativo
app.config['MAIL_DEFAULT_SENDER'] = 'jeizadasilvasantos@gmail.com'

mail = Mail(app)

@app.route('/teste')
def enviar_email_teste():
    msg = Message('Teste de envio', recipients=['jeizadasilvasantos@gmail.com'])
    msg.body = 'Este é um teste de envio de e-mail via Flask.'
    try:
        mail.send(msg)
        return 'E-mail enviado com sucesso!'
    except Exception as e:
        return f'Erro ao enviar: {e}'

if __name__ == '__main__':
    app.run(debug=True)
