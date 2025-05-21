FROM python:3.11-slim

# Instala dependências do sistema + wkhtmltopdf
RUN apt-get update && \
    apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    libx11-6 && \
    apt-get clean

# Define diretório de trabalho
WORKDIR /app

# Copia tudo
COPY . .

# Instala dependências Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expõe a porta padrão
EXPOSE 8000

# Comando para iniciar o app com gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
