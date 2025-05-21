from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from .models import db, User
from . import mail
from itsdangerous import SignatureExpired, BadSignature
from flask import Blueprint
import traceback

auth = Blueprint('auth', __name__)


from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Geração de token para confirmação ou redefinição
def gerar_token(email):
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("SECRET_KEY não está configurada na aplicação Flask.")
    
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(email, salt='email-confirm')

# Verificação de token
def verificar_token(token):
    secret_key = current_app.config.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("SECRET_KEY não está configurada na aplicação Flask.")

    s = URLSafeTimedSerializer(secret_key)
    try:
        return s.loads(token, salt='email-confirm', max_age=3600)
    except (SignatureExpired, BadSignature):
        return None

# Envia e-mail com link de confirmação
def enviar_email_confirmacao(email, token):
    link = url_for('auth.confirmar_email', token=token, _external=True)
    msg = Message('Confirme seu e-mail', recipients=[email])
    msg.body = f'Clique no link para confirmar seu e-mail: {link}'
    mail.send(msg)

# Envia e-mail com link de redefinição de senha
def enviar_email_redefinicao(email, token):
    link = url_for('auth.redefinir_senha', token=token, _external=True)
    msg = Message('Redefinição de senha', recipients=[email])
    msg.body = f'Clique no link para redefinir sua senha e tenha acesso ao seu CAPEANTE ONLINE: {link}'
    mail.send(msg)


# Rota de login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash("Usuário ou senha incorretos.")
    return render_template('login.html')

# Rota de logout
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Rota de registro
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.")
            return redirect(url_for('auth.register'))

        token = gerar_token(email)
        new_user = User(
            username=username,
            email=email,
            email_confirmed=False,
            confirmation_token=token
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        enviar_email_confirmacao(email, token)
        flash("Usuário criado com sucesso! Verifique seu e-mail para confirmar.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Confirmação de e-mail
@auth.route('/confirmar/<token>')
def confirmar_email(token):
    email = verificar_token(token)
    if not email:
        flash('Link inválido ou expirado.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_confirmed = True
        user.confirmation_token = None
        db.session.commit()
        flash('E-mail confirmado com sucesso. Você já pode fazer login.', 'success')
    else:
        flash('Usuário não encontrado.', 'danger')

    return redirect(url_for('auth.login'))

@auth.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            secret = current_app.config.get('SECRET_KEY')
            if not secret:
                flash('Erro interno: chave secreta não configurada.', 'danger')
                return redirect(url_for('auth.login'))

            s = URLSafeTimedSerializer(secret)
            token = s.dumps(email, salt='recupera-senha')

            user.confirmation_token = token
            db.session.commit()

            link = url_for('auth.redefinir_senha', token=token, _external=True)
            msg = Message('Redefinir senha', sender=current_app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
            msg.body = f'Clique no link para redefinir sua senha: {link}'

            try:
                mail.send(msg)
                flash('Um link de redefinição foi enviado para seu e-mail.', 'success')
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")
                flash('Erro ao enviar o e-mail. Verifique as configurações.', 'danger')

            return redirect(url_for('auth.login'))

        flash('E-mail não encontrado.', 'danger')
    return render_template('esqueci_senha.html')

@auth.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    try:
        secret = current_app.config.get('SECRET_KEY')
        if not secret:
            flash('Erro interno: chave secreta não configurada.', 'danger')
            return redirect(url_for('auth.esqueci_senha'))

        s = URLSafeTimedSerializer(secret)
        email = s.loads(token, salt='recupera-senha', max_age=3600)
    except SignatureExpired:
        flash('O link expirou. Solicite um novo.', 'danger')
        return redirect(url_for('auth.esqueci_senha'))
    except BadSignature:
        flash('Token inválido.', 'danger')
        return redirect(url_for('auth.esqueci_senha'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.esqueci_senha'))

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
            user.confirmation_token = None
            db.session.commit()
            flash('Senha redefinida com sucesso.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('redefinir_senha.html', token=token)
