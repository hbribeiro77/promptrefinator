import json
from datetime import datetime

# Carregar prompts existentes
with open('data/prompts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Criar prompt de teste com regra de negócio
prompt_teste = {
    "id": "teste-regra-negocio-123",
    "nome": "Prompt Teste com Regra de Negócio",
    "descricao": "Prompt para testar o botão de copiar regra de negócio",
    "regra_negocio": "Esta é uma regra de negócio de teste. Ela contém informações importantes sobre como processar intimações relacionadas a alvarás e erros de grafia. Quando a Defensoria recebe um alvará, deve verificar se o documento quita o débito e informar ao juízo sobre o interesse no prosseguimento.",
    "conteudo": "Use a seguinte regra de negócio: {REGRADENEGOCIO}\n\nContexto da intimação: {CONTEXTO}",
    "data_criacao": datetime.now().isoformat(),
    "total_usos": 0,
    "acuracia_media": 0.0,
    "tempo_medio": 0.0,
    "custo_total": 0.0,
    "historico_uso": []
}

# Adicionar o prompt de teste
data['prompts'].append(prompt_teste)

# Salvar de volta
with open('data/prompts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Prompt de teste criado com ID: {prompt_teste['id']}")
print(f"Regra de negócio: {prompt_teste['regra_negocio'][:100]}...")
