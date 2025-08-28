import json

with open('data/prompts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total de prompts: {len(data["prompts"])}')

# Verificar campos do primeiro prompt
if data['prompts']:
    primeiro_prompt = data['prompts'][0]
    print(f'Campos do primeiro prompt: {list(primeiro_prompt.keys())}')
    
    # Verificar se há algum campo relacionado a regra de negócio
    campos_com_regra = [k for k in primeiro_prompt.keys() if 'regra' in k.lower() or 'negocio' in k.lower()]
    print(f'Campos com "regra" ou "negocio": {campos_com_regra}')
    
    # Mostrar alguns prompts para ver a estrutura
    for i, p in enumerate(data['prompts'][:3]):
        print(f'\nPrompt {i+1}:')
        print(f'Nome: {p["nome"]}')
        for campo, valor in p.items():
            if campo != 'conteudo' and campo != 'historico_uso':
                print(f'{campo}: {valor}')
