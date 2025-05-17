from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required
from .models import Auditoria, Prestador, Auditor
from . import db
from io import BytesIO
import pdfkit
import locale
from datetime import datetime
import pandas as pd
from flask_login import logout_user
import gspread
from google.oauth2.service_account import Credentials
import os

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
pdfkit_config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

main = Blueprint('main', __name__)

def formatar_moeda(valor):
    try:
        if valor is None or valor == '':
            return ''
        return locale.currency(float(valor), grouping=True)
    except:
        return valor

def limpar_valor(valor_str):
    try:
        if valor_str:
            return float(
                valor_str.replace('R$', '')
                         .replace('\xa0', '')
                         .replace(' ', '')
                         .replace('.', '')
                         .replace(',', '.')
                         .strip()
            )
    except:
        pass
    return 0.0

def parse_data(valor, formato):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor, formato)
        except:
            return None
    return None

@main.route('/')
def index():
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    mes = request.args.get('mes')
    query = Auditoria.query

    if mes:
        query = query.filter(Auditoria.data_auditoria.like(f'{mes}-%'))

    relatorios = query.all()
    total_apresentado = sum([r.total_apresentado or 0 for r in relatorios])
    total_glosa_medico = sum([r.total_glosa_medico or 0 for r in relatorios])
    total_glosa_enfermagem = sum([r.total_glosa_enfermagem or 0 for r in relatorios])
    total_liberado = sum([r.total_liberado or 0 for r in relatorios])

    return render_template('dashboard.html',
                           total_apresentado=total_apresentado,
                           total_glosa_medico=total_glosa_medico,
                           total_glosa_enfermagem=total_glosa_enfermagem,
                           total_liberado=total_liberado,
                           mes=mes)

@main.route('/relatorio')
@login_required
def relatorio():
    registros = Auditoria.query.all()
    return render_template('relatorio.html', registros=registros)

@main.route('/novo', methods=['GET'])
@login_required
def novo_registro():
    nomes_grupos = [
        'DIÁRIAS', 'TAXAS / ALUGUÉIS', 'GASES MEDICINAIS', 'HONORÁRIOS',
        'MEDICAMENTOS', 'MATERIAIS', 'OPME', 'PACOTES', 'SADT', 'TERCEIRO'
    ]

    grupos_despesa = []
    for i, nome in enumerate(nomes_grupos, start=1):
        grupos_despesa.append({
            'indice': i,
            'grupo': nome,
            'qtd_apresentada': '',
            'qtd_autorizada': '',
            'valor_apresentado': '',
            'glosa_medico': '',
            'glosa_enfermagem': '',
            'valor_liberado': ''
        })

    return render_template('formulario.html', registro=None, grupos_despesa=grupos_despesa)

