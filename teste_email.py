html = "<h1>Teste de PDF</h1><p>Funcionando...</p>"
pdf = pdfkit.from_string(html, False, configuration=config, options=options)
return send_file(BytesIO(pdf), download_name="teste.pdf", as_attachment=True)
