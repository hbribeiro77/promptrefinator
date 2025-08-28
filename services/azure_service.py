import time
import re
from typing import Tuple, Dict, Any, Optional, List
from openai import AzureOpenAI
from config import Config
from services.sqlite_service import SQLiteService
from services.ai_service_interface import AIServiceInterface

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
                print("✅ Cliente Azure OpenAI inicializado com sucesso")
                return True
            else:
                print("⚠️  Aviso: Credenciais do Azure OpenAI não configuradas.")
                print("   Configure as credenciais através da interface de configurações.")
                self.client = None
                # Retornar True para permitir seleção do provedor mesmo sem credenciais
                return True
        except Exception as e:
            print(f"❌ Erro ao inicializar cliente Azure OpenAI: {e}")
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
            print("✅ Credenciais do Azure OpenAI atualizadas com sucesso")
        except Exception as e:
            print(f"❌ Erro ao atualizar credenciais do Azure OpenAI: {e}")
            self.client = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Testar conexão com a API do Azure OpenAI"""
        if not self.client:
            return False, "Cliente Azure OpenAI não inicializado. Verifique as credenciais."
        
        try:
            # Fazer uma chamada simples para testar a conexão
            response = self.client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT,
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
            # Construir o prompt
            prompt = self._construir_prompt(prompt_template, contexto)
            
            # Validar parâmetros
            parametros_validados = self._validar_parametros(parametros)
            
            # Fazer chamada com retry
            resposta_completa, tokens_info = self._fazer_chamada_com_retry(prompt, parametros_validados)
            
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
        """Validar e ajustar parâmetros para Azure OpenAI"""
        return {
            'model': parametros.get('modelo', self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT),
            'temperature': min(max(parametros.get('temperatura', self.config.AZURE_OPENAI_DEFAULT_TEMPERATURE), 0), 2),
            'max_tokens': min(parametros.get('max_tokens', self.config.AZURE_OPENAI_DEFAULT_MAX_TOKENS), 4000),
            'top_p': min(max(parametros.get('top_p', self.config.AZURE_OPENAI_DEFAULT_TOP_P), 0), 1),
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
                
                # Extrair informações de tokens
                tokens_info = {
                    'input': response.usage.prompt_tokens if response.usage else 0,
                    'output': response.usage.completion_tokens if response.usage else 0,
                    'total': response.usage.total_tokens if response.usage else 0
                }
                
                return response.choices[0].message.content.strip(), tokens_info
                
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
        """Extrair classificação da resposta"""
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
                tipos_validos = [
                    'RENUNCIAR PRAZO', 'OCULTAR', 'ELABORAR PEÇA', 
                    'CONTATAR ASSISTIDO', 'ANALISAR PROCESSO', 
                    'ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR', 'URGÊNCIA'
                ]
                for tipo in tipos_validos:
                    if tipo.upper() == triagem_ia:
                        return tipo
        except json.JSONDecodeError:
            pass
        
        # Se não conseguiu extrair do JSON, tentar busca direta
        tipos_validos = [
            'RENUNCIAR PRAZO', 'OCULTAR', 'ELABORAR PEÇA', 
            'CONTATAR ASSISTIDO', 'ANALISAR PROCESSO', 
            'ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR', 'URGÊNCIA'
        ]
        
        for tipo_acao in tipos_validos:
            if tipo_acao.upper() in resposta_limpa:
                return tipo_acao
        
        # Tentar correspondência com variações
        for variacao, classificacao_padrao in mapeamento_variacoes.items():
            if variacao in resposta_limpa:
                return classificacao_padrao
        
        # Se não encontrou uma classificação exata, tentar correspondência parcial
        for tipo_acao in tipos_validos:
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
                for tipo_acao in tipos_validos:
                    if tipo_acao.upper() == possivel_classificacao:
                        return tipo_acao
        
        # Padrões para extrair classificação (fallback)
        padroes = [
            r'(?:CLASSIFICAÇÃO|AÇÃO):\s*([A-ZÁÊÇÕ\s]+)',
            r'(?:Classificação|Ação):\s*([A-Záêçõ\s]+)',
            r'\*\*(?:CLASSIFICAÇÃO|AÇÃO)\*\*:\s*([A-ZÁÊÇÕ\s]+)',
            r'\*\*(?:Classificação|Ação)\*\*:\s*([A-Záêçõ\s]+)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, resposta, re.IGNORECASE)
            if match:
                classificacao = match.group(1).strip().upper()
                # Validar se é uma classificação conhecida
                for tipo in tipos_validos:
                    if tipo in classificacao or classificacao in tipo:
                        return tipo
                
                return classificacao
        
        # Se não encontrar padrão, tentar extrair da primeira linha
        linhas = resposta.split('\n')
        for linha in linhas:
            linha = linha.strip()
            if linha and not linha.startswith('**') and len(linha) < 100:
                return linha.upper()
        
        # Se ainda não encontrou, retornar a resposta original com indicação de erro
        return f"ERRO: Classificação não reconhecida - {resposta[:100]}"
    
    def get_available_models(self) -> List[str]:
        """Obter lista de modelos (deployments) disponíveis no Azure"""
        return self.config.AZURE_OPENAI_MODELS
    
    # Função estimate_cost removida - simulação de custos desabilitada
    
    def analyze_text(self, 
                    prompt: str, 
                    modelo: str = None, 
                    temperatura: float = 0.1, 
                    max_tokens: int = 500) -> str:
        """Método simples para análise de texto genérica"""
        if not self.client:
            raise Exception("Cliente Azure OpenAI não inicializado. Configure as credenciais.")
        
        if modelo is None:
            modelo = self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT
        
        parametros = {
            'model': modelo,
            'temperature': temperatura,
            'max_tokens': max_tokens,
            'top_p': 1.0
        }
        
        return self._fazer_chamada_com_retry(prompt, parametros)
    
    def get_provider_name(self) -> str:
        """Obter nome do provedor"""
        return "Azure OpenAI"
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Obter parâmetros padrão do Azure OpenAI"""
        return {
            'modelo': self.config.AZURE_OPENAI_DEFAULT_DEPLOYMENT,
            'temperatura': self.config.AZURE_OPENAI_DEFAULT_TEMPERATURE,
            'max_tokens': self.config.AZURE_OPENAI_DEFAULT_MAX_TOKENS,
            'top_p': self.config.AZURE_OPENAI_DEFAULT_TOP_P,
            'frequency_penalty': 0,
            'presence_penalty': 0
        }
    
    def validate_parameters(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e ajustar parâmetros"""
        return self._validar_parametros(parametros)