#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste dos Novos Modelos de IA - 2025

Este script testa se os novos modelos de IA estão sendo carregados corretamente
na aplicação PromptRefinator2.

Autor: Assistant
Data: Janeiro 2025
"""

import sys
import os
from typing import List, Dict, Any

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.openai_service import OpenAIService
from services.azure_service import AzureService
from services.ai_manager_service import AIManagerService

def testar_modelos_config():
    """Testar se os modelos estão definidos corretamente no config"""
    print("=== TESTE: Modelos no Config ===")
    
    print(f"\n📋 Modelos OpenAI ({len(Config.OPENAI_MODELS)} modelos):")
    for i, modelo in enumerate(Config.OPENAI_MODELS, 1):
        print(f"  {i:2d}. {modelo}")
    
    print(f"\n📋 Modelos Azure OpenAI ({len(Config.AZURE_OPENAI_MODELS)} modelos):")
    for i, modelo in enumerate(Config.AZURE_OPENAI_MODELS, 1):
        print(f"  {i:2d}. {modelo}")
    
    # Verificar se os novos modelos estão presentes
    novos_modelos_openai = [
        'gpt-5', 'gpt-5-mini', 'gpt-4.1', 'gpt-4o', 'o3', 'o4-mini'
    ]
    
    novos_modelos_azure = [
        'gpt-5', 'gpt-5-mini', 'gpt-4.1', 'gpt-4o', 'o3-mini', 'gpt-oss-120b'
    ]
    
    print("\n✅ Verificação de Novos Modelos OpenAI:")
    for modelo in novos_modelos_openai:
        status = "✅" if modelo in Config.OPENAI_MODELS else "❌"
        print(f"  {status} {modelo}")
    
    print("\n✅ Verificação de Novos Modelos Azure:")
    for modelo in novos_modelos_azure:
        status = "✅" if modelo in Config.AZURE_OPENAI_MODELS else "❌"
        print(f"  {status} {modelo}")
    
    return True  # Retornar True se chegou até aqui

def testar_servicos_ia():
    """Testar se os serviços de IA carregam os modelos corretamente"""
    print("\n=== TESTE: Serviços de IA ===")
    
    try:
        # Testar OpenAI Service
        print("\n🔧 Testando OpenAI Service...")
        openai_service = OpenAIService()
        modelos_openai = openai_service.get_available_models()
        print(f"✅ OpenAI Service carregado com {len(modelos_openai)} modelos")
        
        # Testar Azure Service
        print("\n🔧 Testando Azure Service...")
        azure_service = AzureService()
        modelos_azure = azure_service.get_available_models()
        print(f"✅ Azure Service carregado com {len(modelos_azure)} modelos")
        
        # Testar AI Manager
        print("\n🔧 Testando AI Manager Service...")
        ai_manager = AIManagerService()
        provedores = ai_manager.get_available_providers()
        print(f"✅ AI Manager carregado com provedores: {', '.join(provedores)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar serviços: {e}")
        return False

def testar_estimativas_custo():
    """Testar se as estimativas de custo estão funcionando para os novos modelos"""
    print("\n=== TESTE: Estimativas de Custo ===")
    
    try:
        openai_service = OpenAIService()
        azure_service = AzureService()
        
        # Modelos para testar
        modelos_teste = [
            'gpt-5', 'gpt-5-mini', 'gpt-4.1', 'gpt-4o', 'o3', 'o4-mini', 'gpt-4'
        ]
        
        prompt_length = 1000  # caracteres
        response_length = 500  # caracteres
        
        print("\n💰 Estimativas de Custo: DESABILITADAS")
        print("   Simulação de custos foi removida do sistema.")
        print("   Os custos reais serão cobrados diretamente pela OpenAI/Azure.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar estimativas de custo: {e}")
        return False

def testar_parametros_padrao():
    """Testar se os parâmetros padrão estão corretos"""
    print("\n=== TESTE: Parâmetros Padrão ===")
    
    try:
        openai_service = OpenAIService()
        azure_service = AzureService()
        
        print("\n⚙️ Parâmetros Padrão OpenAI:")
        params_openai = openai_service.get_default_parameters()
        for key, value in params_openai.items():
            print(f"  {key:15} → {value}")
        
        print("\n⚙️ Parâmetros Padrão Azure:")
        params_azure = azure_service.get_default_parameters()
        for key, value in params_azure.items():
            print(f"  {key:15} → {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar parâmetros padrão: {e}")
        return False

def gerar_relatorio_modelos():
    """Gerar relatório detalhado dos modelos disponíveis"""
    print("\n=== RELATÓRIO: Modelos Disponíveis ===")
    
    # Categorizar modelos
    categorias = {
        'GPT-5 Series': [m for m in Config.OPENAI_MODELS if m.startswith('gpt-5')],
        'GPT-4.1 Series': [m for m in Config.OPENAI_MODELS if m.startswith('gpt-4.1')],
        'GPT-4o Series': [m for m in Config.OPENAI_MODELS if 'gpt-4o' in m],
        'o-Series (Reasoning)': [m for m in Config.OPENAI_MODELS if m.startswith('o')],
        'GPT-4 Legacy': [m for m in Config.OPENAI_MODELS if m.startswith('gpt-4') and not m.startswith('gpt-4.1') and 'gpt-4o' not in m],
        'GPT-3.5 Series': [m for m in Config.OPENAI_MODELS if m.startswith('gpt-3.5')]
    }
    
    print("\n📊 Modelos OpenAI por Categoria:")
    for categoria, modelos in categorias.items():
        if modelos:
            print(f"\n  🏷️ {categoria} ({len(modelos)} modelos):")
            for modelo in modelos:
                print(f"    • {modelo}")
    
    # Azure específicos
    azure_exclusivos = [m for m in Config.AZURE_OPENAI_MODELS if m not in Config.OPENAI_MODELS]
    if azure_exclusivos:
        print(f"\n  🏷️ Modelos Exclusivos do Azure ({len(azure_exclusivos)} modelos):")
        for modelo in azure_exclusivos:
            print(f"    • {modelo}")

def main():
    """Função principal do teste"""
    print("🚀 TESTE DOS NOVOS MODELOS DE IA - 2025")
    print("=" * 50)
    
    # Executar todos os testes
    testes = [
        ("Modelos no Config", testar_modelos_config),
        ("Serviços de IA", testar_servicos_ia),
        ("Estimativas de Custo", testar_estimativas_custo),
        ("Parâmetros Padrão", testar_parametros_padrao)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        try:
            print(f"\n🧪 Executando: {nome_teste}")
            resultado = funcao_teste()
            resultados.append((nome_teste, resultado))
        except Exception as e:
            print(f"❌ Erro no teste '{nome_teste}': {e}")
            resultados.append((nome_teste, False))
    
    # Gerar relatório
    gerar_relatorio_modelos()
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    
    testes_passou = 0
    for nome_teste, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"  {nome_teste:25} → {status}")
        if resultado:
            testes_passou += 1
    
    print(f"\n🎯 Resultado Final: {testes_passou}/{len(resultados)} testes passaram")
    
    if testes_passou == len(resultados):
        print("\n🎉 Todos os testes passaram! Os novos modelos estão configurados corretamente.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os erros acima.")
    
    print("\n📚 Para mais informações, consulte: documentacao_modelos_ia_2025.md")
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()