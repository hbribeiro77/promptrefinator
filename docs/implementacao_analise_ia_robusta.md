# 🚀 Lições Aprendidas: Implementação de Análise de IA

## 📋 **O que REALMENTE implementamos**

Este documento registra as lições aprendidas durante a implementação do sistema de análise de IA na página de comparação de prompts.

---

## 🎯 **Fluxo Completo Implementado**

### **1. Botão "Configurar" (Modal de Configuração)**
**O que aparece:**
- Modal com campos para configurar o prompt de análise
- **Persona + Instruções**: Campo único para definir como a IA deve se comportar
- **Instruções de Resposta**: Como a IA deve formatar a resposta (JSON ou livre)
- **Checkboxes**: Incluir contexto da intimação e gabarito
- **Persistência**: Configurações salvas no localStorage

**Código relevante:**
```javascript
// static/js/comparar_prompts.js - função configurarPromptAnalise()
const modalHtml = `
    <div class="modal-body">
        <form id="formConfigPrompt">
            <div class="mb-3">
                <label for="persona">Persona + Instruções de Análise:</label>
                <textarea id="persona" rows="6">${configPromptAnalise.persona}</textarea>
            </div>
            <div class="mb-3">
                <label for="instrucoesResposta">Instruções de Resposta:</label>
                <textarea id="instrucoesResposta" rows="5">${configPromptAnalise.instrucoesResposta}</textarea>
            </div>
            <div class="form-check">
                <input type="checkbox" id="incluirContexto" ${configPromptAnalise.incluirContextoIntimacao ? 'checked' : ''}>
                <label for="incluirContexto">Incluir Contexto da Intimação</label>
            </div>
            <div class="form-check">
                <input type="checkbox" id="incluirGabarito" ${configPromptAnalise.incluirInformacaoAdicional ? 'checked' : ''}>
                <label for="incluirGabarito">Incluir Gabarito (Classificação Manual)</label>
            </div>
        </form>
    </div>
`;
```

### **2. Botão "Ver Prompt" (Modal de Visualização)**
**O que aparece:**
- Modal mostrando o prompt completo que será enviado para a IA
- **Seções estruturadas**: INSTRUÇÕES, CONTEXTO DA INTIMAÇÃO, GABARITO, CONJUNTOS DE REGRAS
- **Estatísticas**: Caracteres, palavras, linhas do prompt
- **Taxas reais**: Taxa de acerto de cada prompt capturada dos badges
- **Botão "Copiar Prompt"**: Para área de transferência

**Código relevante:**
```javascript
// static/js/comparar_prompts.js - função visualizarPromptAnalise()
let promptAnalise = `=== INSTRUÇÕES ===
${configPromptAnalise.persona}

=== CONTEXTO DA INTIMAÇÃO ===
`;

// Adicionar contexto se habilitado
if (configPromptAnalise.incluirContextoIntimacao) {
    promptAnalise += `CONTEXTO DA INTIMAÇÃO:
- ID: ${intimacaoData.id}
- Processo: ${intimacaoData.processo}
- Classe: ${intimacaoData.classe}
// ... mais dados
`;
}

// Adicionar gabarito se habilitado
if (configPromptAnalise.incluirInformacaoAdicional) {
    promptAnalise += `=== GABARITO ===
Classificação: ${intimacaoData.classificacao_manual}
Informações: ${intimacaoData.informacao_adicional}
`;
}

// Adicionar regras com taxas reais
promptAnalise += `=== CONJUNTOS DE REGRAS DE NEGÓCIO A COMPARAR ===

CONJUNTO A - ${nome1.toUpperCase()} (Taxa de acerto: ${taxa1}):
${regra1}

CONJUNTO B - ${nome2.toUpperCase()} (Taxa de acerto: ${taxa2}):
${regra2}
`;
```

### **3. Botão "Analisar com IA" (Fluxo Completo)**
**O que acontece:**
1. **Frontend**: Captura taxas reais dos badges, envia para backend
2. **Backend**: Usa configurações do usuário (modelo, temperatura, tokens)
3. **IA**: Processa prompt estruturado com dados reais
4. **Resposta**: Retorna análise em JSON ou texto livre

**Código relevante:**
```javascript
// static/js/comparar_prompts.js - função analisarDiferencasComIA()
fetch('/api/analisar-diferencas-prompts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        regra_negocio_1: regra1Limpa,
        regra_negocio_2: regra2Limpa,
        nome_prompt_1: nome1,
        nome_prompt_2: nome2,
        taxa_prompt_1: taxa1,  // Taxa real capturada do badge
        taxa_prompt_2: taxa2,  // Taxa real capturada do badge
        config_personalizada: configPromptAnalise,  // Configuração do modal
        intimacao_id: window.intimacaoData ? window.intimacaoData.id : null
    })
})
```

