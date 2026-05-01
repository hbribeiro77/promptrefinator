import sqlite3
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager

from services.texto_template_novo_prompt_padrao_triagem_json_instrucoes_dpe_rs_semente_banco_sqlite import (
    DESCRICAO_TEMPLATE_NOVO_PROMPT_PADRAO,
    NOME_TEMPLATE_NOVO_PROMPT_PADRAO,
    TEXTO_TEMPLATE_NOVO_PROMPT_PADRAO_TRIAGEM_JSON,
)


def _seed_prompt_templates_padrao_sqlite(conn) -> None:
    """Se não houver templates, insere o padrão de triagem JSON (Novo prompt)."""
    row = conn.execute('SELECT COUNT(*) AS c FROM prompt_templates').fetchone()
    if row and row['c'] > 0:
        return
    tid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn.execute(
        '''
        INSERT INTO prompt_templates (id, nome, descricao, conteudo, ordem, data_criacao, data_atualizacao)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        ''',
        (
            tid,
            NOME_TEMPLATE_NOVO_PROMPT_PADRAO,
            DESCRICAO_TEMPLATE_NOVO_PROMPT_PADRAO,
            TEXTO_TEMPLATE_NOVO_PROMPT_PADRAO_TRIAGEM_JSON,
            now,
            now,
        ),
    )


def _sql_filtro_modo_avaliacao_sessao(modo_avaliacao_filtro: Optional[str]) -> Optional[str]:
    """
    Fragmento SQL para filtrar sessoes_analise.configuracoes (JSON) por modo_avaliacao.
    Valores aceitos: 'padrao', 'focado'. None ou vazio = sem filtro.
    """
    if modo_avaliacao_filtro is None or str(modo_avaliacao_filtro).strip() == '':
        return None
    m = str(modo_avaliacao_filtro).strip().lower()
    if m == 'focado':
        return (
            "LOWER(TRIM(COALESCE(json_extract(configuracoes, '$.modo_avaliacao'), ''))) = 'focado'"
        )
    if m == 'padrao':
        return (
            "LOWER(TRIM(COALESCE(json_extract(configuracoes, '$.modo_avaliacao'), ''))) != 'focado'"
        )
    return None


