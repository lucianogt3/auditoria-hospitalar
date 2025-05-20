# Usa uma imagem Linux leve com Python
FROM python:3.11-slim

# Instala wkhtmltopdf e bibliotecas necessárias
RUN apt-get update && \
    apt-get install -y wkhtmltopdf build-essential libssl-dev libffi-dev \
        libxrender1 libxext6 libfontconfig1 libx11-6 && \
    apt-get clean

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . .

# Instala dependências do projeto
RUN pip install --upgrade pip && pip install -r requirements.txt

# Comando de inicialização
CMD ["gunicorn", "app:app"]
