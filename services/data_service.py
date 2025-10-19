import json
import os
import shutil
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import Config

class DataService:
    """Serviço para gerenciar dados em arquivos JSON"""
    
    def __init__(self):
        """Inicializar o serviço de dados"""
        self.config = Config()
        # Locks para evitar condição de corrida ao salvar arquivos
        self._file_locks = {}
        self._locks_lock = threading.Lock()
        self._ensure_data_files_exist()
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Obter lock específico para um arquivo"""
        with self._locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]

    
    def _ensure_data_files_exist(self):
        """Garantir que os arquivos de dados existam"""
        # Criar diretórios se não existirem
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        os.makedirs(self.config.BACKUP_DIR, exist_ok=True)
        
        # Criar arquivos vazios se não existirem
        default_files = {
            self.config.INTIMACOES_FILE: {'intimacoes': []},
            self.config.PROMPTS_FILE: {'prompts': []},
            self.config.ANALISES_FILE: {'analises': []},
            self.config.CONFIG_FILE: {
                'openai_api_key': '',
                'parametros_padrao': {
                    'model': self.config.OPENAI_DEFAULT_MODEL,
                    'temperature': self.config.OPENAI_DEFAULT_TEMPERATURE,
                    'max_tokens': self.config.OPENAI_DEFAULT_MAX_TOKENS,
                    'top_p': self.config.OPENAI_DEFAULT_TOP_P
                }
            }
        }
        
        for file_path, default_content in default_files.items():
            if not os.path.exists(file_path):
                self._save_json(file_path, default_content)
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Carregar dados de um arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """Salvar dados em um arquivo JSON com proteção contra condição de corrida"""
        # Usar lock específico do arquivo para evitar condição de corrida
        with self._get_file_lock(file_path):
            try:
                # Fazer backup se configurado (exceto para config.json)
                if self.config.BACKUP_ON_SAVE and os.path.exists(file_path):
                    # Não fazer backup de arquivos sensíveis
                    if 'config.json' not in file_path:
                        self._create_backup(file_path)
                    else:
                        print("🔒 Proteção: Backup de config.json desabilitado por segurança")

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Erro ao salvar {file_path}: {e}")
                raise
    
    def _create_backup(self, file_path: str):
        """Criar backup de um arquivo"""
        try:
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.config.BACKUP_DIR, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            
            # Limpar backups antigos
            self._cleanup_old_backups(filename)
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
    
    def _cleanup_old_backups(self, filename: str):
        """Limpar backups antigos, mantendo apenas os mais recentes"""
        try:
            backup_files = []
            for f in os.listdir(self.config.BACKUP_DIR):
                if f.endswith(filename):
                    backup_files.append(f)
            
            backup_files.sort(reverse=True)  # Mais recentes primeiro
            
            # Remover backups excedentes
            for old_backup in backup_files[self.config.MAX_BACKUPS:]:
                old_backup_path = os.path.join(self.config.BACKUP_DIR, old_backup)
                os.remove(old_backup_path)
        except Exception as e:
            print(f"Erro ao limpar backups antigos: {e}")
    
    # Métodos para Intimações
    def get_all_intimacoes(self) -> List[Dict[str, Any]]:
        """Obter todas as intimações"""
        print("=== DEBUG: DataService.get_all_intimacoes ===")
        data = self._load_json(self.config.INTIMACOES_FILE)
        intimacoes = data.get('intimacoes', [])
        print(f"Intimações carregadas do arquivo: {len(intimacoes)}")
        for i, intimacao in enumerate(intimacoes):
            print(f"  {i+1}. ID: {intimacao.get('id')} | Contexto: {intimacao.get('contexto')[:30]}...")
        return intimacoes
    
    def get_intimacao_by_id(self, intimacao_id: str) -> Optional[Dict[str, Any]]:
        """Obter intimação por ID"""
        print(f"=== DEBUG: DataService.get_intimacao_by_id ===")
        print(f"ID solicitado: {intimacao_id}")
        
        intimacoes = self.get_all_intimacoes()
        for intimacao in intimacoes:
            if intimacao.get('id') == intimacao_id:
                print(f"Intimação encontrada: {intimacao.get('contexto')[:30]}...")
                print(f"=== DEBUG: Campos da intimação encontrada ===")
                print(f"Campos disponíveis: {list(intimacao.keys())}")
                print(f"Informações adicionais: {intimacao.get('informacoes_adicionais')}")
                print(f"Classificação manual: {intimacao.get('classificacao_manual')}")
                return intimacao
        
        print("Intimação não encontrada")
        return None
    
    def save_intimacao(self, intimacao: Dict[str, Any]):
        """Salvar uma intimação"""
        print("=== DEBUG: DataService.save_intimacao ===")
        print(f"Intimação a salvar: {intimacao}")
        
        data = self._load_json(self.config.INTIMACOES_FILE)
        intimacoes = data.get('intimacoes', [])
        print(f"Intimações existentes: {len(intimacoes)}")
        
        # Verificar se é atualização ou nova intimação
        updated = False
        for i, existing in enumerate(intimacoes):
            if existing.get('id') == intimacao.get('id'):
                print(f"DEBUG: Atualizando intimação existente no índice {i}")
                intimacoes[i] = intimacao
                updated = True
                break
        
        if not updated:
            print("DEBUG: Adicionando nova intimação")
            intimacoes.append(intimacao)
        
        print(f"DEBUG: Total de intimações após operação: {len(intimacoes)}")
        data['intimacoes'] = intimacoes
        self._save_json(self.config.INTIMACOES_FILE, data)
        print("DEBUG: Arquivo salvo com sucesso")
    
    def delete_intimacao(self, intimacao_id: str) -> bool:
        """Deletar uma intimação"""
        data = self._load_json(self.config.INTIMACOES_FILE)
        intimacoes = data.get('intimacoes', [])
        
        original_length = len(intimacoes)
        intimacoes = [i for i in intimacoes if i.get('id') != intimacao_id]
        
        if len(intimacoes) < original_length:
            data['intimacoes'] = intimacoes
            self._save_json(self.config.INTIMACOES_FILE, data)
            return True
        return False
    
    def criar_intimacao(self, intimacao_data: Dict[str, Any]) -> str:
        """Criar uma nova intimação"""
        import uuid
        
        print("=== DEBUG: DataService.criar_intimacao ===")
        print(f"Dados recebidos: {intimacao_data}")
        
        # Gerar ID único se não fornecido
        if 'id' not in intimacao_data:
            intimacao_data['id'] = str(uuid.uuid4())
            print(f"ID gerado: {intimacao_data['id']}")
        else:
            print(f"ID já existente: {intimacao_data['id']}")
        
        # Salvar a intimação
        print("DEBUG: Chamando save_intimacao...")
        self.save_intimacao(intimacao_data)
        print("DEBUG: save_intimacao concluído")
        
        return intimacao_data['id']
    
    # Métodos para Prompts
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Obter todos os prompts"""
        data = self._load_json(self.config.PROMPTS_FILE)
        return data.get('prompts', [])
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Obter prompt por ID"""
        prompts = self.get_all_prompts()
        for prompt in prompts:
            if prompt.get('id') == prompt_id:
                return prompt
        return None
    
    def save_prompt(self, prompt: Dict[str, Any]):
        """Salvar um prompt"""
        data = self._load_json(self.config.PROMPTS_FILE)
        prompts = data.get('prompts', [])
        
        # Verificar se é atualização ou novo prompt
        updated = False
        for i, existing in enumerate(prompts):
            if existing.get('id') == prompt.get('id'):
                prompts[i] = prompt
                updated = True
                break
        
        if not updated:
            prompts.append(prompt)
        
        data['prompts'] = prompts
        self._save_json(self.config.PROMPTS_FILE, data)
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Deletar um prompt"""
        data = self._load_json(self.config.PROMPTS_FILE)
        prompts = data.get('prompts', [])
        
        original_length = len(prompts)
        prompts = [p for p in prompts if p.get('id') != prompt_id]
        
        if len(prompts) < original_length:
            data['prompts'] = prompts
            self._save_json(self.config.PROMPTS_FILE, data)
            return True
        return False
    
    def criar_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Criar um novo prompt"""
        import uuid
        
        # Gerar ID único se não fornecido
        if 'id' not in prompt_data:
            prompt_data['id'] = str(uuid.uuid4())
        
        # Salvar o prompt
        self.save_prompt(prompt_data)
        
        return prompt_data['id']
    
    # Métodos para Análises
    def get_all_analises(self) -> List[Dict[str, Any]]:
        """Obter todas as análises"""
        data = self._load_json(self.config.ANALISES_FILE)
        return data.get('analises', [])
    
    def get_analise_by_id(self, analise_id: str) -> Optional[Dict[str, Any]]:
        """Obter análise por ID"""
        analises = self.get_all_analises()
        for analise in analises:
            if analise.get('id') == analise_id:
                return analise
        return None
    
    def get_analises_by_intimacao_id(self, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter análises por ID da intimação"""
        analises = self.get_all_analises()
        return [a for a in analises if a.get('intimacao_id') == intimacao_id]
    
    def get_analises_by_prompt_id(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter análises por ID do prompt"""
        analises = self.get_all_analises()
        return [a for a in analises if a.get('prompt_id') == prompt_id]
    
    def save_analise(self, analise: Dict[str, Any]):
        """Salvar uma análise"""
        data = self._load_json(self.config.ANALISES_FILE)
        analises = data.get('analises', [])
        
        # Verificar se é atualização ou nova análise
        updated = False
        for i, existing in enumerate(analises):
            if existing.get('id') == analise.get('id'):
                analises[i] = analise
                updated = True
                break
        
        if not updated:
            analises.append(analise)
        
        data['analises'] = analises
        self._save_json(self.config.ANALISES_FILE, data)
    
    def delete_analise(self, analise_id: str) -> bool:
        """Deletar uma análise"""
        data = self._load_json(self.config.ANALISES_FILE)
        analises = data.get('analises', [])
        
        original_length = len(analises)
        analises = [a for a in analises if a.get('id') != analise_id]
        
        if len(analises) < original_length:
            data['analises'] = analises
            self._save_json(self.config.ANALISES_FILE, data)
            return True
        return False
    
    def adicionar_analise_intimacao(self, intimacao_id: str, analise_data: Dict[str, Any]):
        """Adicionar análise a uma intimação"""
        intimacao = self.get_intimacao_by_id(intimacao_id)
        if intimacao:
            if 'analises' not in intimacao:
                intimacao['analises'] = []
            
            # Adicionar ID único à análise se não existir
            if 'id' not in analise_data:
                import uuid
                analise_data['id'] = str(uuid.uuid4())
            
            intimacao['analises'].append(analise_data)
            self.save_intimacao(intimacao)
    
    def adicionar_uso_prompt(self, prompt_id: str, uso_data: Dict[str, Any]):
        """Adicionar uso a um prompt"""
        prompt = self.get_prompt_by_id(prompt_id)
        if prompt:
            if 'historico_uso' not in prompt:
                prompt['historico_uso'] = []
            
            # Adicionar ID único ao uso se não existir
            if 'id' not in uso_data:
                import uuid
                uso_data['id'] = str(uuid.uuid4())
            
            prompt['historico_uso'].append(uso_data)
            
            # Atualizar estatísticas do prompt
            total_usos = len(prompt['historico_uso'])
            acertos = sum(1 for uso in prompt['historico_uso'] if uso.get('acuracia') == 1)
            tempo_total = sum(uso.get('tempo_processamento', 0) for uso in prompt['historico_uso'])
            custo_total = 0.0  # Cálculo de custo removido - simulação desabilitada
            
            prompt['total_usos'] = total_usos
            prompt['acuracia_media'] = (acertos / total_usos * 100) if total_usos > 0 else 0
            prompt['tempo_medio'] = (tempo_total / total_usos) if total_usos > 0 else 0
            prompt['custo_total'] = custo_total
            
            self.save_prompt(prompt)
    
    # Métodos para Configurações
    def get_config(self) -> Dict[str, Any]:
        """Obter configurações do sistema"""
        print(f"=== DEBUG: get_config chamada ===")
        config = self._load_json(self.config.CONFIG_FILE)
        print(f"=== DEBUG: config carregado: {config} ===")
        
        # Substituir variáveis de ambiente
        if config and 'openai_api_key' in config:
            api_key = config['openai_api_key']
            if api_key.startswith('${') and api_key.endswith('}'):
                # Extrair nome da variável de ambiente
                env_var = api_key[2:-1]  # Remove ${ e }
                config['openai_api_key'] = os.environ.get(env_var, '')
        
        return config
    
    def save_config(self, config: Dict[str, Any]):
        """Salvar configurações"""
        # Proteger contra salvamento da chave da API
        if 'openai_api_key' in config:
            api_key = config['openai_api_key']
            # Se for uma chave real (começa com sk-), não salvar
            if api_key.startswith('sk-'):
                print("AVISO:  AVISO: Tentativa de salvar chave da API no arquivo de configuração bloqueada!")
                # Manter apenas o placeholder
                config['openai_api_key'] = '${OPENAI_API_KEY}'
            # Se não for placeholder, não salvar
            elif not (api_key.startswith('${') and api_key.endswith('}')):
                print("AVISO:  AVISO: Tentativa de salvar valor inválido para chave da API bloqueada!")
                # Manter apenas o placeholder
                config['openai_api_key'] = '${OPENAI_API_KEY}'
        
        self._save_json(self.config.CONFIG_FILE, config)
    
    # Métodos de estatísticas
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas gerais"""
        intimacoes = self.get_all_intimacoes()
        analises = self.get_all_analises()
        prompts = self.get_all_prompts()
        
        total_intimacoes = len(intimacoes)
        total_analises = len(analises)
        total_prompts = len(prompts)
        
        # Calcular acurácia geral
        acertos = sum(1 for a in analises if a.get('acertou', False))
        taxa_acuracia = (acertos / total_analises * 100) if total_analises > 0 else 0
        
        # Distribuição por classificação
        distribuicao_classificacao = {}
        for intimacao in intimacoes:
            classificacao = intimacao.get('classificacao_manual', 'Não classificado')
            distribuicao_classificacao[classificacao] = distribuicao_classificacao.get(classificacao, 0) + 1
        
        # Estatísticas por prompt
        stats_por_prompt = {}
        for analise in analises:
            prompt_id = analise.get('prompt_id')
            if prompt_id not in stats_por_prompt:
                stats_por_prompt[prompt_id] = {
                    'total': 0,
                    'acertos': 0,
                    'taxa_acuracia': 0
                }
            
            stats_por_prompt[prompt_id]['total'] += 1
            if analise.get('acertou', False):
                stats_por_prompt[prompt_id]['acertos'] += 1
        
        # Calcular taxa de acurácia por prompt
        for prompt_id in stats_por_prompt:
            total = stats_por_prompt[prompt_id]['total']
            acertos = stats_por_prompt[prompt_id]['acertos']
            stats_por_prompt[prompt_id]['taxa_acuracia'] = (acertos / total * 100) if total > 0 else 0
        
        return {
            'total_intimacoes': total_intimacoes,
            'total_analises': total_analises,
            'total_prompts': total_prompts,
            'taxa_acuracia_geral': round(taxa_acuracia, 2),
            'distribuicao_classificacao': distribuicao_classificacao,
            'stats_por_prompt': stats_por_prompt
        }
    
    def calculate_real_cost(self, tokens_input: int, tokens_output: int, model: str, provider: str = None) -> float:
        """Calcular custo real baseado nos tokens de entrada e saída usando preços configurados"""
        try:
            config = self.get_config() or {}
            
            # Determinar o provedor se não especificado
            if not provider:
                provider = config.get('ai_provider', 'openai')
            
            # Obter preços configurados
            if provider.lower() == 'azure':
                precos = config.get('precos_azure', self.config.PRECOS_AZURE_PADRAO)
            else:
                precos = config.get('precos_openai', self.config.PRECOS_OPENAI_PADRAO)
            
            # Mapear nomes de modelos para chaves de preços (formato aninhado)
            model_mapping = {
                # OpenAI/Azure GPT-4o
                'gpt-4o': 'gpt-4o',
                'gpt4o': 'gpt-4o',
                
                # OpenAI/Azure GPT-4o-mini
                'gpt-4o-mini': 'gpt-4o-mini',
                'gpt4o-mini': 'gpt-4o-mini',
                
                # OpenAI/Azure GPT-4-turbo
                'gpt-4-turbo': 'gpt-4-turbo',
                'gpt4-turbo': 'gpt-4-turbo',
                'gpt-4-turbo-preview': 'gpt-4-turbo',
                
                # OpenAI/Azure GPT-3.5-turbo
                'gpt-3.5-turbo': 'gpt-3.5-turbo',
                'gpt35-turbo': 'gpt-3.5-turbo',
                'gpt-35-turbo': 'gpt-3.5-turbo',  # Azure naming
                
                # GPT-4 (usar preços do GPT-4-turbo como fallback)
                'gpt-4': 'gpt-4-turbo'
            }
            
            # Encontrar a chave de preço para o modelo
            model_key = model_mapping.get(model.lower(), 'gpt-4o')  # Default para gpt-4o
            
            # Obter preços do modelo (estrutura aninhada)
            input_price = 0
            output_price = 0
            
            if model_key in precos and isinstance(precos[model_key], dict):
                model_prices = precos[model_key]
                input_price = model_prices.get('input', 0)
                output_price = model_prices.get('output', 0)
            
            # Se não encontrou preços configurados, usar preços padrão
            if input_price == 0 and output_price == 0:
                # Usar preços padrão do Config
                if provider.lower() == 'azure':
                    default_precos = self.config.PRECOS_AZURE_PADRAO
                else:
                    default_precos = self.config.PRECOS_OPENAI_PADRAO
                
                if model_key in default_precos and isinstance(default_precos[model_key], dict):
                    model_prices = default_precos[model_key]
                    input_price = model_prices.get('input', 0)
                    output_price = model_prices.get('output', 0)
            
            # Calcular custo (preços são por 1M tokens, converter para por token)
            input_cost = (tokens_input / 1_000_000) * input_price
            output_cost = (tokens_output / 1_000_000) * output_price
            
            total_cost = input_cost + output_cost
            
            return round(total_cost, 6)  # Arredondar para 6 casas decimais
            
        except Exception as e:
            print(f"AVISO:  Erro ao calcular custo real: {e}")
            return 0.0

    def get_taxa_acerto_por_prompt_especifico(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter taxa de acerto de um prompt específico para todas as intimações"""
        try:
            # Buscar todas as análises do prompt específico
            analises = self.get_analises_by_prompt_id(prompt_id)
            
            # Agrupar por intimação
            intimacoes_stats = {}
            
            for analise in analises:
                intimacao_id = analise.get('intimacao_id')
                if not intimacao_id:
                    continue
                    
                if intimacao_id not in intimacoes_stats:
                    intimacoes_stats[intimacao_id] = {
                        'intimacao_id': intimacao_id,
                        'total_analises': 0,
                        'acertos': 0,
                        'taxa_acerto': 0.0
                    }
                
                intimacoes_stats[intimacao_id]['total_analises'] += 1
                if analise.get('acertou', False):
                    intimacoes_stats[intimacao_id]['acertos'] += 1
            
            # Calcular taxa de acerto para cada intimação
            for intimacao_id in intimacoes_stats:
                stats = intimacoes_stats[intimacao_id]
                if stats['total_analises'] > 0:
                    stats['taxa_acerto'] = round((stats['acertos'] / stats['total_analises']) * 100, 1)
            
            return list(intimacoes_stats.values())
            
        except Exception as e:
            print(f"Erro ao obter taxa de acerto por prompt específico: {e}")
            return []
    
    def get_taxa_acerto_por_prompt_e_temperatura(self, prompt_id: str, temperatura: float) -> List[Dict[str, Any]]:
        """Obter taxa de acerto de um prompt específico com temperatura específica"""
        try:
            # Buscar todas as análises do prompt específico com temperatura específica
            analises = self.get_analises_by_prompt_id(prompt_id)
            
            # Filtrar apenas análises com a temperatura específica
            analises_filtradas = [a for a in analises if a.get('temperatura') == temperatura]
            
            # Agrupar por intimação
            intimacoes_stats = {}
            
            for analise in analises_filtradas:
                intimacao_id = analise.get('intimacao_id')
                if not intimacao_id:
                    continue
                
                if intimacao_id not in intimacoes_stats:
                    intimacoes_stats[intimacao_id] = {
                        'intimacao_id': intimacao_id,
                        'total_analises': 0,
                        'acertos': 0,
                        'taxa_acerto': 0
                    }
                
                intimacoes_stats[intimacao_id]['total_analises'] += 1
                if analise.get('acertou'):
                    intimacoes_stats[intimacao_id]['acertos'] += 1
            
            # Calcular taxa de acerto
            for intimacao_id in intimacoes_stats:
                stats = intimacoes_stats[intimacao_id]
                if stats['total_analises'] > 0:
                    stats['taxa_acerto'] = round((stats['acertos'] / stats['total_analises']) * 100, 1)
            
            return list(intimacoes_stats.values())
            
        except Exception as e:
            print(f"Erro ao obter taxa de acerto por prompt e temperatura: {e}")
            return []

    def get_prompts_acerto_por_intimacao(self, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter prompts e taxas de acerto de uma intimação específica"""
        return sqlite_service.get_prompts_acerto_por_intimacao(intimacao_id)

    def get_dados_analise_intimacao_prompt(self, intimacao_id: str, prompt_id: str) -> Dict[str, Any]:
        """Obter dados completos de uma análise específica (intimação + prompt)"""
        return sqlite_service.get_dados_analise_intimacao_prompt(intimacao_id, prompt_id)