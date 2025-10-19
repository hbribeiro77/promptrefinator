import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

class SQLiteService:
    """Serviço para gerenciar dados em SQLite"""
    
    def __init__(self, db_path: str = None):
        """Inicializar o serviço SQLite"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'database.db')
        
        self.db_path = db_path
        self._ensure_database_exists()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões SQLite"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_database_exists(self):
        """Garantir que o banco de dados e tabelas existam"""
        with self.get_connection() as conn:
            # Criar tabela de prompts
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    regra_negocio TEXT,
                    conteudo TEXT NOT NULL,
                    categoria TEXT,
                    tags TEXT, -- JSON array
                    ativo BOOLEAN DEFAULT 1,
                    data_criacao TEXT NOT NULL,
                    total_usos INTEGER DEFAULT 0,
                    acuracia_media REAL DEFAULT 0.0,
                    tempo_medio REAL DEFAULT 0.0,
                    custo_total REAL DEFAULT 0.0
                )
            ''')
            
            # Criar tabela de intimações
            conn.execute('''
                CREATE TABLE IF NOT EXISTS intimacoes (
                    id TEXT PRIMARY KEY,
                    contexto TEXT NOT NULL,
                    classificacao_manual TEXT NOT NULL,
                    informacao_adicional TEXT,
                    processo TEXT,
                    orgao_julgador TEXT,
                    classe TEXT,
                    disponibilizacao TEXT,
                    intimado TEXT,
                    status TEXT,
                    prazo TEXT,
                    defensor TEXT,
                    id_tarefa TEXT,
                    cor_etiqueta TEXT,
                    data_criacao TEXT NOT NULL
                )
            ''')
            
            # Criar tabela de análises
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analises (
                    id TEXT PRIMARY KEY,
                    intimacao_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_nome TEXT,
                    data_analise TEXT NOT NULL,
                    resultado_ia TEXT,
                    acertou BOOLEAN,
                    tempo_processamento REAL,
                    modelo TEXT,
                    temperatura REAL,
                    tokens_usados INTEGER,
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    custo_real REAL,
                    prompt_completo TEXT,
                    resposta_completa TEXT,
                    FOREIGN KEY (intimacao_id) REFERENCES intimacoes (id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            ''')
            
            # Criar tabela de histórico de acurácia
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historico_acuracia (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    numero_intimacoes INTEGER NOT NULL,
                    temperatura REAL NOT NULL,
                    acuracia REAL NOT NULL,
                    data_analise TEXT NOT NULL,
                    session_id TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            ''')
            
            # Criar índices para performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_intimacao ON analises(intimacao_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_prompt ON analises(prompt_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_historico_acuracia_prompt ON historico_acuracia(prompt_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_historico_acuracia_condicoes ON historico_acuracia(prompt_id, numero_intimacoes, temperatura)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_data ON analises(data_analise)')
            
            conn.commit()
    
    # Métodos para Prompts
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Obter todos os prompts"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM prompts ORDER BY data_criacao DESC')
            prompts = []
            for row in cursor.fetchall():
                prompt = dict(row)
                # Converter tags de JSON string para lista
                if prompt['tags']:
                    try:
                        prompt['tags'] = json.loads(prompt['tags'])
                    except:
                        prompt['tags'] = []
                else:
                    prompt['tags'] = []
                prompts.append(prompt)
            return prompts
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Obter prompt por ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
            row = cursor.fetchone()
            if row:
                prompt = dict(row)
                # Converter tags de JSON string para lista
                if prompt['tags']:
                    try:
                        prompt['tags'] = json.loads(prompt['tags'])
                    except:
                        prompt['tags'] = []
                else:
                    prompt['tags'] = []
                return prompt
            return None
    
    def save_prompt(self, prompt: Dict[str, Any]) -> str:
        """Salvar um prompt"""
        with self.get_connection() as conn:
            # Gerar ID se não existir
            if 'id' not in prompt or not prompt['id']:
                prompt['id'] = str(uuid.uuid4())
            
            # Converter tags para JSON string
            tags_json = json.dumps(prompt.get('tags', []))
            
            # Data de criação
            if 'data_criacao' not in prompt:
                prompt['data_criacao'] = datetime.now().isoformat()
            
            # Inserir ou atualizar
            conn.execute('''
                INSERT OR REPLACE INTO prompts 
                (id, nome, descricao, regra_negocio, conteudo, categoria, tags, ativo, data_criacao, 
                 total_usos, acuracia_media, tempo_medio, custo_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prompt['id'],
                prompt.get('nome', ''),
                prompt.get('descricao', ''),
                prompt.get('regra_negocio', ''),
                prompt.get('conteudo', ''),
                prompt.get('categoria', ''),
                tags_json,
                prompt.get('ativo', True),
                prompt['data_criacao'],
                prompt.get('total_usos', 0),
                prompt.get('acuracia_media', 0.0),
                prompt.get('tempo_medio', 0.0),
                prompt.get('custo_total', 0.0)
            ))
            conn.commit()
            return prompt['id']
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Deletar um prompt"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def toggle_prompt_ativo(self, prompt_id: str) -> bool:
        """Alternar status ativo/inativo de um prompt"""
        with self.get_connection() as conn:
            # Obter status atual
            cursor = conn.execute('SELECT ativo FROM prompts WHERE id = ?', (prompt_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            # Inverter status
            novo_status = not bool(row[0])
            cursor.execute('UPDATE prompts SET ativo = ? WHERE id = ?', (novo_status, prompt_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_prompts_ativos(self) -> List[Dict[str, Any]]:
        """Obter apenas prompts ativos"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM prompts WHERE ativo = 1 ORDER BY data_criacao DESC')
            prompts = []
            for row in cursor.fetchall():
                prompt = dict(row)
                # Converter tags de JSON string para lista
                if prompt['tags']:
                    try:
                        prompt['tags'] = json.loads(prompt['tags'])
                    except:
                        prompt['tags'] = []
                else:
                    prompt['tags'] = []
                prompts.append(prompt)
            return prompts
    
    def criar_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Criar um novo prompt (compatibilidade com DataService)"""
        return self.save_prompt(prompt_data)
    
    # Métodos para Intimações
    def get_all_intimacoes(self) -> List[Dict[str, Any]]:
        """Obter todas as intimações com suas análises"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM intimacoes ORDER BY data_criacao DESC')
            intimacoes = []
            for row in cursor.fetchall():
                intimacao = dict(row)
                # Converter destacada de int para boolean
                if 'destacada' in intimacao:
                    intimacao['destacada'] = bool(intimacao['destacada'])
                # Buscar análises desta intimação
                intimacao['analises'] = self.get_analises_by_intimacao(intimacao['id'])
                intimacoes.append(intimacao)
            return intimacoes
    
    def get_intimacao_by_id(self, intimacao_id: str) -> Optional[Dict[str, Any]]:
        """Obter intimação por ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM intimacoes WHERE id = ?', (intimacao_id,))
            row = cursor.fetchone()
            if row:
                intimacao = dict(row)
                # Converter destacada de int para boolean
                if 'destacada' in intimacao:
                    intimacao['destacada'] = bool(intimacao['destacada'])
                # Buscar análises desta intimação
                intimacao['analises'] = self.get_analises_by_intimacao(intimacao_id)
                return intimacao
            return None
    
    def save_intimacao(self, intimacao: Dict[str, Any]) -> str:
        """Salvar uma intimação"""
        with self.get_connection() as conn:
            # Gerar ID se não existir
            if 'id' not in intimacao or not intimacao['id']:
                intimacao['id'] = str(uuid.uuid4())
            
            # Data de criação
            if 'data_criacao' not in intimacao:
                intimacao['data_criacao'] = datetime.now().isoformat()
            
            # Inserir ou atualizar intimação (SEM salvar análises aninhadas)
            conn.execute('''
                INSERT OR REPLACE INTO intimacoes 
                (id, contexto, classificacao_manual, informacao_adicional, processo,
                 orgao_julgador, classe, disponibilizacao, intimado, status, prazo,
                 defensor, id_tarefa, cor_etiqueta, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                intimacao['id'],
                intimacao.get('contexto', ''),
                intimacao.get('classificacao_manual', ''),
                intimacao.get('informacoes_adicionais', intimacao.get('informacao_adicional', '')),
                intimacao.get('processo', ''),
                intimacao.get('orgao_julgador', ''),
                intimacao.get('classe', ''),
                intimacao.get('disponibilizacao', ''),
                intimacao.get('intimado', ''),
                intimacao.get('status', ''),
                intimacao.get('prazo', ''),
                intimacao.get('defensor', ''),
                intimacao.get('id_tarefa', ''),
                intimacao.get('cor_etiqueta', ''),
                intimacao['data_criacao']
            ))
            
            # NÃO salvar análises aninhadas aqui - elas são salvas separadamente via adicionar_analise_intimacao()
            
            conn.commit()
            return intimacao['id']
    
    def criar_intimacao(self, intimacao_data: Dict[str, Any]) -> str:
        """Criar uma nova intimação (compatibilidade com DataService)"""
        return self.save_intimacao(intimacao_data)
    
    def delete_intimacao(self, intimacao_id: str) -> bool:
        """Deletar uma intimação e suas análises"""
        with self.get_connection() as conn:
            # Deletar análises primeiro
            conn.execute('DELETE FROM analises WHERE intimacao_id = ?', (intimacao_id,))
            # Deletar intimação
            cursor = conn.execute('DELETE FROM intimacoes WHERE id = ?', (intimacao_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Métodos para Análises
    def get_all_analises(self) -> List[Dict[str, Any]]:
        """Obter todas as análises"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT a.*, i.contexto, i.classificacao_manual, p.regra_negocio, p.nome as prompt_nome
                FROM analises a 
                LEFT JOIN intimacoes i ON a.intimacao_id = i.id 
                LEFT JOIN prompts p ON a.prompt_id = p.id
                ORDER BY a.data_analise DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_analises_by_intimacao(self, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter análises de uma intimação"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT a.*, p.regra_negocio, p.nome as prompt_nome
                FROM analises a 
                LEFT JOIN prompts p ON a.prompt_id = p.id
                WHERE a.intimacao_id = ? 
                ORDER BY a.data_analise DESC
            ''', (intimacao_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_analises_by_intimacao_id(self, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter análises de uma intimação (compatibilidade com DataService)"""
        return self.get_analises_by_intimacao(intimacao_id)
    
    def get_analises_by_prompt(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter análises de um prompt"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT a.*, p.regra_negocio, p.nome as prompt_nome
                FROM analises a 
                LEFT JOIN prompts p ON a.prompt_id = p.id
                WHERE a.prompt_id = ? 
                ORDER BY a.data_analise DESC
            ''', (prompt_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_analise(self, analise: Dict[str, Any]) -> str:
        """Salvar uma análise"""
        with self.get_connection() as conn:
            # Gerar ID se não existir
            if 'id' not in analise or not analise['id']:
                analise['id'] = str(uuid.uuid4())
            
            # Data de análise
            if 'data_analise' not in analise:
                analise['data_analise'] = datetime.now().isoformat()
            
            # Inserir ou atualizar
            conn.execute('''
                INSERT OR REPLACE INTO analises 
                (id, intimacao_id, prompt_id, prompt_nome, data_analise, resultado_ia,
                 acertou, tempo_processamento, modelo, temperatura, tokens_usados,
                 tokens_input, tokens_output, custo_real, prompt_completo, resposta_completa, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analise['id'],
                analise.get('intimacao_id', ''),
                analise.get('prompt_id', ''),
                analise.get('prompt_nome', ''),
                analise['data_analise'],
                analise.get('resultado_ia', ''),
                analise.get('acertou', False),
                analise.get('tempo_processamento', 0.0),
                analise.get('modelo', ''),
                analise.get('temperatura', 0.0),
                analise.get('tokens_usados', 0),
                analise.get('tokens_input', 0),
                analise.get('tokens_output', 0),
                analise.get('custo_real', 0.0),
                analise.get('prompt_completo', ''),
                analise.get('resposta_completa', ''),
                analise.get('session_id', None)
            ))
            conn.commit()
            return analise['id']
    
    def delete_analise(self, analise_id: str) -> bool:
        """Deletar uma análise"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM analises WHERE id = ?', (analise_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def adicionar_analise_intimacao(self, intimacao_id: str, analise_data: Dict[str, Any]):
        """Adicionar análise a uma intimação"""
        analise_data['intimacao_id'] = intimacao_id
        self.save_analise(analise_data)
        
        # Atualizar estatísticas do prompt se especificado
        if 'prompt_id' in analise_data:
            self.update_prompt_statistics(analise_data['prompt_id'])
    
    def update_prompt_statistics(self, prompt_id: str):
        """Atualizar estatísticas de um prompt"""
        with self.get_connection() as conn:
            # Calcular estatísticas
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_usos,
                    AVG(CASE WHEN acertou THEN 1.0 ELSE 0.0 END) * 100 as acuracia_media,
                    AVG(tempo_processamento) as tempo_medio,
                    SUM(custo_real) as custo_total
                FROM analises 
                WHERE prompt_id = ?
            ''', (prompt_id,))
            
            stats = cursor.fetchone()
            if stats:
                # Atualizar prompt
                conn.execute('''
                    UPDATE prompts 
                    SET total_usos = ?, acuracia_media = ?, tempo_medio = ?, custo_total = ?
                    WHERE id = ?
                ''', (
                    stats['total_usos'],
                    stats['acuracia_media'] or 0.0,
                    stats['tempo_medio'] or 0.0,
                    stats['custo_total'] or 0.0,
                    prompt_id
                ))
                conn.commit()
    
    # Métodos de estatísticas
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas gerais"""
        with self.get_connection() as conn:
            # Contar registros
            intimacoes_count = conn.execute('SELECT COUNT(*) FROM intimacoes').fetchone()[0]
            prompts_count = conn.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
            analises_count = conn.execute('SELECT COUNT(*) FROM analises').fetchone()[0]
            
            # Calcular acurácia geral
            cursor = conn.execute('SELECT AVG(CASE WHEN acertou THEN 1.0 ELSE 0.0 END) FROM analises')
            acuracia_geral = cursor.fetchone()[0] or 0.0
            
            return {
                'total_intimacoes': intimacoes_count,
                'total_prompts': prompts_count,
                'total_analises': analises_count,
                'acuracia_geral': acuracia_geral * 100
            }
    
    # Métodos de configuração (mantém compatibilidade)
    def get_config(self) -> Dict[str, Any]:
        """Obter configurações (ainda usa JSON por simplicidade)"""
        config_file = os.path.join(os.path.dirname(self.db_path), 'config.json')
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Substituir variáveis de ambiente
            if config and 'openai_api_key' in config:
                api_key = config['openai_api_key']
                if api_key.startswith('${') and api_key.endswith('}'):
                    env_var = api_key[2:-1]
                    config['openai_api_key'] = os.environ.get(env_var, '')
            
            return config
        except:
            return {}
    
    def save_config(self, config: Dict[str, Any]):
        """Salvar configurações (ainda usa JSON por simplicidade)"""
        config_file = os.path.join(os.path.dirname(self.db_path), 'config.json')
        
        # Proteger contra salvamento da chave da API
        if 'openai_api_key' in config:
            api_key = config['openai_api_key']
            if api_key.startswith('sk-'):
                config['openai_api_key'] = '${OPENAI_API_KEY}'
            elif not (api_key.startswith('${') and api_key.endswith('}')):
                config['openai_api_key'] = '${OPENAI_API_KEY}'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Métodos para Sessões de Análise
    def get_sessoes_analise(self, limit: int = 50, offset: int = 0, 
                           data_inicio: str = None, data_fim: str = None,
                           prompt_id: str = None, status: str = None,
                           acuracia_min: str = None) -> List[Dict[str, Any]]:
        """Obter lista de sessões de análise com filtros e paginação"""
        with self.get_connection() as conn:
            # Construir query com filtros
            where_conditions = []
            params = []
            
            if data_inicio:
                where_conditions.append("DATE(data_inicio) >= ?")
                params.append(data_inicio)
            
            if data_fim:
                where_conditions.append("DATE(data_inicio) <= ?")
                params.append(data_fim)
            
            if prompt_id:
                where_conditions.append("prompt_id = ?")
                params.append(prompt_id)
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
            
            # Construir query base
            query = '''
                SELECT 
                    session_id,
                    data_inicio,
                    data_fim,
                    prompt_id,
                    prompt_nome,
                    modelo,
                    temperatura,
                    max_tokens,
                    timeout,
                    total_intimacoes,
                    intimações_processadas,
                    acertos,
                    erros,
                    tempo_total,
                    custo_total,
                    tokens_total,
                    status,
                    configuracoes
                FROM sessoes_analise 
            '''
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Adicionar filtro de acurácia se necessário
            if acuracia_min:
                if where_conditions:
                    query += " AND "
                else:
                    query += " WHERE "
                query += "CASE WHEN intimações_processadas > 0 THEN (acertos * 100.0 / intimações_processadas) ELSE 0 END >= ?"
                params.append(float(acuracia_min))
            
            query += " ORDER BY data_inicio DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            
            sessoes = []
            for row in cursor.fetchall():
                sessao = dict(row)
                
                # Calcular acurácia
                intimações_processadas = sessao['intimações_processadas'] or 0
                acertos = sessao['acertos'] or 0
                if intimações_processadas > 0:
                    sessao['acuracia'] = round((acertos / intimações_processadas) * 100, 1)
                else:
                    sessao['acuracia'] = 0.0
                
                # Formatar datas
                if sessao['data_inicio']:
                    try:
                        data_inicio = datetime.fromisoformat(sessao['data_inicio'].replace('Z', '+00:00'))
                        sessao['data_inicio_formatada'] = data_inicio.strftime('%d/%m/%Y %H:%M')
                    except:
                        sessao['data_inicio_formatada'] = sessao['data_inicio']
                else:
                    sessao['data_inicio_formatada'] = 'N/A'
                
                if sessao['data_fim']:
                    try:
                        data_fim = datetime.fromisoformat(sessao['data_fim'].replace('Z', '+00:00'))
                        sessao['data_fim_formatada'] = data_fim.strftime('%d/%m/%Y %H:%M')
                    except:
                        sessao['data_fim_formatada'] = sessao['data_fim']
                else:
                    sessao['data_fim_formatada'] = None
                
                # Converter configurações de JSON string para dict
                if sessao['configuracoes']:
                    try:
                        sessao['configuracoes'] = json.loads(sessao['configuracoes'])
                    except:
                        sessao['configuracoes'] = {}
                else:
                    sessao['configuracoes'] = {}
                
                sessoes.append(sessao)
            return sessoes
    
    def get_classificacoes_unicas(self) -> List[str]:
        """Obter lista de classificações únicas das intimações"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT classificacao_manual 
                FROM intimacoes 
                WHERE classificacao_manual IS NOT NULL 
                AND classificacao_manual != ''
                ORDER BY classificacao_manual
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_defensores_unicos(self) -> List[str]:
        """Obter lista de defensores únicos das intimações"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT defensor 
                FROM intimacoes 
                WHERE defensor IS NOT NULL 
                AND defensor != ''
                ORDER BY defensor
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_classes_unicas(self) -> List[str]:
        """Obter lista de classes únicas das intimações"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT classe 
                FROM intimacoes 
                WHERE classe IS NOT NULL 
                AND classe != ''
                ORDER BY classe
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_intimacoes_por_prompt(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter intimações que foram analisadas com um prompt específico"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT i.*
                FROM intimacoes i
                INNER JOIN analises a ON i.id = a.intimacao_id
                WHERE a.prompt_id = ?
                ORDER BY i.data_criacao DESC
            ''', (prompt_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_analises_acertos_por_prompt_e_temperatura(self, prompt_id: str) -> Dict[str, Dict[str, Any]]:
        """Obter análises e acertos por intimação para um prompt específico, agrupados por temperatura"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.intimacao_id,
                    a.temperatura,
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto
                FROM analises a
                WHERE a.prompt_id = ?
                GROUP BY a.intimacao_id, a.temperatura
                ORDER BY a.intimacao_id, a.temperatura
            ''', (prompt_id,))
            
            result = {}
            for row in cursor.fetchall():
                intimacao_id = row[0]
                temperatura = row[1]
                
                # Criar estrutura para armazenar todas as temperaturas
                if intimacao_id not in result:
                    result[intimacao_id] = {
                        'temperaturas': [],
                        'total_analises': 0,
                        'acertos': 0,
                        'taxa_acerto': 0
                    }
                
                # Adicionar dados desta temperatura
                result[intimacao_id]['temperaturas'].append({
                    'temperatura': temperatura,
                    'total_analises': row[2],
                    'acertos': row[3],
                    'taxa_acerto': row[4]
                })
                
                # Somar totais gerais
                result[intimacao_id]['total_analises'] += row[2]
                result[intimacao_id]['acertos'] += row[3]
            
            # Calcular taxa de acerto geral para cada intimação
            for intimacao_id in result:
                if result[intimacao_id]['total_analises'] > 0:
                    result[intimacao_id]['taxa_acerto'] = round(
                        (result[intimacao_id]['acertos'] / result[intimacao_id]['total_analises']) * 100, 1
                    )
            
            return result
    
    def get_analises_by_prompt_and_intimacao(self, prompt_id: str, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter análises de um prompt específico com uma intimação específica"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT a.*, p.nome as prompt_nome
                FROM analises a
                LEFT JOIN prompts p ON a.prompt_id = p.id
                WHERE a.prompt_id = ? AND a.intimacao_id = ?
                ORDER BY a.data_analise DESC
            ''', (prompt_id, intimacao_id))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_taxa_acerto_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Obter taxa de acerto de um prompt específico"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto
                FROM analises 
                WHERE prompt_id = ?
            ''', (prompt_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'total_analises': result[0],
                    'acertos': result[1],
                    'taxa_acerto': result[2] if result[0] > 0 else 0.0
                }
            return {
                'total_analises': 0,
                'acertos': 0,
                'taxa_acerto': 0.0
            }
    
    
    def get_taxa_acerto_por_intimacao(self) -> Dict[str, Dict[str, Any]]:
        """Obter taxa de acerto de cada intimação"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.intimacao_id,
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto
                FROM analises a
                WHERE a.intimacao_id IS NOT NULL
                GROUP BY a.intimacao_id
                ORDER BY taxa_acerto DESC
            ''')
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    'total_analises': row[1],
                    'acertos': row[2],
                    'taxa_acerto': row[3]
                }
            
            return result
    
    def get_taxa_acerto_por_prompt_especifico(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter taxa de acerto de um prompt específico para todas as intimações"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.intimacao_id,
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto
                FROM analises a
                WHERE a.prompt_id = ? AND a.intimacao_id IS NOT NULL
                GROUP BY a.intimacao_id
                ORDER BY taxa_acerto DESC
            ''', (prompt_id,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'intimacao_id': row[0],
                    'total_analises': row[1],
                    'acertos': row[2],
                    'taxa_acerto': row[3]
                })
            
            return result
    
    def get_taxa_acerto_por_prompt_e_temperatura(self, prompt_id: str, temperatura: float) -> List[Dict[str, Any]]:
        """Obter taxa de acerto de um prompt específico com temperatura específica"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.intimacao_id,
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto
                FROM analises a
                WHERE a.prompt_id = ? AND a.temperatura = ? AND a.intimacao_id IS NOT NULL
                GROUP BY a.intimacao_id
                ORDER BY taxa_acerto DESC
            ''', (prompt_id, temperatura))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'intimacao_id': row[0],
                    'total_analises': row[1],
                    'acertos': row[2],
                    'taxa_acerto': row[3]
                })
            
            return result
    
    def salvar_historico_acuracia(self, prompt_id: str, numero_intimacoes: int, temperatura: float, 
                                 acuracia: float, session_id: str = None) -> bool:
        """Salvar histórico de acurácia de um prompt"""
        try:
            with self.get_connection() as conn:
                historico_id = str(uuid.uuid4())
                data_analise = datetime.now().isoformat()
                
                conn.execute('''
                    INSERT INTO historico_acuracia 
                    (id, prompt_id, numero_intimacoes, temperatura, acuracia, data_analise, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (historico_id, prompt_id, numero_intimacoes, temperatura, acuracia, data_analise, session_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao salvar histórico de acurácia: {e}")
            return False
    
    def get_historico_acuracia_prompt(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Obter histórico de acurácia de um prompt agrupado por condições"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        prompt_id,
                        numero_intimacoes,
                        temperatura,
                        COUNT(*) as total_analises,
                        AVG(acuracia) as acuracia_media,
                        MIN(acuracia) as acuracia_minima,
                        MAX(acuracia) as acuracia_maxima,
                        MIN(data_analise) as primeira_analise,
                        MAX(data_analise) as ultima_analise
                    FROM historico_acuracia 
                    WHERE prompt_id = ?
                    GROUP BY prompt_id, numero_intimacoes, temperatura
                    ORDER BY numero_intimacoes DESC, temperatura ASC, ultima_analise DESC
                ''', (prompt_id,))
                
                result = []
                for row in cursor.fetchall():
                    result.append({
                        'prompt_id': row[0],
                        'numero_intimacoes': row[1],
                        'temperatura': row[2],
                        'total_analises': row[3],
                        'acuracia_media': round(row[4], 2),
                        'acuracia_minima': round(row[5], 2),
                        'acuracia_maxima': round(row[6], 2),
                        'primeira_analise': row[7],
                        'ultima_analise': row[8]
                    })
                
                return result
        except Exception as e:
            print(f"Erro ao obter histórico de acurácia: {e}")
            return []
    
    def get_acuracia_por_condicoes(self, prompt_id: str, numero_intimacoes: int, temperatura: float) -> Dict[str, Any]:
        """Obter acurácia média para condições específicas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_analises,
                        AVG(acuracia) as acuracia_media,
                        MIN(acuracia) as acuracia_minima,
                        MAX(acuracia) as acuracia_maxima,
                        MIN(data_analise) as primeira_analise,
                        MAX(data_analise) as ultima_analise
                    FROM historico_acuracia 
                    WHERE prompt_id = ? AND numero_intimacoes = ? AND temperatura = ?
                ''', (prompt_id, numero_intimacoes, temperatura))
                
                row = cursor.fetchone()
                if row and row[0] > 0:
                    return {
                        'total_analises': row[0],
                        'acuracia_media': round(row[1], 2),
                        'acuracia_minima': round(row[2], 2),
                        'acuracia_maxima': round(row[3], 2),
                        'primeira_analise': row[4],
                        'ultima_analise': row[5]
                    }
                else:
                    return {
                        'total_analises': 0,
                        'acuracia_media': 0.0,
                        'acuracia_minima': 0.0,
                        'acuracia_maxima': 0.0,
                        'primeira_analise': None,
                        'ultima_analise': None
                    }
        except Exception as e:
            print(f"Erro ao obter acurácia por condições: {e}")
            return {
                'total_analises': 0,
                'acuracia_media': 0.0,
                'acuracia_minima': 0.0,
                'acuracia_maxima': 0.0,
                'primeira_analise': None,
                'ultima_analise': None
            }
    
    def get_prompts_acerto_por_intimacao(self, intimacao_id: str) -> List[Dict[str, Any]]:
        """Obter prompts e taxas de acerto de uma intimação específica"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.prompt_id,
                    a.prompt_nome,
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) as acertos,
                    ROUND(
                        (SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                        1
                    ) as taxa_acerto,
                    a.modelo,
                    a.temperatura,
                    MAX(a.data_analise) as ultima_analise
                FROM analises a
                WHERE a.intimacao_id = ?
                GROUP BY a.prompt_id, a.prompt_nome, a.modelo, a.temperatura
                ORDER BY taxa_acerto DESC, ultima_analise DESC
            ''', (intimacao_id,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'prompt_id': row[0],
                    'prompt_nome': row[1],
                    'total_analises': row[2],
                    'acertos': row[3],
                    'taxa_acerto': row[4],
                    'modelo': row[5],
                    'temperatura': row[6],
                    'ultima_analise': row[7]
                })
            
            return result
    
    def get_dados_analise_intimacao_prompt(self, intimacao_id: str, prompt_id: str) -> Dict[str, Any]:
        """Obter dados completos de uma análise específica (intimação + prompt)"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.*,
                    i.processo,
                    i.orgao_julgador,
                    i.classificacao_manual,
                    i.informacao_adicional,
                    i.intimado,
                    i.status as status_intimacao
                FROM analises a
                LEFT JOIN intimacoes i ON a.intimacao_id = i.id
                WHERE a.intimacao_id = ? AND a.prompt_id = ?
                ORDER BY a.data_analise DESC
                LIMIT 1
            ''', (intimacao_id, prompt_id))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_total_sessoes_analise(self, data_inicio: str = None, data_fim: str = None,
                                 prompt_id: str = None, status: str = None,
                                 acuracia_min: str = None) -> int:
        """Contar total de sessões de análise com filtros"""
        with self.get_connection() as conn:
            # Construir query com filtros
            where_conditions = []
            params = []
            
            if data_inicio:
                where_conditions.append("DATE(data_inicio) >= ?")
                params.append(data_inicio)
            
            if data_fim:
                where_conditions.append("DATE(data_inicio) <= ?")
                params.append(data_fim)
            
            if prompt_id:
                where_conditions.append("prompt_id = ?")
                params.append(prompt_id)
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
            
            # Construir query base
            query = "SELECT COUNT(*) FROM sessoes_analise"
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Adicionar filtro de acurácia se necessário
            if acuracia_min:
                if where_conditions:
                    query += " AND "
                else:
                    query += " WHERE "
                query += "CASE WHEN intimações_processadas > 0 THEN (acertos * 100.0 / intimações_processadas) ELSE 0 END >= ?"
                params.append(float(acuracia_min))
            
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def get_sessao_analise(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obter detalhes de uma sessão específica"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    session_id,
                    data_inicio,
                    data_fim,
                    prompt_id,
                    prompt_nome,
                    modelo,
                    temperatura,
                    max_tokens,
                    timeout,
                    total_intimacoes,
                    intimações_processadas,
                    acertos,
                    erros,
                    tempo_total,
                    custo_total,
                    tokens_total,
                    status,
                    configuracoes
                FROM sessoes_analise 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                sessao = dict(row)
                
                # Calcular acurácia
                intimações_processadas = sessao['intimações_processadas'] or 0
                acertos = sessao['acertos'] or 0
                if intimações_processadas > 0:
                    sessao['acuracia'] = round((acertos / intimações_processadas) * 100, 1)
                else:
                    sessao['acuracia'] = 0.0
                
                # Formatar datas
                if sessao['data_inicio']:
                    try:
                        data_inicio = datetime.fromisoformat(sessao['data_inicio'].replace('Z', '+00:00'))
                        sessao['data_inicio_formatada'] = data_inicio.strftime('%d/%m/%Y %H:%M')
                    except:
                        sessao['data_inicio_formatada'] = sessao['data_inicio']
                else:
                    sessao['data_inicio_formatada'] = 'N/A'
                
                if sessao['data_fim']:
                    try:
                        data_fim = datetime.fromisoformat(sessao['data_fim'].replace('Z', '+00:00'))
                        sessao['data_fim_formatada'] = data_fim.strftime('%d/%m/%Y %H:%M')
                    except:
                        sessao['data_fim_formatada'] = sessao['data_fim']
                else:
                    sessao['data_fim_formatada'] = None
                
                # Converter configurações de JSON string para dict
                if sessao['configuracoes']:
                    try:
                        sessao['configuracoes_parsed'] = json.loads(sessao['configuracoes'])
                    except:
                        sessao['configuracoes_parsed'] = {}
                else:
                    sessao['configuracoes_parsed'] = {}
                
                return sessao
            return None
    
    def get_analise_by_id(self, analise_id: str) -> Optional[Dict[str, Any]]:
        """Obter uma análise específica por ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM analises WHERE id = ?
            ''', (analise_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_analises_por_sessao(self, session_id: str) -> List[Dict[str, Any]]:
        """Obter todas as análises de uma sessão específica"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.*,
                    i.processo,
                    i.orgao_julgador,
                    i.classificacao_manual,
                    i.informacao_adicional,
                    i.intimado,
                    i.status as status_intimacao,
                    i.destacada,
                    -- Estatísticas do prompt para esta intimação específica
                    (SELECT COUNT(*) FROM analises a2 WHERE a2.prompt_id = a.prompt_id AND a2.intimacao_id = a.intimacao_id) as total_testes_intimacao,
                    (SELECT COUNT(*) FROM analises a3 WHERE a3.prompt_id = a.prompt_id AND a3.intimacao_id = a.intimacao_id AND a3.acertou = 1) as acertos_intimacao,
                    -- Estatísticas gerais do prompt
                    (SELECT COUNT(*) FROM analises a4 WHERE a4.prompt_id = a.prompt_id) as total_testes_prompt,
                    (SELECT COUNT(*) FROM analises a5 WHERE a5.prompt_id = a.prompt_id AND a5.acertou = 1) as acertos_prompt
                FROM analises a
                LEFT JOIN intimacoes i ON a.intimacao_id = i.id
                WHERE a.session_id = ?
                ORDER BY a.data_analise DESC
            ''', (session_id,))
            
            analises = []
            for row in cursor.fetchall():
                analise = dict(row)
                
                # Calcular taxa de acerto individual (para esta intimação específica)
                total_testes_intimacao = analise.get('total_testes_intimacao', 0)
                acertos_intimacao = analise.get('acertos_intimacao', 0)
                if total_testes_intimacao > 0:
                    analise['taxa_acerto_intimacao'] = round((acertos_intimacao / total_testes_intimacao) * 100, 1)
                else:
                    analise['taxa_acerto_intimacao'] = 0.0
                
                # Calcular taxa de acerto geral do prompt
                total_testes_prompt = analise.get('total_testes_prompt', 0)
                acertos_prompt = analise.get('acertos_prompt', 0)
                if total_testes_prompt > 0:
                    analise['taxa_acerto_prompt'] = round((acertos_prompt / total_testes_prompt) * 100, 1)
                else:
                    analise['taxa_acerto_prompt'] = 0.0
                
                analises.append(analise)
            return analises
    
    def criar_sessao_analise(self, session_id: str, prompt_id: str, prompt_nome: str, 
                           modelo: str, temperatura: float, max_tokens: int, 
                           timeout: int, total_intimacoes: int, configuracoes: Dict[str, Any] = None) -> bool:
        """Criar uma nova sessão de análise"""
        try:
            print(f"=== DEBUG: criar_sessao_analise chamada ===")
            print(f"=== DEBUG: session_id: {session_id} (tipo: {type(session_id)}) ===")
            print(f"=== DEBUG: prompt_id: {prompt_id} (tipo: {type(prompt_id)}) ===")
            print(f"=== DEBUG: prompt_nome: {prompt_nome} (tipo: {type(prompt_nome)}) ===")
            print(f"=== DEBUG: modelo: {modelo} (tipo: {type(modelo)}) ===")
            print(f"=== DEBUG: temperatura: {temperatura} (tipo: {type(temperatura)}) ===")
            print(f"=== DEBUG: max_tokens: {max_tokens} (tipo: {type(max_tokens)}) ===")
            print(f"=== DEBUG: timeout: {timeout} (tipo: {type(timeout)}) ===")
            print(f"=== DEBUG: total_intimacoes: {total_intimacoes} (tipo: {type(total_intimacoes)}) ===")
            print(f"=== DEBUG: configuracoes: {configuracoes} (tipo: {type(configuracoes)}) ===")
            
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO sessoes_analise (
                        session_id, data_inicio, prompt_id, prompt_nome, modelo,
                        temperatura, max_tokens, timeout, total_intimacoes,
                        configuracoes, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    datetime.now().isoformat(),
                    prompt_id,
                    prompt_nome,
                    modelo,
                    temperatura,
                    max_tokens,
                    timeout,
                    total_intimacoes,
                    json.dumps(configuracoes) if configuracoes else None,
                    'em_andamento'
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return False
    
    def atualizar_sessao_analise(self, session_id: str, **kwargs) -> bool:
        """Atualizar dados de uma sessão de análise"""
        try:
            with self.get_connection() as conn:
                # Construir query dinamicamente
                fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['intimações_processadas', 'acertos', 'erros', 'tempo_total', 
                              'custo_total', 'tokens_total', 'status', 'data_fim']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if not fields:
                    return False
                
                values.append(session_id)
                query = f"UPDATE sessoes_analise SET {', '.join(fields)} WHERE session_id = ?"
                
                conn.execute(query, values)
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao atualizar sessão: {e}")
            return False
    
    def excluir_sessao_analise(self, session_id: str) -> bool:
        """Excluir uma sessão de análise e suas análises associadas"""
        try:
            with self.get_connection() as conn:
                # Excluir análises da sessão
                conn.execute('DELETE FROM analises WHERE session_id = ?', (session_id,))
                
                # Excluir a sessão
                conn.execute('DELETE FROM sessoes_analise WHERE session_id = ?', (session_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao excluir sessão: {e}")
            return False
    
    def finalizar_sessao_analise(self, session_id: str, estatisticas: Dict[str, Any]) -> bool:
        """Finalizar uma sessão de análise com estatísticas"""
        try:
            with self.get_connection() as conn:
                # Atualizar a sessão com estatísticas finais
                conn.execute('''
                    UPDATE sessoes_analise 
                    SET 
                        data_fim = ?,
                        intimações_processadas = ?,
                        acertos = ?,
                        erros = ?,
                        tempo_total = ?,
                        custo_total = ?,
                        tokens_total = ?,
                        status = 'concluida'
                    WHERE session_id = ?
                ''', (
                    datetime.now().isoformat(),
                    estatisticas.get('total_processadas', 0),
                    estatisticas.get('acertos', 0),
                    estatisticas.get('erros', 0),
                    estatisticas.get('tempo_total', 0.0),
                    estatisticas.get('custo_total', 0.0),
                    estatisticas.get('tokens_total', 0),
                    session_id
                ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erro ao finalizar sessão: {e}")
            return False
    
    def calcular_estatisticas_sessao(self, session_id: str) -> Dict[str, Any]:
        """Calcular estatísticas de uma sessão de análise"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_analises,
                    SUM(CASE WHEN acertou THEN 1 ELSE 0 END) as acertos,
                    SUM(CASE WHEN NOT acertou THEN 1 ELSE 0 END) as erros,
                    AVG(tempo_processamento) as tempo_medio,
                    SUM(custo_real) as custo_total,
                    SUM(tokens_input + tokens_output) as tokens_total
                FROM analises 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                stats = dict(row)
                total = stats['total_analises'] or 0
                acertos = stats['acertos'] or 0
                
                return {
                    'total_analises': total,
                    'acertos': acertos,
                    'erros': stats['erros'] or 0,
                    'acuracia': (acertos / total * 100) if total > 0 else 0,
                    'tempo_medio': stats['tempo_medio'] or 0,
                    'custo_total': stats['custo_total'] or 0,
                    'tokens_total': stats['tokens_total'] or 0
                }
            return {
                'total_analises': 0,
                'acertos': 0,
                'erros': 0,
                'acuracia': 0,
                'tempo_medio': 0,
                'custo_total': 0,
                'tokens_total': 0
            }
    
    def calculate_real_cost(self, tokens_input: int, tokens_output: int, modelo: str, provider: str = 'azure') -> float:
        """Calcular custo real baseado nos tokens e modelo"""
        try:
            config = self.get_config()
            
            # Obter preços do provider correto
            if provider.lower() == 'azure':
                precos = config.get('precos_azure', {})
            else:
                precos = config.get('precos_openai', {})
            
            # Obter preços do modelo
            preco_modelo = precos.get(modelo, {})
            preco_input = preco_modelo.get('input', 0.0)  # Por 1M tokens
            preco_output = preco_modelo.get('output', 0.0)  # Por 1M tokens
            
            # Calcular custo (preços são por 1M tokens)
            custo_input = (tokens_input / 1_000_000) * preco_input
            custo_output = (tokens_output / 1_000_000) * preco_output
            custo_total = custo_input + custo_output
            
            return round(custo_total, 6)
            
        except Exception as e:
            print(f"Erro ao calcular custo: {e}")
            return 0.0
