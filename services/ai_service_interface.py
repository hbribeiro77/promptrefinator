from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List

class AIServiceInterface(ABC):
    """Interface abstrata para serviços de IA"""
    
    @abstractmethod
    def __init__(self):
        """Inicializar o serviço de IA"""
        pass
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Inicializar cliente da API
        
        Returns:
            bool: True se inicializado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Testar conexão com a API
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        pass
    
    @abstractmethod
    def analisar_intimacao(self, 
                          contexto: str, 
                          prompt_template: str, 
                          parametros: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
        """Analisar intimação usando IA
        
        Args:
            contexto: Contexto da intimação
            prompt_template: Template do prompt
            parametros: Parâmetros específicos do provedor
            
        Returns:
            Tuple[str, str, Dict[str, int]]: (classificação, resposta_completa, tokens_info)
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Obter lista de modelos disponíveis
        
        Returns:
            List[str]: Lista de modelos disponíveis
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Obter nome do provedor
        
        Returns:
            str: Nome do provedor (ex: 'OpenAI', 'Anthropic', etc.)
        """
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Obter parâmetros padrão do provedor
        
        Returns:
            Dict[str, Any]: Parâmetros padrão
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros
        
        Args:
            parametros: Parâmetros a serem validados
            
        Returns:
            Dict[str, Any]: Parâmetros validados
        """
        pass
    
    # Função estimate_cost removida - simulação de custos desabilitada
    
    @abstractmethod
    def analyze_text(self, prompt: str, modelo: str = "gpt-4", temperatura: float = 0.1, max_tokens: int = 500) -> str:
        """Método simples para análise de texto genérica
        
        Args:
            prompt: Texto do prompt
            modelo: Modelo a ser usado
            temperatura: Temperatura para geração
            max_tokens: Máximo de tokens
            
        Returns:
            str: Resposta da IA
        """
        pass