import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user, logout_user
from .models import Auditoria, Prestador, Auditor
from . import db
from io import BytesIO
from datetime import datetime
import pandas as pd
import locale
from weasyprint import HTML
import gspread
from google.oauth2.service_account import Credentials
from flask import make_response
import base64
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

# REMOVIDO: O bloco de detecção de sistema operacional e inicialização de pdfkit.configuration
# e options foi removido daqui, pois já está definido globalmente em __init__.py
# e deve ser importado e reutilizado para evitar duplicação e inconsistências.

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

def limpar_inteiro(valor):
    try:
        if valor in [None, '', 'N/A']:
            return None
        return int(valor)
    except (ValueError, TypeError):
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
        # Intervalo de datas do mês selecionado
        data_inicio = f"{mes}-01"
        ano, mes_num = map(int, mes.split("-"))

        if mes_num == 12:
            data_fim = f"{ano + 1}-01-01"
        else:
            data_fim = f"{ano}-{mes_num + 1:02d}-01"

        query = query.filter(
            Auditoria.data_auditoria >= data_inicio,
            Auditoria.data_auditoria < data_fim
        )

    relatorios = query.all()
    
    # Somatórios
    total_apresentado = sum([r.total_apresentado or 0 for r in relatorios])
    total_glosa_medico = sum([r.total_glosa_medico or 0 for r in relatorios])
    total_glosa_enfermagem = sum([r.total_glosa_enfermagem or 0 for r in relatorios])
    total_liberado = sum([r.total_liberado or 0 for r in relatorios])
    
    # Cálculos adicionais
    total_glosa_total = total_glosa_medico + total_glosa_enfermagem
    total_registros = len(relatorios)

    percentual_glosa = (total_glosa_total / total_apresentado * 100) if total_apresentado else 0
    percentual_liberado = (total_liberado / total_apresentado * 100) if total_apresentado else 0
    media_valor_apresentado = (total_apresentado / total_registros) if total_registros else 0

    return render_template(
        'dashboard.html',
        mes=mes,
        total_apresentado=total_apresentado,
        total_glosa_medico=total_glosa_medico,
        total_glosa_enfermagem=total_glosa_enfermagem,
        total_liberado=total_liberado,
        total_registros=total_registros,
        percentual_glosa=percentual_glosa,
        percentual_liberado=percentual_liberado,
        media_valor_apresentado=media_valor_apresentado,
        total_glosa_total=total_glosa_total
    )

@main.route('/relatorio')
@login_required
def relatorio():
    data_filtro = request.args.get('data')

    query = Auditoria.query

    if data_filtro:
        try:
            data_dt = datetime.strptime(data_filtro, '%Y-%m-%d')
            query = query.filter(db.func.date(Auditoria.data_registro) == data_dt.date())
        except ValueError:
            flash("Data inválida no filtro.", "danger")

    registros = query.order_by(Auditoria.data_registro.desc()).all()
    total_registros = len(registros) # <-- Adicione esta linha

    return render_template('relatorio.html', registros=registros, total_registros=total_registros)

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
        setattr(registro, f'qtd_apresentada_{i}', limpar_inteiro(request.form.get(f'qtd_apresentada_{i}')))
        setattr(registro, f'qtd_autorizada_{i}', limpar_inteiro(request.form.get(f'qtd_autorizada_{i}')))
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
            setattr(registro, f'qtd_apresentada_{i}', limpar_inteiro(request.form.get(f'qtd_apresentada_{i}')))
            setattr(registro, f'qtd_autorizada_{i}', limpar_inteiro(request.form.get(f'qtd_autorizada_{i}')))
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
            'valor_apresentado': getattr(registro, f'valor_apresentado_{i}', '') or '',
            'glosa_medico': getattr(registro, f'glosa_medico_{i}', '') or '',
            'glosa_enfermagem': getattr(registro, f'glosa_enfermagem_{i}', '') or '',
            'valor_liberado': getattr(registro, f'valor_liberado_{i}', '') or '',

        })

    
    return render_template('formulario.html', registro=registro, grupos_despesa=grupos_despesa, modo='editar')

