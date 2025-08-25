# Componente: Tabela de Análises Avançada

## Visão Geral

O componente `tabela_analises_avancada.html` é uma versão avançada da tabela de análises que inclui funcionalidades completas de configuração, filtros, paginação e exportação. Este componente é ideal para páginas de relatórios detalhados e análise avançada de dados.

## Arquivo

```
templates/partials/tabela_analises_avancada.html
```

## Características Principais

### ✅ **Configuração de Colunas**
- **Visibilidade**: Controle individual de cada coluna
- **Persistência**: Configurações salvas no localStorage
- **Interface**: Checkboxes organizados por categoria
- **Ações**: Selecionar todas, limpar seleção, salvar

### ✅ **Filtros Rápidos**
- **Status**: Acertou/Errou
- **Prompt**: Filtro por prompt específico
- **Período**: Hoje, última semana, último mês
- **Limpeza**: Botão para limpar todos os filtros

### ✅ **Contadores e Métricas**
- **Total**: Número de análises encontradas
- **Acertos**: Contador de análises corretas
- **Erros**: Contador de análises incorretas
- **Tempo Real**: Atualização automática

### ✅ **Paginação**
- **Navegação**: Botões anterior/próximo
- **Informação**: Página atual e total de páginas
- **Configurável**: Itens por página ajustáveis

### ✅ **Exportação**
- **Seleção**: Exportar análises selecionadas
- **Validação**: Verificação de itens selecionados
- **Feedback**: Mensagens de status

### ✅ **Interatividade**
- **Checkboxes**: Seleção individual e em massa
- **Modais**: Visualização de prompts e respostas
- **Ações**: Visualizar e excluir análises
- **Responsivo**: Adaptação a diferentes tamanhos de tela

## Como Usar

### 1. Incluir o Componente

```html
{% set analises = lista_de_analises %}
{% set prompts = lista_de_prompts %}
{% include 'partials/tabela_analises_avancada.html' %}
```

### 2. Passar Dados

```python
# No seu route/controller
analises = [
    {
        'id': 'analise-001',
        'intimacao_id': 'demo-001',
        'data_analise': '2025-01-15T10:30:00',
        'contexto': 'Contexto da intimação...',
        'prompt_nome': 'Classificar Intimação',
        'prompt_completo': 'Prompt completo...',
        'classificacao_manual': 'ELABORAR PEÇA',
        'informacao_adicional': 'Informação adicional...',
        'resultado_ia': 'ELABORAR PEÇA',
        'acertou': True,
        'modelo': 'gpt-4',
        'temperatura': 0.1,
        'tempo_processamento': 2.5,
        
        'resposta_completa': 'Resposta da IA...'
    }
]

prompts = [
    {'id': 'prompt-001', 'nome': 'Classificar Intimação'},
    {'id': 'prompt-002', 'nome': 'Analisar Processo'}
]

return render_template('sua_pagina.html', analises=analises, prompts=prompts)
```

### 3. Personalizar Título e Subtítulo

```html
{% set titulo = 'Minhas Análises Detalhadas' %}
{% set subtitulo = 'Visualize e configure as análises do período' %}
{% include 'partials/tabela_analises_avancada.html' %}
```

## Estrutura de Dados

### Objeto de Análise

```javascript
{
    id: 'string',                    // ID único da análise
    intimacao_id: 'string',          // ID da intimação relacionada
    data_analise: 'string',          // Data/hora da análise (ISO)
    contexto: 'string',              // Contexto da intimação
    prompt_nome: 'string',           // Nome do prompt usado
    prompt_completo: 'string',       // Prompt completo enviado
    classificacao_manual: 'string',  // Classificação manual
    informacao_adicional: 'string',  // Informações adicionais
    resultado_ia: 'string',          // Resultado da IA
    acertou: boolean,                // Se a IA acertou
    modelo: 'string',                // Modelo usado (ex: gpt-4)
    temperatura: number,             // Temperatura usada
    tempo_processamento: number,     // Tempo em segundos
    
    resposta_completa: 'string'      // Resposta completa da IA
}
```

### Objeto de Prompt

```javascript
{
    id: 'string',    // ID único do prompt
    nome: 'string'   // Nome do prompt
}
```

## Funcionalidades JavaScript

### Configuração de Colunas

```javascript
// Carregar configuração salva
carregarConfiguracaoColunas();

// Aplicar configuração às colunas
aplicarConfiguracaoColunas();

// Salvar configuração
salvarConfiguracaoColunas();

// Selecionar todas as colunas
selecionarTodasColunas();

// Limpar seleção de colunas
limparSelecaoColunas();
```