@main.route('/salvar', methods=['POST'])
@login_required
def salvar():
    data_internacao = parse_data(request.form.get('data_internacao'), '%Y-%m-%dT%H:%M')
    data_alta = parse_data(request.form.get('data_alta'), '%Y-%m-%dT%H:%M')
    fatura_de = parse_data(request.form.get('periodo_fatura_inicio'), '%Y-%m-%d') or (data_internacao.date() if data_internacao else None)
    fatura_ate = parse_data(request.form.get('periodo_fatura_fim'), '%Y-%m-%d') or (data_alta.date() if data_alta else None)

    registro = Auditoria(
        nome_beneficiario=request.form.get('nome_beneficiario'),
        cod_beneficiario=request.form.get('cod_beneficiario'),
        cod_prestador=request.form.get('cod_prestador'),
        nome_prestador=request.form.get('nome_prestador'),
        guia_principal=request.form.get('guia_principal'),
        data_auditoria=parse_data(request.form.get('data_auditoria'), '%Y-%m-%d'),
        data_internacao=data_internacao,
        hora_internacao=data_internacao.strftime('%H:%M') if data_internacao else '',
        data_alta=data_alta,
        hora_alta=data_alta.strftime('%H:%M') if data_alta else '',
        tipo_internacao=request.form.get('tipo_internacao'),
        caracter_internacao=', '.join(request.form.getlist('carater_internacao[]')),
        parcial=request.form.get('parcial'),
        fatura_de=fatura_de,
        fatura_ate=fatura_ate,
        cod_procedimento=request.form.get('cod_procedimento'),
        descricao_procedimento=request.form.get('descricao_procedimento'),
        cid_codigo=request.form.get('cid'),
        cid_descricao='',
        auditor=request.form.get('auditor'),
        acomodacao=request.form.get('acomodacao'),
        motivo_glosa=request.form.get('motivo_glosa'),
        total_apresentado=limpar_valor(request.form.get('total_apresentado')),
        total_glosa_medico=limpar_valor(request.form.get('total_glosa_medico')),
        total_glosa_enfermagem=limpar_valor(request.form.get('total_glosa_enfermagem')),
        total_liberado=limpar_valor(request.form.get('total_liberado')),
        salvo=True
    )

    for i in range(1, 101):
        setattr(registro, f'grupo_{i}', request.form.get(f'grupo_{i}'))
        setattr(registro, f'qtd_apresentada_{i}', request.form.get(f'qtd_apresentada_{i}'))
        setattr(registro, f'qtd_autorizada_{i}', request.form.get(f'qtd_autorizada_{i}'))
        setattr(registro, f'valor_apresentado_{i}', limpar_valor(request.form.get(f'valor_apresentado_{i}')))
        setattr(registro, f'glosa_medico_{i}', limpar_valor(request.form.get(f'glosa_medico_{i}')))
        setattr(registro, f'glosa_enfermagem_{i}', limpar_valor(request.form.get(f'glosa_enfermagem_{i}')))
        setattr(registro, f'valor_liberado_{i}', limpar_valor(request.form.get(f'valor_liberado_{i}')))

    db.session.add(registro)
    db.session.commit()
    flash("Relatório salvo com sucesso.", "success")
    return redirect(url_for('main.dashboard'))

@main.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    registro = Auditoria.query.get_or_404(id)

    registro.data_auditoria = parse_data(registro.data_auditoria, '%Y-%m-%d')
    registro.data_internacao = parse_data(registro.data_internacao, '%Y-%m-%dT%H:%M')
    registro.data_alta = parse_data(registro.data_alta, '%Y-%m-%dT%H:%M')
    registro.fatura_de = parse_data(registro.fatura_de, '%Y-%m-%d')
    registro.fatura_ate = parse_data(registro.fatura_ate, '%Y-%m-%d')

    def tratar(valor):
        return '' if valor in [None, 'None'] else valor

    def formatar(valor):
        try:
            return f"{float(valor):.2f}".replace('.', ',')
        except:
            return '0,00'

    grupos_despesa = []
    total_apresentado = 0
    total_glosa_medico = 0
    total_glosa_enfermagem = 0
    total_liberado = 0

    for i in range(1, 11):
        valor_apresentado = getattr(registro, f'valor_apresentado_{i}', 0) or 0
        glosa_medico = getattr(registro, f'glosa_medico_{i}', 0) or 0
        glosa_enfermagem = getattr(registro, f'glosa_enfermagem_{i}', 0) or 0
        valor_liberado = valor_apresentado - glosa_medico - glosa_enfermagem

        total_apresentado += valor_apresentado
        total_glosa_medico += glosa_medico
        total_glosa_enfermagem += glosa_enfermagem
        total_liberado += valor_liberado

        grupos_despesa.append({
            'indice': i,
            'grupo': tratar(getattr(registro, f'grupo_{i}', '')),
            'qtd_apresentada': tratar(getattr(registro, f'qtd_apresentada_{i}', '')),
            'qtd_autorizada': tratar(getattr(registro, f'qtd_autorizada_{i}', '')),
            'valor_apresentado': formatar(valor_apresentado),
            'glosa_medico': formatar(glosa_medico),
            'glosa_enfermagem': formatar(glosa_enfermagem),
            'valor_liberado': formatar(valor_liberado),
            'glosa_medico_raw': glosa_medico,
            'glosa_enfermagem_raw': glosa_enfermagem,
            'tem_glosa': glosa_medico > 0 or glosa_enfermagem > 0,
            'glosa_medico_classe': 'text-danger fw-bold' if glosa_medico > 0 else '',
            'glosa_enfermagem_classe': 'text-danger fw-bold' if glosa_enfermagem > 0 else ''
        })

    totais = {
        'valor_apresentado': formatar(total_apresentado),
        'glosa_medico': formatar(total_glosa_medico),
        'glosa_enfermagem': formatar(total_glosa_enfermagem),
        'valor_liberado': formatar(total_liberado),
    }

    return render_template('visualizar.html', registro=registro, grupos_despesa=grupos_despesa, totais=totais)

