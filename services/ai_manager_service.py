from typing import Dict, Any, List, Tuple, Optional
from services.ai_service_interface import AIServiceInterface
from services.openai_service import OpenAIService
from services.azure_service import AzureService
from services.data_service import DataService

class AIManagerService:
    """Gerenciador de serviços de IA que permite alternar entre diferentes provedores"""
    
    def __init__(self):
        """Inicializar o gerenciador de IA"""
        self.data_service = DataService()
        self.providers = {
            'openai': OpenAIService,
            'azure': AzureService
        }
        self.current_provider = None
        self.current_service = None
        self._initialize_current_provider()
    
    def _initialize_current_provider(self):
        """Inicializar o provedor atual baseado na configuração"""
        config = self.data_service.get_config()
        provider_name = config.get('ai_provider', 'openai')
        self.set_provider(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Obter lista de provedores disponíveis"""
        return list(self.providers.keys())
    
    def get_current_provider(self) -> str:
        """Obter nome do provedor atual"""
        return self.current_provider or 'openai'
    
    def set_provider(self, provider_name: str) -> bool:
        """Definir o provedor de IA atual
        
        Args:
            provider_name: Nome do provedor ('openai', etc.)
            
        Returns:
            bool: True se o provedor foi definido com sucesso
        """
        if provider_name not in self.providers:
            print(f"❌ Provedor '{provider_name}' não disponível")
            return False
        
        try:
            # Instanciar o serviço do provedor
            service_class = self.providers[provider_name]
            self.current_service = service_class()
            
            # Tentar inicializar o cliente
            if self.current_service.initialize_client():
                self.current_provider = provider_name
                print(f"✅ Provedor '{provider_name}' definido com sucesso")
                
                # Salvar configuração
                self._save_provider_config(provider_name)
                return True
            else:
                print(f"❌ Falha ao inicializar provedor '{provider_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao definir provedor '{provider_name}': {e}")
            return False
    
    def _save_provider_config(self, provider_name: str):
        """Salvar configuração do provedor atual"""
        try:
            config = self.data_service.get_config() or {}
            config['ai_provider'] = provider_name
            self.data_service.save_config(config)
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível salvar configuração do provedor: {e}")
    
    def get_current_service(self) -> Optional[AIServiceInterface]:
        """Obter instância do serviço atual"""
        return self.current_service
    
    def test_connection(self) -> Tuple[bool, str]:
        """Testar conexão com o provedor atual"""
        if not self.current_service:
            return False, "Nenhum provedor configurado"
        
        return self.current_service.test_connection()
    
    def analisar_intimacao(self, 
                          contexto: str, 
                          prompt_template: str, 
                          parametros: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
        """Analisar intimação usando o provedor atual"""
        if not self.current_service:
            raise Exception("Nenhum provedor de IA configurado")
        
        return self.current_service.analisar_intimacao(contexto, prompt_template, parametros)
    
    def get_available_models(self) -> List[str]:
        """Obter modelos disponíveis do provedor atual"""
        if not self.current_service:
            return []
        
        return self.current_service.get_available_models()
    
    def get_provider_display_name(self) -> str:
        """Obter nome de exibição do provedor atual"""
        if not self.current_service:
            return "Nenhum provedor"
        
        return self.current_service.get_provider_name()
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Obter parâmetros padrão do provedor atual"""
        if not self.current_service:
            return {}
        
        return self.current_service.get_default_parameters()
    
    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parâmetros para o provedor atual"""
        if not self.current_service:
            return parametros
        
        return self.current_service.validate_parameters(parametros)
    
    # Função estimate_cost removida - simulação de custos desabilitada
    
    def analyze_text(self, prompt: str, modelo: str = "gpt-4", temperatura: float = 0.1, max_tokens: int = 500) -> str:
        """Método simples para análise de texto genérica usando o provedor atual"""
        if not self.current_service:
            raise Exception("Nenhum provedor de IA configurado")
        
        return self.current_service.analyze_text(prompt, modelo, temperatura, max_tokens)
    
    def add_provider(self, name: str, service_class):
        """Adicionar novo provedor de IA
        
        Args:
            name: Nome do provedor
            service_class: Classe que implementa AIServiceInterface
        """
        if not issubclass(service_class, AIServiceInterface):
            raise ValueError(f"Classe {service_class} deve implementar AIServiceInterface")
        
        self.providers[name] = service_class
        print(f"✅ Provedor '{name}' adicionado com sucesso")