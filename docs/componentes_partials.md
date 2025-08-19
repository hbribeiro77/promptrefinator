# Componentes Partials do Sistema

## Visão Geral

O sistema utiliza **componentes partials** do Jinja2 para reutilização de código HTML, CSS e JavaScript. Os partials são arquivos que podem ser incluídos em múltiplas páginas.

## Estrutura de Arquivos

```
templates/
├── partials/
│   ├── card_intimacao.html              # Card completo com ações
│   ├── card_intimacao_compact.html      # Card compacto para tabela
│   ├── tabela_analises.html             # Tabela de análises básica
│   ├── tabela_analises_avancada.html    # Tabela de análises avançada
│   └── modais_prompt_resposta.html      # Modais de prompt/resposta
```

## Componentes Disponíveis

### 1. Card de Intimação Completo
**Arquivo**: `templates/partials/card_intimacao.html`

**Uso**:
```html
{% include 'partials/card_intimacao.html' %}
```

**Características**:
- Card completo com todas as informações
- Botões de ação (visualizar, editar, excluir)
- Design responsivo
- Animações e hover effects
- CSS e JavaScript incluídos

**Parâmetros**:
- `intimacao`: Objeto com dados da intimação
- `show_actions`: Boolean para mostrar/esconder botões

### 2. Card de Intimação Compacto
**Arquivo**: `templates/partials/card_intimacao_compact.html`

**Uso**:
```html
{% include 'partials/card_intimacao_compact.html' %}
```

**Características**:
- Card reduzido para uso em tabelas
- Apenas informações essenciais
- Design compacto e otimizado
- Sem botões de ação

**Parâmetros**:
- `intimacao`: Objeto com dados da intimação

### 3. Tabela de Análises Básica
**Arquivo**: `templates/partials/tabela_analises.html`

**Uso**:
```html
{% include 'partials/tabela_analises.html' %}
```

**Características**:
- Tabela de resultados de análises
- Formatação de dados
- Ações específicas para análises

### 4. Tabela de Análises Avançada
**Arquivo**: `templates/partials/tabela_analises_avancada.html`

**Uso**:
```html
{% include 'partials/tabela_analises_avancada.html' %}
```

**Características**:
- Tabela avançada com configuração de colunas
- Filtros rápidos e paginação
- Contadores e métricas em tempo real
- Exportação de dados selecionados
- Configuração persistente no localStorage

### 5. Modais de Prompt/Resposta
**Arquivo**: `templates/partials/modais_prompt_resposta.html`

**Uso**:
```html
{% include 'partials/modais_prompt_resposta.html' %}
```

**Características**:
- Modais para exibir prompts e respostas
- Formatação de código
- Botões de cópia e fechamento

## Como Criar um Novo Componente

### 1. Estrutura Básica
```html
<!-- templates/partials/meu_componente.html -->
<div class="meu-componente">
    <!-- HTML do componente -->
</div>

<style>
/* CSS específico do componente */
.meu-componente {
    /* estilos */
}
</style>

<script>
// JavaScript específico do componente
function minhaFuncao() {
    // lógica
}
</script>
```

### 2. Incluir o Componente
```html
<!-- Em qualquer template -->
{% include 'partials/meu_componente.html' %}
```

### 3. Passar Dados
```html
<!-- Definir variáveis antes de incluir -->
{% set dados = {'campo': 'valor'} %}
{% include 'partials/meu_componente.html' %}
```

## Vantagens dos Partials

### 1. ✅ Reutilização
- Mesmo código em múltiplas páginas
- Manutenção centralizada
- Consistência visual

### 2. ✅ Organização
- Código modular e organizado
- Separação de responsabilidades
- Fácil localização de componentes

### 3. ✅ Manutenção
- Alterações em um local
- Menos duplicação de código
- Debugging simplificado

### 4. ✅ Performance
- Cache de componentes
- Carregamento otimizado
- Menos código repetido

## Exemplos de Uso

### 1. Lista de Intimações
```html
<div class="row">
    {% for intimacao in intimacoes %}
    <div class="col-md-6 col-lg-4 mb-3">
        {% include 'partials/card_intimacao.html' %}
    </div>
    {% endfor %}
</div>
```

### 2. Tabela com Cards Compactos
```html
<table class="table">
    <tbody>
        {% for intimacao in intimacoes %}
        <tr>
            <td>
                {% include 'partials/card_intimacao_compact.html' %}
            </td>
            <td>{{ intimacao.classificacao }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### 3. Dashboard
```html
<div class="dashboard">
    <div class="recentes">
        {% for intimacao in intimacoes_recentes %}
        {% set show_actions = False %}
        {% include 'partials/card_intimacao.html' %}
        {% endfor %}
    </div>
</div>
```

## Boas Práticas

### 1. ✅ Nomenclatura
- Use nomes descritivos: `card_intimacao.html`
- Evite nomes genéricos: `component.html`
- Siga padrão snake_case

### 2. ✅ Estrutura
- HTML primeiro
- CSS depois
- JavaScript por último
- Comentários explicativos

### 3. ✅ Responsividade
- Sempre inclua media queries
- Teste em diferentes tamanhos
- Use classes Bootstrap quando possível

### 4. ✅ Acessibilidade
- Use atributos `title` e `alt`
- Estrutura semântica
- Contraste adequado

### 5. ✅ Performance
- CSS específico do componente
- JavaScript modular
- Evite duplicação de código

## Debugging

### 1. Verificar Inclusão
```html
<!-- Adicionar comentário para debug -->
<!-- INCLUINDO: partials/card_intimacao.html -->
{% include 'partials/card_intimacao.html' %}
<!-- FIM: partials/card_intimacao.html -->
```

### 2. Verificar Variáveis
```html
<!-- Debug de variáveis -->
<!-- DEBUG: {{ intimacao }} -->
{% include 'partials/card_intimacao.html' %}
```

### 3. Verificar CSS
- Use DevTools do navegador
- Verifique se estilos estão sendo aplicados
- Confirme responsividade

## Conclusão

Os componentes partials são fundamentais para:
- **Organização** do código
- **Reutilização** de componentes
- **Manutenção** simplificada
- **Consistência** visual
- **Performance** otimizada

Use sempre que possível para manter o código limpo e organizado! 🚀
