#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Recuperação de Análises Perdidas

Este script permite recuperar análises que foram perdidas de intimações específicas,
restaurando-as a partir do backup mais recente.

Autor: Assistente IA
Data: 2025-01-28
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

def carregar_json(caminho_arquivo: str) -> Dict:
    """Carrega um arquivo JSON e retorna seu conteúdo."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON em {caminho_arquivo}: {e}")
        return {}

def salvar_json(dados: Dict, caminho_arquivo: str) -> bool:
    """Salva dados em um arquivo JSON."""
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo {caminho_arquivo}: {e}")
        return False

def criar_backup_atual():
    """Cria um backup do estado atual antes da recuperação."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"data/backups/{timestamp}_intimacoes_antes_recuperacao_analises.json"
    
    try:
        shutil.copy2("data/intimacoes.json", nome_backup)
        print(f"✅ Backup criado: {nome_backup}")
        return nome_backup
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None

def obter_backup_mais_recente() -> str:
    """Encontra o backup mais recente de intimações."""
    pasta_backups = "data/backups"
    arquivos_backup = []
    
    if not os.path.exists(pasta_backups):
        print(f"❌ Pasta de backups não encontrada: {pasta_backups}")
        return ""
    
    for arquivo in os.listdir(pasta_backups):
        if arquivo.endswith("_intimacoes.json") and "antes_recuperacao_analises" not in arquivo:
            caminho_completo = os.path.join(pasta_backups, arquivo)
            timestamp = os.path.getmtime(caminho_completo)
            arquivos_backup.append((arquivo, timestamp, caminho_completo))
    
    if not arquivos_backup:
        print("❌ Nenhum backup de intimações encontrado")
        return ""
    
    # Ordena por timestamp (mais recente primeiro)
    arquivos_backup.sort(key=lambda x: x[1], reverse=True)
    backup_mais_recente = arquivos_backup[0]
    
    print(f"📁 Usando backup: {backup_mais_recente[0]}")
    return backup_mais_recente[2]

def encontrar_intimacao_por_id(dados: Dict, id_intimacao: str) -> Optional[Dict]:
    """Encontra uma intimação específica pelo ID."""
    if 'intimacoes' not in dados:
        return None
    
    for intimacao in dados['intimacoes']:
        if intimacao.get('id') == id_intimacao:
            return intimacao
    
    return None

def recuperar_analises_perdidas(id_intimacao: str = None):
    """Recupera análises perdidas de uma intimação específica ou de todas."""
    print("🔄 RECUPERAÇÃO DE ANÁLISES PERDIDAS")
    print("=" * 50)
    
    # Criar backup do estado atual
    backup_atual = criar_backup_atual()
    if not backup_atual:
        print("❌ Não foi possível criar backup. Operação cancelada.")
        return False
    
    # Carregar dados atuais
    dados_atuais = carregar_json("data/intimacoes.json")
    if not dados_atuais:
        print("❌ Não foi possível carregar dados atuais")
        return False
    
    # Carregar backup mais recente
    caminho_backup = obter_backup_mais_recente()
    if not caminho_backup:
        return False
    
    dados_backup = carregar_json(caminho_backup)
    if not dados_backup:
        print("❌ Não foi possível carregar dados do backup")
        return False
    
    # Processar recuperação
    intimacoes_processadas = 0
    analises_recuperadas = 0
    
    for i, intimacao_atual in enumerate(dados_atuais.get('intimacoes', [])):
        id_atual = intimacao_atual.get('id')
        
        # Se foi especificado um ID, processar apenas essa intimação
        if id_intimacao and id_atual != id_intimacao:
            continue
        
        # Encontrar a intimação correspondente no backup
        intimacao_backup = encontrar_intimacao_por_id(dados_backup, id_atual)
        if not intimacao_backup:
            continue
        
        # Comparar análises
        analises_atuais = intimacao_atual.get('analises', [])
        analises_backup = intimacao_backup.get('analises', [])
        
        if len(analises_backup) > len(analises_atuais):
            print(f"\n📋 Processando intimação: {intimacao_atual.get('processo', 'N/A')}")
            print(f"   ID: {id_atual}")
            print(f"   Análises atuais: {len(analises_atuais)}")
            print(f"   Análises no backup: {len(analises_backup)}")
            
            # Recuperar análises perdidas
            analises_perdidas = len(analises_backup) - len(analises_atuais)
            
            # Verificar se as análises atuais são um subconjunto das do backup
            ids_atuais = {analise.get('id') for analise in analises_atuais if analise.get('id')}
            analises_para_recuperar = []
            
            for analise_backup in analises_backup:
                if analise_backup.get('id') not in ids_atuais:
                    analises_para_recuperar.append(analise_backup)
            
            if analises_para_recuperar:
                # Adicionar análises recuperadas
                dados_atuais['intimacoes'][i]['analises'].extend(analises_para_recuperar)
                analises_recuperadas += len(analises_para_recuperar)
                
                print(f"   ✅ Recuperadas {len(analises_para_recuperar)} análises")
                
                for analise in analises_para_recuperar:
                    print(f"      • Análise ID: {analise.get('id', 'N/A')}")
                    print(f"        Data: {analise.get('data_analise', 'N/A')}")
                    print(f"        Resultado: {analise.get('resultado_ia', 'N/A')}")
            
            intimacoes_processadas += 1
    
    if analises_recuperadas > 0:
        # Salvar dados atualizados
        if salvar_json(dados_atuais, "data/intimacoes.json"):
            print(f"\n✅ RECUPERAÇÃO CONCLUÍDA:")
            print(f"   • Intimações processadas: {intimacoes_processadas}")
            print(f"   • Análises recuperadas: {analises_recuperadas}")
            print(f"   • Backup criado em: {backup_atual}")
            return True
        else:
            print("❌ Erro ao salvar dados recuperados")
            return False
    else:
        print("\nℹ️  Nenhuma análise perdida foi encontrada para recuperar.")
        # Remover backup desnecessário
        try:
            os.remove(backup_atual)
            print("🗑️  Backup desnecessário removido.")
        except:
            pass
        return True

def main():
    """Função principal."""
    print("🔄 SCRIPT DE RECUPERAÇÃO DE ANÁLISES PERDIDAS")
    print("=" * 60)
    print()
    
    # Verificar se há análises para recuperar
    print("Verificando se há análises perdidas...")
    
    try:
        # Executar recuperação
        sucesso = recuperar_analises_perdidas()
        
        if sucesso:
            print("\n🎉 Processo de recuperação finalizado com sucesso!")
        else:
            print("\n❌ Processo de recuperação falhou.")
            
    except Exception as e:
        print(f"❌ Erro durante a recuperação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()