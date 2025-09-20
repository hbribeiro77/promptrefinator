import os
from datetime import timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações base da aplicação"""
    
    # Configurações Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_muito_segura_aqui'
    
    # Configurações de dados
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # Arquivos de dados (apenas config.json ainda é usado)
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    # Nota: intimacoes.json, prompts.json e analises.json foram substituídos pelo SQLite
    
    # Configurações OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_DEFAULT_MODEL = 'gpt-4'
    OPENAI_DEFAULT_TEMPERATURE = 0.7
    OPENAI_DEFAULT_MAX_TOKENS = 500
    OPENAI_DEFAULT_TOP_P = 1.0
    
    # Configurações Azure OpenAI
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    AZURE_OPENAI_DEFAULT_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEFAULT_DEPLOYMENT', 'gpt-4')
    AZURE_OPENAI_DEFAULT_TEMPERATURE = 0.7
    AZURE_OPENAI_DEFAULT_MAX_TOKENS = 500
    AZURE_OPENAI_DEFAULT_TOP_P = 1.0
    
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
    
    # Lista de defensores disponíveis
    DEFENSORES = [
        'Rodrigo Ahlert Weirich',
        'André Iglésias e Silva Borges',
        'Walter Luchese Willig',
        'Felipe Frota Aguiar Pizarro Drummond',
        'Marcus de Freitas Gregorio',
        'Eugenio Pedro Gomes de Oliveira Junior'
    ]
    
    @staticmethod
    def get_portal_tarefa_link(tarefa_id: str, config_data: dict = None) -> str:
        """
        Gera o link completo para uma tarefa no Portal da Defensoria
        
        Args:
            tarefa_id: ID da tarefa
            config_data: Dados de configuração (opcional)
            
        Returns:
            Link completo para a tarefa ou string vazia se não configurado
        """
        if not config_data:
            return ''
            
        portal_link = config_data.get('portal_defensoria_link', '')
        if not portal_link or not tarefa_id:
            return ''
            
        # Verificar se o link já tem parâmetro (contém ?)
        if '?' in portal_link:
            # Se já tem parâmetro, apenas concatenar o ID
            return f"{portal_link}{tarefa_id}"
        else:
            # Se não tem parâmetro, adicionar / antes do ID
            if not portal_link.endswith('/'):
                portal_link += '/'
            return f"{portal_link}{tarefa_id}"
    
    # Modelos OpenAI disponíveis (2025)
    OPENAI_MODELS = [
        # GPT-5 Series (Flagship models - 2025)
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano',
        'gpt-5-chat',
        
        # GPT-4.1 Series (April 2025)
        'gpt-4.1',
        'gpt-4.1-mini',
        'gpt-4.1-nano',
        
        # GPT-4o Series (Multimodal)
        'gpt-4o',
        'gpt-4o-mini',
        'chatgpt-4o-latest',
        
        # o-Series (Reasoning models)
        'o3',
        'o3-pro',
        'o3-mini',
        'o4-mini',
        
        # GPT-4 Series (Legacy but still supported)
        'gpt-4',
        'gpt-4-turbo',
        'gpt-4-turbo-preview',
        
        # GPT-3.5 Series (Cost-effective)
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k'
    ]
    
    # Preços padrão da API OpenAI (por 1M tokens)
    PRECOS_OPENAI_PADRAO = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        'data_atualizacao': '2025-01-23'
    }
    
    # Preços padrão da API Azure OpenAI (por 1M tokens)
    PRECOS_AZURE_PADRAO = {
        'gpt-4o': {'input': 5.00, 'output': 15.00},
        'gpt-4o-mini': {'input': 0.165, 'output': 0.66},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        'data_atualizacao': '2025-01-23'
    }
    
    # Modelos Azure OpenAI disponíveis (deployments) - 2025
    AZURE_OPENAI_MODELS = [
        # GPT-5 Series (Limited access required)
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano',
        'gpt-5-chat',
        
        # GPT-4.1 Series
        'gpt-4.1',
        'gpt-4.1-mini',
        'gpt-4.1-nano',
        
        # GPT-4o Series
        'gpt-4o',
        'gpt-4o-mini',
        
        # o-Series (Reasoning)
        'o3-mini',
        'o4-mini',
        
        # Open Source Reasoning Models
        'gpt-oss-120b',
        'gpt-oss-20b',
        
        # GPT-4 Series (Stable)
        'gpt-4',
        'gpt-4-turbo',
        
        # GPT-3.5 Series (Azure naming convention)
        'gpt-35-turbo',
        'gpt-35-turbo-16k'
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