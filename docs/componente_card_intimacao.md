# Componente Card de Intimação

## Visão Geral

O componente `card_intimacao.html` é um elemento reutilizável que exibe informações de uma intimação em formato de card, baseado no design mostrado na imagem de referência.

## Características

- **Design responsivo** que se adapta a diferentes tamanhos de tela
- **Animações suaves** com hover effects
- **Cores temáticas** para diferentes status
- **Ações integradas** (visualizar, editar, excluir)
- **Flexível** - pode ser usado com ou sem ações

## Como Usar

### 1. Incluir o Componente

```html
{% include 'partials/card_intimacao.html' %}
```

### 2. Passar Dados da Intimação

O componente espera um objeto `intimacao` com os seguintes campos:

```python
intimacao = {
    'id': 'uuid-da-intimacao',
    'processo': '5000002-31.2025.8.21.0103',
    'orgao_julgador': 'Juízo da Vara Judicial da Comarca de Herval',
    'classe': 'Procedimento Comum',
    'disponibilizacao': '07/08/2025 às 16:30',
    'intimado': 'MINISTÉRIO PÚBLICO DO ESTADO DO RIO GRANDE DO SUL',
    'status': 'Pendente',
    'prazo': '15 dias',
    'classificacao_manual': 'ELABORAR PEÇA'  # opcional
}
```

### 3. Controlar Ações

Para mostrar/esconder os botões de ação:

```html
{% set show_actions = True %}
{% include 'partials/card_intimacao.html' %}
```

## Variações de Tema

O componente suporta diferentes temas baseados no status:

```html
<!-- Tema padrão (vermelho/laranja) -->
<div class="card-intimacao">

<!-- Tema sucesso (verde) -->
<div class="card-intimacao card-intimacao-success">

<!-- Tema aviso (amarelo/laranja) -->
<div class="card-intimacao card-intimacao-warning">

<!-- Tema perigo (vermelho/rosa) -->
<div class="card-intimacao card-intimacao-danger">

<!-- Tema informação (azul) -->
<div class="card-intimacao card-intimacao-info">
```

## JavaScript

### Funções Disponíveis

- `visualizarIntimacao(id)` - Navega para a página de visualização
- `editarIntimacao(id)` - Abre modal de edição (a implementar)
- `excluirIntimacao(id)` - Exclui a intimação com confirmação
- `criarCardIntimacao(intimacao, showActions)` - Cria card dinamicamente

### Exemplo de Uso Dinâmico

```javascript
const intimacao = {
    id: '123',
    processo: '5000002-31.2025.8.21.0103',
    orgao_julgador: 'Juízo da Vara Judicial',
    classe: 'Procedimento Comum',
    disponibilizacao: '07/08/2025 às 16:30',
    intimado: 'MINISTÉRIO PÚBLICO',
    status: 'Pendente',
    prazo: '15 dias'
};

const cardHTML = criarCardIntimacao(intimacao, true);
document.getElementById('container').innerHTML = cardHTML;
```

## Estrutura HTML

```html
<div class="card-intimacao" data-intimacao-id="{{ intimacao.id }}">
    <!-- Header com número do processo -->
    <div class="card-intimacao-header">
        <div class="card-intimacao-processo">
            <i class="bi bi-hourglass"></i>
            <span class="processo-numero">{{ intimacao.processo }}</span>
            <i class="bi bi-search"></i>
        </div>
    </div>
    
    <!-- Conteúdo com informações -->
    <div class="card-intimacao-content">
        <!-- Linhas de informações -->
    </div>
    
    <!-- Footer com ações (opcional) -->
    <div class="card-intimacao-footer">
        <!-- Botões de ação -->
    </div>
</div>
```

## Responsividade

- **Desktop**: Layout em 2 colunas
- **Tablet**: Layout em 1 coluna
- **Mobile**: Layout empilhado com botões em coluna

## Personalização

### Cores

As cores podem ser personalizadas editando as variáveis CSS:

```css
.card-intimacao::before {
    background: linear-gradient(135deg, #dc3545, #fd7e14);
}
```

### Tamanhos

```css
.card-intimacao {
    margin-bottom: 16px;  /* Espaçamento entre cards */
    border-radius: 8px;   /* Bordas arredondadas */
}
```

## Exemplos de Implementação

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

### 2. Dashboard

```html
<div class="row">
    <div class="col-12">
        <h4>Intimações Recentes</h4>
        {% for intimacao in intimacoes_recentes %}
        <div class="mb-3">
            {% set show_actions = False %}
            {% include 'partials/card_intimacao.html' %}
        </div>
        {% endfor %}
    </div>
</div>
```

### 3. Modal de Seleção

```html
<div class="modal-body">
    <div class="row">
        {% for intimacao in intimacoes_disponiveis %}
        <div class="col-md-6 mb-2">
            <div class="card-intimacao" onclick="selecionarIntimacao('{{ intimacao.id }}')">
                <!-- Conteúdo do card -->
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

## Dependências

- Bootstrap 5
- Bootstrap Icons
- CSS customizado (incluído no componente)

## Compatibilidade

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
