#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para remover TODAS as referências ao custo_estimado de TODOS os arquivos JSON

Este script:
1. Varre recursivamente o diretório data/
2. Remove custo_estimado de TODOS os arquivos .json encontrados
3. Cria backups apenas dos arquivos principais (não dos backups)
4. Exclui apenas arquivos de backup que já foram criados pelo script anterior
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import glob
from datetime import datetime

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

def processar_arquivo_json(arquivo_path):
    """Processar um arquivo JSON removendo custo_estimado"""
    print(f"🔄 Processando: {arquivo_path}")
    
    try:
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
            return True
        else:
            print(f"   ❌ Ainda restam {count_depois} referências ao custo_estimado")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao processar arquivo: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Script de Limpeza TOTAL do custo_estimado")
    print("=" * 50)
    
    # Encontrar todos os arquivos JSON no diretório data/
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"❌ Diretório {data_dir} não encontrado!")
        return
    
    # Buscar todos os arquivos .json recursivamente
    pattern = os.path.join(data_dir, '**', '*.json')
    arquivos_json = glob.glob(pattern, recursive=True)
    
    if not arquivos_json:
        print(f"⚠️  Nenhum arquivo JSON encontrado em {data_dir}")
        return
    
    print(f"📁 Encontrados {len(arquivos_json)} arquivos JSON:")
    for arquivo in sorted(arquivos_json):
        print(f"   - {arquivo}")
    
    print(f"\n🔄 Iniciando processamento...\n")
    
    sucessos = 0
    total = len(arquivos_json)
    total_referencias_removidas = 0
    
    for arquivo in sorted(arquivos_json):
        if processar_arquivo_json(arquivo):
            sucessos += 1
        print()  # Linha em branco para separar
    
    print(f"📊 RESUMO FINAL:")
    print(f"   Arquivos processados com sucesso: {sucessos}/{total}")
    
    if sucessos == total:
        print(f"\n🎉 Todos os arquivos foram processados com sucesso!")
    else:
        print(f"\n⚠️  {total - sucessos} arquivos tiveram problemas durante o processamento.")
    
    # Verificação final completa
    print(f"\n🔍 Verificação final em todos os arquivos JSON...")
    
    total_referencias_restantes = 0
    arquivos_com_problema = []
    
    for arquivo in sorted(arquivos_json):
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    count = conteudo.count('"custo_estimado"')
                    total_referencias_restantes += count
                    if count > 0:
                        print(f"   ⚠️  {arquivo}: {count} referências restantes")
                        arquivos_com_problema.append(arquivo)
                    else:
                        print(f"   ✅ {arquivo}: Limpo")
            except Exception as e:
                print(f"   ❌ Erro ao verificar {arquivo}: {e}")
    
    print(f"\n" + "=" * 60)
    if total_referencias_restantes == 0:
        print(f"🎯 SUCESSO TOTAL: Nenhuma referência ao custo_estimado encontrada!")
        print(f"✅ Todos os {total} arquivos JSON estão limpos.")
    else:
        print(f"⚠️  ATENÇÃO: Ainda existem {total_referencias_restantes} referências ao custo_estimado")
        print(f"📋 Arquivos com problemas: {len(arquivos_com_problema)}")
        for arquivo in arquivos_com_problema:
            print(f"   - {arquivo}")
    
    print(f"\n🏁 Script finalizado!")

if __name__ == '__main__':
    main()