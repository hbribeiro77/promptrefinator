# 🐳 Dockerfile para Sistema Prompt Refinator
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

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

# Expor porta (Railway vai definir PORT)
EXPOSE ${PORT:-5000}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/ || exit 1

# Comando para executar a aplicação (usando PORT do Railway ou 5000 como fallback)
CMD ["sh", "-c", "echo 'Iniciando aplicação na porta ${PORT:-5000}' && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 600 --graceful-timeout 60 --access-logfile - --error-logfile - --log-level info app:app"]
