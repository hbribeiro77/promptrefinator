#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recuperar intimações perdidas após exclusão acidental
"""

import json
import shutil
from datetime import datetime

def carregar_json(arquivo):
    """Carregar arquivo JSON com encoding UTF-8"""
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {arquivo}: {e}")
        return None

def salvar_json(arquivo, dados):
    """Salvar arquivo JSON com encoding UTF-8"""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar {arquivo}: {e}")
        return False

def main():
    print("=== RECUPERAÇÃO DE INTIMAÇÕES PERDIDAS ===")
    
    # Carregar arquivo atual
    arquivo_atual = 'data/intimacoes.json'
    dados_atuais = carregar_json(arquivo_atual)
    
    if not dados_atuais:
        print("Erro ao carregar arquivo atual de intimações")
        return
    
    intimacoes_atuais = dados_atuais.get('intimacoes', [])
    print(f"Intimações atuais: {len(intimacoes_atuais)}")
    
    # Carregar backup mais recente
    arquivo_backup = 'data/backups/20250822_182821_intimacoes.json'
    dados_backup = carregar_json(arquivo_backup)
    
    if not dados_backup:
        print("Erro ao carregar arquivo de backup")
        return
    
    intimacoes_backup = dados_backup.get('intimacoes', [])
    print(f"Intimações no backup: {len(intimacoes_backup)}")
    
    # Identificar intimações perdidas
    ids_atuais = {intimacao['id'] for intimacao in intimacoes_atuais}
    ids_backup = {intimacao['id'] for intimacao in intimacoes_backup}
    
    ids_perdidos = ids_backup - ids_atuais
    print(f"Intimações perdidas: {len(ids_perdidos)}")
    
    if ids_perdidos:
        print("\nIDs das intimações perdidas:")
        for id_perdido in ids_perdidos:
            intimacao_perdida = next((i for i in intimacoes_backup if i['id'] == id_perdido), None)
            if intimacao_perdida:
                processo = intimacao_perdida.get('processo', 'N/A')
                classificacao = intimacao_perdida.get('classificacao_manual', 'N/A')
                print(f"  - {id_perdido}: {processo} ({classificacao})")
        
        # Perguntar se deseja recuperar
        resposta = input("\nDeseja recuperar as intimações perdidas? (s/n): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            # Fazer backup do arquivo atual
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_atual = f'data/backups/{timestamp}_intimacoes_antes_recuperacao.json'
            shutil.copy2(arquivo_atual, backup_atual)
            print(f"Backup do arquivo atual salvo em: {backup_atual}")
            
            # Recuperar intimações perdidas
            intimacoes_perdidas = [i for i in intimacoes_backup if i['id'] in ids_perdidos]
            intimacoes_atuais.extend(intimacoes_perdidas)
            
            # Salvar arquivo atualizado
            dados_atuais['intimacoes'] = intimacoes_atuais
            if salvar_json(arquivo_atual, dados_atuais):
                print(f"\n✅ Recuperação concluída! {len(ids_perdidos)} intimações foram restauradas.")
                print(f"Total de intimações agora: {len(intimacoes_atuais)}")
            else:
                print("❌ Erro ao salvar arquivo recuperado")
        else:
            print("Recuperação cancelada pelo usuário.")
    else:
        print("\n✅ Nenhuma intimação perdida encontrada.")

if __name__ == '__main__':
    main()