def _seed_areas_padrao_sqlite(conn) -> None:
    """Garante as quatro áreas padrão (ids estáveis). Função de módulo evita falha se o método da classe sumir por merge."""
    padroes = [
        ('civel', 'Cível', 1),
        ('familia', 'Família', 2),
        ('crime', 'Crime', 3),
        ('violencia_domestica', 'Violência doméstica', 4),
    ]
    for aid, nome, ordem in padroes:
        conn.execute(
            '''
            INSERT OR IGNORE INTO areas (id, nome, ordem)
            VALUES (?, ?, ?)
            ''',
            (aid, nome, ordem),
        )


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

    def _backfill_historico_acuracia_modelo_desde_sessao_e_analises(self, conn) -> None:
        """Preenche `historico_acuracia.modelo` vazio a partir da sessão ou das análises."""
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessoes_analise'"
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE historico_acuracia
                    SET modelo = (
                        SELECT TRIM(s.modelo) FROM sessoes_analise s
                        WHERE s.session_id = historico_acuracia.session_id
                          AND s.modelo IS NOT NULL AND TRIM(s.modelo) != ''
                        LIMIT 1
                    )
                    WHERE (historico_acuracia.modelo IS NULL OR TRIM(historico_acuracia.modelo) = '')
                      AND historico_acuracia.session_id IS NOT NULL
                    """
                )
        except Exception as e:
            print(f"Aviso: backfill historico_acuracia.modelo (sessão): {e}")
        try:
            conn.execute(
                """
                UPDATE historico_acuracia
                SET modelo = (
                    SELECT TRIM(a.modelo) FROM analises a
                    WHERE a.session_id = historico_acuracia.session_id
                      AND a.prompt_id = historico_acuracia.prompt_id
                      AND a.modelo IS NOT NULL AND TRIM(a.modelo) != ''
                    ORDER BY a.data_analise DESC
                    LIMIT 1
                )
                WHERE (historico_acuracia.modelo IS NULL OR TRIM(historico_acuracia.modelo) = '')
                  AND historico_acuracia.session_id IS NOT NULL
                """
            )
        except Exception as e:
            print(f"Aviso: backfill historico_acuracia.modelo (analises): {e}")
    
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
                    smart_context BOOLEAN DEFAULT 0,
                    data_criacao TEXT NOT NULL
                )
            ''')
            
            # Adicionar coluna smart_context se não existir (para bancos já criados)
            try:
                conn.execute('ALTER TABLE intimacoes ADD COLUMN smart_context BOOLEAN DEFAULT 0')
            except sqlite3.OperationalError:
                # Coluna já existe, ignorar erro
                pass

            # ID externo do portal (ex.: intimacaoId do eProc) — deduplicação na importação
            try:
                conn.execute(
                    'ALTER TABLE intimacoes ADD COLUMN intimacao_id_externo TEXT'
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    'CREATE UNIQUE INDEX IF NOT EXISTS idx_intimacoes_id_externo '
                    'ON intimacoes(intimacao_id_externo)'
                )
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute(
                    'ALTER TABLE intimacoes ADD COLUMN regras_usuario_prioridade_alta TEXT'
                )
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute('ALTER TABLE intimacoes ADD COLUMN observacoes TEXT')
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute(
                    'ALTER TABLE intimacoes ADD COLUMN destacada BOOLEAN DEFAULT 0'
                )
            except sqlite3.OperationalError:
                pass
            
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
                    session_id TEXT,
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
                    modelo TEXT,
                    temperatura REAL NOT NULL,
                    acuracia REAL NOT NULL,
                    data_analise TEXT NOT NULL,
                    session_id TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            ''')

            # Sessões de análise (modelo/temp da execução em lote — usado para enriquecer histórico de acurácia)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessoes_analise (
                    session_id TEXT PRIMARY KEY,
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT,
                    prompt_id TEXT NOT NULL,
                    prompt_nome TEXT,
                    modelo TEXT,
                    temperatura REAL,
                    max_tokens INTEGER,
                    timeout INTEGER,
                    total_intimacoes INTEGER,
                    intimações_processadas INTEGER DEFAULT 0,
                    acertos INTEGER DEFAULT 0,
                    erros INTEGER DEFAULT 0,
                    tempo_total REAL DEFAULT 0.0,
                    custo_total REAL DEFAULT 0.0,
                    tokens_total INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'em_andamento',
                    configuracoes TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sessoes_data ON sessoes_analise(data_inicio)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sessoes_prompt ON sessoes_analise(prompt_id)')

            # Tabela de defensores (cadastro administrativo)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS defensores (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    ativo INTEGER DEFAULT 1,
                    data_criacao TEXT NOT NULL
                )
            ''')
            
            # Criar índices para performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_intimacao ON analises(intimacao_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_prompt ON analises(prompt_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_historico_acuracia_prompt ON historico_acuracia(prompt_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_historico_acuracia_condicoes ON historico_acuracia(prompt_id, numero_intimacoes, temperatura)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_data ON analises(data_analise)')
            conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_defensores_nome_lower ON defensores(LOWER(nome))')

            try:
                conn.execute('ALTER TABLE analises ADD COLUMN session_id TEXT')
            except sqlite3.OperationalError:
                pass
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analises_session ON analises(session_id)')
            try:
                conn.execute(
                    "ALTER TABLE analises ADD COLUMN modo_avaliacao TEXT DEFAULT 'padrao'"
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute('ALTER TABLE analises ADD COLUMN tipo_alvo_focado TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute('ALTER TABLE historico_acuracia ADD COLUMN session_id TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute('ALTER TABLE historico_acuracia ADD COLUMN modelo TEXT')
            except sqlite3.OperationalError:
                pass
            conn.execute('CREATE INDEX IF NOT EXISTS idx_historico_acuracia_condicoes_modelo ON historico_acuracia(prompt_id, numero_intimacoes, temperatura, modelo)')

            self._backfill_historico_acuracia_modelo_desde_sessao_e_analises(conn)

            conn.execute('''
                CREATE TABLE IF NOT EXISTS areas (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    ordem INTEGER NOT NULL DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS area_classe (
                    classe TEXT PRIMARY KEY,
                    area_id TEXT NOT NULL,
                    FOREIGN KEY (area_id) REFERENCES areas (id) ON DELETE CASCADE
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    conteudo TEXT NOT NULL,
                    ordem INTEGER NOT NULL DEFAULT 0,
                    data_criacao TEXT NOT NULL,
                    data_atualizacao TEXT
                )
            ''')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_prompt_templates_ordem ON prompt_templates(ordem, nome)'
            )
            _seed_areas_padrao_sqlite(conn)
            _seed_prompt_templates_padrao_sqlite(conn)
            
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
    def _normalizar_campos_bool_intimacao(self, intimacao: Dict[str, Any]) -> None:
        if 'destacada' in intimacao:
            intimacao['destacada'] = bool(intimacao['destacada'])
        if 'smart_context' in intimacao:
            intimacao['smart_context'] = bool(intimacao['smart_context'])

    def get_analises_agrupadas_por_intimacao_ids(
        self, intimacao_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Uma ou poucas queries em lote em vez de N chamadas get_analises_by_intimacao."""
        if not intimacao_ids:
            return {}
        out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        chunk_size = 400
        with self.get_connection() as conn:
            for start in range(0, len(intimacao_ids), chunk_size):
                chunk = intimacao_ids[start : start + chunk_size]
                placeholders = ','.join('?' * len(chunk))
                cursor = conn.execute(
                    f'''
                    SELECT a.*, p.regra_negocio, p.nome as prompt_nome
                    FROM analises a
                    LEFT JOIN prompts p ON a.prompt_id = p.id
                    WHERE a.intimacao_id IN ({placeholders})
                    ORDER BY a.intimacao_id, a.data_analise DESC
                    ''',
                    chunk,
                )
                for row in cursor.fetchall():
                    d = dict(row)
                    out[d['intimacao_id']].append(d)
        return dict(out)

    def get_all_intimacoes(self) -> List[Dict[str, Any]]:
        """Obter todas as intimações com suas análises (2 queries em lote, sem N+1)."""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM intimacoes ORDER BY data_criacao DESC')
            rows = cursor.fetchall()
        intimacoes: List[Dict[str, Any]] = []
        ids: List[str] = []
        for row in rows:
            intimacao = dict(row)
            self._normalizar_campos_bool_intimacao(intimacao)
            intimacoes.append(intimacao)
            ids.append(intimacao['id'])
        agrupadas = self.get_analises_agrupadas_por_intimacao_ids(ids)
        for intimacao in intimacoes:
            intimacao['analises'] = agrupadas.get(intimacao['id'], [])
        return intimacoes

    def listar_intimacoes_resumo_sem_contexto_sem_analises_para_pagina_analise_ia(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Lista intimações para a página Análise IA sem ler a coluna contexto (substituída por '')
        e sem consultar análises — reduz memória e peso do HTML.
        """
        sql = '''
            SELECT
                id,
                CAST('' AS TEXT) AS contexto,
                classificacao_manual,
                informacao_adicional,
                processo,
                orgao_julgador,
                classe,
                disponibilizacao,
                intimado,
                status,
                prazo,
                defensor,
                id_tarefa,
                cor_etiqueta,
                smart_context,
                data_criacao,
                intimacao_id_externo,
                regras_usuario_prioridade_alta,
                observacoes,
                COALESCE(destacada, 0) AS destacada
            FROM intimacoes
            ORDER BY data_criacao DESC
        '''
        with self.get_connection() as conn:
            cursor = conn.execute(sql)
            out: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                intimacao = dict(row)
                self._normalizar_campos_bool_intimacao(intimacao)
                intimacao['analises'] = []
                out.append(intimacao)
        return out

    def _montar_where_listagem_intimacoes(
        self,
        busca: str,
        classificacao: str,
        defensor: str,
        destacadas: str,
    ) -> Tuple[str, List[Any]]:
        clauses: List[str] = []
        params: List[Any] = []
        if busca and busca.strip():
            clauses.append("INSTR(LOWER(COALESCE(i.contexto, '')), LOWER(?)) > 0")
            params.append(busca.strip())
        if classificacao:
            clauses.append('i.classificacao_manual = ?')
            params.append(classificacao)
        if defensor:
            clauses.append('i.defensor = ?')
            params.append(defensor)
        if destacadas == 'true':
            clauses.append('COALESCE(i.destacada, 0) = 1')
        where_sql = ' AND '.join(clauses) if clauses else '1=1'
        return where_sql, params

    def _montar_order_listagem_intimacoes(
        self,
        ordenacao: str,
        prompt_especifico: str,
        temperatura_especifica: str,
    ) -> Tuple[str, List[Any]]:
        """Retorna fragmento ORDER BY (sem ORDER BY keyword) e parâmetros extras."""
        ord_key = (ordenacao or 'data_desc').strip()
        taxa_parts: List[str] = ['a.intimacao_id = i.id']
        taxa_params: List[Any] = []
        pe = (prompt_especifico or '').strip()
        if pe:
            taxa_parts.append('a.prompt_id = ?')
            taxa_params.append(pe)
        ts = (temperatura_especifica or '').strip()
        if ts != '':
            try:
                tf = float(ts.replace(',', '.'))
                taxa_parts.append('ABS(COALESCE(a.temperatura, 0) - ?) < 0.001')
                taxa_params.append(tf)
            except (TypeError, ValueError):
                pass
        taxa_where = ' AND '.join(taxa_parts)
        taxa_expr = (
            f'COALESCE(('
            f'SELECT AVG(CASE WHEN a.acertou THEN 1.0 ELSE 0.0 END) '
            f'FROM analises a WHERE {taxa_where}'
            f'), 0.0)'
        )

        if ord_key == 'data_asc':
            return 'i.data_criacao ASC, i.id ASC', []
        if ord_key == 'classificacao':
            return 'COALESCE(i.classificacao_manual, "") ASC, i.data_criacao DESC', []
        if ord_key == 'taxa_acerto_desc':
            return f'{taxa_expr} DESC, i.data_criacao DESC', taxa_params
        if ord_key == 'taxa_acerto_asc':
            return f'{taxa_expr} ASC, i.data_criacao DESC', taxa_params
        # data_desc default
        return 'i.data_criacao DESC, i.id DESC', []

    def count_intimacoes_listagem(
        self,
        busca: str = '',
        classificacao: str = '',
        defensor: str = '',
        destacadas: str = '',
    ) -> int:
        where_sql, params = self._montar_where_listagem_intimacoes(
            busca, classificacao, defensor, destacadas
        )
        with self.get_connection() as conn:
            row = conn.execute(
                f'SELECT COUNT(*) AS c FROM intimacoes i WHERE {where_sql}',
                params,
            ).fetchone()
            return int(row['c']) if row else 0

    def stats_intimacoes_listagem(
        self,
        busca: str = '',
        classificacao: str = '',
        defensor: str = '',
        destacadas: str = '',
    ) -> Dict[str, Any]:
        """Totais alinhados aos mesmos filtros da listagem (para cards e stats)."""
        where_sql, base_params = self._montar_where_listagem_intimacoes(
            busca, classificacao, defensor, destacadas
        )
        out: Dict[str, Any] = {}
        with self.get_connection() as conn:
            row = conn.execute(
                f'SELECT COUNT(*) AS c FROM intimacoes i WHERE {where_sql}',
                base_params,
            ).fetchone()
            total = int(row['c']) if row else 0
            out['total'] = total

            row = conn.execute(
                f'''
                SELECT COUNT(*) AS c FROM intimacoes i
                WHERE {where_sql}
                  AND i.classificacao_manual IS NOT NULL
                  AND TRIM(i.classificacao_manual) != ''
                ''',
                base_params,
            ).fetchone()
            out['com_classificacao'] = int(row['c']) if row else 0

            row = conn.execute(
                f'''
                SELECT COUNT(*) AS c FROM intimacoes i
                WHERE {where_sql}
                  AND EXISTS (SELECT 1 FROM analises a WHERE a.intimacao_id = i.id)
                ''',
                base_params,
            ).fetchone()
            analisadas = int(row['c']) if row else 0
            out['analisadas'] = analisadas
            out['pendentes'] = max(0, total - analisadas)

            for key, classe in (
                ('count_elaborar_peca', 'ELABORAR PEÇA'),
                ('count_urgencia', 'URGÊNCIA'),
                ('count_analisar_processo', 'ANALISAR PROCESSO'),
            ):
                row = conn.execute(
                    f'''
                    SELECT COUNT(*) AS c FROM intimacoes i
                    WHERE {where_sql} AND i.classificacao_manual = ?
                    ''',
                    base_params + [classe],
                ).fetchone()
                out[key] = int(row['c']) if row else 0
        return out

    def list_intimacoes_listagem_pagina(
        self,
        busca: str = '',
        classificacao: str = '',
        defensor: str = '',
        destacadas: str = '',
        ordenacao: str = 'data_desc',
        prompt_especifico: str = '',
        temperatura_especifica: str = '',
        pagina: int = 1,
        itens_por_pagina: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Lista uma página de intimações com filtros e ordenação no SQLite.
        Cada item inclui analises=[] (taxa na UI continua via API / JS).
        Chame stats_intimacoes_listagem / count_intimacoes_listagem para totais.
        """
        where_sql, where_params = self._montar_where_listagem_intimacoes(
            busca, classificacao, defensor, destacadas
        )
        order_sql, order_params = self._montar_order_listagem_intimacoes(
            ordenacao, prompt_especifico, temperatura_especifica
        )
        offset = max(0, (max(1, pagina) - 1) * max(1, itens_por_pagina))
        limit = max(1, itens_por_pagina)

        sql = (
            f'SELECT i.* FROM intimacoes i WHERE {where_sql} '
            f'ORDER BY {order_sql} LIMIT ? OFFSET ?'
        )
        qparams = list(where_params) + order_params + [limit, offset]

        with self.get_connection() as conn:
            cursor = conn.execute(sql, qparams)
            page: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                d = dict(row)
                self._normalizar_campos_bool_intimacao(d)
                d['analises'] = []
                page.append(d)
        return page
    
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
                # Converter smart_context de int para boolean
                if 'smart_context' in intimacao:
                    intimacao['smart_context'] = bool(intimacao['smart_context'])
                # Buscar análises desta intimação
                intimacao['analises'] = self.get_analises_by_intimacao(intimacao_id)
                return intimacao
            return None
    
    def get_id_por_intimacao_id_externo(self, intimacao_id_externo: str) -> Optional[str]:
        """Retorna o id interno (UUID) se já existir intimação com esse ID externo."""
        if not intimacao_id_externo or not str(intimacao_id_externo).strip():
            return None
        key = str(intimacao_id_externo).strip()
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT id FROM intimacoes WHERE intimacao_id_externo = ?',
                (key,),
            ).fetchone()
            return row[0] if row else None

    def save_intimacao(self, intimacao: Dict[str, Any]) -> str:
        """Salvar uma intimação"""
        with self.get_connection() as conn:
            # Gerar ID se não existir
            if 'id' not in intimacao or not intimacao['id']:
                intimacao['id'] = str(uuid.uuid4())
            
            # Data de criação
            if 'data_criacao' not in intimacao:
                intimacao['data_criacao'] = datetime.now().isoformat()

            ext_raw = intimacao.get('intimacao_id_externo')
            if ext_raw is not None and str(ext_raw).strip() != '':
                ext_key = str(ext_raw).strip()
                existing = conn.execute(
                    'SELECT id FROM intimacoes WHERE intimacao_id_externo = ? AND id != ?',
                    (ext_key, intimacao['id']),
                ).fetchone()
                if existing:
                    raise ValueError(
                        f'Já existe intimação com intimacaoId (externo) {ext_key!r}. '
                        f'ID interno existente: {existing[0]}.'
                    )
            
            # Inserir ou atualizar intimação (SEM salvar análises aninhadas)
            conn.execute('''
                INSERT OR REPLACE INTO intimacoes 
                (id, contexto, classificacao_manual, informacao_adicional, processo,
                 orgao_julgador, classe, disponibilizacao, intimado, status, prazo,
                 defensor, id_tarefa, cor_etiqueta, smart_context, data_criacao,
                 intimacao_id_externo, regras_usuario_prioridade_alta, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                1 if intimacao.get('smart_context', False) else 0,  # Converter boolean para int (0/1)
                intimacao['data_criacao'],
                (str(ext_raw).strip() if ext_raw is not None and str(ext_raw).strip() != '' else None),
                intimacao.get('regras_usuario_prioridade_alta') or '',
                intimacao.get('observacoes') or '',
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

    def _where_relatorios_analises(
        self,
        data_inicio: str = "",
        data_fim: str = "",
        prompt_id: str = "",
        classificacao_manual: str = "",
    ) -> Tuple[str, List[Any]]:
        clauses: List[str] = ["1=1"]
        params: List[Any] = []
        if data_inicio and str(data_inicio).strip():
            clauses.append("substr(a.data_analise, 1, 10) >= ?")
            params.append(str(data_inicio).strip())
        if data_fim and str(data_fim).strip():
            clauses.append("substr(a.data_analise, 1, 10) <= ?")
            params.append(str(data_fim).strip())
        if prompt_id and str(prompt_id).strip():
            clauses.append("a.prompt_id = ?")
            params.append(str(prompt_id).strip())
        if classificacao_manual and str(classificacao_manual).strip():
            clauses.append("i.classificacao_manual = ?")
            params.append(str(classificacao_manual).strip())
        return " AND ".join(clauses), params

    def contar_analises_relatorios_filtradas(
        self,
        data_inicio: str = "",
        data_fim: str = "",
        prompt_id: str = "",
        classificacao_manual: str = "",
    ) -> int:
        where_sql, params = self._where_relatorios_analises(
            data_inicio=data_inicio,
            data_fim=data_fim,
            prompt_id=prompt_id,
            classificacao_manual=classificacao_manual,
        )
        with self.get_connection() as conn:
            row = conn.execute(
                f"""
                SELECT COUNT(*) AS c
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                WHERE {where_sql}
                """,
                params,
            ).fetchone()
            return int(row["c"] if row else 0)

    def listar_analises_relatorios_paginadas(
        self,
        pagina: int = 1,
        itens_por_pagina: int = 10,
        data_inicio: str = "",
        data_fim: str = "",
        prompt_id: str = "",
        classificacao_manual: str = "",
    ) -> List[Dict[str, Any]]:
        where_sql, params = self._where_relatorios_analises(
            data_inicio=data_inicio,
            data_fim=data_fim,
            prompt_id=prompt_id,
            classificacao_manual=classificacao_manual,
        )
        page = max(1, int(pagina or 1))
        limit = max(1, int(itens_por_pagina or 10))
        offset = (page - 1) * limit
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT
                    a.id,
                    a.intimacao_id,
                    a.prompt_id,
                    COALESCE(a.prompt_nome, p.nome, '') AS prompt_nome,
                    a.data_analise,
                    a.resultado_ia,
                    a.acertou,
                    a.tempo_processamento,
                    a.modelo,
                    a.temperatura,
                    a.tokens_input,
                    a.tokens_output,
                    a.custo_real,
                    p.regra_negocio,
                    i.classificacao_manual,
                    i.informacao_adicional,
                    i.contexto,
                    i.processo,
                    i.orgao_julgador,
                    i.classe,
                    i.disponibilizacao,
                    i.intimado,
                    i.status,
                    i.prazo,
                    i.defensor,
                    i.regras_usuario_prioridade_alta,
                    i.observacoes,
                    COALESCE(i.destacada, 0) AS destacada
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                LEFT JOIN prompts p ON p.id = a.prompt_id
                WHERE {where_sql}
                ORDER BY a.data_analise DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            )
            return [dict(row) for row in cursor.fetchall()]

    def obter_agregados_relatorios_filtrados(
        self,
        data_inicio: str = "",
        data_fim: str = "",
        prompt_id: str = "",
        classificacao_manual: str = "",
    ) -> Dict[str, Any]:
        where_sql, params = self._where_relatorios_analises(
            data_inicio=data_inicio,
            data_fim=data_fim,
            prompt_id=prompt_id,
            classificacao_manual=classificacao_manual,
        )
        with self.get_connection() as conn:
            row_geral = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS total_analises,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) AS acertos,
                    COALESCE(SUM(COALESCE(a.tempo_processamento, 0.0)), 0.0) AS tempo_total,
                    COALESCE(SUM(COALESCE(a.custo_real, 0.0)), 0.0) AS custo_total,
                    SUM(
                        CASE WHEN substr(a.data_analise, 1, 10) = date('now', 'localtime')
                        THEN 1 ELSE 0 END
                    ) AS analises_hoje
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                WHERE {where_sql}
                """,
                params,
            ).fetchone()

            total_analises = int((row_geral["total_analises"] or 0) if row_geral else 0)
            acertos = int((row_geral["acertos"] or 0) if row_geral else 0)
            tempo_total = float((row_geral["tempo_total"] or 0.0) if row_geral else 0.0)
            custo_total = float((row_geral["custo_total"] or 0.0) if row_geral else 0.0)
            analises_hoje = int((row_geral["analises_hoje"] or 0) if row_geral else 0)

            dist_manual: Dict[str, int] = {}
            cur_manual = conn.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(COALESCE(i.classificacao_manual, '')), ''), 'Não classificado') AS label,
                    COUNT(*) AS c
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                WHERE {where_sql}
                GROUP BY 1
                ORDER BY c DESC
                """,
                params,
            )
            for r in cur_manual.fetchall():
                dist_manual[str(r["label"])] = int(r["c"])

            dist_ia: Dict[str, int] = {}
            cur_ia = conn.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(COALESCE(a.resultado_ia, '')), ''), 'Não classificado') AS label,
                    COUNT(*) AS c
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                WHERE {where_sql}
                GROUP BY 1
                ORDER BY c DESC
                """,
                params,
            )
            for r in cur_ia.fetchall():
                dist_ia[str(r["label"])] = int(r["c"])

            performance_prompts: Dict[str, Dict[str, Any]] = {}
            cur_perf = conn.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(COALESCE(a.prompt_nome, p.nome, '')), ''), 'Desconhecido') AS prompt_nome,
                    COUNT(*) AS total,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) AS acertos,
                    COALESCE(SUM(COALESCE(a.tempo_processamento, 0.0)), 0.0) AS tempo_total
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                LEFT JOIN prompts p ON p.id = a.prompt_id
                WHERE {where_sql}
                GROUP BY 1
                ORDER BY total DESC
                """,
                params,
            )
            for r in cur_perf.fetchall():
                nome = str(r["prompt_nome"])
                total = int(r["total"] or 0)
                ac = int(r["acertos"] or 0)
                t_total = float(r["tempo_total"] or 0.0)
                performance_prompts[nome] = {
                    "total": total,
                    "acertos": ac,
                    "tempo_total": t_total,
                    "acuracia": round((ac / total) * 100, 1) if total > 0 else 0,
                    "tempo_medio": round(t_total / total, 3) if total > 0 else 0,
                }

            meses_ordem = []
            cur_meses = conn.execute(
                f"""
                SELECT
                    substr(a.data_analise, 1, 7) AS mes_iso,
                    COUNT(*) AS total,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) AS acertos
                FROM analises a
                LEFT JOIN intimacoes i ON i.id = a.intimacao_id
                WHERE {where_sql}
                GROUP BY mes_iso
                ORDER BY mes_iso DESC
                LIMIT 6
                """,
                params,
            )
            meses_raw = [dict(r) for r in cur_meses.fetchall()]
            meses_raw.reverse()
            acuracia_labels: List[str] = []
            acuracia_data: List[float] = []
            for r in meses_raw:
                mes_iso = str(r.get("mes_iso") or "")
                if not mes_iso:
                    continue
                y, m = mes_iso.split("-")
                acuracia_labels.append(f"{m}/{y}")
                total_mes = int(r.get("total") or 0)
                ac_mes = int(r.get("acertos") or 0)
                acuracia_data.append(round((ac_mes / total_mes) * 100, 1) if total_mes > 0 else 0)
                meses_ordem.append(mes_iso)

            return {
                "total_analises": total_analises,
                "acertos": acertos,
                "tempo_total": tempo_total,
                "custo_total": custo_total,
                "analises_hoje": analises_hoje,
                "distribuicao_manual": dist_manual,
                "distribuicao_ia": dist_ia,
                "performance_prompts": performance_prompts,
                "dados_graficos": {
                    "acuracia_periodo": {"labels": acuracia_labels, "data": acuracia_data},
                    "classificacoes_manuais": {
                        "labels": list(dist_manual.keys()),
                        "data": list(dist_manual.values()),
                    },
                    "resultados_ia": {
                        "labels": list(dist_ia.keys()),
                        "data": list(dist_ia.values()),
                    },
                    "performance_prompts": {
                        "labels": list(performance_prompts.keys()),
                        "acuracia": [v["acuracia"] for v in performance_prompts.values()],
                        "usos": [v["total"] for v in performance_prompts.values()],
                    },
                },
            }

    def get_analise_prompt_resposta_completa_por_id(
        self,
        analise_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Busca prompt/resposta completos de uma análise específica para modal on-demand."""
        if not analise_id:
            return None
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    a.id,
                    a.intimacao_id,
                    a.prompt_completo,
                    a.resposta_completa
                FROM analises a
                WHERE a.id = ?
                LIMIT 1
                """,
                (analise_id,),
            ).fetchone()
            return dict(row) if row else None

    _REL_DIM_CLASSIFICACAO_MANUAL = "classificacao_manual"
    _REL_DIM_CLASSE_PROCESSUAL = "classe_processual"
    _REL_DIM_DEFENSOR = "defensor"
    _REL_DIM_SQL = {
        _REL_DIM_CLASSIFICACAO_MANUAL: (
            "COALESCE(NULLIF(TRIM(COALESCE(i.classificacao_manual, '')), ''), '(Sem classificação manual)')"
        ),
        _REL_DIM_CLASSE_PROCESSUAL: (
            "COALESCE(NULLIF(TRIM(COALESCE(i.classe, '')), ''), '(Sem classe)')"
        ),
        _REL_DIM_DEFENSOR: (
            "COALESCE(NULLIF(TRIM(COALESCE(i.defensor, '')), ''), "
            "NULLIF(TRIM(COALESCE(i.intimado, '')), ''), '(Sem defensor)')"
        ),
    }

    def _relatorio_intimacao_ids_com_analise_por_todos_prompts(
        self,
        conn: sqlite3.Connection,
        prompt_ids: List[str],
        data_inicio: str,
        data_fim: str,
        classificacao_manual_filtro: str,
    ) -> List[str]:
        """Intimações que possuem pelo menos uma linha em analises para cada prompt_id no recorte."""
        if len(prompt_ids) < 2:
            return []
        placeholders = ",".join("?" * len(prompt_ids))
        where = [f"a2.prompt_id IN ({placeholders})"]
        params: List[Any] = list(prompt_ids)
        if data_inicio and str(data_inicio).strip():
            where.append("a2.data_analise >= ?")
            params.append(str(data_inicio).strip())
        if data_fim and str(data_fim).strip():
            where.append("a2.data_analise <= ?")
            params.append(str(data_fim).strip())
        if classificacao_manual_filtro and str(classificacao_manual_filtro).strip():
            where.append("i2.classificacao_manual = ?")
            params.append(str(classificacao_manual_filtro).strip())
        where_sql = " AND ".join(where)
        sql = f"""
            SELECT a2.intimacao_id
            FROM analises a2
            INNER JOIN intimacoes i2 ON i2.id = a2.intimacao_id
            WHERE {where_sql}
            GROUP BY a2.intimacao_id
            HAVING COUNT(DISTINCT a2.prompt_id) = ?
        """
        params.append(len(prompt_ids))
        cursor = conn.execute(sql, params)
        return [str(row[0]) for row in cursor.fetchall()]

    def contar_intimacoes_cadastradas_agrupadas_por_dimensao_relatorio(
        self,
        dimensao: str,
        classificacao_manual_filtro: str = "",
    ) -> Dict[str, int]:
        """
        Conta intimações cadastradas por rótulo da dimensão (mesmas expressões SQL do relatório).
        Se classificacao_manual_filtro for informado, considera só intimações com essa classificação manual.
        """
        dim_key = (dimensao or "").strip()
        if dim_key not in self._REL_DIM_SQL:
            raise ValueError(
                "dimensao deve ser classificacao_manual, classe_processual ou defensor"
            )
        dim_expr = self._REL_DIM_SQL[dim_key]
        where_parts: List[str] = ["1=1"]
        params: List[Any] = []
        if classificacao_manual_filtro and str(classificacao_manual_filtro).strip():
            where_parts.append("i.classificacao_manual = ?")
            params.append(str(classificacao_manual_filtro).strip())
        where_sql = " AND ".join(where_parts)
        sql = f"""
            SELECT {dim_expr} AS dim_label, COUNT(*) AS c
            FROM intimacoes i
            WHERE {where_sql}
            GROUP BY {dim_expr}
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return {str(dict(row)["dim_label"]): int(dict(row)["c"]) for row in cursor.fetchall()}

    def listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
        self,
        prompt_ids: List[str],
        dimensao: str,
        data_inicio: str = "",
        data_fim: str = "",
        classificacao_manual_filtro: str = "",
        apenas_intimacoes_com_todos_prompts: bool = False,
        limite_amostra_pequena: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Agrega taxa de acerto por dimensão (rótulo da intimação) para cada prompt.
        Só entram análises com acertou avaliado (NOT NULL), alinhado ao serviço de sessão.
        Cada linha inclui total (n de análises) e total_intimacoes_distintas (COUNT DISTINCT).
        """
        ids = []
        seen = set()
        for pid in prompt_ids or []:
            if pid and str(pid).strip() and pid not in seen:
                seen.add(pid)
                ids.append(str(pid).strip())
        if not ids:
            return []

        dim_key = (dimensao or "").strip()
        if dim_key not in self._REL_DIM_SQL:
            raise ValueError(
                "dimensao deve ser classificacao_manual, classe_processual ou defensor"
            )

        dim_expr = self._REL_DIM_SQL[dim_key]
        apenas = bool(
            apenas_intimacoes_com_todos_prompts and len(ids) >= 2
        )

        placeholders = ",".join("?" * len(ids))
        where_parts = [
            f"a.prompt_id IN ({placeholders})",
            "a.acertou IS NOT NULL",
        ]
        params: List[Any] = list(ids)

        if data_inicio and str(data_inicio).strip():
            where_parts.append("a.data_analise >= ?")
            params.append(str(data_inicio).strip())
        if data_fim and str(data_fim).strip():
            where_parts.append("a.data_analise <= ?")
            params.append(str(data_fim).strip())
        if classificacao_manual_filtro and str(classificacao_manual_filtro).strip():
            where_parts.append("i.classificacao_manual = ?")
            params.append(str(classificacao_manual_filtro).strip())

        with self.get_connection() as conn:
            if apenas:
                comuns = self._relatorio_intimacao_ids_com_analise_por_todos_prompts(
                    conn,
                    ids,
                    str(data_inicio).strip() if data_inicio else "",
                    str(data_fim).strip() if data_fim else "",
                    str(classificacao_manual_filtro).strip()
                    if classificacao_manual_filtro
                    else "",
                )
                if not comuns:
                    out_empty: List[Dict[str, Any]] = []
                    for pid in ids:
                        row_n = conn.execute(
                            "SELECT nome FROM prompts WHERE id = ?", (pid,)
                        ).fetchone()
                        nome = row_n[0] if row_n else ""
                        out_empty.append(
                            {"prompt_id": pid, "prompt_nome": nome or "", "linhas": []}
                        )
                    return out_empty
                ic_place = ",".join("?" * len(comuns))
                where_parts.append(f"a.intimacao_id IN ({ic_place})")
                params.extend(comuns)

            where_sql = " AND ".join(where_parts)
            sql = f"""
                SELECT
                    a.prompt_id,
                    COALESCE(p.nome, '') AS prompt_nome,
                    {dim_expr} AS dim_label,
                    COUNT(*) AS total,
                    COUNT(DISTINCT a.intimacao_id) AS total_intimacoes_distintas,
                    SUM(CASE WHEN a.acertou = 1 THEN 1 ELSE 0 END) AS acertos
                FROM analises a
                INNER JOIN intimacoes i ON i.id = a.intimacao_id
                LEFT JOIN prompts p ON p.id = a.prompt_id
                WHERE {where_sql}
                GROUP BY a.prompt_id, p.nome, {dim_expr}
            """

            cursor = conn.execute(sql, params)
            by_prompt: Dict[str, Dict[str, Any]] = {}
            for row in cursor.fetchall():
                d = dict(row)
                pid = d["prompt_id"]
                if pid not in by_prompt:
                    by_prompt[pid] = {
                        "prompt_id": pid,
                        "prompt_nome": d.get("prompt_nome") or "",
                        "linhas": [],
                    }
                total = int(d["total"] or 0)
                ni = int(d["total_intimacoes_distintas"] or 0)
                acertos = int(d["acertos"] or 0)
                erros = total - acertos
                taxa = round(100.0 * acertos / total, 1) if total else 0.0
                by_prompt[pid]["linhas"].append(
                    {
                        "label": d["dim_label"],
                        "total": total,
                        "total_intimacoes_distintas": ni,
                        "acertos": acertos,
                        "erros": erros,
                        "taxa_pct": taxa,
                        "amostra_pequena": 0 < total < limite_amostra_pequena,
                    }
                )

            for pid in by_prompt:
                by_prompt[pid]["linhas"].sort(
                    key=lambda x: (-x["total"], x["label"])
                )

            result: List[Dict[str, Any]] = []
            for pid in ids:
                if pid in by_prompt:
                    result.append(by_prompt[pid])
                else:
                    row_n = conn.execute(
                        "SELECT nome FROM prompts WHERE id = ?", (pid,)
                    ).fetchone()
                    nome = row_n[0] if row_n else ""
                    result.append(
                        {"prompt_id": pid, "prompt_nome": nome or "", "linhas": []}
                    )
            return result

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
                 tokens_input, tokens_output, custo_real, prompt_completo, resposta_completa, session_id,
                 modo_avaliacao, tipo_alvo_focado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                analise.get('session_id', None),
                analise.get('modo_avaliacao', 'padrao'),
                analise.get('tipo_alvo_focado'),
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
            
            acuracia_pct = acuracia_geral * 100
            return {
                'total_intimacoes': intimacoes_count,
                'total_prompts': prompts_count,
                'total_analises': analises_count,
                'acuracia_geral': acuracia_pct,
                'taxa_acuracia_geral': acuracia_pct,
            }

    def get_dashboard_resumo_graficos(self) -> Dict[str, Any]:
        """
        Agregações só com SQL para o dashboard — evita carregar todas as intimações (contexto)
        e todas as análises na memória.
        """
        with self.get_connection() as conn:
            distribuicao: Dict[str, int] = {}
            cur = conn.execute(
                '''
                SELECT cls, COUNT(*) AS cnt
                FROM (
                    SELECT CASE
                        WHEN classificacao_manual IS NULL OR TRIM(classificacao_manual) = ''
                        THEN 'Não classificada'
                        ELSE TRIM(classificacao_manual)
                    END AS cls
                    FROM intimacoes
                )
                GROUP BY cls
                ORDER BY cnt DESC
                '''
            )
            for row in cur.fetchall():
                distribuicao[row['cls']] = row['cnt']

            total_analises = conn.execute('SELECT COUNT(*) AS c FROM analises').fetchone()['c']
            pendente = conn.execute(
                '''
                SELECT COUNT(*) AS c FROM intimacoes i
                WHERE NOT EXISTS (
                    SELECT 1 FROM analises a WHERE a.intimacao_id = i.id
                )
                '''
            ).fetchone()['c']

            return {
                'distribuicao_classificacao': distribuicao,
                'status_analises': {
                    'Pendente': pendente,
                    'Concluída': total_analises,
                    'Erro': 0,
                },
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
                           acuracia_min: str = None,
                           modo_avaliacao_filtro: str = None) -> List[Dict[str, Any]]:
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

            sql_modo = _sql_filtro_modo_avaliacao_sessao(modo_avaliacao_filtro)
            if sql_modo:
                where_conditions.append(f"({sql_modo})")
            
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

                cfg = sessao['configuracoes']
                if isinstance(cfg, dict):
                    raw_modo = cfg.get('modo_avaliacao') or 'padrao'
                    modo = str(raw_modo).strip().lower()
                    if modo not in ('padrao', 'focado'):
                        modo = 'padrao'
                    alvo = cfg.get('tipo_alvo_focado')
                    sessao['modo_avaliacao'] = modo
                    sessao['tipo_alvo_focado'] = alvo if modo == 'focado' else None
                    if modo == 'focado' and alvo:
                        sessao['modo_teste_rotulo'] = f'Focado: {alvo}'
                    else:
                        sessao['modo_teste_rotulo'] = 'Padrão'
                else:
                    sessao['modo_avaliacao'] = 'padrao'
                    sessao['tipo_alvo_focado'] = None
                    sessao['modo_teste_rotulo'] = 'Padrão'
                
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

    # Métodos para cadastro administrativo de defensores
    def seed_defensores(self, nomes: List[str]) -> int:
        """Garante que uma lista de defensores exista no cadastro"""
        inseridos = 0
        if not nomes:
            return inseridos

        with self.get_connection() as conn:
            for nome in nomes:
                nome_limpo = (nome or '').strip()
                if not nome_limpo:
                    continue

                cursor = conn.execute(
                    'SELECT id FROM defensores WHERE LOWER(nome) = LOWER(?)',
                    (nome_limpo,),
                )
                if cursor.fetchone():
                    continue

                conn.execute(
                    '''
                    INSERT INTO defensores (id, nome, ativo, data_criacao)
                    VALUES (?, ?, 1, ?)
                    ''',
                    (str(uuid.uuid4()), nome_limpo, datetime.now().isoformat()),
                )
                inseridos += 1

            conn.commit()

        return inseridos

    def get_defensores_cadastrados(self, incluir_inativos: bool = False) -> List[Dict[str, Any]]:
        """Lista defensores cadastrados"""
        with self.get_connection() as conn:
            query = 'SELECT id, nome, ativo, data_criacao FROM defensores'
            params: List[Any] = []
            if not incluir_inativos:
                query += ' WHERE ativo = 1'
            query += ' ORDER BY nome'

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_nomes_defensores_cadastrados(self, incluir_inativos: bool = False) -> List[str]:
        """Lista somente os nomes dos defensores cadastrados"""
        defensores = self.get_defensores_cadastrados(incluir_inativos=incluir_inativos)
        return [d.get('nome') for d in defensores if d.get('nome')]

    def criar_defensor(self, nome: str) -> Dict[str, Any]:
        """Cria um novo defensor"""
        nome_limpo = (nome or '').strip()
        if not nome_limpo:
            raise ValueError('Nome do defensor é obrigatório.')

        with self.get_connection() as conn:
            existente = conn.execute(
                'SELECT id FROM defensores WHERE LOWER(nome) = LOWER(?)',
                (nome_limpo,),
            ).fetchone()
            if existente:
                raise ValueError('Já existe um defensor com esse nome.')

            defensor = {
                'id': str(uuid.uuid4()),
                'nome': nome_limpo,
                'ativo': 1,
                'data_criacao': datetime.now().isoformat(),
            }
            conn.execute(
                '''
                INSERT INTO defensores (id, nome, ativo, data_criacao)
                VALUES (?, ?, ?, ?)
                ''',
                (defensor['id'], defensor['nome'], defensor['ativo'], defensor['data_criacao']),
            )
            conn.commit()
            return defensor

    def atualizar_defensor(self, defensor_id: str, nome: str) -> Dict[str, Any]:
        """Atualiza o nome de um defensor e propaga para intimações"""
        nome_limpo = (nome or '').strip()
        if not nome_limpo:
            raise ValueError('Nome do defensor é obrigatório.')

        with self.get_connection() as conn:
            atual = conn.execute(
                'SELECT id, nome, ativo, data_criacao FROM defensores WHERE id = ?',
                (defensor_id,),
            ).fetchone()
            if not atual:
                raise ValueError('Defensor não encontrado.')

            duplicado = conn.execute(
                'SELECT id FROM defensores WHERE LOWER(nome) = LOWER(?) AND id != ?',
                (nome_limpo, defensor_id),
            ).fetchone()
            if duplicado:
                raise ValueError('Já existe um defensor com esse nome.')

            nome_anterior = atual['nome']
            conn.execute('UPDATE defensores SET nome = ? WHERE id = ?', (nome_limpo, defensor_id))
            conn.execute('UPDATE intimacoes SET defensor = ? WHERE defensor = ?', (nome_limpo, nome_anterior))
            conn.commit()

            return {
                'id': atual['id'],
                'nome': nome_limpo,
                'ativo': atual['ativo'],
                'data_criacao': atual['data_criacao'],
            }

    def definir_status_defensor(self, defensor_id: str, ativo: bool) -> None:
        """Ativa ou inativa defensor"""
        with self.get_connection() as conn:
            cursor = conn.execute('UPDATE defensores SET ativo = ? WHERE id = ?', (1 if ativo else 0, defensor_id))
            if cursor.rowcount == 0:
                raise ValueError('Defensor não encontrado.')
            conn.commit()

    def excluir_defensor(self, defensor_id: str) -> None:
        """Exclui defensor se não houver uso em intimações"""
        with self.get_connection() as conn:
            defensor = conn.execute(
                'SELECT id, nome FROM defensores WHERE id = ?',
                (defensor_id,),
            ).fetchone()
            if not defensor:
                raise ValueError('Defensor não encontrado.')

            total_usos = conn.execute(
                'SELECT COUNT(*) FROM intimacoes WHERE defensor = ?',
                (defensor['nome'],),
            ).fetchone()[0]
            if total_usos > 0:
                raise ValueError('Não é possível excluir: defensor já utilizado em intimações.')

            conn.execute('DELETE FROM defensores WHERE id = ?', (defensor_id,))
            conn.commit()
    
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

    def get_areas(self) -> List[Dict[str, Any]]:
        """Lista áreas ordenadas (para UI e filtros)."""
        with self.get_connection() as conn:
            cur = conn.execute(
                'SELECT id, nome, ordem FROM areas ORDER BY ordem ASC, nome ASC'
            )
            return [dict(row) for row in cur.fetchall()]

    def get_mapeamento_classe_para_area(self) -> Dict[str, Dict[str, str]]:
        """Match exato classe (string da intimação) → {id, nome} da área."""
        with self.get_connection() as conn:
            cur = conn.execute(
                '''
                SELECT ac.classe AS classe, a.id AS area_id, a.nome AS area_nome
                FROM area_classe ac
                INNER JOIN areas a ON a.id = ac.area_id
                '''
            )
            out: Dict[str, Dict[str, str]] = {}
            for row in cur.fetchall():
                r = dict(row)
                out[r['classe']] = {'id': r['area_id'], 'nome': r['area_nome']}
            return out

    def get_mapeamento_classe_para_area_id(self) -> Dict[str, str]:
        """classe → area_id (para formulário de configurações)."""
        with self.get_connection() as conn:
            cur = conn.execute('SELECT classe, area_id FROM area_classe')
            return {dict(row)['classe']: dict(row)['area_id'] for row in cur.fetchall()}

    def replace_mapeamento_classes_areas(self, mapeamento: Dict[str, Optional[str]]) -> None:
        """Substitui todo o mapeamento. Valores vazios/nulos = classe sem área."""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM area_classe')
            for classe, area_id in mapeamento.items():
                if classe is None or not str(classe).strip():
                    continue
                cl = str(classe).strip()
                aid = (area_id or '').strip() if area_id is not None else ''
                if not aid:
                    continue
                ok = conn.execute(
                    'SELECT 1 FROM areas WHERE id = ?', (aid,)
                ).fetchone()
                if not ok:
                    raise ValueError(f'Área inválida: {aid!r}')
                conn.execute(
                    'INSERT INTO area_classe (classe, area_id) VALUES (?, ?)',
                    (cl, aid),
                )
            conn.commit()
    
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
    
    def _modelo_historico_acuracia_a_partir_de_analises(
        self,
        conn,
        prompt_id: str,
        session_id: Optional[str],
        modelo_param: str,
    ) -> str:
        """
        Prefere o modelo registrado em `analises` da sessão (fonte do que de fato rodou).
        Vários modelos distintos na mesma sessão viram rótulo estável ordenado, ex.: "a, b".
        Se não houver linhas com modelo, usa o parâmetro `modelo_param`.
        """
        param = (modelo_param or "").strip()
        if not session_id or not str(session_id).strip():
            return param
        sid = str(session_id).strip()
        pid = str(prompt_id).strip()
        cur = conn.execute(
            """
            SELECT DISTINCT TRIM(modelo) AS m
            FROM analises
            WHERE session_id = ? AND prompt_id = ?
              AND modelo IS NOT NULL AND TRIM(modelo) != ''
            """,
            (sid, pid),
        )
        vals = sorted(
            {
                str(r[0]).strip()
                for r in cur.fetchall()
                if r[0] is not None and str(r[0]).strip()
            }
        )
        if len(vals) == 1:
            return vals[0]
        if len(vals) > 1:
            return ", ".join(vals)
        try:
            cur_sess = conn.execute(
                """
                SELECT TRIM(modelo) FROM sessoes_analise
                WHERE session_id = ?
                  AND modelo IS NOT NULL AND TRIM(modelo) != ''
                LIMIT 1
                """,
                (sid,),
            )
            row_sess = cur_sess.fetchone()
            if row_sess and row_sess[0] and str(row_sess[0]).strip():
                return str(row_sess[0]).strip()
        except Exception:
            pass
        return param

    def salvar_historico_acuracia(self, prompt_id: str, numero_intimacoes: int, temperatura: float,
                                 acuracia: float, session_id: str = None, modelo: str = "") -> bool:
        """Salvar histórico de acurácia de um prompt.

        O campo `modelo` gravado prioriza valores distintos em `analises` da mesma
        `session_id` e `prompt_id`; se não houver, usa o argumento `modelo`.
        """
        try:
            with self.get_connection() as conn:
                historico_id = str(uuid.uuid4())
                data_analise = datetime.now().isoformat()
                modelo_final = self._modelo_historico_acuracia_a_partir_de_analises(
                    conn, prompt_id, session_id, modelo
                )

                conn.execute('''
                    INSERT INTO historico_acuracia 
                    (id, prompt_id, numero_intimacoes, modelo, temperatura, acuracia, data_analise, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    historico_id,
                    prompt_id,
                    numero_intimacoes,
                    modelo_final,
                    temperatura,
                    acuracia,
                    data_analise,
                    session_id,
                ))
                
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
                        h.prompt_id,
                        h.numero_intimacoes,
                        COALESCE(
                            NULLIF(TRIM(h.modelo), ''),
                            NULLIF(TRIM(s.modelo), ''),
                            NULLIF(TRIM((
                                SELECT a.modelo FROM analises a
                                WHERE a.session_id = h.session_id AND a.prompt_id = h.prompt_id
                                  AND a.modelo IS NOT NULL AND TRIM(a.modelo) != ''
                                ORDER BY a.data_analise DESC LIMIT 1
                            )), ''),
                            'N/D'
                        ) AS modelo,
                        h.temperatura,
                        COUNT(*) as total_analises,
                        AVG(h.acuracia) as acuracia_media,
                        MIN(h.acuracia) as acuracia_minima,
                        MAX(h.acuracia) as acuracia_maxima,
                        MIN(h.data_analise) as primeira_analise,
                        MAX(h.data_analise) as ultima_analise
                    FROM historico_acuracia h
                    LEFT JOIN sessoes_analise s ON s.session_id = h.session_id
                    WHERE h.prompt_id = ?
                    GROUP BY 1, 2, 3, 4
                    ORDER BY h.numero_intimacoes DESC, h.temperatura ASC, modelo ASC, ultima_analise DESC
                ''', (prompt_id,))
                
                result = []
                for row in cursor.fetchall():
                    result.append({
                        'prompt_id': row[0],
                        'numero_intimacoes': row[1],
                        'modelo': row[2],
                        'temperatura': row[3],
                        'total_analises': row[4],
                        'acuracia_media': round(row[5], 2),
                        'acuracia_minima': round(row[6], 2),
                        'acuracia_maxima': round(row[7], 2),
                        'primeira_analise': row[8],
                        'ultima_analise': row[9]
                    })
                
                return result
        except Exception as e:
            print(f"Erro ao obter histórico de acurácia: {e}")
            return []

    def get_historico_acuracia_prompt_multi(
        self, prompt_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Histórico de acurácia para vários prompts (uma consulta por id; uso em batch HTTP)."""
        out: Dict[str, List[Dict[str, Any]]] = {}
        seen = set()
        for pid in prompt_ids:
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out[pid] = self.get_historico_acuracia_prompt(pid)
        return out

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
                                 acuracia_min: str = None,
                                 modo_avaliacao_filtro: str = None) -> int:
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

            sql_modo = _sql_filtro_modo_avaliacao_sessao(modo_avaliacao_filtro)
            if sql_modo:
                where_conditions.append(f"({sql_modo})")
            
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
                    i.classe,
                    i.defensor,
                    i.informacao_adicional,
                    i.intimado,
                    i.status as status_intimacao,
                    i.destacada,
                    i.regras_usuario_prioridade_alta,
                    i.observacoes,
                    -- Estatísticas do prompt para esta intimação específica
                    (SELECT COUNT(*) FROM analises a2 WHERE a2.prompt_id = a.prompt_id AND a2.intimacao_id = a.intimacao_id) as total_testes_intimacao,
                    (SELECT COUNT(*) FROM analises a3 WHERE a3.prompt_id = a.prompt_id AND a3.intimacao_id = a.intimacao_id AND a3.acertou = 1) as acertos_intimacao,
                    -- Estatísticas gerais do prompt
                    (SELECT COUNT(*) FROM analises a4 WHERE a4.prompt_id = a.prompt_id) as total_testes_prompt,
                    (SELECT COUNT(*) FROM analises a5 WHERE a5.prompt_id = a.prompt_id AND a5.acertou = 1) as acertos_prompt
                FROM analises a
                LEFT JOIN intimacoes i ON a.intimacao_id = i.id
                WHERE a.session_id = ?
                ORDER BY COALESCE(i.destacada, 0) DESC, a.data_analise DESC
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

    def list_prompt_templates(self) -> List[Dict[str, Any]]:
        """Lista templates para a página Novo prompt (ordem, depois nome)."""
        with self.get_connection() as conn:
            _seed_prompt_templates_padrao_sqlite(conn)
            conn.commit()
            cur = conn.execute(
                '''
                SELECT id, nome, descricao, conteudo, ordem, data_criacao, data_atualizacao
                FROM prompt_templates
                ORDER BY ordem ASC, nome COLLATE NOCASE ASC
                '''
            )
            return [dict(row) for row in cur.fetchall()]

    def get_prompt_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                '''
                SELECT id, nome, descricao, conteudo, ordem, data_criacao, data_atualizacao
                FROM prompt_templates WHERE id = ?
                ''',
                (template_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def save_prompt_template(self, data: Dict[str, Any]) -> str:
        """Cria ou atualiza template. Exige {CONTEXTO} no corpo."""
        nome = (data.get('nome') or '').strip()
        conteudo = (data.get('conteudo') or '').strip()
        if not nome:
            raise ValueError('Nome do template é obrigatório.')
        if not conteudo:
            raise ValueError('Conteúdo do template é obrigatório.')
        if '{CONTEXTO}' not in conteudo:
            raise ValueError('O conteúdo deve conter a variável {CONTEXTO}.')
        descricao = (data.get('descricao') or '').strip() or None
        try:
            ordem = int(data.get('ordem', 0))
        except (TypeError, ValueError):
            ordem = 0
        now = datetime.now().isoformat()
        tid = (data.get('id') or '').strip()
        with self.get_connection() as conn:
            if tid:
                existing = conn.execute(
                    'SELECT id FROM prompt_templates WHERE id = ?', (tid,)
                ).fetchone()
                if not existing:
                    raise ValueError('Template não encontrado.')
                conn.execute(
                    '''
                    UPDATE prompt_templates
                    SET nome = ?, descricao = ?, conteudo = ?, ordem = ?, data_atualizacao = ?
                    WHERE id = ?
                    ''',
                    (nome, descricao, conteudo, ordem, now, tid),
                )
                conn.commit()
                return tid
            new_id = str(uuid.uuid4())
            conn.execute(
                '''
                INSERT INTO prompt_templates (id, nome, descricao, conteudo, ordem, data_criacao, data_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (new_id, nome, descricao, conteudo, ordem, now, now),
            )
            conn.commit()
            return new_id

    def delete_prompt_template(self, template_id: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute('DELETE FROM prompt_templates WHERE id = ?', (template_id,))
            conn.commit()
            return cur.rowcount > 0
