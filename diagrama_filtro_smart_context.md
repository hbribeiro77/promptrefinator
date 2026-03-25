# 📊 Diagrama em Blocos - Filtro Smart Context

## 🎯 Objetivo
Implementar filtro por Smart Context na página de análise, permitindo filtrar intimações que possuem ou não contexto inteligente.

---

## 📦 Diagrama de Blocos das Modificações

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODIFICAÇÕES - FILTRO SMART CONTEXT                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼──────────┐        ┌───────────▼──────────┐
        │  1. MODAL DE FILTROS │        │  2. ESTRUTURA HTML   │
        │     (HTML)           │        │     (Tabela)         │
        └───────────┬──────────┘        └───────────┬──────────┘
                    │                               │
                    │                               │
        ┌───────────▼──────────┐        ┌───────────▼──────────┐
        │ Seção "Smart Context"│        │ data-smart-context   │
        │ - Checkbox "Todas"   │        │ no atributo <tr>    │
        │ - Checkbox "Com SC"  │        │ (valor: '1' ou '0') │
        │ - Checkbox "Sem SC"  │        │                      │
        └──────────────────────┘        └──────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  3. JAVASCRIPT - LÓGICA       │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐      ┌──────────▼──────────┐    ┌──────────▼──────────┐
│ aplicarFiltro() │      │ limparFiltros()     │    │ Event Listeners    │
│                 │      │                     │    │                     │
│ - Lê checkboxes │      │ - Reseta checkboxes │    │ - "Todas" desmarca │
│ - Obtém valor    │      │ - Mostra todas      │    │   "Com" e "Sem"    │
│   data-attr    │      │   intimações        │    │ - "Com" desmarca    │
│ - Calcula      │      │                     │    │   "Todas" e "Sem"   │
│   mostrarSmart │      │                     │    │ - "Sem" desmarca    │
│   Context      │      │                     │    │   "Todas" e "Com"   │
│ - Aplica filtro│      │                     │    │                     │
└────────────────┘      └─────────────────────┘    └─────────────────────┘
```

---

## 🔧 Detalhamento dos Blocos

### **BLOCO 1: Modal de Filtros (HTML)**

```
┌─────────────────────────────────────────────────────────────┐
│  MODAL DE FILTROS - Seção Smart Context                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚡ Smart Context:                                          │
│                                                             │
│  ☑ Todas as intimações (padrão: checked)                  │
│  ☐ Apenas com Smart Context                                │
│  ☐ Apenas sem Smart Context                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Localização:** `templates/analise.html` - Linhas 733-759

**Elementos:**
- `#filtro-todos-smart-context` - Checkbox "Todas as intimações"
- `#filtro-apenas-smart-context` - Checkbox "Apenas com Smart Context"
- `#filtro-sem-smart-context` - Checkbox "Apenas sem Smart Context"

---

### **BLOCO 2: Estrutura HTML da Tabela**

```
┌─────────────────────────────────────────────────────────────┐
│  ATRIBUTO data-smart-context na Tag <tr>                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  <tr class="intimacao-row"                                  │
│      data-intimacao-id="..."                               │
│      data-defensor="..."                                    │
│      data-classe="..."                                      │
│      data-smart-context="1" ou "0">  ← NOVO               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Localização:** `templates/analise.html` - Linha 332

**Valores:**
- `data-smart-context="1"` - Quando `intimacao.smart_context = True`
- `data-smart-context="0"` - Quando `intimacao.smart_context = False`

---

### **BLOCO 3: JavaScript - Função aplicarFiltro()**

```
┌─────────────────────────────────────────────────────────────┐
│  FUNÇÃO aplicarFiltro() - Lógica Smart Context              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. LER CHECKBOXES:                                         │
│     ✓ todosSmartContext = #filtro-todos-smart-context       │
│     ✓ apenasSmartContext = #filtro-apenas-smart-context   │
│     ✓ semSmartContext = #filtro-sem-smart-context          │
│                                                             │
│  2. OBTER VALOR DO DATA-ATTR:                               │
│     ✓ smartContextValue = row.dataset.smartContext          │
│     ✓ temSmartContext = (smartContextValue === '1')        │
│                                                             │
│  3. CALCULAR mostrarSmartContext:                           │
│     Se "Todas" marcado:                                     │
│       → mostrarSmartContext = true                          │
│                                                             │
│     Se "Apenas com SC" marcado:                             │
│       → mostrarSmartContext = temSmartContext               │
│                                                             │
│     Se "Apenas sem SC" marcado:                             │
│       → mostrarSmartContext = !temSmartContext              │
│                                                             │
│  4. APLICAR FILTRO:                                         │
│     → Incluído na condição final:                          │
│        if (mostrarDefensor && ... && mostrarSmartContext)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Localização:** `templates/analise.html` - Linhas 2515-2559

---

### **BLOCO 4: JavaScript - Função limparFiltros()**

