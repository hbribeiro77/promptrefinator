"""
Serviço dedicado para cálculo e exibição de custos de IA
Isola toda a lógica de custos para evitar quebras em outras funcionalidades
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class CostCalculationService:
    """Serviço para cálculo e exibição de custos de IA"""
    
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = config_path
        self._precos_cache = None
        self._last_config_check = None
    
    def _load_config(self) -> Dict:
        """Carrega configurações do arquivo config.json"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar config.json: {e}")
            return {}
    
    def _get_precos_modelos(self) -> Dict:
        """Obtém preços dos modelos com cache"""
        config = self._load_config()
        
        # Verificar se o cache ainda é válido
        if self._precos_cache and self._last_config_check:
            try:
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime <= self._last_config_check:
                    return self._precos_cache
            except OSError:
                pass
        
        # Carregar preços do Azure
        precos_azure = config.get('precos_azure', {})
        if not precos_azure:
            # Preços padrão do Azure se não configurados
            precos_azure = {
                "gpt-4o": {"input": 2.5, "output": 10.0},
                "gpt-4o-mini": {"input": 0.15, "output": 0.6},
                "gpt-4": {"input": 30.0, "output": 60.0},
                "gpt-4-turbo": {"input": 10.0, "output": 30.0},
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
            }
        
        # Carregar preços do OpenAI
        precos_openai = config.get('precos_openai', {})
        if not precos_openai:
            # Preços padrão do OpenAI se não configurados
            precos_openai = {
                "gpt-4o": {"input": 2.5, "output": 10.0},
                "gpt-4o-mini": {"input": 0.15, "output": 0.6},
                "gpt-4": {"input": 30.0, "output": 60.0},
                "gpt-4-turbo": {"input": 10.0, "output": 30.0},
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
            }
        
        precos = {
            'azure': precos_azure,
            'openai': precos_openai
        }
        
        # Atualizar cache
        self._precos_cache = precos
        self._last_config_check = datetime.now().timestamp()
        
        return precos
    
    def calculate_real_cost(self, 
                          tokens_input: int, 
                          tokens_output: int, 
                          modelo: str, 
                          provider: str) -> float:
        """
        Calcula o custo real baseado em tokens e preços configurados
        
        Args:
            tokens_input: Número de tokens de entrada
            tokens_output: Número de tokens de saída
            modelo: Nome do modelo usado
            provider: Provedor (azure ou openai)
        
        Returns:
            Custo total calculado
        """
        try:
            precos = self._get_precos_modelos()
            
            # Obter preços do provedor
            provider_precos = precos.get(provider.lower(), {})
            if not provider_precos:
                print(f"Provedor '{provider}' não encontrado nos preços")
                return 0.0
            
            # Obter preços do modelo
            modelo_precos = provider_precos.get(modelo, {})
            if not modelo_precos:
                print(f"Modelo '{modelo}' não encontrado nos preços do {provider}")
                return 0.0
            
            preco_input = modelo_precos.get('input', 0)
            preco_output = modelo_precos.get('output', 0)
            
            # Calcular custos (preços são por 1M tokens)
            custo_input = (tokens_input / 1000000) * preco_input
            custo_output = (tokens_output / 1000000) * preco_output
            
            # Total
            custo_total = custo_input + custo_output
            
            return round(custo_total, 6)
            
        except Exception as e:
            print(f"Erro ao calcular custo: {e}")
            return 0.0
    
    def get_model_prices(self, modelo: str, provider: str) -> Dict[str, float]:
        """
        Obtém preços de um modelo específico
        
        Args:
            modelo: Nome do modelo
            provider: Provedor (azure ou openai)
        
        Returns:
            Dicionário com preços de input e output
        """
        try:
            precos = self._get_precos_modelos()
            provider_precos = precos.get(provider.lower(), {})
            modelo_precos = provider_precos.get(modelo, {})
            
            return {
                'input': modelo_precos.get('input', 0),
                'output': modelo_precos.get('output', 0)
            }
        except Exception as e:
            print(f"Erro ao obter preços do modelo: {e}")
            return {'input': 0, 'output': 0}
    
    def generate_cost_tooltip(self, 
                            tokens_input: int, 
                            tokens_output: int, 
                            modelo: str, 
                            provider: str,
                            custo_real: float) -> str:
        """
        Gera tooltip com memória de cálculo de custos
        
        Args:
            tokens_input: Tokens de entrada
            tokens_output: Tokens de saída
            modelo: Nome do modelo
            provider: Provedor
            custo_real: Custo real calculado
        
        Returns:
            HTML do tooltip
        """
        try:
            precos = self.get_model_prices(modelo, provider)
            
            # Calcular custos individuais
            custo_input = (tokens_input / 1000000) * precos['input']
            custo_output = (tokens_output / 1000000) * precos['output']
            
            # Calcular total somando os custos individuais
            total_calculado = custo_input + custo_output
            
            tooltip = f"""<strong>Memória de Cálculo:</strong><br>
                        Provider: {provider}<br>
                        Modelo: {modelo}<br>
                        Tokens Input: {tokens_input:,}<br>
                        Tokens Output: {tokens_output:,}<br>
                        <hr style='margin: 4px 0;'>
                        Preço Input: ${precos['input']:.3f}/1M tokens<br>
                        Preço Output: ${precos['output']:.3f}/1M tokens<br>
                        <hr style='margin: 4px 0;'>
                        Custo Input: ${custo_input:.6f}<br>
                        Custo Output: ${custo_output:.6f}<br>
                        <strong>Total: ${total_calculado:.6f}</strong>"""
            
            return tooltip
            
        except Exception as e:
            print(f"Erro ao gerar tooltip: {e}")
            return f"<strong>Erro ao calcular custo:</strong> {str(e)}"
    
    def calculate_total_cost(self, resultados: List[Dict]) -> float:
        """
        Calcula custo total de uma lista de resultados
        
        Args:
            resultados: Lista de resultados de análise
        
        Returns:
            Custo total
        """
        try:
            total = 0.0
            for resultado in resultados:
                if 'erro' not in resultado:
                    custo = resultado.get('custo_real', 0)
                    total += custo
            return round(total, 6)
        except Exception as e:
            print(f"Erro ao calcular custo total: {e}")
            return 0.0
    
    def format_cost_display(self, custo: float, casas_decimais: int = 6) -> str:
        """
        Formata custo para exibição
        
        Args:
            custo: Valor do custo
            casas_decimais: Número de casas decimais
        
        Returns:
            String formatada
        """
        try:
            if custo > 0:
                return f"${custo:.{casas_decimais}f}"
            else:
                return f"$0.{'0' * casas_decimais}"
        except Exception as e:
            print(f"Erro ao formatar custo: {e}")
            return "$0.000000"

# Instância global do serviço
cost_service = CostCalculationService()
