#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar as intimações recuperadas
"""

import json

def main():
    print("=== VERIFICAÇÃO DAS INTIMAÇÕES RECUPERADAS ===")
    
    # Carregar arquivo atual
    with open('data/intimacoes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    intimacoes = data.get('intimacoes', [])
    print(f"Total de intimações: {len(intimacoes)}")
    print("\nLista de intimações:")
    
    for i, intimacao in enumerate(intimacoes, 1):
        processo = intimacao.get('processo', 'N/A')
        classificacao = intimacao.get('classificacao_manual', 'N/A')
        id_intimacao = intimacao.get('id', 'N/A')
        print(f"{i}. {id_intimacao}: {processo} ({classificacao})")

if __name__ == '__main__':
    main()