@main.route('/imprimir/<int:id>')
@login_required
def imprimir(id):
    r = Auditoria.query.get_or_404(id)

    def parse_data(data, fmt='%d/%m/%Y'):
        if not data:
            return ''
        try:
            return data.strftime(fmt)
        except Exception:
            return ''

    r.data_auditoria_br = parse_data(r.data_auditoria)
    r.data_internacao_br = parse_data(r.data_internacao, '%d/%m/%Y %H:%M')
    r.data_alta_br = parse_data(r.data_alta, '%d/%m/%Y %H:%M')
    r.fatura_de_br = parse_data(r.fatura_de)
    r.fatura_ate_br = parse_data(r.fatura_ate)
    r.data_registro_br = parse_data(r.data_registro)

    r.total_apresentado = 0
    r.total_glosa_medico = 0
    r.total_glosa_enfermagem = 0
    r.total_liberado = 0

    for i in range(1, 11):
        va = getattr(r, f'valor_apresentado_{i}', None) or 0
        gm = getattr(r, f'glosa_medico_{i}', None) or 0
        ge = getattr(r, f'glosa_enfermagem_{i}', None) or 0

        try: va = float(va)
        except: va = 0
        try: gm = float(gm)
        except: gm = 0
        try: ge = float(ge)
        except: ge = 0

        vl = va - gm - ge
        setattr(r, f'valor_liberado_{i}', vl)

        r.total_apresentado += va
        r.total_glosa_medico += gm
        r.total_glosa_enfermagem += ge
        r.total_liberado += vl

    # ✅ Carrega logo como base64
    caminho_logo = os.path.join(current_app.root_path, 'static', 'img', 'logo_ipasgo.png')
    with open(caminho_logo, 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode('utf-8')

    # ✅ Gera HTML
    html = render_template('pdf_individual.html', r=r, logo_base64=logo_base64)

    # ✅ Gera PDF com base_url para suportar CSS local
    pdf = HTML(string=html, base_url=request.host_url).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={r.nome_beneficiario or "relatorio"}.pdf'
    return response

@main.route('/imprimir-lote')
@login_required
def imprimir_lote():
    ids_param = request.args.get('ids')
    if not ids_param:
        flash("Nenhum ID informado para impressão.", "warning")
        return redirect(url_for('main.relatorio'))

    try:
        ids = [int(x) for x in ids_param.split(',')]
    except ValueError:
        flash("IDs inválidos.", "danger")
        return redirect(url_for('main.relatorio'))

    registros = Auditoria.query.filter(Auditoria.id.in_(ids)).all()
    if not registros:
        flash("Nenhum registro encontrado para os IDs informados.", "info")
        return redirect(url_for('main.relatorio'))

    def parse_data(data, fmt='%d/%m/%Y'):
        if not data:
            return ''
        try:
            return data.strftime(fmt)
        except Exception:
            return ''

    for r in registros:
        r.data_auditoria_br = parse_data(r.data_auditoria)
        r.data_internacao_br = parse_data(r.data_internacao, '%d/%m/%Y %H:%M')
        r.data_alta_br = parse_data(r.data_alta, '%d/%m/%Y %H:%M')
        r.fatura_de_br = parse_data(r.fatura_de)
        r.fatura_ate_br = parse_data(r.fatura_ate)
        r.data_registro_br = parse_data(r.data_registro)

        r.total_apresentado = 0
        r.total_glosa_medico = 0
        r.total_glosa_enfermagem = 0
        r.total_liberado = 0

        for i in range(1, 11):
            va = getattr(r, f'valor_apresentado_{i}', None) or 0
            gm = getattr(r, f'glosa_medico_{i}', None) or 0
            ge = getattr(r, f'glosa_enfermagem_{i}', None) or 0

            try: va = float(va)
            except: va = 0
            try: gm = float(gm)
            except: gm = 0
            try: ge = float(ge)
            except: ge = 0

            vl = va - gm - ge
            setattr(r, f'valor_liberado_{i}', vl)

            r.total_apresentado += va
            r.total_glosa_medico += gm
            r.total_glosa_enfermagem += ge
            r.total_liberado += vl

    # ✅ Logo como base64
    caminho_logo = os.path.join(current_app.root_path, 'static', 'img', 'logo_ipasgo.png')
    with open(caminho_logo, 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode('utf-8')

    html = render_template('pdf_lote.html', registros=registros, logo_base64=logo_base64)

    pdf = HTML(string=html, base_url=request.host_url).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=lote_auditoria.pdf'
    return response

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
    from io import BytesIO

    mes = request.args.get('mes')
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')

    query = Auditoria.query

    # Parsing das datas
    try:
        if mes:
            ano, mes_num = map(int, mes.split('-'))
            data_inicio = datetime(ano, mes_num, 1)
            if mes_num == 12:
                data_fim = datetime(ano + 1, 1, 1)
            else:
                data_fim = datetime(ano, mes_num + 1, 1)
        else:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d") if data_inicio_str else None
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d") if data_fim_str else None
            if data_fim:
                data_fim = data_fim.replace(hour=23, minute=59, second=59)
    except Exception as e:
        flash("Erro ao interpretar as datas. Use o formato correto: AAAA-MM ou AAAA-MM-DD", "danger")
        return redirect(url_for('main.relatorio'))

    if data_inicio:
        query = query.filter(Auditoria.data_auditoria >= data_inicio)
    if data_fim:
        query = query.filter(Auditoria.data_auditoria <= data_fim)

    registros = query.all()

    if not registros:
        flash("Nenhum dado encontrado para exportar com os filtros aplicados.", "warning")
        return redirect(url_for('main.relatorio'))

    # Construção dos dados
    dados = []
    for r in registros:
        dados.append({
            'ID': r.id,
            'Auditor': r.auditor,
            'Nome do Beneficiário': r.nome_beneficiario,
            'Código do Beneficiário': r.cod_beneficiario,
            'Código do Prestador': r.cod_prestador,
            'Nome do Prestador': r.nome_prestador,
            'Guia Principal': r.guia_principal,
            'Data Internação': r.data_internacao.strftime("%d/%m/%Y %H:%M") if r.data_internacao else '',
            'Hora Internação': r.hora_internacao,
            'Data Alta': r.data_alta.strftime("%d/%m/%Y %H:%M") if r.data_alta else '',
            'Hora Alta': r.hora_alta,
            'Data Auditoria': r.data_auditoria.strftime("%d/%m/%Y") if r.data_auditoria else '',
            'Tipo Internação': r.tipo_internacao,
            'Caracter Internação': r.caracter_internacao,
            'Parcial': r.parcial,
            'Código Procedimento': r.cod_procedimento,
            'Descrição Procedimento': r.descricao_procedimento,
            'CID Código': r.cid_codigo,
            'CID Descrição': r.cid_descricao,
            'Fatura De': r.fatura_de.strftime("%d/%m/%Y") if r.fatura_de else '',
            'Fatura Até': r.fatura_ate.strftime("%d/%m/%Y") if r.fatura_ate else '',
            'Acomodação': r.acomodacao,
            'Motivo Glosa': r.motivo_glosa,
            'Total Apresentado': r.total_apresentado,
            'Total Glosa Médico': r.total_glosa_medico,
            'Total Glosa Enfermagem': r.total_glosa_enfermagem,
            'Total Liberado': r.total_liberado,
            'Data Registro': r.data_registro.strftime("%d/%m/%Y") if r.data_registro else ''
        })

    df = pd.DataFrame(dados)

    # Exporta para Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Auditoria')

    output.seek(0)

    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='auditoria_completa.xlsx',
                     as_attachment=True)

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


@main.route('/sair')
def sair():
    logout_user()
    flash("Sessão encerrada com sucesso.", "success")
    return redirect(url_for('auth.login'))


@main.route('/enviar_sheets', methods=['POST'])
@login_required
def enviar_sheets():
    import gspread
    import json
    from google.oauth2.service_account import Credentials

    data = request.get_json()
    ids = data.get('ids', [])

    if not ids:
        return jsonify(success=False, message="Nenhum ID recebido.")

    registros = Auditoria.query.filter(Auditoria.id.in_(ids)).all()

    # ✅ Conexão segura com Google Sheets usando variável de ambiente
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credenciais_json = os.getenv("GOOGLE_CREDENTIALS")
    if not credenciais_json:
        return jsonify(success=False, message="Credenciais do Google não encontradas.")

    try:
        info = json.loads(credenciais_json)
        CREDS = Credentials.from_service_account_info(info, scopes=SCOPES)
        gc = gspread.authorize(CREDS)
    except Exception as e:
        return jsonify(success=False, message=f"Erro na autenticação com o Google: {e}")

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
@main.route('/excluir_prestador/<int:id>', methods=['POST'])
def excluir_prestador(id):
    prestador = Prestador.query.get_or_404(id)
    db.session.delete(prestador)
    db.session.commit()
    flash('Prestador excluído com sucesso!', 'success')
    return redirect(url_for('main.cadastro_prestador'))

    return jsonify(success=True)

@main.route('/excluir_auditor/<int:id>', methods=['POST'])
def excluir_auditor(id):
    auditor = Auditor.query.get_or_404(id)
    db.session.delete(auditor)
    db.session.commit()
    flash('Auditor excluído com sucesso!', 'success')
    return redirect(url_for('main.cadastro_auditor'))