```
┌─────────────────────────────────────────────────────────────┐
│  FUNÇÃO limparFiltros() - Reset Smart Context              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Resetar checkboxes:                                        │
│  ✓ #filtro-todos-smart-context.checked = true              │
│  ✓ #filtro-apenas-smart-context.checked = false            │
│  ✓ #filtro-sem-smart-context.checked = false               │
│                                                             │
│  Mostrar todas as intimações:                               │
│  ✓ row.style.display = ''                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Localização:** `templates/analise.html` - Linhas 2601-2603

---

### **BLOCO 5: JavaScript - Event Listeners**

```
┌─────────────────────────────────────────────────────────────┐
│  EVENT LISTENERS - Controle Mutuamente Exclusivo          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────┐              │
│  │ "Todas" marcado                          │              │
│  │   → Desmarca "Com SC"                    │              │
│  │   → Desmarca "Sem SC"                    │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
│  ┌──────────────────────────────────────────┐              │
│  │ "Com SC" marcado                         │              │
│  │   → Desmarca "Todas"                     │              │
│  │   → Desmarca "Sem SC"                    │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
│  ┌──────────────────────────────────────────┐              │
│  │ "Sem SC" marcado                         │              │
│  │   → Desmarca "Todas"                     │              │
│  │   → Desmarca "Com SC"                    │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Localização:** `templates/analise.html` - Linhas 2448-2481

---

## 🔄 Fluxo Completo de Funcionamento

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DO FILTRO                          │
└─────────────────────────────────────────────────────────────┘
                    │
        ┌───────────▼──────────┐
        │ Usuário clica        │
        │ "Filtrar"            │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Modal abre           │
        │ Carrega filtros      │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Usuário seleciona:   │
        │ - "Apenas com SC"    │
        │   OU                 │
        │ - "Apenas sem SC"    │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Event Listener       │
        │ desmarca opções      │
        │ conflitantes         │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Usuário clica        │
        │ "Aplicar Filtro"     │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ aplicarFiltro()      │
        │ executa              │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Para cada linha:     │
        │ 1. Lê data-smart-    │
        │    context           │
        │ 2. Calcula se deve   │
        │    mostrar           │
        │ 3. Oculta/Exibe      │
        └───────────┬───────────┘
                    │
        ┌───────────▼──────────┐
        │ Tabela atualizada    │
        │ Modal fecha           │
        └───────────────────────┘
```

---

## 📍 Arquivos Modificados

```
templates/analise.html
│
├── Linha 332: data-smart-context no <tr>
│
├── Linhas 733-759: Seção de filtro no modal
│
├── Linhas 2448-2481: Event listeners
│
├── Linhas 2515-2559: Lógica na função aplicarFiltro()
│
└── Linhas 2601-2603: Reset na função limparFiltros()
```

---

## ✅ Funcionalidades Implementadas

```
┌─────────────────────────────────────────────────────────────┐
│                    CHECKLIST DE FUNCIONALIDADES            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Seção de filtro no modal                               │
│  ✅ 3 opções: Todas / Com SC / Sem SC                      │
│  ✅ Atributo data-smart-context na linha                    │
│  ✅ Lógica de filtro na função aplicarFiltro()             │
│  ✅ Event listeners para controle mutuamente exclusivo     │
│  ✅ Reset na função limparFiltros()                         │
│  ✅ Integração com outros filtros existentes                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Visual da Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Modal: Filtrar Intimações                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚡ Smart Context:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Todas as intimações                               │   │
│  │ ☐ Apenas com Smart Context                           │   │
│  │ ☐ Apenas sem Smart Context                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Aplicar Filtro  │  │  Limpar Filtros   │              │
│  └──────────────────┘  └──────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Resumo das Modificações

### **1. HTML - Modal**
- ✅ Adicionada seção "Smart Context" com 3 checkboxes
- ✅ Posicionada antes do filtro "Destaque"

### **2. HTML - Tabela**
- ✅ Adicionado `data-smart-context` no atributo `<tr>`
- ✅ Valor: `'1'` se `smart_context = True`, `'0'` se `False`

### **3. JavaScript - Lógica de Filtro**
- ✅ Função `aplicarFiltro()` atualizada
- ✅ Lê valor do `data-smart-context`
- ✅ Calcula `mostrarSmartContext` baseado nos checkboxes
- ✅ Aplica filtro junto com outros filtros existentes

### **4. JavaScript - Event Listeners**
- ✅ Controle mutuamente exclusivo entre opções
- ✅ Quando uma opção é marcada, as outras são desmarcadas

### **5. JavaScript - Limpar Filtros**
- ✅ Reset dos checkboxes de Smart Context
- ✅ Mostra todas as intimações ao limpar

---

## 🎯 Resultado Final

O filtro de Smart Context está totalmente funcional e integrado ao sistema de filtros existente. O usuário pode:

1. ✅ Filtrar por **todas as intimações** (padrão)
2. ✅ Filtrar **apenas intimações com Smart Context**
3. ✅ Filtrar **apenas intimações sem Smart Context**
4. ✅ Combinar com outros filtros (defensor, classe, etc.)
5. ✅ Limpar o filtro e voltar ao estado padrão

