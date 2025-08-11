# 🚀 Guia de Deploy - Sistema Prompt Refinator

## 📋 **Pré-requisitos da VPS**

### **Sistema Operacional**
- Ubuntu 20.04+ ou Debian 11+
- 2GB RAM mínimo (4GB recomendado)
- 20GB espaço em disco
- Acesso SSH

### **Software Necessário**
- Python 3.8+
- Nginx
- Supervisor
- Git

---

## 🔧 **Passo a Passo do Deploy**

### **1. Conectar na VPS e Atualizar Sistema**
```bash
ssh usuario@ip-da-vps
sudo apt update && sudo apt upgrade -y
```

### **2. Instalar Dependências do Sistema**
```bash
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git
```

### **3. Criar Usuário para a Aplicação**
```bash
sudo adduser promptrefinator
sudo usermod -aG sudo promptrefinator
```

### **4. Clonar o Repositório**
```bash
sudo su - promptrefinator
cd /home/promptrefinator
git clone https://github.com/hbribeiro77/promptrefinator.git
cd promptrefinator
```

### **5. Configurar Ambiente Virtual**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **6. Configurar Variáveis de Ambiente**
```bash
nano .env
```

**Conteúdo do arquivo .env:**
```env
OPENAI_API_KEY=sk-sua-chave-aqui
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-muito-segura
```

### **7. Configurar Supervisor**

Criar arquivo de configuração:
```bash
sudo nano /etc/supervisor/conf.d/promptrefinator.conf
```

**Conteúdo:**
```ini
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
```

### **8. Criar Diretório de Logs**
```bash
sudo mkdir -p /var/log/promptrefinator
sudo chown promptrefinator:www-data /var/log/promptrefinator
```

### **9. Instalar Gunicorn**
```bash
source venv/bin/activate
pip install gunicorn
```

### **10. Configurar Nginx**

Criar arquivo de configuração:
```bash
sudo nano /etc/nginx/sites-available/promptrefinator
```

**Conteúdo:**
```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

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
```

### **11. Ativar Site Nginx**
```bash
sudo ln -s /etc/nginx/sites-available/promptrefinator /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### **12. Iniciar Serviços**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start promptrefinator
```

### **13. Configurar Firewall**
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 🔒 **Configurações de Segurança**

### **SSL/HTTPS (Recomendado)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

### **Configurações Adicionais de Segurança**
```bash
# Desabilitar login root
sudo nano /etc/ssh/sshd_config
# Alterar: PermitRootLogin no

# Reiniciar SSH
sudo systemctl restart ssh
```

---

## 📊 **Monitoramento e Logs**

### **Verificar Status dos Serviços**
```bash
sudo supervisorctl status promptrefinator
sudo systemctl status nginx
```

### **Ver Logs**
```bash
# Logs da aplicação
sudo tail -f /var/log/promptrefinator/promptrefinator.out.log
sudo tail -f /var/log/promptrefinator/promptrefinator.err.log

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🔄 **Atualizações**

### **Atualizar Código**
```bash
cd /home/promptrefinator/promptrefinator
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart promptrefinator
```

### **Backup dos Dados**
```bash
# Backup automático dos dados
sudo crontab -e

# Adicionar linha para backup diário às 2h da manhã:
0 2 * * * tar -czf /home/promptrefinator/backups/backup-$(date +\%Y\%m\%d).tar.gz /home/promptrefinator/promptrefinator/data/
```

---

## 🚨 **Troubleshooting**

### **Problemas Comuns**

**1. Aplicação não inicia**
```bash
sudo supervisorctl status promptrefinator
sudo tail -f /var/log/promptrefinator/promptrefinator.err.log
```

**2. Erro de permissão**
```bash
sudo chown -R promptrefinator:www-data /home/promptrefinator/promptrefinator
sudo chmod -R 755 /home/promptrefinator/promptrefinator
```

**3. Nginx não carrega**
```bash
sudo nginx -t
sudo systemctl status nginx
```

**4. Porta 80 bloqueada**
```bash
sudo ufw status
sudo ufw allow 80
```

---

## 📈 **Otimizações de Performance**

### **Configurações do Gunicorn**
```ini
# Ajustar workers baseado no número de CPUs
workers = (2 x num_cores) + 1
```

### **Configurações do Nginx**
```nginx
# Adicionar ao arquivo nginx.conf
client_max_body_size 10M;
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

---

## 🔧 **Comandos Úteis**

### **Gerenciamento de Serviços**
```bash
# Reiniciar aplicação
sudo supervisorctl restart promptrefinator

# Parar aplicação
sudo supervisorctl stop promptrefinator

# Ver status
sudo supervisorctl status

# Reiniciar Nginx
sudo systemctl restart nginx
```

### **Logs em Tempo Real**
```bash
# Acompanhar logs da aplicação
sudo tail -f /var/log/promptrefinator/promptrefinator.out.log

# Acompanhar logs de erro
sudo tail -f /var/log/promptrefinator/promptrefinator.err.log
```

---

## ✅ **Checklist de Deploy**

- [ ] VPS configurada com Ubuntu/Debian
- [ ] Python 3.8+ instalado
- [ ] Nginx instalado e configurado
- [ ] Supervisor instalado e configurado
- [ ] Repositório clonado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Arquivo .env configurado
- [ ] Chave da API OpenAI configurada
- [ ] Supervisor iniciado
- [ ] Nginx iniciado
- [ ] Firewall configurado
- [ ] SSL configurado (opcional)
- [ ] Backup configurado
- [ ] Aplicação acessível via navegador

---

## 🆘 **Suporte**

Em caso de problemas:
1. Verificar logs: `sudo tail -f /var/log/promptrefinator/promptrefinator.err.log`
2. Verificar status dos serviços: `sudo supervisorctl status`
3. Verificar conectividade: `curl -I http://localhost`
4. Verificar permissões: `ls -la /home/promptrefinator/promptrefinator/`

**Contato:** [Seu email de suporte]
