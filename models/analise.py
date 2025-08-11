import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class Analise:
    """Modelo para representar uma análise de intimação"""
    
    def __init__(self, 
                 intimacao_id: str,
                 prompt_id: str,
                 parametros_openai: Dict[str, Any],
                 resultado_ia: str,
                 resposta_completa_ia: str,
                 classificacao_manual: str,
                 acertou: bool,
                 tempo_processamento: float,
                 id: Optional[str] = None,
                 data_analise: Optional[datetime] = None):
        """
        Inicializar uma nova análise
        
        Args:
            intimacao_id: ID da intimação analisada
            prompt_id: ID do prompt utilizado
            parametros_openai: Parâmetros usados na chamada da OpenAI
            resultado_ia: Classificação retornada pela IA
            resposta_completa_ia: Resposta completa da IA
            classificacao_manual: Classificação manual da intimação
            acertou: Se a IA acertou a classificação
            tempo_processamento: Tempo em segundos para processar
            id: ID único da análise (gerado automaticamente se não fornecido)
            data_analise: Data da análise (atual se não fornecida)
        """
        self.id = id or str(uuid.uuid4())
        self.intimacao_id = intimacao_id
        self.prompt_id = prompt_id
        self.parametros_openai = parametros_openai or {}
        self.resultado_ia = resultado_ia
        self.resposta_completa_ia = resposta_completa_ia
        self.classificacao_manual = classificacao_manual
        self.acertou = acertou
        self.tempo_processamento = tempo_processamento
        self.data_analise = data_analise or datetime.now()
    
    def to_dict(self) -> dict:
        """Converter para dicionário para serialização JSON"""
        return {
            'id': self.id,
            'intimacao_id': self.intimacao_id,
            'prompt_id': self.prompt_id,
            'parametros_openai': self.parametros_openai,
            'resultado_ia': self.resultado_ia,
            'resposta_completa_ia': self.resposta_completa_ia,
            'classificacao_manual': self.classificacao_manual,
            'acertou': self.acertou,
            'tempo_processamento': self.tempo_processamento,
            'data_analise': self.data_analise.isoformat() if isinstance(self.data_analise, datetime) else self.data_analise
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Analise':
        """Criar instância a partir de dicionário"""
        data_analise = data.get('data_analise')
        if isinstance(data_analise, str):
            try:
                data_analise = datetime.fromisoformat(data_analise.replace('Z', '+00:00'))
            except ValueError:
                data_analise = datetime.now()
        elif data_analise is None:
            data_analise = datetime.now()
        
        return cls(
            id=data.get('id'),
            intimacao_id=data.get('intimacao_id', ''),
            prompt_id=data.get('prompt_id', ''),
            parametros_openai=data.get('parametros_openai', {}),
            resultado_ia=data.get('resultado_ia', ''),
            resposta_completa_ia=data.get('resposta_completa_ia', ''),
            classificacao_manual=data.get('classificacao_manual', ''),
            acertou=data.get('acertou', False),
            tempo_processamento=data.get('tempo_processamento', 0.0),
            data_analise=data_analise
        )
    
    def validate(self) -> list:
        """Validar dados da análise"""
        errors = []
        
        if not self.intimacao_id or not self.intimacao_id.strip():
            errors.append('ID da intimação é obrigatório')
        
        if not self.prompt_id or not self.prompt_id.strip():
            errors.append('ID do prompt é obrigatório')
        
        if not self.resultado_ia or not self.resultado_ia.strip():
            errors.append('Resultado da IA é obrigatório')
        
        if not self.classificacao_manual or not self.classificacao_manual.strip():
            errors.append('Classificação manual é obrigatória')
        
        if self.tempo_processamento < 0:
            errors.append('Tempo de processamento deve ser positivo')
        
        # Validar parâmetros OpenAI
        if not isinstance(self.parametros_openai, dict):
            errors.append('Parâmetros OpenAI devem ser um dicionário')
        else:
            required_params = ['model', 'temperature', 'max_tokens', 'top_p']
            for param in required_params:
                if param not in self.parametros_openai:
                    errors.append(f'Parâmetro OpenAI obrigatório ausente: {param}')
        
        return errors
    
    def get_accuracy_status(self) -> str:
        """Obter status de acurácia em texto"""
        return "Acertou" if self.acertou else "Errou"
    
    def get_accuracy_class(self) -> str:
        """Obter classe CSS para status de acurácia"""
        return "success" if self.acertou else "danger"
    
    def get_processing_time_formatted(self) -> str:
        """Obter tempo de processamento formatado"""
        if self.tempo_processamento < 1:
            return f"{self.tempo_processamento * 1000:.0f}ms"
        else:
            return f"{self.tempo_processamento:.2f}s"
    
    def estimate_cost(self) -> float:
        """Estimativa de custo baseada no modelo usado"""
        model = self.parametros_openai.get('model', 'gpt-4')
        max_tokens = self.parametros_openai.get('max_tokens', 500)
        
        # Estimativas de custo por 1K tokens (valores aproximados)
        costs_per_1k = {
            'gpt-4': 0.03,
            'gpt-4-turbo-preview': 0.01,
            'gpt-3.5-turbo': 0.002,
            'gpt-3.5-turbo-16k': 0.004
        }
        
        cost_per_1k = costs_per_1k.get(model, 0.03)
        estimated_tokens = max_tokens + len(self.resposta_completa_ia) // 4  # Estimativa simples
        
        return (estimated_tokens / 1000) * cost_per_1k
    
    def __str__(self) -> str:
        """Representação string da análise"""
        status = "✓" if self.acertou else "✗"
        return f"Análise({self.id}): {self.resultado_ia} vs {self.classificacao_manual} {status}"
    
    def __repr__(self) -> str:
        """Representação para debug"""
        return f"Analise(id='{self.id}', acertou={self.acertou})"