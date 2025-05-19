import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from auditoria_app import db
from auditoria_app.models import Auditoria
from datetime import datetime

# Caminho do arquivo de credenciais JSON
CAMINHO_CREDENCIAL = 'auditoria_app/credentials/capeante-4cf77adc317f.json'

# ID da planilha
SPREADSHEET_ID = '169SOR_FnD7z3BR_D9a1NWe5iknoFqHWckM3Shxnf9-c'
ABA_NOME = 'Planilha1'  # ajuste aqui se sua aba tiver outro nome

# Escopo da API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Autenticação
credenciais = ServiceAccountCredentials.from_json_keyfile_name(CAMINHO_CREDENCIAL, scope)
cliente = gspread.authorize(credenciais)
sheet = cliente.open_by_key(SPREADSHEET_ID).worksheet(ABA_NOME)

# Buscar registros do banco
registros = Auditoria.query.all()

dados = []
for r in registros:
    data_auditoria = r.data_auditoria.strftime('%d/%m/%Y') if r.data_auditoria else ''
    mes_referencia = r.data_auditoria.strftime('%Y-%m') if r.data_auditoria else ''
    dados.append([
        data_auditoria,
        mes_referencia,
        r.auditor or '',
        r.nome_prestador or '',
        r.cod_prestador or '',
        r.nome_beneficiario or '',
        r.tipo_internacao or '',
        r.caracter_internacao or '',
        r.acomodacao or '',
        r.data_internacao.strftime('%d/%m/%Y') if r.data_internacao else '',
        r.data_alta.strftime('%d/%m/%Y') if r.data_alta else '',
        r.cid_codigo or '',
        f'R$ {r.total_apresentado:,.2f}' if r.total_apresentado else '',
        f'R$ {r.total_glosa_enfermagem:,.2f}' if r.total_glosa_enfermagem else '',
        f'R$ {r.total_glosa_medico:,.2f}' if r.total_glosa_medico else '',
        r.motivo_glosa or ''
    ])

# Cabeçalhos na ordem certa
colunas = [
    "DATA AUDITORIA", "MÊS REFERÊNCIA", "AUDITOR", "PRESTADOR", "CÓD. PRESTADOR",
    "BENEFICIÁRIO", "TIPO DE INTERNAÇÃO (CLÍNICA/CIRÚRGICA)", "URGÊNCIA/ELETIVA",
    "ACOMODAÇÃO", "DATA ADMISSÃO", "DATA ALTA", "CID PRINCIPAL",
    "VALOR APRESENTADO", "VALOR GLOSA ENF", "VALOR GL MED", "MOTIVO DA GLOSA"
]

# Apagar conteúdo existente
sheet.clear()

# Escrever cabeçalho e dados
sheet.insert_row(colunas, 1)
sheet.insert_rows(dados, row=2)
print("✅ Dados enviados para o Google Sheets com sucesso.")
