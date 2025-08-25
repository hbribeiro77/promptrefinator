import openai
import time
import re
from typing import Tuple, Dict, Any, Optional, List
from config import Config
from services.data_service import DataService
from services.ai_service_interface import AIServiceInterface

class OpenAIService(AIServiceInterface):
    """Serviço para integração com a API da OpenAI"""
    
    def __init__(self):
        """Inicializar o serviço OpenAI"""
        self.data_service = DataService()
        self.config = Config()
        self.client = None
        self._initialize_client()
    
    def initialize_client(self) -> bool:
        """Inicializar cliente OpenAI com a chave da API"""
        return self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Inicializar cliente OpenAI com a chave da API"""
        try:
            # Priorizar variável de ambiente sobre arquivo de configuração
            api_key = self.config.OPENAI_API_KEY
            
            if not api_key:
                # Fallback para arquivo de configuração
                config = self.data_service.get_config()
                api_key = config.get('openai_api_key', '')
            
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                print("✅ Cliente OpenAI inicializado com sucesso")
                return True
            else:
                print("⚠️  Aviso: Chave da API OpenAI não configurada.")
                print("   Configure a variável de ambiente OPENAI_API_KEY ou use a interface de configurações.")
                self.client = None
                return False
        except Exception as e:
            print(f"❌ Erro ao inicializar cliente OpenAI: {e}")
            self.client = None
            return False
    
    def update_api_key(self, api_key: str):
        """Atualizar chave da API"""
        try:
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                self.client = None
        except Exception as e:
            print(f"Erro ao atualizar chave da API: {e}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """Testar conexão com a API OpenAI"""
        if not self.client:
            return False, "Cliente OpenAI não inicializado. Verifique a chave da API."
        
        try:
            # Fazer uma chamada simples para testar
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Teste de conexão. Responda apenas 'OK'."}
                ],
                max_tokens=5,
                temperature=0
            )
            
            return True, "Conexão com OpenAI estabelecida com sucesso"
            
        except openai.AuthenticationError:
            return False, "Erro de autenticação. Verifique a chave da API."
        except openai.RateLimitError:
            return False, "Limite de taxa excedido. Tente novamente mais tarde."
        except openai.APIError as e:
            return False, f"Erro da API OpenAI: {str(e)}"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    def analisar_intimacao(self, 
                          contexto: str, 
                          prompt_template: str, 
                          parametros: Dict[str, Any]) -> Tuple[str, str]:
        """Analisar intimação usando OpenAI"""
        if not self.client:
            raise Exception("Cliente OpenAI não inicializado. Configure a chave da API.")
        
        # Construir prompt completo
        prompt_completo = self._construir_prompt(prompt_template, contexto)
        
        # Validar parâmetros
        parametros_validados = self._validar_parametros(parametros)
        
        # Fazer chamada para OpenAI com retry
        resposta_completa = self._fazer_chamada_com_retry(
            prompt_completo, 
            parametros_validados
        )
        
        # Extrair classificação da resposta
        classificacao = self._extrair_classificacao(resposta_completa)
        
        return classificacao, resposta_completa
    
    def _construir_prompt(self, template: str, contexto: str) -> str:
        """Construir prompt completo substituindo variáveis"""
        # Lista de tipos de ação para incluir no prompt
        tipos_acao = self.config.TIPOS_ACAO
        tipos_acao_str = "\n".join([f"- {acao}" for acao in tipos_acao])
        
        # Substituir variáveis no template
        prompt = template.replace('{contexto}', contexto)
        prompt = prompt.replace('{tipos_acao}', tipos_acao_str)
        
        # Adicionar instruções específicas se não estiverem no template
        if 'tipos de ação' not in prompt.lower() and 'classificação' not in prompt.lower():
            prompt += f"\n\nTipos de ação disponíveis:\n{tipos_acao_str}\n\nResponda APENAS com um dos tipos de ação listados acima."
        
        return prompt
    
    def _validar_parametros(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros da OpenAI"""
        config = self.data_service.get_config()
        parametros_padrao = config.get('parametros_padrao', {})
        
        # Usar valores padrão se não fornecidos
        parametros_validados = {
            'model': parametros.get('model', parametros_padrao.get('model', 'gpt-4')),
            'temperature': float(parametros.get('temperature', parametros_padrao.get('temperature', 0.7))),
            'max_tokens': int(parametros.get('max_tokens', parametros_padrao.get('max_tokens', 500))),
            'top_p': float(parametros.get('top_p', parametros_padrao.get('top_p', 1.0)))
        }
        
        # Validar limites
        parametros_validados['temperature'] = max(0.0, min(2.0, parametros_validados['temperature']))
        parametros_validados['max_tokens'] = max(1, min(4000, parametros_validados['max_tokens']))
        parametros_validados['top_p'] = max(0.0, min(1.0, parametros_validados['top_p']))
        
        # Verificar se o modelo está na lista de modelos disponíveis
        if parametros_validados['model'] not in self.config.OPENAI_MODELS:
            parametros_validados['model'] = 'gpt-4'
        
        return parametros_validados
    
    def _fazer_chamada_com_retry(self, 
                                prompt: str, 
                                parametros: Dict[str, Any], 
                                max_retries: int = 3) -> str:
        """Fazer chamada para OpenAI com retry e backoff exponencial"""
        for tentativa in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=parametros['model'],
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um assistente especializado em análise de intimações jurídicas. Responda sempre com uma das classificações solicitadas."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=parametros['temperature'],
                    max_tokens=parametros['max_tokens'],
                    top_p=parametros['top_p']
                )
                
                return response.choices[0].message.content.strip()
                
            except openai.RateLimitError:
                if tentativa < max_retries - 1:
                    # Backoff exponencial: 1s, 2s, 4s
                    wait_time = 2 ** tentativa
                    print(f"Rate limit atingido. Aguardando {wait_time}s antes da próxima tentativa...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Limite de taxa da OpenAI excedido após múltiplas tentativas")
            
            except openai.APIError as e:
                if tentativa < max_retries - 1:
                    wait_time = 2 ** tentativa
                    print(f"Erro da API OpenAI: {e}. Tentando novamente em {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Erro da API OpenAI após múltiplas tentativas: {str(e)}")
            
            except Exception as e:
                raise Exception(f"Erro inesperado na chamada OpenAI: {str(e)}")
        
        raise Exception("Falha ao completar chamada OpenAI após múltiplas tentativas")
    
    def _extrair_classificacao(self, resposta: str) -> str:
        """Extrair classificação da resposta da IA"""
        if not resposta:
            return "ERRO: Resposta vazia"
        
        # Limpar resposta
        resposta_limpa = resposta.strip().upper()
        
        # Mapeamento de variações para classificações padrão
        mapeamento_variacoes = {
            'ELABORAR_PECA': 'ELABORAR PEÇA',
            'ELABORAR PECA': 'ELABORAR PEÇA',
            'CONTATAR_ASSISTIDO': 'CONTATAR ASSISTIDO',
            'ANALISAR_PROCESSO': 'ANALISAR PROCESSO',
            'RENUNCIAR_PRAZO': 'RENUNCIAR PRAZO',
            'ENCAMINHAR_INTIMACAO_PARA_OUTRO_DEFENSOR': 'ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR',
            'URGENCIA': 'URGÊNCIA'
        }
        
        # Primeiro, tentar extrair o valor do JSON
        import json
        try:
            # Tentar fazer parse do JSON
            dados_json = json.loads(resposta)
            if 'triagem' in dados_json:
                triagem_ia = dados_json['triagem'].upper().strip()
                # Verificar se existe no mapeamento
                if triagem_ia in mapeamento_variacoes:
                    return mapeamento_variacoes[triagem_ia]
                # Verificar se é uma das classificações padrão
                for tipo_acao in self.config.TIPOS_ACAO:
                    if tipo_acao.upper() == triagem_ia:
                        return tipo_acao
        except json.JSONDecodeError:
            pass
        
        # Se não conseguiu extrair do JSON, tentar busca direta
        for tipo_acao in self.config.TIPOS_ACAO:
            if tipo_acao.upper() in resposta_limpa:
                return tipo_acao
        
        # Tentar correspondência com variações
        for variacao, classificacao_padrao in mapeamento_variacoes.items():
            if variacao in resposta_limpa:
                return classificacao_padrao
        
        # Se não encontrou uma classificação exata, tentar correspondência parcial
        for tipo_acao in self.config.TIPOS_ACAO:
            palavras_chave = tipo_acao.upper().split()
            if all(palavra in resposta_limpa for palavra in palavras_chave):
                return tipo_acao
        
        # Tentar extrair usando regex para padrões comuns
        patterns = [
            r'"triagem":\s*"([^"]+)"',
            r'triagem[:\s]*([^\n\.]+)',
            r'classificação[:\s]*([^\n\.]+)',
            r'resposta[:\s]*([^\n\.]+)',
            r'ação[:\s]*([^\n\.]+)',
            r'^([^\n\.]+)$'  # Linha única
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resposta_limpa, re.IGNORECASE)
            if match:
                possivel_classificacao = match.group(1).strip()
                # Verificar se existe no mapeamento
                if possivel_classificacao in mapeamento_variacoes:
                    return mapeamento_variacoes[possivel_classificacao]
                # Verificar se é uma das classificações padrão
                for tipo_acao in self.config.TIPOS_ACAO:
                    if tipo_acao.upper() == possivel_classificacao:
                        return tipo_acao
        
        # Se ainda não encontrou, retornar a resposta original com indicação de erro
        return f"ERRO: Classificação não reconhecida - {resposta[:100]}"
    
    def get_available_models(self) -> list:
        """Obter lista de modelos disponíveis"""
        return self.config.OPENAI_MODELS
    
    def estimate_cost(self, 
                     prompt_length: int, 
                     response_length: int, 
                     model: str) -> float:
        """Estimar custo de uma chamada"""
        # Estimativas de custo por 1K tokens (valores aproximados em USD - 2025)
        costs_per_1k = {
            # GPT-5 Series (Premium pricing)
            'gpt-5': {'input': 0.10, 'output': 0.20},
            'gpt-5-mini': {'input': 0.05, 'output': 0.10},
            'gpt-5-nano': {'input': 0.02, 'output': 0.04},
            'gpt-5-chat': {'input': 0.03, 'output': 0.06},
            
            # GPT-4.1 Series
            'gpt-4.1': {'input': 0.04, 'output': 0.08},
            'gpt-4.1-mini': {'input': 0.015, 'output': 0.03},
            'gpt-4.1-nano': {'input': 0.008, 'output': 0.015},
            
            # GPT-4o Series (Multimodal)
            'gpt-4o': {'input': 0.025, 'output': 0.05},
            'gpt-4o-mini': {'input': 0.01, 'output': 0.02},
            'chatgpt-4o-latest': {'input': 0.025, 'output': 0.05},
            
            # o-Series (Reasoning - Higher cost due to compute)
            'o3': {'input': 0.15, 'output': 0.30},
            'o3-pro': {'input': 0.25, 'output': 0.50},
            'o3-mini': {'input': 0.08, 'output': 0.16},
            'o4-mini': {'input': 0.06, 'output': 0.12},
            
            # GPT-4 Series (Legacy)
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
            
            # GPT-3.5 Series (Cost-effective)
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004}
        }
        
        if model not in costs_per_1k:
            model = 'gpt-4'  # Usar gpt-4 como padrão para estimativa
        
        # Estimativa simples: ~4 caracteres por token
        input_tokens = prompt_length / 4
        output_tokens = response_length / 4
        
        input_cost = (input_tokens / 1000) * costs_per_1k[model]['input']
        output_cost = (output_tokens / 1000) * costs_per_1k[model]['output']
        
        return input_cost + output_cost
    
    def analyze_text(self, 
                    prompt: str, 
                    modelo: str = "gpt-4", 
                    temperatura: float = 0.1, 
                    max_tokens: int = 500) -> str:
        """Método simples para análise de texto genérica"""
        if not self.client:
            raise Exception("Cliente OpenAI não inicializado. Configure a chave da API.")
        
        parametros = {
            'model': modelo,
            'temperature': temperatura,
            'max_tokens': max_tokens,
            'top_p': 1.0
        }
        
        return self._fazer_chamada_com_retry(prompt, parametros)
    
    def get_provider_name(self) -> str:
        """Obter nome do provedor"""
        return "OpenAI"
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Obter parâmetros padrão do OpenAI"""
        return {
            'model': self.config.OPENAI_DEFAULT_MODEL,
            'temperature': self.config.OPENAI_DEFAULT_TEMPERATURE,
            'max_tokens': self.config.OPENAI_DEFAULT_MAX_TOKENS,
            'top_p': self.config.OPENAI_DEFAULT_TOP_P
        }
    
    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros (reutiliza método existente)"""
        return self._validar_parametros(parametros)