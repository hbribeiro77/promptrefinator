# 🐳 Dockerfile para Sistema Prompt Refinator
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Instalar dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r promptrefinator && useradd -r -g promptrefinator promptrefinator

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/data/backups \
    && mkdir -p /app/logs

# Configurar permissões
RUN chown -R promptrefinator:promptrefinator /app \
    && chmod -R 755 /app

# Mudar para usuário não-root
USER promptrefinator

# Expor porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Comando para executar a aplicação
CMD gunicorn --bind 0.0.0.0:5000 --workers 3 --timeout 120 --access-logfile - --error-logfile - app:app
