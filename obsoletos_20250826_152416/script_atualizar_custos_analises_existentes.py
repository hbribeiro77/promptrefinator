#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar custos das análises existentes

Este script:
1. Carrega todas as análises existentes
2. Para análises que têm apenas tokens_usados, calcula tokens_input e tokens_output
3. Calcula o custo real usando a nova função
4. Atualiza os dados salvos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_service import DataService
import json
from datetime import datetime

def carregar_intimacoes():
    """Carregar dados das intimações"""
    try:
        with open('data/intimacoes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar intimações: {e}")
        return None

def salvar_intimacoes(dados):
    """Salvar dados das intimações"""
    try:
        # Criar backup antes de salvar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/backups/{timestamp}_intimacoes_antes_atualizacao_custos.json'
        
        os.makedirs('data/backups', exist_ok=True)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"📋 Backup criado: {backup_path}")
        
        # Salvar dados atualizados
        with open('data/intimacoes.json', 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar intimações: {e}")
        return False

def estimar_tokens_separados(tokens_usados):
    """Estimar tokens_input e tokens_output baseado no total"""
    if tokens_usados <= 0:
        return 0, 0
    
    # Estimativa baseada em proporção típica:
    # Input geralmente é maior que output em análises de intimações
    # Proporção aproximada: 70% input, 30% output
    tokens_input = int(tokens_usados * 0.7)
    tokens_output = int(tokens_usados * 0.3)
    
    return tokens_input, tokens_output

def atualizar_custos_analises():
    """Atualizar custos das análises existentes"""
    print("🔄 Iniciando atualização de custos das análises existentes...")
    
    # Carregar dados
    dados = carregar_intimacoes()
    if not dados:
        return False
    
    data_service = DataService()
    intimacoes = dados.get('intimacoes', [])
    
    total_intimacoes = len(intimacoes)
    total_analises = 0
    analises_atualizadas = 0
    analises_com_tokens_separados = 0
    
    print(f"📊 Processando {total_intimacoes} intimações...")
    
    for i, intimacao in enumerate(intimacoes):
        processo = intimacao.get('processo', 'N/A')
        analises = intimacao.get('analises', [])
        total_analises += len(analises)
        
        if analises:
            print(f"\n📋 Intimação {i+1}/{total_intimacoes}: {processo}")
            print(f"   Análises: {len(analises)}")
            
            for j, analise in enumerate(analises):
                tokens_input = analise.get('tokens_input', 0)
                tokens_output = analise.get('tokens_output', 0)
                tokens_usados = analise.get('tokens_usados', 0)
                modelo = analise.get('modelo', 'gpt-4o')
                
                # Se não tem tokens separados mas tem total, estimar
                if (tokens_input == 0 and tokens_output == 0) and tokens_usados > 0:
                    tokens_input, tokens_output = estimar_tokens_separados(tokens_usados)
                    analise['tokens_input'] = tokens_input
                    analise['tokens_output'] = tokens_output
                    print(f"     Análise {j+1}: Estimados {tokens_input} input + {tokens_output} output (total: {tokens_usados})")
                elif tokens_input > 0 or tokens_output > 0:
                    analises_com_tokens_separados += 1
                    print(f"     Análise {j+1}: Já tem tokens separados ({tokens_input} input + {tokens_output} output)")
                
                # Calcular custo real se há tokens
                if tokens_input > 0 or tokens_output > 0:
                    try:
                        custo_real = data_service.calculate_real_cost(tokens_input, tokens_output, modelo)
                        analise['custo_real'] = custo_real
                        analises_atualizadas += 1
                        print(f"       Custo calculado: ${custo_real:.6f} (modelo: {modelo})")
                    except Exception as e:
                        print(f"       ❌ Erro ao calcular custo: {e}")
                        analise['custo_real'] = 0.0
                else:
                    analise['custo_real'] = 0.0
                    print(f"     Análise {j+1}: Sem tokens, custo = $0.000000")
    
    # Salvar dados atualizados
    if analises_atualizadas > 0:
        if salvar_intimacoes(dados):
            print(f"\n✅ ATUALIZAÇÃO CONCLUÍDA:")
            print(f"   📊 Total de intimações: {total_intimacoes}")
            print(f"   📊 Total de análises: {total_analises}")
            print(f"   ✅ Análises atualizadas: {analises_atualizadas}")
            print(f"   ℹ️  Análises já com tokens separados: {analises_com_tokens_separados}")
            print(f"   💾 Backup criado com sucesso")
            return True
        else:
            print("❌ Erro ao salvar dados atualizados")
            return False
    else:
        print("\nℹ️  Nenhuma análise precisou ser atualizada.")
        return True

def verificar_custos_atualizados():
    """Verificar se os custos foram atualizados corretamente"""
    print("\n🔍 Verificando custos atualizados...")
    
    dados = carregar_intimacoes()
    if not dados:
        return
    
    intimacoes = dados.get('intimacoes', [])
    total_analises = 0
    analises_com_custo = 0
    custo_total = 0.0
    
    for intimacao in intimacoes:
        for analise in intimacao.get('analises', []):
            total_analises += 1
            custo_real = analise.get('custo_real', 0.0)
            if custo_real > 0:
                analises_com_custo += 1
                custo_total += custo_real
    
    print(f"📊 Resumo dos custos:")
    print(f"   Total de análises: {total_analises}")
    print(f"   Análises com custo > 0: {analises_com_custo}")
    print(f"   Custo total: ${custo_total:.6f}")
    if total_analises > 0:
        print(f"   Custo médio por análise: ${custo_total/total_analises:.6f}")
    
    # Mostrar algumas análises como exemplo
    print(f"\n📋 Exemplos de análises atualizadas:")
    count = 0
    for intimacao in intimacoes:
        if count >= 3:
            break
        for analise in intimacao.get('analises', []):
            if count >= 3:
                break
            custo_real = analise.get('custo_real', 0.0)
            tokens_input = analise.get('tokens_input', 0)
            tokens_output = analise.get('tokens_output', 0)
            modelo = analise.get('modelo', 'N/A')
            
            print(f"   Análise {count+1}:")
            print(f"     Modelo: {modelo}")
            print(f"     Tokens Input: {tokens_input}")
            print(f"     Tokens Output: {tokens_output}")
            print(f"     Custo Real: ${custo_real:.6f}")
            count += 1

if __name__ == '__main__':
    print("🚀 Script de Atualização de Custos das Análises")
    print("=" * 50)
    
    if atualizar_custos_analises():
        verificar_custos_atualizados()
        print("\n🎉 Script executado com sucesso!")
    else:
        print("\n❌ Erro durante a execução do script.")