#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para reproduzir o problema de exclusão em massa de análises
que pode estar excluindo intimações junto
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
        analises = intimacao.get('analises', [])
        contadores[id_intimacao] = {
            'processo': intimacao.get('processo', 'N/A'),
            'total_analises': len(analises),
            'analises_ids': [a.get('id') for a in analises if a.get('id')]
        }
    return contadores

def simular_exclusao_massa():
    """Simular exclusão em massa de análises via API"""
    print("=== TESTE DE EXCLUSÃO EM MASSA DE ANÁLISES ===")
    print(f"Início do teste: {datetime.now()}")
    
    # Estado inicial
    print("\n1. ESTADO INICIAL:")
    intimacoes_inicial = carregar_intimacoes()
    contadores_inicial = contar_analises_por_intimacao(intimacoes_inicial)
    
    print(f"Total de intimações: {len(intimacoes_inicial)}")
    for id_int, info in contadores_inicial.items():
        print(f"  - {id_int}: {info['processo']} ({info['total_analises']} análises)")
        if info['analises_ids']:
            print(f"    IDs das análises: {info['analises_ids'][:3]}{'...' if len(info['analises_ids']) > 3 else ''}")
    
    # Coletar análises para exclusão
    analises_para_excluir = []
    for intimacao in intimacoes_inicial:
        id_intimacao = intimacao.get('id')
        analises = intimacao.get('analises', [])
        for analise in analises:
            if analise.get('id'):
                analises_para_excluir.append({
                    'intimacao_id': id_intimacao,
                    'analise_id': analise.get('id'),
                    'processo': intimacao.get('processo', 'N/A')
                })
    
    print(f"\n2. ANÁLISES IDENTIFICADAS PARA EXCLUSÃO: {len(analises_para_excluir)}")
    for i, analise in enumerate(analises_para_excluir[:5]):  # Mostrar apenas as primeiras 5
        print(f"  {i+1}. Intimação: {analise['processo']} | Análise: {analise['analise_id'][:8]}...")
    
    if len(analises_para_excluir) > 5:
        print(f"  ... e mais {len(analises_para_excluir) - 5} análises")
    
    if not analises_para_excluir:
        print("❌ Nenhuma análise encontrada para testar exclusão")
        return
    
    # Simular exclusão (limitando a 3 análises para teste)
    analises_teste = analises_para_excluir[:3]
    print(f"\n3. SIMULANDO EXCLUSÃO DE {len(analises_teste)} ANÁLISES:")
    
    sucessos = 0
    erros = 0
    
    for i, analise in enumerate(analises_teste, 1):
        print(f"\n  Excluindo {i}/{len(analises_teste)}: {analise['analise_id'][:8]}...")
        
        try:
            # Fazer requisição para a API local
            response = requests.delete(
                'http://localhost:5000/api/analises/excluir',
                json={
                    'intimacao_id': analise['intimacao_id'],
                    'analise_id': analise['analise_id']
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"    ✅ Sucesso: {result.get('message', 'Análise excluída')}")
                    sucessos += 1
                else:
                    print(f"    ❌ Erro na resposta: {result.get('error', 'Erro desconhecido')}")
                    erros += 1
            else:
                print(f"    ❌ Erro HTTP {response.status_code}: {response.text}")
                erros += 1
                
        except requests.exceptions.ConnectionError:
            print(f"    ⚠️  Servidor não está rodando. Pulando teste de API.")
            print(f"    💡 Para testar completamente, execute: python app.py")
            break
        except Exception as e:
            print(f"    ❌ Erro na requisição: {e}")
            erros += 1
        
        # Pequena pausa entre exclusões
        time.sleep(0.5)
    
    print(f"\n4. RESULTADO DA EXCLUSÃO:")
    print(f"  ✅ Sucessos: {sucessos}")
    print(f"  ❌ Erros: {erros}")
    
    # Estado final
    print("\n5. ESTADO FINAL:")
    intimacoes_final = carregar_intimacoes()
    contadores_final = contar_analises_por_intimacao(intimacoes_final)
    
    print(f"Total de intimações: {len(intimacoes_final)}")
    for id_int, info in contadores_final.items():
        print(f"  - {id_int}: {info['processo']} ({info['total_analises']} análises)")
    
    # Comparação
    print("\n6. COMPARAÇÃO:")
    intimacoes_perdidas = len(intimacoes_inicial) - len(intimacoes_final)
    if intimacoes_perdidas > 0:
        print(f"  ⚠️  PROBLEMA DETECTADO: {intimacoes_perdidas} intimação(ões) foi(ram) perdida(s)!")
        
        # Identificar quais intimações foram perdidas
        ids_inicial = {i.get('id') for i in intimacoes_inicial}
        ids_final = {i.get('id') for i in intimacoes_final}
        ids_perdidos = ids_inicial - ids_final
        
        print("  Intimações perdidas:")
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
    total_analises_inicial = sum(info['total_analises'] for info in contadores_inicial.values())
    total_analises_final = sum(info['total_analises'] for info in contadores_final.values())
    analises_perdidas = total_analises_inicial - total_analises_final
    
    print(f"  📊 Análises: {total_analises_inicial} → {total_analises_final} (diferença: {analises_perdidas})")
    
    print(f"\nTeste concluído: {datetime.now()}")

def main():
    try:
        simular_exclusao_massa()
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()