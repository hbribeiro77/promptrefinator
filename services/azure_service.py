import time
import re
from typing import Tuple, Dict, Any, Optional, List
from openai import AzureOpenAI
from config import Config
from services.sqlite_service import SQLiteService
from services.ai_service_interface import AIServiceInterface
from services.classificacao_ia_extracao_resposta_texto_para_tipo_canonico_service import (
    classificacao_extracao_indica_falha_nucleo,
    extrair_classificacao_da_resposta_ia,
)
from services.extracao_texto_resposta_chat_completions_openai_compat import (
    texto_mensagem_assistente,
)

class AzureService(AIServiceInterface):
    """Serviço para integração com a API do Azure OpenAI"""
    
    def __init__(self):
        """Inicializar o serviço Azure OpenAI"""
        self.data_service = SQLiteService()
        self.config = Config()
        self.client = None
        self._initialize_client()
    
    def initialize_client(self) -> bool:
        """Inicializar cliente Azure OpenAI com as credenciais"""
        return self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Inicializar cliente Azure OpenAI com as credenciais"""
        try:
            # Priorizar variáveis de ambiente sobre arquivo de configuração
            api_key = self.config.AZURE_OPENAI_API_KEY
            endpoint = self.config.AZURE_OPENAI_ENDPOINT
            api_version = self.config.AZURE_OPENAI_API_VERSION
            
            if not api_key or not endpoint:
                # Fallback para arquivo de configuração
                config = self.data_service.get_config()
                api_key = api_key or config.get('azure_api_key', '')
                endpoint = endpoint or config.get('azure_endpoint', '')
                api_version = api_version or config.get('azure_api_version', '2024-02-15-preview')
            
            if api_key and endpoint:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=api_version
                )
                print("Cliente Azure OpenAI inicializado com sucesso")
                return True
            else:
                print("Aviso: Credenciais do Azure OpenAI não configuradas.")
                print("   Configure as credenciais através da interface de configurações.")
                self.client = None
                # Retornar True para permitir seleção do provedor mesmo sem credenciais
                return True
        except Exception as e:
            print(f"Erro ao inicializar cliente Azure OpenAI: {e}")
            self.client = None
            return False
    
    def update_credentials(self, api_key: str, endpoint: str, api_version: str = None):
        """Atualizar credenciais do Azure"""
        try:
            if api_version is None:
                api_version = self.config.AZURE_OPENAI_API_VERSION
            
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version
            )
            print("SUCESSO: Credenciais do Azure OpenAI atualizadas com sucesso")
        except Exception as e:
            print(f"ERRO: Erro ao atualizar credenciais do Azure OpenAI: {e}")
            self.client = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Testar conexão com a API do Azure OpenAI"""
        if not self.client:
            return False, "Cliente Azure OpenAI não inicializado. Verifique as credenciais."
        
        try:
            db = self.data_service.get_config() or {}
            deployment = Config.normalize_azure_deployment(
                (db.get('azure_deployment') or '').strip() or self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT
            )
            # Fazer uma chamada simples para testar a conexão
            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "user", "content": "Teste de conexão. Responda apenas 'OK'."}
                ],
                max_tokens=5,
                temperature=0
            )
            return True, "Conexão com Azure OpenAI estabelecida com sucesso!"
        except Exception as e:
            return False, f"Erro na conexão com Azure OpenAI: {str(e)}"
    
    def analisar_intimacao(self, 
                          contexto: str, 
                          prompt_template: str, 
                          parametros: Dict[str, Any]) -> Tuple[str, str, Dict[str, int]]:
        """Analisar intimação usando Azure OpenAI"""
        if not self.client:
            raise Exception("Cliente Azure OpenAI não inicializado")
        
        try:
            p = dict(parametros)
            raw_user_only = bool(p.pop("raw_user_prompt_only", False))
            prompt = (
                prompt_template
                if raw_user_only
                else self._construir_prompt(prompt_template, contexto)
            )
            parametros_validados = self._validar_parametros(p)
            parametros_validados["_raw_user_only"] = raw_user_only

            resposta_completa, tokens_info = self._fazer_chamada_com_retry(
                prompt, parametros_validados
            )
            
            # Extrair classificação
            classificacao = self._extrair_classificacao(resposta_completa)
            
            return classificacao, resposta_completa, tokens_info
            
        except Exception as e:
            raise Exception(f"Erro na análise com Azure OpenAI: {str(e)}")
    
    def _construir_prompt(self, template: str, contexto: str) -> str:
        """Construir prompt substituindo placeholders"""
        try:
            # Substituir placeholder do contexto
            prompt = template.replace('{contexto}', contexto)
            
            # Adicionar instruções específicas se necessário
            if '{instrucoes}' in prompt:
                instrucoes = "Analise o contexto fornecido e classifique a ação necessária."
                prompt = prompt.replace('{instrucoes}', instrucoes)
            
            return prompt
        except Exception as e:
            raise Exception(f"Erro ao construir prompt: {str(e)}")
    
    def _validar_parametros(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros para Azure OpenAI.

        Aceita as chaves usadas pelo app.py (`model`, `temperature`, `max_tokens`)
        e também `modelo` / `temperatura` (legado).
        """
        modelo_api = (
            parametros.get('model')
            or parametros.get('modelo')
            or self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT
        )
        modelo_api = Config.normalize_azure_deployment(modelo_api)
        if 'temperature' in parametros:
            temp_raw = parametros['temperature']
        elif 'temperatura' in parametros:
            temp_raw = parametros['temperatura']
        else:
            temp_raw = self.config.AZURE_OPENAI_DEFAULT_TEMPERATURE
        temperatura = float(temp_raw)

        return {
            'model': modelo_api,
            'temperature': min(max(temperatura, 0), 2),
            'max_tokens': parametros.get('max_tokens', self.config.AZURE_OPENAI_DEFAULT_MAX_TOKENS),
            'frequency_penalty': min(max(parametros.get('frequency_penalty', 0), -2), 2),
            'presence_penalty': min(max(parametros.get('presence_penalty', 0), -2), 2)
        }
    
    def _fazer_chamada_com_retry(self, 
                                prompt: str, 
                                parametros: Dict[str, Any], 
                                max_retries: int = 3) -> Tuple[str, Dict[str, int]]:
        """Fazer chamada para Azure OpenAI com retry e backoff exponencial"""
        for tentativa in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=parametros['model'],
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=parametros['temperature'],
                    max_tokens=parametros['max_tokens'],
                )
                
                # Extrair informações de tokens
                tokens_info = {
                    'input': response.usage.prompt_tokens if response.usage else 0,
                    'output': response.usage.completion_tokens if response.usage else 0,
                    'total': response.usage.total_tokens if response.usage else 0
                }
                choice0 = response.choices[0]
                texto = texto_mensagem_assistente(choice0.message)
                if not texto:
                    fr = getattr(choice0, "finish_reason", None)
                    print(
                        "Azure OpenAI: corpo assistant vazio após extração. "
                        f"finish_reason={fr!r}, model={parametros.get('model')!r}"
                    )
                return texto, tokens_info
                
            except Exception as e:
                if tentativa < max_retries - 1:
                    # Backoff exponencial: 1s, 2s, 4s
                    wait_time = 2 ** tentativa
                    print(f"Erro na chamada Azure OpenAI: {e}. Tentando novamente em {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Erro da API Azure OpenAI após múltiplas tentativas: {str(e)}")
        
        raise Exception("Falha ao completar chamada Azure OpenAI após múltiplas tentativas")
    
    def _extrair_classificacao(self, resposta: str) -> str:
        """Extrair classificação da resposta (núcleo compartilhado + fallbacks específicos Azure)."""
        tipos = self.config.TIPOS_ACAO
        core = extrair_classificacao_da_resposta_ia(resposta, tipos)
        if not classificacao_extracao_indica_falha_nucleo(core):
            return core
        fb = self._extrair_classificacao_fallback_azure(resposta, tipos)
        return fb if fb is not None else core

    def _extrair_classificacao_fallback_azure(
        self, resposta: str, tipos_validos: List[str]
    ) -> Optional[str]:
        """Regex e heurísticas que existiam só no Azure quando o núcleo não resolve."""
        padroes = [
            r"(?:CLASSIFICAÇÃO|AÇÃO):\s*([A-ZÁÊÇÕ\s]+)",
            r"(?:Classificação|Ação):\s*([A-Záêçõ\s]+)",
            r"\*\*(?:CLASSIFICAÇÃO|AÇÃO)\*\*:\s*([A-ZÁÊÇÕ\s]+)",
            r"\*\*(?:Classificação|Ação)\*\*:\s*([A-Záêçõ\s]+)",
        ]
        for padrao in padroes:
            match = re.search(padrao, resposta, re.IGNORECASE)
            if match:
                classificacao = match.group(1).strip().upper()
                for tipo in tipos_validos:
                    if tipo in classificacao or classificacao in tipo:
                        return tipo
                return classificacao

        linhas = resposta.split("\n")
        for linha in linhas:
            linha = linha.strip()
            if linha and not linha.startswith("**") and len(linha) < 100:
                return linha.upper()
        return None
    
    def get_available_models(self) -> List[str]:
        """Obter lista de modelos (deployments) disponíveis no Azure"""
        return self.config.AZURE_OPENAI_MODELS
    
    # Função estimate_cost removida - simulação de custos desabilitada
    
    def analyze_text(self, 
                    prompt: str, 
                    modelo: str = None, 
                    temperatura: float = 0.1, 
                    max_tokens: int = None) -> str:
        """Método simples para análise de texto genérica"""
        if not self.client:
            raise Exception("Cliente Azure OpenAI não inicializado. Configure as credenciais.")
        
        if max_tokens is None:
            config = self.data_service.get_config()
            max_tokens = config.get('azure_max_tokens')
        
        if modelo is None:
            modelo = self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT
        
        parametros = {
            'modelo': modelo,
            'temperatura': temperatura,
            'max_tokens': max_tokens,
        }
        
        # Validar parâmetros antes de fazer a chamada
        parametros_validados = self._validar_parametros(parametros)
        
        return self._fazer_chamada_com_retry(prompt, parametros_validados)
    
    def get_provider_name(self) -> str:
        """Obter nome do provedor"""
        return "Azure OpenAI"
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Obter parâmetros padrão do Azure OpenAI"""
        return {
            'modelo': self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT,
            'temperatura': self.config.AZURE_OPENAI_DEFAULT_TEMPERATURE,
            'max_tokens': self.config.AZURE_OPENAI_DEFAULT_MAX_TOKENS,
            'frequency_penalty': 0,
            'presence_penalty': 0
        }
    
    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros"""
        return self._validar_parametros(parametros)
