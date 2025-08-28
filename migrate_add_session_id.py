#!/usr/bin/env python3
"""
Script para adicionar a coluna session_id à tabela analises
Execute: python migrate_add_session_id.py
"""

import sqlite3
import os

def migrate_add_session_id():
    """Adicionar coluna session_id à tabela analises"""
    print("🔧 Iniciando migração para adicionar session_id...")
    
    # Caminho do banco
    db_path = os.path.join('data', 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(analises)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'session_id' in columns:
            print("✅ Coluna session_id já existe!")
            return
        
        print("📋 Adicionando coluna session_id...")
        
        # Adicionar a coluna session_id
        cursor.execute('ALTER TABLE analises ADD COLUMN session_id TEXT')
        
        # Criar índice para a nova coluna
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analises_session ON analises(session_id)')
        
        # Verificar se a tabela sessoes_analise existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessoes_analise'")
        if not cursor.fetchone():
            print("📋 Criando tabela sessoes_analise...")
            
            # Criar tabela de sessões de análise
            cursor.execute('''
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
            
            # Criar índices para a tabela de sessões
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessoes_data ON sessoes_analise(data_inicio)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessoes_prompt ON sessoes_analise(prompt_id)')
        
        # Commit das mudanças
        conn.commit()
        
        print("✅ Migração concluída com sucesso!")
        print(f"📊 Coluna session_id adicionada à tabela analises")
        print(f"📊 Tabela sessoes_analise criada/verificada")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_session_id()

