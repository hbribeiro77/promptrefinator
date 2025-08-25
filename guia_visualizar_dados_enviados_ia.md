# 👁️ Guia: Como Ver Exatamente o que Está Sendo Enviado para a IA

## 🎯 **Sim! Você pode ver TUDO que é enviado para a IA**

Existem várias formas de visualizar os dados enviados para a IA. Aqui estão todas as opções:

## 🔍 **Método 1: Console do Navegador (Mais Detalhado)**

### **Passo a Passo:**
1. **Abra a página de análise**: http://localhost:5000/analise
2. **Pressione F12** para abrir as ferramentas de desenvolvedor
3. **Vá para a aba "Console"**
4. **Execute uma análise**
5. **Veja os logs detalhados**:

```javascript
=== DEBUG: executarAnaliseReal chamada com dados: {
  "prompt_id": "1",
  "intimacao_ids": ["1", "2"],
  "configuracoes": {
    "modelo": "gpt-4",
    "temperatura": 0.7,
    "max_tokens": 500,
    "timeout": 30,
    "salvar_resultados": true,
    "calcular_acuracia": true,
    "modo_paralelo": false
  }
}
```

### **O que você verá:**
- ✅ **Dados enviados**: Prompt ID, intimações selecionadas, configurações
- ✅ **Status da requisição**: Se foi enviada com sucesso
- ✅ **Resposta do backend**: Dados retornados pela IA
- ✅ **Prompt completo**: O texto exato enviado para a IA
- ✅ **Resposta completa**: A resposta bruta da IA

## 🖥️ **Método 2: Terminal do Servidor (Logs Detalhados)**

### **No terminal onde o Flask está rodando, você verá:**

```
=== DEBUG: Prompt ID: 1 ===
=== DEBUG: Intimação IDs: ['1', '2'] ===
=== DEBUG: Configurações - Modelo: gpt-4, Temp: 0.7, Tokens: 500 ===
=== DEBUG: Prompt encontrado: Classificação de Intimações ===
=== DEBUG: Analisando intimação 1 ===
=== DEBUG: Classificação manual: CUMPRIR PRAZO ===
=== DEBUG: Prompt final preparado (primeiros 200 chars): 
Você é um assistente especializado em análise de intimações...
=== DEBUG: Prompt final (primeiros 500 chars): [TEXTO COMPLETO] ===
=== DEBUG: Prompt final (últimos 500 chars): [TEXTO COMPLETO] ===
=== DEBUG: Chamando OpenAI com parâmetros: {
  'model': 'gpt-4',
  'temperature': 0.7,
  'max_tokens': 500,
  'top_p': 1.0
} ===
=== DEBUG: Resposta completa da OpenAI: [RESPOSTA BRUTA] ===
=== DEBUG: Classificação extraída: CUMPRIR PRAZO ===
```

## 🌐 **Método 3: Aba Network do Navegador**

### **Para ver a requisição HTTP completa:**
1. **F12** → aba "Network" (Rede)
2. **Execute uma análise**
3. **Clique na requisição "executar-analise"**
4. **Veja as abas**:
   - **Headers**: Cabeçalhos da requisição
   - **Request**: Dados enviados (JSON completo)
   - **Response**: Resposta do servidor

### **Exemplo do que você verá na aba Request:**
```json
{
  "prompt_id": "1",
  "intimacao_ids": ["1"],
  "configuracoes": {
    "modelo": "gpt-4",
    "temperatura": 0.7,
    "max_tokens": 500,
    "timeout": 30,
    "salvar_resultados": true,
    "calcular_acuracia": true,
    "modo_paralelo": false
  }
}
```

## 📊 **Método 4: Resultados na Interface**

### **Após a análise, você pode ver:**
- **Prompt Completo**: Clique no botão "Ver Prompt" nos resultados
- **Resposta Completa**: Clique no botão "Ver Resposta" nos resultados
- **Parâmetros Utilizados**: Modelo, temperatura, tokens usados
- **Tempo de Processamento**: Quanto tempo levou
- **Custo Estimado**: Custo da requisição

## 🔧 **Método 5: Arquivo de Log Personalizado**

### **Criar um log detalhado:**
```python
# Adicione no app.py para salvar tudo em arquivo
import logging

# Configurar logging
logging.basicConfig(
    filename='analises_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s'
)

# No código da análise:
logging.debug(f"Dados enviados: {dados}")
logging.debug(f"Prompt final: {prompt_final}")
logging.debug(f"Parâmetros IA: {parametros}")
logging.debug(f"Resposta IA: {resposta_completa}")
```

## 🎯 **O que Exatamente Você Pode Ver:**

### **1. Dados de Entrada:**
- ✅ Prompt selecionado (ID e conteúdo)
- ✅ Intimações selecionadas (IDs e contextos)
- ✅ Configurações escolhidas (modelo, temperatura, etc.)

### **2. Processamento:**
- ✅ Prompt final montado (com contexto das intimações)
- ✅ Parâmetros exatos enviados para a IA
- ✅ Tempo de processamento

### **3. Resposta da IA:**
- ✅ Resposta bruta completa
- ✅ Classificação extraída
- ✅ Tokens utilizados
- ✅ Custo estimado

### **4. Comparação:**
- ✅ Classificação manual vs IA
- ✅ Se acertou ou não
- ✅ Informações adicionais

## 🚀 **Teste Prático Agora:**

### **1. Console do Navegador:**
```
1. Abra http://localhost:5000/analise
2. F12 → Console
3. Execute uma análise
4. Veja os logs detalhados
```

### **2. Terminal do Servidor:**
```
1. Olhe o terminal onde Flask está rodando
2. Execute uma análise
3. Veja todos os logs de DEBUG
```

### **3. Network Tab:**
```
1. F12 → Network
2. Execute análise
3. Clique em "executar-analise"
4. Veja Request/Response
```

## 💡 **Dicas Extras:**

### **Para ver ainda mais detalhes:**
- **Ative modo debug**: No `app.py`, certifique-se que `debug=True`
- **Logs personalizados**: Adicione seus próprios `print()` onde quiser
- **Breakpoints**: Use debugger do navegador para pausar e inspecionar

### **Para salvar os dados:**
- **Screenshots**: Tire prints dos logs
- **Copy/Paste**: Copie os logs do console
- **Arquivo de log**: Implemente logging em arquivo
- **Exportar**: Use as funções de exportação da aplicação

## ✅ **Resumo:**

**SIM, você pode ver TUDO:**
- 🔍 **Console**: Logs detalhados em tempo real
- 🖥️ **Terminal**: Logs do servidor com todos os detalhes
- 🌐 **Network**: Requisição HTTP completa
- 📊 **Interface**: Resultados formatados
- 📝 **Logs**: Arquivo de log personalizado

**Transparência total!** Você tem acesso completo a todos os dados enviados e recebidos da IA.