#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se as configurações da página de análise estão sendo utilizadas pela IA

Este script demonstra como as configurações da interface são processadas e utilizadas:
1. Coleta os parâmetros da interface (modelo, temperatura, max_tokens, timeout)
2. Mostra como eles sobrescrevem as configurações padrão do sistema
3. Confirma que são passados corretamente para a IA
"""

import json
import requests
from datetime import datetime

def testar_configuracoes_analise():
    """
    Testa se as configurações da página de análise são realmente utilizadas
    """
    print("=== TESTE: Verificação das Configurações da Página de Análise ===")
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Simular dados que seriam enviados da página de análise
    dados_teste = {
        "prompt_id": "1",  # ID de um prompt existente
        "intimacao_ids": ["1"],  # ID de uma intimação existente
        "configuracoes": {
            "modelo": "gpt-4",  # Modelo específico escolhido na página
            "temperatura": 0.3,  # Temperatura baixa para respostas mais determinísticas
            "max_tokens": 200,  # Limite específico de tokens
            "timeout": 45,  # Timeout personalizado
            "salvar_resultados": True,
            "calcular_acuracia": True,
            "modo_paralelo": False
        }
    }
    
    print("1. CONFIGURAÇÕES ENVIADAS DA PÁGINA:")
    print(f"   - Modelo: {dados_teste['configuracoes']['modelo']}")
    print(f"   - Temperatura: {dados_teste['configuracoes']['temperatura']}")
    print(f"   - Max Tokens: {dados_teste['configuracoes']['max_tokens']}")
    print(f"   - Timeout: {dados_teste['configuracoes']['timeout']}")
    print()
    
    try:
        # Fazer requisição para o endpoint de análise
        url = "http://localhost:5000/executar-analise"
        headers = {'Content-Type': 'application/json'}
        
        print("2. ENVIANDO REQUISIÇÃO PARA O BACKEND...")
        response = requests.post(url, json=dados_teste, headers=headers, timeout=60)
        
        if response.status_code == 200:
            resultado = response.json()
            print("✅ SUCESSO: Análise executada com sucesso!")
            print()
            
            print("3. VERIFICAÇÃO DOS PARÂMETROS UTILIZADOS:")
            if 'resultados' in resultado and len(resultado['resultados']) > 0:
                primeiro_resultado = resultado['resultados'][0]
                
                # Verificar se os parâmetros da página foram utilizados
                modelo_usado = primeiro_resultado.get('modelo')
                temperatura_usada = primeiro_resultado.get('temperatura')
                
                print(f"   - Modelo utilizado pela IA: {modelo_usado}")
                print(f"   - Temperatura utilizada: {temperatura_usada}")
                print(f"   - Tempo de processamento: {primeiro_resultado.get('tempo_processamento')}s")
                print(f"   - Tokens utilizados: {primeiro_resultado.get('tokens_usados')}")
                print()
                
                # Verificar se as configurações foram respeitadas
                configuracoes_respeitadas = (
                    modelo_usado == dados_teste['configuracoes']['modelo'] and
                    temperatura_usada == dados_teste['configuracoes']['temperatura']
                )
                
                if configuracoes_respeitadas:
                    print("✅ CONFIRMADO: As configurações da página foram utilizadas pela IA!")
                    print("   - O modelo escolhido na interface foi respeitado")
                    print("   - A temperatura definida na interface foi aplicada")
                    print("   - Os parâmetros da página têm precedência sobre as configurações padrão")
                else:
                    print("❌ PROBLEMA: As configurações da página não foram utilizadas corretamente")
                    print(f"   - Esperado modelo: {dados_teste['configuracoes']['modelo']}, Usado: {modelo_usado}")
                    print(f"   - Esperado temperatura: {dados_teste['configuracoes']['temperatura']}, Usado: {temperatura_usada}")
            else:
                print("⚠️  AVISO: Não foi possível verificar os parâmetros nos resultados")
                
        else:
            print(f"❌ ERRO: Falha na requisição - Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao servidor Flask")
        print("Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
    
    print()
    print("=== COMO VERIFICAR MANUALMENTE ===")
    print("1. Abra a página de análise (http://localhost:5000/analise)")
    print("2. Altere as configurações (modelo, temperatura, max tokens)")
    print("3. Execute uma análise")
    print("4. Verifique no console do navegador (F12) os logs de DEBUG")
    print("5. Procure por linhas como:")
    print("   - '=== DEBUG: Configurações - Modelo: X, Temp: Y, Tokens: Z ==='")
    print("   - '=== DEBUG: Chamando OpenAI com parâmetros: {...} ==='")
    print("6. Confirme que os valores correspondem ao que você configurou")
    print()
    print("=== FLUXO DE CONFIGURAÇÕES ===")
    print("1. Interface (analise.html) coleta os valores dos campos")
    print("2. JavaScript envia via AJAX para /executar-analise")
    print("3. Backend (app.py) recebe e sobrescreve configurações padrão")
    print("4. Parâmetros são passados para ai_manager_service.analisar_intimacao()")
    print("5. IA utiliza exatamente os parâmetros fornecidos")

if __name__ == "__main__":
    testar_configuracoes_analise()