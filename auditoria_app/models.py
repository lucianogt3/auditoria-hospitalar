from flask_login import UserMixin
from . import db
from sqlalchemy import DateTime
from flask_login import UserMixin
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)  # <-- novo
    password_hash = db.Column(db.String(512), nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)          # <-- novo
    confirmation_token = db.Column(db.String(255), nullable=True)   # <-- novo

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Prestador(db.Model):
    __tablename__ = 'prestador'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)

class Auditor(db.Model):
    __tablename__ = 'auditor'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    matricula = db.Column(db.String(50), nullable=False, unique=True)

class CID(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)

class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    # Dados principais
    nome_beneficiario = db.Column(db.String(255), nullable=False)
    cod_beneficiario = db.Column(db.String(50))
    cod_prestador = db.Column(db.String(50))
    nome_prestador = db.Column(db.String(255))
    guia_principal = db.Column(db.String(100))
    data_internacao = db.Column(DateTime)
    hora_internacao = db.Column(db.String(10))
    data_alta = db.Column(DateTime)
    hora_alta = db.Column(db.String(10))
    data_auditoria = db.Column(DateTime)

    # Classificações
    tipo_internacao = db.Column(db.String(50))
    caracter_internacao = db.Column(db.String(50))
    parcial = db.Column(db.String(50))
    cod_procedimento = db.Column(db.String(50))
    descricao_procedimento = db.Column(db.String(255))
    cid_codigo = db.Column(db.String(10))
    cid_descricao = db.Column(db.String(255))

    # Período da fatura
    fatura_de = db.Column(DateTime)
    fatura_ate = db.Column(DateTime)

    # Valores por grupo
    for i in range(1, 11):
        locals()[f'grupo_{i}'] = db.Column(db.String(100))
        locals()[f'qtd_apresentada_{i}'] = db.Column(db.Integer)
        locals()[f'qtd_autorizada_{i}'] = db.Column(db.Integer)
        locals()[f'valor_apresentado_{i}'] = db.Column(db.Float)
        locals()[f'glosa_medico_{i}'] = db.Column(db.Float)
        locals()[f'glosa_enfermagem_{i}'] = db.Column(db.Float)
        locals()[f'valor_liberado_{i}'] = db.Column(db.Float)

    # Linhas extras
    for i in range(1, 6):
        locals()[f'linhaextra_grupo_{i}'] = db.Column(db.String(100))
        locals()[f'linhaextra_qtd_apresentada_{i}'] = db.Column(db.Integer)
        locals()[f'linhaextra_qtd_autorizada_{i}'] = db.Column(db.Integer)
        locals()[f'linhaextra_valor_apresentado_{i}'] = db.Column(db.Float)
        locals()[f'linhaextra_glosa_medico_{i}'] = db.Column(db.Float)
        locals()[f'linhaextra_glosa_enfermagem_{i}'] = db.Column(db.Float)
        locals()[f'linhaextra_valor_liberado_{i}'] = db.Column(db.Float)

    # Totais
    total_apresentado = db.Column(db.Float)
    total_glosa_medico = db.Column(db.Float)
    total_glosa_enfermagem = db.Column(db.Float)
    total_liberado = db.Column(db.Float)

    # Extras
    auditor = db.Column(db.String(100))
    acomodacao = db.Column(db.String(50))
    motivo_glosa = db.Column(db.Text)

    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    salvo = db.Column(db.Boolean, default=False)