### **4. Backend - API `/api/analisar-diferencas-prompts`**
**O que faz:**
1. **Recebe dados**: Regras, nomes, taxas, configuração personalizada
2. **Carrega intimação**: Se intimacao_id fornecido
3. **Constrói prompt**: Baseado na configuração personalizada ou padrão
4. **Usa configurações do usuário**: Modelo, temperatura, tokens da página de configuração
5. **Chama IA**: Com parâmetros corretos
6. **Retorna resposta**: JSON estruturado ou texto livre

**Código relevante:**
```python
# app.py - função analisar_diferencas_prompts()
# Usar configuração personalizada se disponível
if config_personalizada and config_personalizada != {}:
    persona = config_personalizada.get('persona', 'Você é um especialista...')
    instrucoes_resposta = config_personalizada.get('instrucoesResposta', '')
    incluir_contexto = config_personalizada.get('incluirContextoIntimacao', True)
    incluir_gabarito = config_personalizada.get('incluirInformacaoAdicional', True)
    
    # Construir prompt com dados reais
    prompt_analise = f"""{persona}

{contexto_intimacao}

{informacao_adicional}

CONJUNTO A - {nome_prompt_1.upper()} (Taxa de acerto: {taxa_prompt_1}):
{regra_negocio_1}

CONJUNTO B - {nome_prompt_2.upper()} (Taxa de acerto: {taxa_prompt_2}):
{regra_negocio_2}

{instrucoes_resposta}"""

# Usar configurações do usuário (não hardcode)
provider_atual = ai_service.get_current_provider()
config = data_service.get_config() or {}

if provider_atual == 'azure':
    modelo_analise = config.get('azure_deployment')
    temperatura_analise = config.get('azure_temperatura')
    max_tokens_analise = config.get('azure_max_tokens')
elif provider_atual == 'openai':
    modelo_analise = config.get('modelo_padrao')
    temperatura_analise = config.get('temperatura_padrao')
    max_tokens_analise = config.get('max_tokens_padrao')

# Chamar IA com parâmetros corretos
parametros_analise = {
    'model': modelo_analise,
    'temperature': temperatura_analise,
    'max_tokens': max_tokens_analise,
    'top_p': 1.0
}

classificacao, resposta_texto, tokens_info = ai_service.analisar_intimacao(
    "",  # contexto vazio - já está no prompt
    prompt_analise,  # prompt completo
    parametros_analise
)
```

---

## 🎯 **De onde vêm os parâmetros da IA**

### **1. Configuração do Usuário (Página de Configuração)**
- **Modelo**: `config.get('azure_deployment')` ou `config.get('modelo_padrao')`
- **Temperatura**: `config.get('azure_temperatura')` ou `config.get('temperatura_padrao')`
- **Max Tokens**: `config.get('azure_max_tokens')` ou `config.get('max_tokens_padrao')`

### **2. Configuração Personalizada (Modal "Configurar")**
- **Persona**: Campo "Persona + Instruções de Análise"
- **Instruções de Resposta**: Campo "Instruções de Resposta"
- **Incluir Contexto**: Checkbox "Incluir Contexto da Intimação"
- **Incluir Gabarito**: Checkbox "Incluir Gabarito (Classificação Manual)"

### **3. Dados Reais (Não Inventados)**
- **Taxas de Acerto**: Capturadas dos badges na página
- **Nomes dos Prompts**: Capturados dos links clicáveis
- **Regras de Negócio**: Capturadas dos elementos `[id^="regra-comparacao-"]`
- **Dados da Intimação**: Carregados via `window.intimacaoData`

---

## 🚨 **Problemas que enfrentamos e soluções**

### **1. Erro de Encoding com Emojis**
**❌ Problema:** `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4d1'`
**✅ Solução:** Remoção automática de emojis no JavaScript
```javascript
// Remover emojis do prompt antes de enviar
promptAnalise = promptAnalise.replace(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, "");
```

### **2. JavaScript Quebrado**
**❌ Problema:** Console.log com emoji quebrava o JavaScript
**✅ Solução:** Remover emojis de todos os console.log

### **3. IA Alucinando**
**❌ Problema:** IA inventava taxas de acerto (80%, 95%) e nomes
**✅ Solução:** 
- Usar taxas REAIS capturadas dos badges
- Usar nomes REAIS capturados dos links
- Estruturar prompt com dados reais

### **4. Configuração Incompleta**
**❌ Problema:** Azure OpenAI não configurado, deployment inexistente
**✅ Solução:** 
- Configurar Azure OpenAI completo
- Usar deployment válido (gpt-4o)
- Temperatura 0.0, 16k tokens

---

## 🎯 **Resultado Final**

**✅ Funcionamento Perfeito:**
- Botões funcionando
- Sem erros de encoding
- IA respondendo corretamente
- Taxas reais sendo usadas
- Configuração respeitada

**✅ Fluxo Completo:**
1. **Configurar**: Modal com configurações personalizadas
2. **Ver Prompt**: Modal mostrando prompt completo
3. **Analisar com IA**: Usa configurações do usuário + dados reais
4. **Resposta**: Análise estruturada ou texto livre

**O segredo:** dados reais, configuração correta, e zero emojis no código!