@main.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    registro = Auditoria.query.get_or_404(id)

    if request.method == 'POST':
        registro.nome_beneficiario = request.form.get('nome_beneficiario')
        registro.cod_beneficiario = request.form.get('cod_beneficiario')
        registro.nome_prestador = request.form.get('nome_prestador')
        registro.cod_prestador = request.form.get('cod_prestador')
        registro.guia_principal = request.form.get('guia_principal')
        registro.data_auditoria = parse_data(request.form.get('data_auditoria'), '%Y-%m-%d')
        registro.data_internacao = parse_data(request.form.get('data_internacao'), '%Y-%m-%dT%H:%M')
        registro.hora_internacao = registro.data_internacao.strftime('%H:%M') if registro.data_internacao else ''
        registro.data_alta = parse_data(request.form.get('data_alta'), '%Y-%m-%dT%H:%M')
        registro.hora_alta = registro.data_alta.strftime('%H:%M') if registro.data_alta else ''
        registro.tipo_internacao = request.form.get('tipo_internacao')
        registro.caracter_internacao = ', '.join(request.form.getlist('carater_internacao[]'))
        registro.parcial = request.form.get('parcial')
        registro.fatura_de = parse_data(request.form.get('periodo_fatura_inicio'), '%Y-%m-%d')
        registro.fatura_ate = parse_data(request.form.get('periodo_fatura_fim'), '%Y-%m-%d')
        registro.cod_procedimento = request.form.get('cod_procedimento')
        registro.descricao_procedimento = request.form.get('descricao_procedimento')
        registro.cid_codigo = request.form.get('cid')
        registro.cid_descricao = ''
        registro.auditor = request.form.get('auditor')
        registro.acomodacao = request.form.get('acomodacao')
        registro.motivo_glosa = request.form.get('motivo_glosa')
        registro.total_apresentado = limpar_valor(request.form.get('total_apresentado'))
        registro.total_glosa_medico = limpar_valor(request.form.get('total_glosa_medico'))
        registro.total_glosa_enfermagem = limpar_valor(request.form.get('total_glosa_enfermagem'))
        registro.total_liberado = limpar_valor(request.form.get('total_liberado'))

        for i in range(1, 101):
            setattr(registro, f'grupo_{i}', request.form.get(f'grupo_{i}'))
            setattr(registro, f'qtd_apresentada_{i}', request.form.get(f'qtd_apresentada_{i}'))
            setattr(registro, f'qtd_autorizada_{i}', request.form.get(f'qtd_autorizada_{i}'))
            setattr(registro, f'valor_apresentado_{i}', limpar_valor(request.form.get(f'valor_apresentado_{i}')))
            setattr(registro, f'glosa_medico_{i}', limpar_valor(request.form.get(f'glosa_medico_{i}')))
            setattr(registro, f'glosa_enfermagem_{i}', limpar_valor(request.form.get(f'glosa_enfermagem_{i}')))
            setattr(registro, f'valor_liberado_{i}', limpar_valor(request.form.get(f'valor_liberado_{i}')))

        db.session.commit()
        flash("Relatório atualizado com sucesso.", "success")
        return redirect(url_for('main.dashboard'))

    # Corrigir datas no modo GET para exibição no formulário
    registro.data_auditoria = parse_data(registro.data_auditoria, '%Y-%m-%d')
    registro.data_internacao = parse_data(registro.data_internacao, '%Y-%m-%dT%H:%M')
    registro.data_alta = parse_data(registro.data_alta, '%Y-%m-%dT%H:%M')
    registro.fatura_de = parse_data(registro.fatura_de, '%Y-%m-%d')
    registro.fatura_ate = parse_data(registro.fatura_ate, '%Y-%m-%d')

    grupos_despesa = []
    for i in range(1, 11):
        grupos_despesa.append({
            'indice': i,
            'grupo': getattr(registro, f'grupo_{i}', ''),
            'qtd_apresentada': getattr(registro, f'qtd_apresentada_{i}', ''),
            'qtd_autorizada': getattr(registro, f'qtd_autorizada_{i}', ''),
            'valor_apresentado': formatar_moeda(getattr(registro, f'valor_apresentado_{i}', 0)),
            'glosa_medico': formatar_moeda(getattr(registro, f'glosa_medico_{i}', 0)),
            'glosa_enfermagem': formatar_moeda(getattr(registro, f'glosa_enfermagem_{i}', 0)),
            'valor_liberado': formatar_moeda(getattr(registro, f'valor_liberado_{i}', 0)),
        })

    
    return render_template('formulario.html', registro=registro, grupos_despesa=grupos_despesa, modo='editar')

