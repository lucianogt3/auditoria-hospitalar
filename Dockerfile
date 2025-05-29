# Usa uma imagem base com Python
FROM python:3.11-slim

FROM python:3.11-slim

# Instala dependências necessárias
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xz-utils \
    libjpeg-dev \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libx11-6 \
    && apt-get clean

# Instala o wkhtmltopdf oficial com Qt (suporte completo para PDF)
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb && \
    rm wkhtmltox_0.12.6-1.buster_amd64.deb

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos do projeto
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expõe a porta para o Render
EXPOSE 5000

# Inicia o app com Gunicorn
CMD ["gunicorn", "auditoria_app:app", "--bind", "0.0.0.0:5000"]
