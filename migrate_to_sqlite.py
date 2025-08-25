#!/usr/bin/env python3
"""
Script para migrar dados JSON para SQLite
Execute: python migrate_to_sqlite.py
"""

import json
import os
from datetime import datetime
from services.sqlite_service import SQLiteService

def migrate_data():
    """Migrar todos os dados JSON para SQLite"""
    print("🚀 Iniciando migração JSON → SQLite...")
    
    # Inicializar serviço SQLite
    sqlite_service = SQLiteService()
    print("✅ Banco SQLite criado/conectado")
    
    # Caminhos dos arquivos JSON
    data_dir = 'data'
    intimacoes_file = os.path.join(data_dir, 'intimacoes.json')
    prompts_file = os.path.join(data_dir, 'prompts.json')
    analises_file = os.path.join(data_dir, 'analises.json')
    
    # Contadores
    total_intimacoes = 0
    total_prompts = 0
    total_analises = 0
    
    # 1. Migrar Intimações
    print("\n📋 Migrando intimações...")
    try:
        with open(intimacoes_file, 'r', encoding='utf-8') as f:
            intimacoes_data = json.load(f)
        
        for intimacao in intimacoes_data.get('intimacoes', []):
            # Extrair análises antes de salvar intimação
            analises = intimacao.pop('analises', [])
            
            # Salvar intimação
            intimacao_id = sqlite_service.save_intimacao(intimacao)
            total_intimacoes += 1
            
            # Salvar análises desta intimação
            for analise in analises:
                analise['intimacao_id'] = intimacao_id
                sqlite_service.save_analise(analise)
                total_analises += 1
        
        print(f"✅ {total_intimacoes} intimações migradas")
        print(f"✅ {total_analises} análises das intimações migradas")
        
    except FileNotFoundError:
        print("⚠️  Arquivo intimacoes.json não encontrado")
    except Exception as e:
        print(f"❌ Erro ao migrar intimações: {e}")
    
    # 2. Migrar Prompts (e extrair análises do historico_uso)
    print("\n🤖 Migrando prompts...")
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        for prompt in prompts_data.get('prompts', []):
            # Extrair histórico de uso (que são na verdade análises!)
            historico_uso = prompt.pop('historico_uso', [])
            
            # Salvar prompt limpo (sem o histórico gigante)
            prompt_id = sqlite_service.save_prompt(prompt)
            total_prompts += 1
            
            # Migrar análises do histórico de uso
            print(f"   📊 Migrando {len(historico_uso)} análises do prompt '{prompt.get('nome', 'sem nome')}'...")
            for analise in historico_uso:
                # Mapear campos do historico_uso para estrutura de análise
                analise_normalizada = {
                    'id': analise.get('id'),
                    'prompt_id': prompt_id,
                    'prompt_nome': prompt.get('nome', ''),
                    'data_analise': analise.get('data_analise'),
                    'resultado_ia': analise.get('resultado_ia'),
                    'acertou': analise.get('acertou', False),
                    'tempo_processamento': analise.get('tempo_processamento', 0.0),
                    'modelo': analise.get('modelo', ''),
                    'temperatura': analise.get('temperatura', 0.0),
                    'tokens_usados': analise.get('tokens_usados', 0),
                    'tokens_input': analise.get('tokens_input', 0),
                    'tokens_output': analise.get('tokens_output', 0),
                    'custo_real': analise.get('custo_real', 0.0),
                    'prompt_completo': analise.get('prompt_completo', ''),
                    'resposta_completa': analise.get('resposta_completa', ''),
                    'intimacao_id': analise.get('intimacao_id', '')  # Pode estar vazio
                }
                
                sqlite_service.save_analise(analise_normalizada)
                total_analises += 1
            
            # Atualizar estatísticas do prompt
            sqlite_service.update_prompt_statistics(prompt_id)
        
        print(f"✅ {total_prompts} prompts migrados")
        
    except FileNotFoundError:
        print("⚠️  Arquivo prompts.json não encontrado")
    except Exception as e:
        print(f"❌ Erro ao migrar prompts: {e}")
    
    # 3. Migrar Análises avulsas (se existir arquivo separado)
    print("\n📊 Migrando análises avulsas...")
    try:
        with open(analises_file, 'r', encoding='utf-8') as f:
            analises_data = json.load(f)
        
        analises_avulsas = 0
        for analise in analises_data.get('analises', []):
            sqlite_service.save_analise(analise)
            analises_avulsas += 1
            total_analises += 1
        
        print(f"✅ {analises_avulsas} análises avulsas migradas")
        
    except FileNotFoundError:
        print("⚠️  Arquivo analises.json não encontrado")
    except Exception as e:
        print(f"❌ Erro ao migrar análises: {e}")
    
    # 4. Resumo final
    print(f"\n🎉 MIGRAÇÃO CONCLUÍDA!")
    print(f"📋 Total de intimações: {total_intimacoes}")
    print(f"🤖 Total de prompts: {total_prompts}")
    print(f"📊 Total de análises: {total_analises}")
    
    # 5. Verificar integridade
    print(f"\n🔍 Verificando integridade...")
    stats = sqlite_service.get_statistics()
    print(f"✅ Intimações no banco: {stats['total_intimacoes']}")
    print(f"✅ Prompts no banco: {stats['total_prompts']}")
    print(f"✅ Análises no banco: {stats['total_analises']}")
    print(f"✅ Acurácia geral: {stats['acuracia_geral']:.1f}%")
    
    # 6. Informações sobre o banco
    db_path = sqlite_service.db_path
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
        print(f"\n💾 Banco SQLite criado: {db_path}")
        print(f"💾 Tamanho do banco: {db_size / 1024:.1f} KB")
        
        # Comparar com tamanhos dos arquivos JSON
        json_size = 0
        for file in [intimacoes_file, prompts_file, analises_file]:
            if os.path.exists(file):
                json_size += os.path.getsize(file)
        
        print(f"📄 Tamanho total dos JSONs: {json_size / 1024:.1f} KB")
        print(f"🚀 Economia de espaço: {((json_size - db_size) / json_size * 100):.1f}%")

if __name__ == "__main__":
    migrate_data()

