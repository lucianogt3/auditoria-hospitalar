<%page args="r, logo_url"/>

<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; font-size: 10px; margin: 30px; line-height: 1.5; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 10px; }
    td, th { border: 1px solid #000; padding: 4px; vertical-align: top; } 
    .center { text-align: center; }
    .bold { font-weight: bold; }
    .assinatura td { height: 60px; padding-top: 20px; }
    .sub-label { font-size: 9px; font-style: italic; color: #333; }
  </style>
</head>
<body>

<div class="logo-container">
  <img src="${logo_url}" alt="Logo IPASGO" style="height: 60px;">
</div>

<h3 class="center">Relatório de Auditoria Hospitalar</h3>

<table>
  <tr>
    <td colspan="2" class="bold">Nome Prestador:<br>${r.nome_prestador or ''}</td>
    <td colspan="2" class="bold">Código Prestador:<br>${r.cod_prestador or ''}</td>
  </tr>
  <tr>
    <td colspan="2" class="bold">Nome do Beneficiário:<br>${r.nome_beneficiario or ''}</td>
    <td colspan="2" class="bold">Código Beneficiário:<br>${r.cod_beneficiario or ''}</td>
  </tr>
  <tr>
    <td colspan="2" class="bold">Data da auditoria:<br>${r.data_auditoria_br or ''}</td>
    <td colspan="2" class="bold">Data e hora internação:<br>${r.data_internacao_br or ''}</td>
  </tr>
  <tr>
    <td colspan="2" class="bold">Data e hora alta:<br>${r.data_alta_br or ''}</td>
    <td colspan="2" class="bold">Período da fatura:<br>${r.fatura_de_br or ''} a ${r.fatura_ate_br or ''}</td>
  </tr>
</table>

<table>
  <thead>
    <tr class="center bold">
      <td rowspan="2">Grupo de despesas</td>
      <td colspan="2">Quantidade (diárias)</td>
      <td rowspan="2">Valor apresentado (R$)</td>
      <td rowspan="2">Glosa médica (R$)</td>
      <td rowspan="2">Glosa enfermagem (R$)</td>
      <td rowspan="2">Valor liberado (R$)</td>
    </tr>
    <tr class="center bold">
      <td class="sub-label">Apresentada</td>
      <td class="sub-label">Autorizada</td>
    </tr>
  </thead>
  <tbody>
    % for i in range(1, 11):
    <tr class="center">
      <td>${r.get('grupo_' + str(i), '')}</td>
      <td>${r.get('qtd_apresentada_' + str(i)) or ''}</td>
      <td>${r.get('qtd_autorizada_' + str(i)) or ''}</td>
      <td>
        % if r.get('valor_apresentado_' + str(i)) and r.get('valor_apresentado_' + str(i)) > 0:
          R$ ${'%.2f' % r.get('valor_apresentado_' + str(i))}
        % endif
      </td>
      <td>
        % if r.get('glosa_medico_' + str(i)) and r.get('glosa_medico_' + str(i)) > 0:
          R$ ${'%.2f' % r.get('glosa_medico_' + str(i))}
        % endif
      </td>
      <td>
        % if r.get('glosa_enfermagem_' + str(i)) and r.get('glosa_enfermagem_' + str(i)) > 0:
          R$ ${'%.2f' % r.get('glosa_enfermagem_' + str(i))}
        % endif
      </td>
      <td>
        % if r.get('valor_liberado_' + str(i)) and r.get('valor_liberado_' + str(i)) > 0:
          R$ ${'%.2f' % r.get('valor_liberado_' + str(i))}
        % endif
      </td>
    </tr>
    % endfor
  </tbody>
  <tfoot>
    <tr class="center bold">
      <td colspan="3">TOTAL</td>
      <td>R$ ${'%.2f' % (r.total_apresentado or 0)}</td>
      <td>R$ ${'%.2f' % (r.total_glosa_medico or 0)}</td>
      <td>R$ ${'%.2f' % (r.total_glosa_enfermagem or 0)}</td>
      <td>R$ ${'%.2f' % (r.total_liberado or 0)}</td>
    </tr>
  </tfoot>
</table>

<p><strong>* N/A - Não se aplica</strong></p>

<table class="assinatura">
  <tr>
    <td>
      <strong>De acordo Auditoria/Faturamento Prestador:</strong><br><br>
      Data: ${r.data_registro_br or 'N/A'}<br><br>
      Assinatura e carimbo: ___________________________________________
    </td>
    <td>
      <strong>Auditoria Operadora:</strong><br><br>
      Data: ${r.data_registro_br or 'N/A'}<br><br>
      Médico Auditor:<br>
      Assinatura e carimbo: ___________________________________________<br><br>
      Enfermeiro Auditor:<br>
      Assinatura e carimbo: ___________________________________________
    </td>
  </tr>
</table>

</body>
</html>
