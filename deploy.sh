#!/bin/bash

# 🚀 Script de Deploy Automatizado - Sistema Prompt Refinator
# Uso: ./deploy.sh [DOMINIO] [OPENAI_API_KEY]

set -e  # Para o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    error "Este script deve ser executado como root (sudo)"
fi

# Verificar parâmetros
if [ $# -lt 2 ]; then
    echo "Uso: $0 <DOMINIO> <OPENAI_API_KEY>"
    echo "Exemplo: $0 promptrefinator.com sk-proj-abc123..."
    exit 1
fi

DOMINIO=$1
OPENAI_API_KEY=$2

log "🚀 Iniciando deploy do Sistema Prompt Refinator"
log "Domínio: $DOMINIO"
log "API Key: ${OPENAI_API_KEY:0:10}..."

# 1. Atualizar sistema
log "📦 Atualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependências
log "🔧 Instalando dependências do sistema..."
apt install -y python3 python3-pip python3-venv nginx supervisor git curl

# 3. Criar usuário
log "👤 Criando usuário promptrefinator..."
if id "promptrefinator" &>/dev/null; then
    warn "Usuário promptrefinator já existe"
else
    adduser --disabled-password --gecos "" promptrefinator
    usermod -aG sudo promptrefinator
fi

# 4. Clonar repositório
log "📥 Clonando repositório..."
if [ -d "/home/promptrefinator/promptrefinator" ]; then
    warn "Diretório já existe, fazendo pull..."
    su - promptrefinator -c "cd /home/promptrefinator/promptrefinator && git pull origin main"
else
    su - promptrefinator -c "cd /home/promptrefinator && git clone https://github.com/hbribeiro77/promptrefinator.git"
fi

# 5. Configurar ambiente virtual
log "🐍 Configurando ambiente virtual..."
su - promptrefinator -c "cd /home/promptrefinator/promptrefinator && python3 -m venv venv"
su - promptrefinator -c "cd /home/promptrefinator/promptrefinator && source venv/bin/activate && pip install -r requirements.txt"

# 6. Configurar variáveis de ambiente
log "🔐 Configurando variáveis de ambiente..."
cat > /home/promptrefinator/promptrefinator/.env << EOF
OPENAI_API_KEY=$OPENAI_API_KEY
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
EOF

chown promptrefinator:promptrefinator /home/promptrefinator/promptrefinator/.env
chmod 600 /home/promptrefinator/promptrefinator/.env

# 7. Configurar Supervisor
log "⚙️ Configurando Supervisor..."
mkdir -p /var/log/promptrefinator
chown promptrefinator:www-data /var/log/promptrefinator

cat > /etc/supervisor/conf.d/promptrefinator.conf << EOF
[program:promptrefinator]
directory=/home/promptrefinator/promptrefinator
command=/home/promptrefinator/promptrefinator/venv/bin/gunicorn --workers 3 --bind unix:promptrefinator.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/promptrefinator/promptrefinator.err.log
stdout_logfile=/var/log/promptrefinator/promptrefinator.out.log
user=promptrefinator
group=www-data
environment=PATH="/home/promptrefinator/promptrefinator/venv/bin"
EOF

# 8. Configurar Nginx
log "🌐 Configurando Nginx..."
cat > /etc/nginx/sites-available/promptrefinator << EOF
server {
    listen 80;
    server_name $DOMINIO www.$DOMINIO;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/promptrefinator/promptrefinator/promptrefinator.sock;
    }

    location /static {
        alias /home/promptrefinator/promptrefinator/static;
    }

    # Configurações de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# 9. Ativar site Nginx
if [ -L "/etc/nginx/sites-enabled/promptrefinator" ]; then
    rm /etc/nginx/sites-enabled/promptrefinator
fi
ln -s /etc/nginx/sites-available/promptrefinator /etc/nginx/sites-enabled

# Remover site default se existir
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

# 10. Configurar permissões
log "🔒 Configurando permissões..."
chown -R promptrefinator:www-data /home/promptrefinator/promptrefinator
chmod -R 755 /home/promptrefinator/promptrefinator

# 11. Configurar firewall
log "🔥 Configurando firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# 12. Iniciar serviços
log "🚀 Iniciando serviços..."
supervisorctl reread
supervisorctl update
supervisorctl start promptrefinator

systemctl restart nginx
systemctl enable nginx
systemctl enable supervisor

# 13. Verificar status
log "✅ Verificando status dos serviços..."
sleep 5

if supervisorctl status promptrefinator | grep -q "RUNNING"; then
    log "✅ Supervisor: OK"
else
    error "❌ Supervisor não está rodando"
fi

if systemctl is-active --quiet nginx; then
    log "✅ Nginx: OK"
else
    error "❌ Nginx não está rodando"
fi

# 14. Testar aplicação
log "🧪 Testando aplicação..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
    log "✅ Aplicação respondendo corretamente"
else
    warn "⚠️ Aplicação pode não estar respondendo corretamente"
fi

# 15. Configurar SSL (opcional)
read -p "Deseja configurar SSL/HTTPS com Let's Encrypt? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "🔒 Configurando SSL..."
    apt install -y certbot python3-certbot-nginx
    certbot --nginx -d $DOMINIO -d www.$DOMINIO --non-interactive --agree-tos --email admin@$DOMINIO
fi

# 16. Configurar backup automático
log "💾 Configurando backup automático..."
mkdir -p /home/promptrefinator/backups

# Adicionar ao crontab do root
(crontab -l 2>/dev/null; echo "0 2 * * * tar -czf /home/promptrefinator/backups/backup-\$(date +\%Y\%m\%d).tar.gz /home/promptrefinator/promptrefinator/data/") | crontab -

log "🎉 Deploy concluído com sucesso!"
log "🌐 Acesse: http://$DOMINIO"
log "📊 Logs: sudo tail -f /var/log/promptrefinator/promptrefinator.out.log"
log "🔧 Status: sudo supervisorctl status promptrefinator"
log "🔄 Reiniciar: sudo supervisorctl restart promptrefinator"
