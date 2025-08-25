#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Verificação de Perda de Intimações

Este script compara o estado atual das intimações com o backup mais recente
para identificar se houve perda de dados após operações de exclusão.

Autor: Assistente IA
Data: 2025-01-28
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set

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

def obter_backup_mais_recente() -> str:
    """Encontra o backup mais recente de intimações."""
    pasta_backups = "data/backups"
    arquivos_backup = []
    
    if not os.path.exists(pasta_backups):
        print(f"❌ Pasta de backups não encontrada: {pasta_backups}")
        return ""
    
    for arquivo in os.listdir(pasta_backups):
        if arquivo.endswith("_intimacoes.json"):
            caminho_completo = os.path.join(pasta_backups, arquivo)
            timestamp = os.path.getmtime(caminho_completo)
            arquivos_backup.append((arquivo, timestamp, caminho_completo))
    
    if not arquivos_backup:
        print("❌ Nenhum backup de intimações encontrado")
        return ""
    
    # Ordena por timestamp (mais recente primeiro)
    arquivos_backup.sort(key=lambda x: x[1], reverse=True)
    backup_mais_recente = arquivos_backup[0]
    
    print(f"📁 Backup mais recente: {backup_mais_recente[0]}")
    return backup_mais_recente[2]

def extrair_ids_intimacoes(dados: Dict) -> Set[str]:
    """Extrai os IDs de todas as intimações dos dados."""
    if 'intimacoes' not in dados:
        return set()
    
    return {intimacao.get('id', '') for intimacao in dados['intimacoes'] if intimacao.get('id')}

def extrair_detalhes_intimacoes(dados: Dict) -> Dict[str, Dict]:
    """Extrai detalhes das intimações indexados por ID."""
    detalhes = {}
    
    if 'intimacoes' not in dados:
        return detalhes
    
    for intimacao in dados['intimacoes']:
        if intimacao.get('id'):
            detalhes[intimacao['id']] = {
                'processo': intimacao.get('processo', 'N/A'),
                'intimado': intimacao.get('intimado', 'N/A'),
                'classe': intimacao.get('classe', 'N/A'),
                'data_criacao': intimacao.get('data_criacao', 'N/A'),
                'num_analises': len(intimacao.get('analises', []))
            }
    
    return detalhes

def comparar_intimacoes():
    """Compara o estado atual das intimações com o backup mais recente."""
    print("🔍 VERIFICAÇÃO DE PERDA DE INTIMAÇÕES")
    print("=" * 50)
    
    # Carregar dados atuais
    dados_atuais = carregar_json("data/intimacoes.json")
    ids_atuais = extrair_ids_intimacoes(dados_atuais)
    detalhes_atuais = extrair_detalhes_intimacoes(dados_atuais)
    
    print(f"📊 Intimações atuais: {len(ids_atuais)}")
    
    # Carregar backup mais recente
    caminho_backup = obter_backup_mais_recente()
    if not caminho_backup:
        print("❌ Não foi possível encontrar backup para comparação")
        return
    
    dados_backup = carregar_json(caminho_backup)
    ids_backup = extrair_ids_intimacoes(dados_backup)
    detalhes_backup = extrair_detalhes_intimacoes(dados_backup)
    
    print(f"📊 Intimações no backup: {len(ids_backup)}")
    print()
    
    # Análise de diferenças
    intimacoes_perdidas = ids_backup - ids_atuais
    intimacoes_novas = ids_atuais - ids_backup
    intimacoes_mantidas = ids_atuais & ids_backup
    
    print("📈 RESULTADO DA COMPARAÇÃO:")
    print("-" * 30)
    
    if intimacoes_perdidas:
        print(f"❌ INTIMAÇÕES PERDIDAS: {len(intimacoes_perdidas)}")
        print("\nDetalhes das intimações perdidas:")
        for id_perdido in intimacoes_perdidas:
            detalhes = detalhes_backup.get(id_perdido, {})
            print(f"  • ID: {id_perdido}")
            print(f"    Processo: {detalhes.get('processo', 'N/A')}")
            print(f"    Intimado: {detalhes.get('intimado', 'N/A')}")
            print(f"    Classe: {detalhes.get('classe', 'N/A')}")
            print(f"    Análises: {detalhes.get('num_analises', 0)}")
            print()
    else:
        print("✅ Nenhuma intimação foi perdida")
    
    if intimacoes_novas:
        print(f"➕ INTIMAÇÕES NOVAS: {len(intimacoes_novas)}")
        print("\nDetalhes das intimações novas:")
        for id_novo in intimacoes_novas:
            detalhes = detalhes_atuais.get(id_novo, {})
            print(f"  • ID: {id_novo}")
            print(f"    Processo: {detalhes.get('processo', 'N/A')}")
            print(f"    Intimado: {detalhes.get('intimado', 'N/A')}")
            print(f"    Classe: {detalhes.get('classe', 'N/A')}")
            print()
    
    print(f"🔄 INTIMAÇÕES MANTIDAS: {len(intimacoes_mantidas)}")
    
    # Verificar mudanças nas análises
    print("\n🔍 VERIFICAÇÃO DE ANÁLISES:")
    print("-" * 30)
    
    total_analises_backup = sum(detalhes.get('num_analises', 0) for detalhes in detalhes_backup.values())
    total_analises_atual = sum(detalhes.get('num_analises', 0) for detalhes in detalhes_atuais.values())
    
    print(f"📊 Análises no backup: {total_analises_backup}")
    print(f"📊 Análises atuais: {total_analises_atual}")
    print(f"📊 Diferença: {total_analises_atual - total_analises_backup}")
    
    # Verificar intimações que perderam análises
    intimacoes_com_menos_analises = []
    for id_intimacao in intimacoes_mantidas:
        analises_backup = detalhes_backup.get(id_intimacao, {}).get('num_analises', 0)
        analises_atual = detalhes_atuais.get(id_intimacao, {}).get('num_analises', 0)
        
        if analises_atual < analises_backup:
            intimacoes_com_menos_analises.append({
                'id': id_intimacao,
                'processo': detalhes_atuais.get(id_intimacao, {}).get('processo', 'N/A'),
                'analises_perdidas': analises_backup - analises_atual,
                'analises_restantes': analises_atual
            })
    
    if intimacoes_com_menos_analises:
        print(f"\n⚠️  INTIMAÇÕES QUE PERDERAM ANÁLISES: {len(intimacoes_com_menos_analises)}")
        for intimacao in intimacoes_com_menos_analises:
            print(f"  • Processo: {intimacao['processo']}")
            print(f"    ID: {intimacao['id']}")
            print(f"    Análises perdidas: {intimacao['analises_perdidas']}")
            print(f"    Análises restantes: {intimacao['analises_restantes']}")
            print()
    
    print("\n" + "=" * 50)
    
    if intimacoes_perdidas:
        print("🚨 ATENÇÃO: Foram detectadas intimações perdidas!")
        print("   Recomenda-se executar o script de recuperação.")
        return False
    else:
        print("✅ SISTEMA ÍNTEGRO: Nenhuma intimação foi perdida.")
        if intimacoes_com_menos_analises:
            print("ℹ️  Algumas intimações perderam análises, mas isso pode ser normal.")
        return True

def main():
    """Função principal."""
    try:
        comparar_intimacoes()
    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()