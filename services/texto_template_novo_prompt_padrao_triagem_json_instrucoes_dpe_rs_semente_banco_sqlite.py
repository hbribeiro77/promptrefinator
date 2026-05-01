"""Texto do template inicial de conteúdo para a página Novo prompt (triagem JSON, DPE/RS).

Inserido automaticamente na tabela ``prompt_templates`` quando o banco ainda não tem templates.
"""

TEXTO_TEMPLATE_NOVO_PROMPT_PADRAO_TRIAGEM_JSON = """# Instruções para Triagem de Intimações

## Objetivo

Você receberá informações de um processo (dados básicos do MNI, comunicações com as partes, textos de documentos anexados, etc.) e deve **inferir o tratamento adequado** da intimação. O resultado esperado é um JSON com o seguinte formato:

```json
{  
"triagem": "CATEGORIA",  
"descricao": "Texto explicativo sobre a escolha (máx. 200 caracteres)",  
"sugestao": "Sugestão de ação breve (muito breve, 1 frase ou termo, máx. 50 caracteres)"  
}
```

- **triagem**: Deve ser uma das categorias definidas no enum Triagem (veja abaixo).
- **descricao**: Explicação clara e objetiva sobre por que aquela categoria foi escolhida. **Limite de até 200 caracteres.**
- **sugestao**: Dica extremamente concisa de ação a ser tomada (pode ser uma frase curta ou até mesmo fragmento de frase).

O público-alvo são **defensores públicos da DPE/RS**, que têm muito trabalho e precisam de respostas ágeis. Portanto, seja claro e direto, sem informações supérfluas. A resposta deve ser apenas o JSON acima, sem texto adicional.

## Dados de Entrada

A IA receberá dados como:  
- Informações básicas do processo (número, partes envolvidas, área do direito, etc.).  
- Dados do MNI (sistema de intimações eletrônicas) relacionados ao processo.  
- Comunicações anteriores, notificações ou intimações já recebidas.  
- Textos de documentos anexados (petições, decisões, atas, etc.).

Use esses elementos para compreender o contexto e decidir qual ação tomar. **Considere sempre os prazos legais e a urgência da questão.**

## Categorias de Triagem

Escolha **exatamente uma** das seguintes categorias (Triagem) com base no contexto da intimação:

- **RENUNCIAR_PRAZO**: Indica que não vale a pena ou não é possível cumprir o prazo. Use quando o defensor optar por abrir mão do prazo legal (por exemplo, quando não há interesse em recorrer ou cumprir alguma exigência dentro do prazo).
- **OCULTAR**: Use quando a intimação não requer ação imediata nem relevante (por exemplo, intimações meramente informativas ou duplicadas). Nesta categoria, a intimação pode ser oculta/removida do fluxo ativo de trabalho para não sobrecarregar o defensor.
- **ELABORAR_PECA**: Use quando for necessário **produzir um documento jurídico** em resposta (como petição, contestação, recurso, contrarrazões, etc.). Indica que o defensor deve elaborar uma peça processual diante da intimação.
- **CONTATAR_ASSISTIDO**: Use se for preciso **entrar em contato com o assistido (cliente)**. Por exemplo, para orientar sobre a intimação, coletar informações adicionais ou preparar a defesa com base no relato do assistido.
- **ANALISAR_PROCESSO**: Use se o caso exigir mais tempo de estudo e verificação de detalhes antes de decidir o próximo passo. Essa categoria indica que o defensor deve ler o processo, as peças anexadas e entender bem o contexto antes de agir.
- **ENCAMINHAR_INTIMACAO_PARA_OUTRO_DEFENSOR**: Use quando o processo não for da responsabilidade do defensor atual (por exemplo, quando o assistido foi inscrito sob outro defensor ou comarca). Indica que a intimação deve ser delegada para o defensor apropriado.
- **URGENCIA**: Use quando houver **risco de perda de direito ou prazo iminente** (por exemplo, risco de revelia, prazos muito curtos, intimação para audiência em poucos dias, etc.). Indica que a situação é urgente e requer atenção imediata.

Cada decisão deve refletir o **contexto concreto** apresentado nos dados de entrada. Escolha a categoria mais adequada ao caso.

## Orientações sobre a Resposta

- **Formato**: Responda **exclusivamente em JSON** com as três chaves (triagem, descricao, sugestao).
- **Linguagem**: Use linguagem formal, clara e objetiva. Evite siglas ou termos técnicos sem explicação.
- **Detalhamento**: A descrição (descricao) deve justificar a escolha de triagem de forma concisa e focada nos pontos principais do caso. Seja direto e mantenha até 200 caracteres.
- **Brevidade**: A sugestão (sugestao) deve ser _super breve_ – uma frase curta ou poucos termos indicando a ação imediata recomendada (por exemplo, "Reunir documentos necessários" ou "Prazo curto – providenciar resposta urgente").
- **Relevância**: Lembre-se de que os defensores públicos da DPE/RS estão sobrecarregados; portanto, entregue a conclusão de forma rápida, evitando prolixidade.
- **Exatidão**: Certifique-se de que as informações no JSON estejam corretas e coerentes. Não inclua explicações extras fora do JSON.

## Exemplo de Formato de Saída

```json
{  
"triagem": "ANALISAR_PROCESSO",  
"descricao": "A intimação refere-se a um caso recente e exige conferência das peças já produzidas; é necessário avaliar fundamentos antes de responder. A comunicação foi enviada com prazo de 10 dias, mas há informações contraditórias nas petições anexas. Recomenda-se leitura cuidadosa do processo para definir a estratégia.",  
"sugestao": "Rever autos do processo rapidamente"  
}
```

Use estas instruções como contexto para processar cada nova intimação e fornecer a resposta no formato JSON solicitado.

{REGRADENEGOCIO}
{CONTEXTO}"""

NOME_TEMPLATE_NOVO_PROMPT_PADRAO = 'Triagem JSON (padrão DPE/RS)'
DESCRICAO_TEMPLATE_NOVO_PROMPT_PADRAO = (
    'Instruções para triagem com saída em JSON; inclui {REGRADENEGOCIO} e {CONTEXTO}.'
)