### Filtros

```javascript
// Aplicar filtros rápidos
aplicarFiltroRapido();

// Limpar filtros
limparFiltrosRapidos();
```

### Paginação

```javascript
// Navegar para página anterior
paginaAnterior();

// Navegar para próxima página
proximaPagina();

// Atualizar informações de paginação
atualizarPaginacao();
```

### Seleção

```javascript
// Selecionar/desselecionar todas as análises
toggleSelectAllAnalises();

// Atualizar contadores de seleção
updateAnalisesSelection();
```

### Ações

```javascript
// Atualizar tabela
atualizarTabelaAnalises();

// Exportar análises selecionadas
exportarTabelaAnalises();

// Visualizar análise específica
visualizarAnalise(id);

// Excluir análise
excluirAnalise(id);
```

## Personalização

### CSS Customizado

```css
/* Personalizar cores das badges */
.badge.bg-success {
    background-color: #28a745 !important;
}

/* Personalizar hover das linhas */
.table-hover tbody tr:hover {
    background-color: #f8f9fa;
}

/* Personalizar botões de ação */
.btn-group-sm .btn {
    border-radius: 0.25rem;
}
```

### JavaScript Customizado

```javascript
// Sobrescrever função de exportação
function exportarTabelaAnalises() {
    const checkboxes = document.querySelectorAll('.analise-checkbox:checked');
    const dados = Array.from(checkboxes).map(cb => cb.value);
    
    // Sua lógica de exportação personalizada
    console.log('Exportando:', dados);
}

// Adicionar validações customizadas
function validarAnalise(analise) {
    return analise.acertou && analise.tempo_processamento < 5;
}
```

## Dependências

### CSS
- Bootstrap 5
- Bootstrap Icons

### JavaScript
- Navegador com suporte a ES6+
- localStorage para persistência

### HTML
- Estrutura de dados compatível com Jinja2

## Compatibilidade

- **Navegadores**: Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- **Dispositivos**: Desktop, tablet, mobile (responsivo)
- **Frameworks**: Flask/Jinja2, Bootstrap 5

## Exemplos de Uso

### 1. Página de Relatórios

```html
{% extends "base.html" %}
{% block content %}
<div class="container-fluid">
    <h1>Relatórios de Análises</h1>
    
    {% set titulo = 'Análises do Período' %}
    {% set subtitulo = 'Visualize todas as análises realizadas' %}
    {% include 'partials/tabela_analises_avancada.html' %}
</div>
{% endblock %}
```

### 2. Dashboard Administrativo

```html
{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-12">
        {% set titulo = 'Análises Recentes' %}
        {% set subtitulo = 'Últimas 50 análises do sistema' %}
        {% include 'partials/tabela_analises_avancada.html' %}
    </div>
</div>
{% endblock %}
```

### 3. Página de Análise de Performance

```html
{% extends "base.html" %}
{% block content %}
<div class="container-fluid">
    <div class="alert alert-info">
        <i class="bi bi-graph-up"></i>
        <strong>Análise de Performance:</strong> Compare a performance de diferentes prompts e modelos.
    </div>
    
    {% set titulo = 'Performance de Prompts' %}
    {% set subtitulo = 'Análise detalhada de acurácia e tempo' %}
    {% include 'partials/tabela_analises_avancada.html' %}
</div>
{% endblock %}
```

## Troubleshooting

### Problema: Colunas não aparecem/desaparecem
**Solução**: Verificar se o localStorage está disponível e se as configurações estão sendo salvas corretamente.

### Problema: Filtros não funcionam
**Solução**: Implementar a lógica de filtro no JavaScript ou conectar com backend.

### Problema: Exportação não funciona
**Solução**: Implementar a lógica de exportação específica para seu caso de uso.

### Problema: Paginação não atualiza
**Solução**: Verificar se `analisesFiltradas` está sendo populada corretamente.

## Boas Práticas

1. **Performance**: Use paginação para grandes volumes de dados
2. **UX**: Mantenha configurações persistentes no localStorage
3. **Acessibilidade**: Use labels e aria-labels apropriados
4. **Responsividade**: Teste em diferentes tamanhos de tela
5. **Feedback**: Forneça feedback visual para ações do usuário

## Contribuição

Para melhorar este componente:

1. Mantenha a compatibilidade com Bootstrap 5
2. Teste em diferentes navegadores
3. Documente novas funcionalidades
4. Mantenha o código limpo e bem comentado
5. Adicione exemplos de uso