@main.route('/imprimir/<int:id>')
@login_required
def imprimir(id):
    r = Auditoria.query.get_or_404(id)

    r.data_auditoria = parse_data(r.data_auditoria, '%Y-%m-%d')
    r.data_internacao = parse_data(r.data_internacao, '%Y-%m-%dT%H:%M')
    r.data_alta = parse_data(r.data_alta, '%Y-%m-%dT%H:%M')
    r.fatura_de = parse_data(r.fatura_de, '%Y-%m-%d')
    r.fatura_ate = parse_data(r.fatura_ate, '%Y-%m-%d')

    r.data_auditoria_br = r.data_auditoria.strftime('%d/%m/%Y') if r.data_auditoria else 'N/A'
    r.data_internacao_br = r.data_internacao.strftime('%d/%m/%Y %H:%M') if r.data_internacao else 'N/A'
    r.data_alta_br = r.data_alta.strftime('%d/%m/%Y %H:%M') if r.data_alta else 'N/A'
    r.fatura_de_br = r.fatura_de.strftime('%d/%m/%Y') if r.fatura_de else 'N/A'
    r.fatura_ate_br = r.fatura_ate.strftime('%d/%m/%Y') if r.fatura_ate else 'N/A'

    options = {
        'enable-local-file-access': '',
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'encoding': 'UTF-8',
    }

    rendered = render_template("pdf_individual.html", r=r)
    pdf = pdfkit.from_string(rendered, False, configuration=pdfkit_config, options=options)
    return send_file(BytesIO(pdf), download_name="relatorio.pdf", as_attachment=False)


@main.route('/formulario/primeiro')
@login_required
def formulario_primeiro():
    primeiro = Auditoria.query.order_by(Auditoria.id.asc()).first()
    if primeiro:
        return redirect(url_for('main.visualizar', id=primeiro.id))
    flash("Nenhum registro encontrado.", "warning")
    return redirect(url_for('main.dashboard'))

@main.route('/formulario/anterior/<int:id>')
@login_required
def formulario_anterior(id):
    anterior = Auditoria.query.filter(Auditoria.id < id).order_by(Auditoria.id.desc()).first()
    if anterior:
        return redirect(url_for('main.visualizar', id=anterior.id))
    flash("Esse é o primeiro registro.", "info")
    return redirect(url_for('main.visualizar', id=id))

