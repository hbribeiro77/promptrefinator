#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para remover completamente todas as referências ao custo_estimado

Este script:
1. Remove custo_estimado de intimacoes.json
2. Remove custo_estimado de prompts.json
3. Remove custo_estimado de analises.json (se existir)
4. Cria backups antes das modificações
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime

def criar_backup(arquivo_path):
    """Criar backup de um arquivo"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = os.path.basename(arquivo_path)
        backup_path = f'data/backups/{timestamp}_{nome_arquivo}_antes_remover_custo_estimado'
        
        os.makedirs('data/backups', exist_ok=True)
        
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Backup criado: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar backup de {arquivo_path}: {e}")
        return False

def remover_custo_estimado_recursivo(obj):
    """Remove custo_estimado de qualquer estrutura de dados recursivamente"""
    if isinstance(obj, dict):
        # Remover custo_estimado se existir
        if 'custo_estimado' in obj:
            del obj['custo_estimado']
        
        # Processar recursivamente todos os valores
        for key, value in obj.items():
            remover_custo_estimado_recursivo(value)
    
    elif isinstance(obj, list):
        # Processar recursivamente todos os itens da lista
        for item in obj:
            remover_custo_estimado_recursivo(item)

def processar_arquivo(arquivo_path):
    """Processar um arquivo JSON removendo custo_estimado"""
    if not os.path.exists(arquivo_path):
        print(f"⚠️  Arquivo não encontrado: {arquivo_path}")
        return False
    
    print(f"\n🔄 Processando: {arquivo_path}")
    
    try:
        # Criar backup
        if not criar_backup(arquivo_path):
            return False
        
        # Carregar dados
        with open(arquivo_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Contar custo_estimado antes da remoção
        dados_str = json.dumps(dados)
        count_antes = dados_str.count('"custo_estimado"')
        
        if count_antes == 0:
            print(f"   ℹ️  Nenhuma referência ao custo_estimado encontrada")
            return True
        
        print(f"   📊 Encontradas {count_antes} referências ao custo_estimado")
        
        # Remover custo_estimado recursivamente
        remover_custo_estimado_recursivo(dados)
        
        # Verificar se foi removido
        dados_str_depois = json.dumps(dados)
        count_depois = dados_str_depois.count('"custo_estimado"')
        
        if count_depois == 0:
            # Salvar dados limpos
            with open(arquivo_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Removidas {count_antes} referências ao custo_estimado")
            print(f"   💾 Arquivo salvo com sucesso")
            return True
        else:
            print(f"   ❌ Ainda restam {count_depois} referências ao custo_estimado")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao processar arquivo: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Script de Remoção Completa do custo_estimado")
    print("=" * 50)
    
    # Arquivos para processar
    arquivos = [
        'data/intimacoes.json',
        'data/prompts.json',
        'data/analises.json'
    ]
    
    sucessos = 0
    total = 0
    
    for arquivo in arquivos:
        total += 1
        if processar_arquivo(arquivo):
            sucessos += 1
    
    print(f"\n📊 RESUMO:")
    print(f"   Arquivos processados: {sucessos}/{total}")
    
    if sucessos == total:
        print(f"\n🎉 Todos os arquivos foram processados com sucesso!")
        print(f"✅ O custo_estimado foi completamente removido do sistema.")
    else:
        print(f"\n⚠️  Alguns arquivos tiveram problemas durante o processamento.")
    
    # Verificação final
    print(f"\n🔍 Verificação final...")
    
    total_referencias = 0
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    count = conteudo.count('"custo_estimado"')
                    total_referencias += count
                    if count > 0:
                        print(f"   ⚠️  {arquivo}: {count} referências restantes")
                    else:
                        print(f"   ✅ {arquivo}: Limpo")
            except Exception as e:
                print(f"   ❌ Erro ao verificar {arquivo}: {e}")
    
    if total_referencias == 0:
        print(f"\n🎯 SUCESSO TOTAL: Nenhuma referência ao custo_estimado encontrada!")
    else:
        print(f"\n⚠️  ATENÇÃO: Ainda existem {total_referencias} referências ao custo_estimado")

if __name__ == '__main__':
    main()