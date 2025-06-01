from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Configurações de e-mail (use sua senha de app correta aqui)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jeizadasilvasantos@gmail.com'
app.config['MAIL_PASSWORD'] = 'qizqngkkmsvrjpxb'
app.config['MAIL_DEFAULT_SENDER'] = 'jeizadasilvasantos@gmail.com'

mail = Mail(app)

@app.route('/teste')
def enviar_email_teste():
    try:
        msg = Message("Teste de envio", recipients=["jeizadasilvasantos@gmail.com"])
        msg.body = "Este é um teste de envio de e-mail com Flask + Gmail."
        mail.send(msg)
        return "E-mail enviado com sucesso!"
    except Exception as e:
        return f"Erro ao enviar: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