@main.route('/formulario/proximo/<int:id>')
@login_required
def formulario_proximo(id):
    proximo = Auditoria.query.filter(Auditoria.id > id).order_by(Auditoria.id.asc()).first()
    if proximo:
        return redirect(url_for('main.visualizar', id=proximo.id))
    flash("Esse é o último registro.", "info")
    return redirect(url_for('main.visualizar', id=id))

@main.route('/formulario/ultimo')
@login_required
def formulario_ultimo():
    ultimo = Auditoria.query.order_by(Auditoria.id.desc()).first()
    if ultimo:
        return redirect(url_for('main.visualizar', id=ultimo.id))
    flash("Nenhum registro encontrado.", "warning")
    return redirect(url_for('main.dashboard'))

@main.route('/exportar_excel')
@login_required
def exportar_excel():
    mes = request.args.get('mes')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = Auditoria.query
    if mes:
        query = query.filter(Auditoria.data_auditoria.like(f'{mes}-%'))
    if data_inicio:
        query = query.filter(Auditoria.data_auditoria >= data_inicio)
    if data_fim:
        query = query.filter(Auditoria.data_auditoria <= data_fim)

    registros = query.all()
    if not registros:
        flash("Nenhum dado encontrado para exportar com os filtros aplicados.", "warning")
        return redirect(url_for('main.relatorio'))

    dados = []
    for r in registros:
        data_internacao = parse_data(r.data_internacao, '%Y-%m-%dT%H:%M')
        data_alta = parse_data(r.data_alta, '%Y-%m-%dT%H:%M')

        dados.append({
            "AUDITOR": r.auditor or '',
            "PRESTADOR": r.nome_prestador or '',
            "BENEFICIÁRIO": r.nome_beneficiario or '',
            "TIPO DE INTERNAÇÃO (CLÍNICA/CIRÚRGICA)": r.tipo_internacao or '',
            "URGÊNCIA/ELETIVA": r.caracter_internacao or '',
            "ACOMODAÇÃO": r.acomodacao or '',
            "DATA ADMISSÃO": data_internacao.strftime('%d/%m/%Y') if data_internacao else '',
            "DATA ALTA": data_alta.strftime('%d/%m/%Y') if data_alta else '',
            "CID PRINCIPAL": r.cid_codigo or '',
            "VALOR APRESENTADO": r.total_apresentado or 0,
            "VALOR GLOSA ENF": r.total_glosa_enfermagem or 0,
            "VALOR GL MED": r.total_glosa_medico or 0,
            "MOTIVO DA GLOSA": r.motivo_glosa or ''
        })

    df = pd.DataFrame(dados)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Auditoria')
    output.seek(0)

    return send_file(
        output,
        download_name="lista_auditoria.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@main.route('/excluir/<int:id>')
@login_required
def excluir(id):
    registro = Auditoria.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash("Registro excluído com sucesso.", "success")
    return redirect(url_for('main.relatorio'))

@main.route('/prestadores', methods=['GET', 'POST'])
@login_required
def listar_prestadores():
    if request.method == 'POST':
        nome = request.form['nome']
        codigo = request.form['codigo']
        prestador = Prestador(nome=nome, codigo=codigo)
        db.session.add(prestador)
        db.session.commit()
        flash('Prestador cadastrado com sucesso.', 'success')
        return redirect(url_for('main.listar_prestadores'))

    prestadores = Prestador.query.all()
    return render_template('prestadores.html', prestadores=prestadores)

@main.route('/cadastro-prestador')
@login_required
def cadastro_prestador():
    prestadores = Prestador.query.filter_by(ativo=True).all()
    return jsonify([{'nome': p.nome, 'codigo': p.codigo} for p in prestadores])

@main.route("/auditor", methods=["GET"])
@login_required
def form_auditor():
    auditores = Auditor.query.all()
    return render_template("auditor.html", auditores=auditores)

@main.route("/auditor/novo", methods=["POST"])
@login_required
def salvar_auditor():
    nome = request.form["nome"]
    matricula = request.form["matricula"]
    auditor = Auditor(nome=nome, matricula=matricula)
    db.session.add(auditor)
    db.session.commit()
    flash("Auditor cadastrado com sucesso.", "success")
    return redirect(url_for("main.form_auditor"))

@main.route("/cadastro-auditor")
@login_required
def listar_auditores():
    auditores = Auditor.query.all()
    return jsonify([{'nome': a.nome, 'matricula': a.matricula} for a in auditores])
@main.route('/imprimir-lote')
@login_required
def imprimir_lote():
    ids = request.args.get('ids')
    if not ids:
        flash("Nenhum registro selecionado para impressão.", "warning")
        return redirect(url_for('main.relatorio'))

    id_list = [int(x) for x in ids.split(',') if x.isdigit()]
    registros = Auditoria.query.filter(Auditoria.id.in_(id_list)).all()

    for r in registros:
        r.data_auditoria = parse_data(r.data_auditoria, '%Y-%m-%d')
        r.data_internacao = parse_data(r.data_internacao, '%Y-%m-%dT%H:%M')
        r.data_alta = parse_data(r.data_alta, '%Y-%m-%dT%H:%M')
        r.fatura_de = parse_data(r.fatura_de, '%Y-%m-%d')
        r.fatura_ate = parse_data(r.fatura_ate, '%Y-%m-%d')
        r.data_auditoria_br = r.data_auditoria.strftime('%d/%m/%Y') if r.data_auditoria else 'N/A'
        r.data_internacao_br = r.data_internacao.strftime('%d/%m/%Y %H:%M') if r.data_internacao else 'N/A'
        r.data_alta_br = r.data_alta.strftime('%d/%m/%Y %H:%M') if r.data_alta else 'N/A'
        r.fatura_de_br = r.fatura_de.strftime('%d/%m/%Y') if r.fatura_de else 'N/A'
        r.fatura_ate_br = r.fatura_ate.strftime('%d/%m/%Y') if r.fatura_ate else 'N/A'

    rendered = render_template('pdf_lote.html', registros=registros)

    options = {
        'enable-local-file-access': '',
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'encoding': 'UTF-8'
    }

    pdf = pdfkit.from_string(rendered, False, configuration=pdfkit_config, options=options)
    return send_file(BytesIO(pdf), download_name="lote_auditoria.pdf", as_attachment=False)

@main.route('/sair')
def sair():
    logout_user()
    flash("Sessão encerrada com sucesso.", "success")
    return redirect(url_for('auth.login'))
@main.route('/enviar_sheets', methods=['POST'])
@login_required
def enviar_sheets():
    import gspread
    from google.oauth2.service_account import Credentials

    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify(success=False, message="Nenhum ID recebido.")

    registros = Auditoria.query.filter(Auditoria.id.in_(ids)).all()

    # Conexão com Google Sheets
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    cred_path = os.path.join(os.path.dirname(__file__), 'credentials', 'credenciais.json')
    CREDS = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    gc = gspread.authorize(CREDS)

    # Abre a planilha
    planilha = gc.open_by_key("169SOR_FnD7z3BR_D9a1NWe5iknoFqHWckM3Shxnf9-c")
    aba = planilha.worksheet("automatizado")

    for r in registros:
        aba.append_row([
            r.auditor or '',
            r.nome_prestador or '',
            r.nome_beneficiario or '',
            r.tipo_internacao or '',
            r.caracter_internacao or '',
            r.acomodacao or '',
            r.data_internacao.strftime('%d/%m/%Y') if r.data_internacao else '',
            r.data_alta.strftime('%d/%m/%Y') if r.data_alta else '',
            r.cid_codigo or '',
            f"R$ {r.total_apresentado:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',') if r.total_apresentado else '',
            f"R$ {r.total_glosa_enfermagem:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',') if r.total_glosa_enfermagem else '',
            f"R$ {r.total_glosa_medico:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',') if r.total_glosa_medico else '',
            r.motivo_glosa or ''
        ])

    return jsonify(success=True)

