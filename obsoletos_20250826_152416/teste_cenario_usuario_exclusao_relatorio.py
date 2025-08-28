#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para reproduzir o cenário específico descrito pelo usuário:
- Selecionar uns 10 resultados no relatório
- Clicar no botão "Excluir" ao lado de "Colunas"
- Verificar se as intimações desaparecem
"""

import json
import requests
import time
from datetime import datetime

def carregar_intimacoes():
    """Carregar intimações do arquivo"""
    try:
        with open('data/intimacoes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('intimacoes', [])
    except Exception as e:
        print(f"Erro ao carregar intimações: {e}")
        return []

def contar_analises_por_intimacao(intimacoes):
    """Contar análises por intimação"""
    contadores = {}
    for intimacao in intimacoes:
        id_intimacao = intimacao.get('id')
        processo = intimacao.get('processo', 'N/A')
        analises = intimacao.get('analises', [])
        analises_ids = [a.get('id') for a in analises if a.get('id')]
        
        contadores[id_intimacao] = {
            'processo': processo,
            'total_analises': len(analises),
            'analises_ids': analises_ids
        }
    return contadores

def coletar_analises_reais(intimacoes):
    """Coletar todas as análises reais das intimações"""
    analises_reais = []
    for intimacao in intimacoes:
        intimacao_id = intimacao.get('id')
        processo = intimacao.get('processo', 'N/A')
        analises = intimacao.get('analises', [])
        
        for analise in analises:
            if analise.get('id'):
                analises_reais.append({
                    'intimacao_id': intimacao_id,
                    'analise_id': analise.get('id'),
                    'processo': processo,
                    'analise_data': analise
                })
    
    return analises_reais

def simular_exclusao_relatorio():
    """Simular o cenário específico do usuário no relatório"""
    print("=== TESTE DO CENÁRIO DO USUÁRIO - EXCLUSÃO NO RELATÓRIO ===")
    print(f"Início do teste: {datetime.now()}")
    
    # Estado inicial
    print("\n1. ESTADO INICIAL:")
    intimacoes_inicial = carregar_intimacoes()
    contadores_inicial = contar_analises_por_intimacao(intimacoes_inicial)
    analises_reais = coletar_analises_reais(intimacoes_inicial)
    
    print(f"Total de intimações: {len(intimacoes_inicial)}")
    print(f"Total de análises reais encontradas: {len(analises_reais)}")
    
    for id_int, info in contadores_inicial.items():
        print(f"  - {id_int}: {info['processo']} ({info['total_analises']} análises)")
        if info['analises_ids']:
            print(f"    IDs das análises: {info['analises_ids'][:3]}{'...' if len(info['analises_ids']) > 3 else ''}")
    
    # Simular seleção de ~10 análises (ou todas disponíveis se menos de 10)
    analises_para_excluir = analises_reais[:min(10, len(analises_reais))]
    
    print(f"\n2. SIMULANDO EXCLUSÃO DE {len(analises_para_excluir)} ANÁLISES DO RELATÓRIO:")
    
    if not analises_para_excluir:
        print("❌ Nenhuma análise real disponível para excluir")
        return False
    
    # Mostrar quais análises serão excluídas
    for i, item in enumerate(analises_para_excluir):
        print(f"  {i+1}. Análise {item['analise_id']} da intimação {item['intimacao_id']} (processo: {item['processo']})")
    
    # Simular exclusões via API (como faria o JavaScript do relatório)
    print("\n3. EXECUTANDO EXCLUSÕES VIA API:")
    exclusoes_bem_sucedidas = 0
    exclusoes_falharam = 0
    
    for item in analises_para_excluir:
        intimacao_id = item['intimacao_id']
        analise_id = item['analise_id']
        
        try:
            # Fazer requisição DELETE para a API
            response = requests.delete(
                'http://localhost:5000/api/analises/excluir',
                json={
                    'intimacao_id': intimacao_id,
                    'analise_id': analise_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"  ✅ Análise {analise_id} excluída com sucesso")
                    exclusoes_bem_sucedidas += 1
                else:
                    print(f"  ❌ Falha ao excluir análise {analise_id}: {data.get('error', 'Erro desconhecido')}")
                    exclusoes_falharam += 1
            else:
                print(f"  ❌ Erro HTTP {response.status_code} ao excluir análise {analise_id}")
                exclusoes_falharam += 1
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Erro de conexão ao excluir análise {analise_id}: {e}")
            exclusoes_falharam += 1
        
        # Pequena pausa entre requisições
        time.sleep(0.1)
    
    print(f"\n4. RESULTADO DAS EXCLUSÕES:")
    print(f"  ✅ Exclusões bem-sucedidas: {exclusoes_bem_sucedidas}")
    print(f"  ❌ Exclusões que falharam: {exclusoes_falharam}")
    
    # Aguardar um pouco para garantir que as operações foram processadas
    print("\n5. AGUARDANDO PROCESSAMENTO...")
    time.sleep(2)
    
    # Estado final
    print("\n6. ESTADO FINAL:")
    intimacoes_final = carregar_intimacoes()
    contadores_final = contar_analises_por_intimacao(intimacoes_final)
    analises_reais_final = coletar_analises_reais(intimacoes_final)
    
    print(f"Total de intimações: {len(intimacoes_final)}")
    print(f"Total de análises reais: {len(analises_reais_final)}")
    
    for id_int, info in contadores_final.items():
        print(f"  - {id_int}: {info['processo']} ({info['total_analises']} análises)")
        if info['analises_ids']:
            print(f"    IDs das análises: {info['analises_ids'][:3]}{'...' if len(info['analises_ids']) > 3 else ''}")
    
    # Análise dos resultados
    print("\n7. ANÁLISE DOS RESULTADOS:")
    
    # Intimações perdidas
    intimacoes_perdidas = len(intimacoes_inicial) - len(intimacoes_final)
    print(f"  📊 Intimações: {len(intimacoes_inicial)} → {len(intimacoes_final)} (diferença: {intimacoes_perdidas})")
    
    if intimacoes_perdidas > 0:
        print(f"  🚨 PROBLEMA CONFIRMADO: {intimacoes_perdidas} intimação(ões) foi(ram) perdida(s)!")
        
        # Identificar quais intimações foram perdidas
        ids_inicial = {i.get('id') for i in intimacoes_inicial}
        ids_final = {i.get('id') for i in intimacoes_final}
        ids_perdidos = ids_inicial - ids_final
        
        print(f"  📋 Intimações perdidas:")
        for id_perdido in ids_perdidos:
            intimacao_perdida = next((i for i in intimacoes_inicial if i.get('id') == id_perdido), None)
            if intimacao_perdida:
                processo = intimacao_perdida.get('processo', 'N/A')
                print(f"    - {id_perdido}: {processo}")
    elif intimacoes_perdidas < 0:
        print(f"  ⚠️  ANOMALIA: {abs(intimacoes_perdidas)} intimação(ões) foi(ram) adicionada(s)!")
    else:
        print(f"  ✅ Nenhuma intimação foi perdida")
    
    # Análises perdidas
    analises_perdidas = len(analises_reais) - len(analises_reais_final)
    print(f"  📊 Análises: {len(analises_reais)} → {len(analises_reais_final)} (diferença: {analises_perdidas})")
    
    # Verificar se alguma intimação ficou sem análises
    print("\n8. VERIFICAÇÃO DE INTIMAÇÕES SEM ANÁLISES:")
    intimacoes_sem_analises = []
    for intimacao in intimacoes_final:
        analises = intimacao.get('analises', [])
        if not analises:
            intimacoes_sem_analises.append(intimacao)
    
    if intimacoes_sem_analises:
        print(f"  ⚠️  {len(intimacoes_sem_analises)} intimação(ões) ficou(ram) sem análises:")
        for intimacao in intimacoes_sem_analises:
            print(f"    - {intimacao.get('id')}: {intimacao.get('processo', 'N/A')}")
    else:
        print(f"  ✅ Todas as intimações ainda têm análises")
    
    print(f"\nTeste concluído: {datetime.now()}")
    
    # Conclusão
    if intimacoes_perdidas > 0:
        print("\n🚨 CONCLUSÃO: O problema foi reproduzido! A exclusão de análises está causando perda de intimações.")
        return True
    else:
        print("\n✅ CONCLUSÃO: O problema não foi reproduzido. As intimações foram preservadas.")
        return False

def verificar_cenario_especifico():
    """Verificar se existe um cenário específico que pode causar o problema"""
    print("\n=== VERIFICAÇÃO DE CENÁRIOS ESPECÍFICOS ===")
    
    intimacoes = carregar_intimacoes()
    
    # Verificar se há intimações que ficariam sem análises após exclusão
    print("\n1. INTIMAÇÕES QUE PODEM FICAR SEM ANÁLISES:")
    intimacoes_vulneraveis = []
    
    for intimacao in intimacoes:
        analises = intimacao.get('analises', [])
        if len(analises) <= 10:  # Se tem 10 ou menos análises, pode ficar sem nenhuma
            intimacoes_vulneraveis.append({
                'id': intimacao.get('id'),
                'processo': intimacao.get('processo', 'N/A'),
                'total_analises': len(analises)
            })
    
    if intimacoes_vulneraveis:
        print(f"  ⚠️  {len(intimacoes_vulneraveis)} intimação(ões) pode(m) ficar sem análises:")
        for item in intimacoes_vulneraveis:
            print(f"    - {item['id']}: {item['processo']} ({item['total_analises']} análises)")
    else:
        print(f"  ✅ Nenhuma intimação ficaria sem análises")
    
    return intimacoes_vulneraveis

if __name__ == '__main__':
    # Primeiro, verificar cenários específicos
    intimacoes_vulneraveis = verificar_cenario_especifico()
    
    # Depois, executar o teste principal
    problema_reproduzido = simular_exclusao_relatorio()
    
    if problema_reproduzido:
        print("\n⚠️  RECOMENDAÇÃO: Investigar o código de exclusão de análises para identificar por que está removendo intimações.")
    else:
        print("\n✅ SISTEMA FUNCIONANDO CORRETAMENTE: A exclusão de análises não está afetando as intimações.")
        
        if intimacoes_vulneraveis:
            print("\n💡 OBSERVAÇÃO: Embora o teste não tenha reproduzido o problema, existem intimações que podem ficar vulneráveis se todas as suas análises forem excluídas.")