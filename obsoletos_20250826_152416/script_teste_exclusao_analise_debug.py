#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste - Debug da Exclusão de Análises

Este script testa o processo de exclusão de análises para identificar
onde está ocorrendo a corrupção dos dados das intimações.
"""

import json
import os
import shutil
from datetime import datetime
from services.data_service import DataService
from config import Config

def criar_backup_teste():
    """Criar backup dos arquivos antes do teste"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    arquivos = [
        'data/intimacoes.json',
        'data/analises.json'
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            backup_name = f"{arquivo.replace('.json', '')}_{timestamp}_teste.json"
            shutil.copy2(arquivo, backup_name)
            print(f"✅ Backup criado: {backup_name}")

def verificar_integridade_antes():
    """Verificar integridade dos dados antes do teste"""
    print("\n=== VERIFICAÇÃO ANTES DO TESTE ===")
    
    try:
        with open('data/intimacoes.json', 'r', encoding='utf-8') as f:
            intimacoes_data = json.load(f)
            intimacoes = intimacoes_data.get('intimacoes', [])
            print(f"📋 Intimações encontradas: {len(intimacoes)}")
            
            for i, intimacao in enumerate(intimacoes):
                print(f"  - ID: {intimacao.get('id', 'N/A')}")
                print(f"    Análises: {len(intimacao.get('analises', []))}")
                
    except Exception as e:
        print(f"❌ Erro ao verificar intimações: {e}")
        return False
    
    try:
        with open('data/analises.json', 'r', encoding='utf-8') as f:
            analises_data = json.load(f)
            analises = analises_data.get('analises', [])
            print(f"📊 Análises encontradas: {len(analises)}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar análises: {e}")
        return False
    
    return True

def simular_exclusao_analise():
    """Simular o processo de exclusão de análise"""
    print("\n=== SIMULANDO EXCLUSÃO DE ANÁLISE ===")
    
    data_service = DataService()
    
    # Obter primeira intimação com análises
    intimacoes = data_service.get_all_intimacoes()
    
    if not intimacoes:
        print("❌ Nenhuma intimação encontrada")
        return False
    
    intimacao_teste = None
    for intimacao in intimacoes:
        if intimacao.get('analises') and len(intimacao['analises']) > 0:
            intimacao_teste = intimacao
            break
    
    if not intimacao_teste:
        print("❌ Nenhuma intimação com análises encontrada")
        return False
    
    print(f"🎯 Testando com intimação: {intimacao_teste['id']}")
    print(f"   Análises antes: {len(intimacao_teste['analises'])}")
    
    # Obter primeira análise para excluir
    if not intimacao_teste['analises']:
        print("❌ Intimação não tem análises")
        return False
    
    analise_id = intimacao_teste['analises'][0]['id']
    print(f"🗑️ Excluindo análise: {analise_id}")
    
    # Simular o processo da rota /api/analises/excluir
    try:
        # 1. Buscar intimação
        intimacao = data_service.get_intimacao_by_id(intimacao_teste['id'])
        if not intimacao:
            print("❌ Intimação não encontrada")
            return False
        
        print(f"✅ Intimação encontrada: {intimacao['id']}")
        print(f"   Análises atuais: {len(intimacao.get('analises', []))}")
        
        # 2. Remover análise da lista
        if 'analises' in intimacao:
            intimacao['analises'] = [a for a in intimacao['analises'] if a.get('id') != analise_id]
            print(f"   Análises após remoção: {len(intimacao['analises'])}")
        
        # 3. Salvar intimação atualizada
        print("💾 Salvando intimação atualizada...")
        data_service.save_intimacao(intimacao)
        print("✅ Intimação salva")
        
        # 4. Excluir análise do arquivo de análises
        print("🗑️ Excluindo análise do arquivo de análises...")
        resultado = data_service.delete_analise(analise_id)
        print(f"✅ Análise excluída: {resultado}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante exclusão: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_integridade_depois():
    """Verificar integridade dos dados depois do teste"""
    print("\n=== VERIFICAÇÃO DEPOIS DO TESTE ===")
    
    try:
        with open('data/intimacoes.json', 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 Tamanho do arquivo: {len(content)} caracteres")
            
            # Verificar se é JSON válido
            try:
                intimacoes_data = json.loads(content)
                intimacoes = intimacoes_data.get('intimacoes', [])
                print(f"📋 Intimações encontradas: {len(intimacoes)}")
                
                for i, intimacao in enumerate(intimacoes):
                    print(f"  - ID: {intimacao.get('id', 'N/A')}")
                    print(f"    Análises: {len(intimacao.get('analises', []))}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ ERRO JSON: {e}")
                print(f"   Posição: linha {e.lineno}, coluna {e.colno}")
                
                # Mostrar contexto do erro
                lines = content.split('\n')
                if e.lineno <= len(lines):
                    start = max(0, e.lineno - 3)
                    end = min(len(lines), e.lineno + 2)
                    print("   Contexto:")
                    for i in range(start, end):
                        marker = " >>> " if i == e.lineno - 1 else "     "
                        print(f"{marker}{i+1:3d}: {lines[i]}")
                
                return False
                
    except Exception as e:
        print(f"❌ Erro ao verificar intimações: {e}")
        return False
    
    return True

def main():
    """Função principal"""
    print("🔍 TESTE DE DEBUG - EXCLUSÃO DE ANÁLISES")
    print("=" * 50)
    
    # Criar backup
    criar_backup_teste()
    
    # Verificar integridade antes
    if not verificar_integridade_antes():
        print("❌ Falha na verificação inicial")
        return
    
    # Simular exclusão
    if not simular_exclusao_analise():
        print("❌ Falha na simulação de exclusão")
        return
    
    # Verificar integridade depois
    if not verificar_integridade_depois():
        print("❌ PROBLEMA DETECTADO: Corrupção após exclusão")
    else:
        print("✅ Teste concluído sem problemas")

if __name__ == "__main__":
    main()