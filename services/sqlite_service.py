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
            
            # Criar índices para performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_intimacao ON analises(intimacao_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_prompt ON analises(prompt_id)')
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
                (id, nome, descricao, regra_negocio, conteudo, categoria, tags, data_criacao, 
                 total_usos, acuracia_media, tempo_medio, custo_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prompt['id'],
                prompt.get('nome', ''),
                prompt.get('descricao', ''),
                prompt.get('regra_negocio', ''),
                prompt.get('conteudo', ''),
                prompt.get('categoria', ''),
                tags_json,
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
                SELECT a.*, i.contexto, i.classificacao_manual, p.regra_negocio
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
                SELECT a.*, p.regra_negocio
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
                SELECT a.*, p.regra_negocio
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
    def get_sessoes_analise(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obter lista de sessões de análise"""
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
                ORDER BY data_inicio DESC 
                LIMIT ?
            ''', (limit,))
            
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
                    i.status as status_intimacao
                FROM analises a
                LEFT JOIN intimacoes i ON a.intimacao_id = i.id
                WHERE a.session_id = ?
                ORDER BY a.data_analise DESC
            ''', (session_id,))
            
            analises = []
            for row in cursor.fetchall():
                analises.append(dict(row))
            return analises
    
    def criar_sessao_analise(self, session_id: str, prompt_id: str, prompt_nome: str, 
                           modelo: str, temperatura: float, max_tokens: int, 
                           timeout: int, total_intimacoes: int, configuracoes: Dict[str, Any] = None) -> bool:
        """Criar uma nova sessão de análise"""
        try:
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
