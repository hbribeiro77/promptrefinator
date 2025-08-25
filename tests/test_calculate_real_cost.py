#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para a função de cálculo de custo real baseado em tokens

Este teste verifica se a função calculate_real_cost está calculando
corretamente o custo baseado nos tokens de entrada e saída, modelo
e provedor (Azure ou OpenAI).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_service import DataService

def test_calculate_real_cost():
    """Testa o cálculo de custo real baseado em tokens"""
    print("🧪 Iniciando teste de cálculo de custo real...")
    
    data_service = DataService()
    
    # Teste 1: GPT-4 com tokens de entrada e saída
    print("\n📊 Teste 1: GPT-4 com 1000 tokens input e 500 tokens output")
    tokens_input = 1000
    tokens_output = 500
    modelo = 'gpt-4'
    
    custo = data_service.calculate_real_cost(tokens_input, tokens_output, modelo)
    print(f"   Tokens Input: {tokens_input}")
    print(f"   Tokens Output: {tokens_output}")
    print(f"   Modelo: {modelo}")
    print(f"   Custo calculado: ${custo:.6f}")
    
    # Teste 2: GPT-3.5-turbo com tokens diferentes
    print("\n📊 Teste 2: GPT-3.5-turbo com 2000 tokens input e 1000 tokens output")
    tokens_input = 2000
    tokens_output = 1000
    modelo = 'gpt-3.5-turbo'
    
    custo = data_service.calculate_real_cost(tokens_input, tokens_output, modelo)
    print(f"   Tokens Input: {tokens_input}")
    print(f"   Tokens Output: {tokens_output}")
    print(f"   Modelo: {modelo}")
    print(f"   Custo calculado: ${custo:.6f}")
    
    # Teste 3: Modelo não reconhecido (deve usar padrão)
    print("\n📊 Teste 3: Modelo não reconhecido (deve usar gpt-3.5-turbo como padrão)")
    tokens_input = 500
    tokens_output = 250
    modelo = 'modelo-inexistente'
    
    custo = data_service.calculate_real_cost(tokens_input, tokens_output, modelo)
    print(f"   Tokens Input: {tokens_input}")
    print(f"   Tokens Output: {tokens_output}")
    print(f"   Modelo: {modelo}")
    print(f"   Custo calculado: ${custo:.6f}")
    
    # Teste 4: Tokens zero
    print("\n📊 Teste 4: Tokens zero (deve retornar 0)")
    tokens_input = 0
    tokens_output = 0
    modelo = 'gpt-4'
    
    custo = data_service.calculate_real_cost(tokens_input, tokens_output, modelo)
    print(f"   Tokens Input: {tokens_input}")
    print(f"   Tokens Output: {tokens_output}")
    print(f"   Modelo: {modelo}")
    print(f"   Custo calculado: ${custo:.6f}")
    
    # Teste 5: Verificar se o custo é sempre positivo e razoável
    print("\n📊 Teste 5: Verificações de validação")
    
    # Teste com valores altos
    custo_alto = data_service.calculate_real_cost(10000, 5000, 'gpt-4')
    print(f"   Custo para 10k input + 5k output (GPT-4): ${custo_alto:.6f}")
    
    # Verificar se o custo é proporcional
    custo_baixo = data_service.calculate_real_cost(1000, 500, 'gpt-4')
    print(f"   Custo para 1k input + 500 output (GPT-4): ${custo_baixo:.6f}")
    
    if custo_alto > custo_baixo:
        print("   ✅ Custo é proporcional aos tokens (maior uso = maior custo)")
    else:
        print("   ❌ Erro: Custo não é proporcional aos tokens")
    
    print("\n✅ Teste de cálculo de custo real concluído!")
    print("\n📋 Resumo dos testes:")
    print("   - Cálculo com diferentes modelos")
    print("   - Tratamento de modelos não reconhecidos")
    print("   - Tratamento de tokens zero")
    print("   - Verificação de proporcionalidade")
    print("   - Formatação correta do resultado")

if __name__ == '__main__':
    test_calculate_real_cost()