# Usa uma imagem base com Python
FROM python:3.11-slim

# Instala dependências do sistema (inclusive o wkhtmltopdf)
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libx11-6 \
    && apt-get clean

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos
COPY . .

# Instala dependências Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expõe a porta
EXPOSE 5000

# Comando para iniciar o app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
