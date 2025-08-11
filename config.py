import os
from datetime import timedelta

class Config:
    """Configurações base da aplicação"""
    
    # Configurações Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_muito_segura_aqui'
    
    # Configurações de dados
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # Arquivos de dados
    INTIMACOES_FILE = os.path.join(DATA_DIR, 'intimacoes.json')
    PROMPTS_FILE = os.path.join(DATA_DIR, 'prompts.json')
    ANALISES_FILE = os.path.join(DATA_DIR, 'analises.json')
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    
    # Configurações OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_DEFAULT_MODEL = 'gpt-4'
    OPENAI_DEFAULT_TEMPERATURE = 0.7
    OPENAI_DEFAULT_MAX_TOKENS = 500
    OPENAI_DEFAULT_TOP_P = 1.0
    
    # Configurações de backup
    MAX_BACKUPS = 10
    BACKUP_ON_SAVE = True
    
    # Configurações de paginação
    ITEMS_PER_PAGE = 20
    
    # Configurações de exportação
    EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    
    # Tipos de ação disponíveis
    TIPOS_ACAO = [
        'RENUNCIAR PRAZO',
        'OCULTAR',
        'ELABORAR PEÇA',
        'CONTATAR ASSISTIDO',
        'ANALISAR PROCESSO',
        'ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR',
        'URGÊNCIA'
    ]
    
    # Modelos OpenAI disponíveis
    OPENAI_MODELS = [
        'gpt-4',
        'gpt-4-turbo-preview',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k'
    ]
    
    @staticmethod
    def init_app(app):
        """Inicializar configurações da aplicação"""
        # Criar diretórios necessários
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Configurações para testes"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}