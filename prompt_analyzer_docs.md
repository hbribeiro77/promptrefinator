# Sistema Analisador de Eficácia de Prompts

## 1. Visão Geral do Projeto

Sistema web para comparar análises manuais de intimações jurídicas com análises automáticas realizadas pela OpenAI, permitindo testar e medir a eficácia de diferentes prompts.

### Objetivo Principal
Permitir que usuários testem diferentes prompts de IA para classificação de intimações e meçam sua acurácia comparando com classificações manuais.

## 2. Tecnologias Sugeridas

- **Backend**: Python com Flask ou FastAPI
- **Frontend**: HTML, CSS, JavaScript (pode usar Bootstrap para UI)
- **Armazenamento**: Arquivos JSON
- **API**: OpenAI API
- **Exportação**: Pandas para gerar CSV

## 3. Estrutura de Dados

### 3.1 Arquivo: `data/intimacoes.json`
```json
{
  "intimacoes": [
    {
      "id": "uuid_v4",
      "contexto": "Texto completo da intimação",
      "classificacao_manual": "RENUNCIAR PRAZO",
      "informacao_adicional": "Observações opcionais do usuário",
      "data_criacao": "2025-08-10T14:30:00Z"
    }
  ]
}
```

### 3.2 Arquivo: `data/prompts.json`
```json
{
  "prompts": [
    {
      "id": "uuid_v4",
      "nome": "Prompt Padrão v1.0",
      "descricao": "Descrição opcional do prompt",
      "conteudo": "Analise a seguinte intimação jurídica e classifique...",
      "data_criacao": "2025-08-10T14:30:00Z"
    }
  ]
}
```

### 3.3 Arquivo: `data/analises.json`
```json
{
  "analises": [
    {
      "id": "uuid_v4",
      "intimacao_id": "uuid_da_intimacao",
      "prompt_id": "uuid_do_prompt",
      "parametros_openai": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 1.0
      },
      "resultado_ia": "ELABORAR PEÇA",
      "resposta_completa_ia": "Resposta detalhada da IA",
      "classificacao_manual": "RENUNCIAR PRAZO",
      "acertou": false,
      "data_analise": "2025-08-10T14:30:00Z",
      "tempo_processamento": 2.5
    }
  ]
}
```

### 3.4 Arquivo: `data/config.json`
```json
{
  "openai_api_key": "",
  "parametros_padrao": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1.0
  }
}
```

## 4. Tipos de Ação (Enum)

Lista fixa de classificações disponíveis:
- `RENUNCIAR PRAZO`
- `OCULTAR`
- `ELABORAR PEÇA`
- `CONTATAR ASSISTIDO`
- `ANALISAR PROCESSO`
- `ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR`
- `URGÊNCIA`

## 5. Funcionalidades Detalhadas

### 5.1 Gestão de Intimações

#### 5.1.1 Cadastrar Nova Intimação
- **Rota**: `POST /intimacoes`
- **Campos**:
  - `contexto` (text, obrigatório): Texto da intimação
  - `classificacao_manual` (select, obrigatório): Uma das opções do enum
  - `informacao_adicional` (text, opcional): Observações do usuário

#### 5.1.2 Listar Intimações
- **Rota**: `GET /intimacoes`
- **Funcionalidades**:
  - Paginação
  - Busca por contexto
  - Filtro por classificação
  - Checkbox para seleção individual
  - Checkbox "Selecionar Todos"
  - Ordenação por data

#### 5.1.3 Visualizar Intimação
- **Rota**: `GET /intimacoes/{id}`
- Exibir todos os dados da intimação
- Histórico de análises realizadas

### 5.2 Gestão de Prompts

#### 5.2.1 Cadastrar Novo Prompt
- **Rota**: `POST /prompts`
- **Campos**:
  - `nome` (text, obrigatório): Nome identificador
  - `descricao` (text, opcional): Descrição do prompt
  - `conteudo` (textarea, obrigatório): Texto do prompt

#### 5.2.2 Listar Prompts
- **Rota**: `GET /prompts`
- Exibir nome, descrição e data de criação
- Link para visualizar conteúdo completo
- Contador de quantas vezes foi usado

#### 5.2.3 Visualizar Prompt
- **Rota**: `GET /prompts/{id}`
- Exibir prompt completo
- Estatísticas de uso
- Histórico de análises com este prompt

### 5.3 Análise de Intimações

#### 5.3.1 Página de Análise
- **Rota**: `GET /analise`
- Seleção de intimações (individual ou múltipla)
- Seleção de prompt
- Configuração de parâmetros OpenAI:
  - Model (dropdown: gpt-4, gpt-3.5-turbo, etc.)
  - Temperature (slider: 0.0 - 2.0)
  - Max Tokens (input: 1-4000)
  - Top P (slider: 0.0 - 1.0)

#### 5.3.2 Executar Análise
- **Rota**: `POST /executar-analise`
- **Payload**:
```json
{
  "intimacao_ids": ["uuid1", "uuid2"],
  "prompt_id": "uuid_prompt",
  "parametros_openai": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1.0
  }
}
```
- Processar em background se múltiplas intimações
- Retornar status de progresso via WebSocket ou polling

#### 5.3.3 Visualizar Resultados
- **Rota**: `GET /analise/{id}`
- Comparação lado a lado: Manual vs IA
- Status: Acertou/Errou
- Tempo de processamento
- Resposta completa da IA

### 5.4 Dashboard e Relatórios

#### 5.4.1 Dashboard Principal
- **Rota**: `GET /`
- **Métricas**:
  - Total de intimações cadastradas
  - Total de análises realizadas
  - Taxa de acurácia geral
  - Taxa de acurácia por prompt (top 5)
  - Distribuição de classificações manuais (gráfico pizza)
  - Histórico de análises (gráfico linha)

#### 5.4.2 Relatório Detalhado
- **Rota**: `GET /relatorios`
- **Filtros**:
  - Período (data início/fim)
  - Prompt específico
  - Tipo de classificação
- **Métricas**:
  - Taxa de acurácia por prompt
  - Taxa de acurácia por tipo de ação
  - Matriz de confusão
  - Tempo médio de processamento

#### 5.4.3 Exportar Dados
- **Rota**: `GET /exportar`
- **Formatos**: CSV
- **Opções**:
  - Todas as análises
  - Filtrar por período
  - Filtrar por prompt
- **Colunas CSV**:
  - ID da Intimação
  - Contexto (truncado)
  - Classificação Manual
  - Prompt Usado
  - Classificação IA
  - Acertou (S/N)
  - Data Análise
  - Tempo Processamento

## 6. Estrutura de Arquivos do Projeto

```
projeto/
├── app.py                 # Arquivo principal Flask/FastAPI
├── requirements.txt       # Dependências Python
├── config.py             # Configurações da aplicação
├── models/
│   ├── __init__.py
│   ├── intimacao.py      # Classe para intimações
│   ├── prompt.py         # Classe para prompts
│   └── analise.py        # Classe para análises
├── services/
│   ├── __init__.py
│   ├── openai_service.py # Integração com OpenAI
│   ├── data_service.py   # Manipulação dos JSONs
│   └── export_service.py # Exportação CSV
├── templates/            # Templates HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── intimacoes.html
│   ├── prompts.html
│   ├── analise.html
│   └── relatorios.html
├── static/              # CSS, JS, imagens
│   ├── css/
│   ├── js/
│   └── images/
└── data/                # Arquivos JSON
    ├── intimacoes.json
    ├── prompts.json
    ├── analises.json
    └── config.json
```

## 7. Requisitos Técnicos

### 7.1 Dependências Python
```txt
flask>=2.3.0
openai>=1.0.0
pandas>=2.0.0
uuid
datetime
json
```

### 7.2 Funcionalidades Específicas

#### 7.2.1 Integração OpenAI
- Implementar retry com backoff exponencial
- Tratamento de rate limits
- Validação de API key
- Log de erros e custos

#### 7.2.2 Validação de Dados
- Validar tipos de ação contra enum
- Validar parâmetros OpenAI
- Sanitizar inputs do usuário

#### 7.2.3 Backup e Recuperação
- Backup automático dos JSONs a cada operação
- Rotação de backups (manter últimos 10)
- Função de restore em caso de erro

#### 7.2.4 Performance
- Cache de prompts usados recentemente
- Paginação para listas grandes
- Processamento assíncrono para análises em lote

## 8. Interface do Usuário

### 8.1 Layout Geral
- Header com navegação principal
- Sidebar com estatísticas rápidas
- Área principal responsiva
- Footer com informações do sistema

### 8.2 Componentes Reutilizáveis
- Tabelas com ordenação e filtros
- Modal para confirmações
- Progress bar para análises em andamento
- Toast notifications para feedback
- Cards para métricas no dashboard

### 8.3 UX Considerations
- Loading states durante processamento OpenAI
- Confirmação antes de executar análises custosas
- Feedback visual para ações bem-sucedidas/falhas
- Breadcrumb navigation
- Tooltips para explicar funcionalidades

## 9. Critérios de Aceitação

### 9.1 Funcionalidades Essenciais
- [ ] Cadastrar intimações com classificação manual
- [ ] Criar e gerenciar prompts
- [ ] Executar análise individual e em lote
- [ ] Comparar resultados manual vs IA
- [ ] Visualizar métricas de acurácia
- [ ] Exportar dados em CSV
- [ ] Configurar parâmetros OpenAI

### 9.2 Qualidade
- [ ] Interface responsiva
- [ ] Validação de dados no frontend e backend
- [ ] Tratamento de erros da API OpenAI
- [ ] Performance adequada para até 1000 intimações
- [ ] Backup automático dos dados

### 9.3 Documentação
- [ ] README com instruções de instalação
- [ ] Documentação da API (endpoints)
- [ ] Manual do usuário
- [ ] Exemplos de prompts

## 10. Próximos Passos para Desenvolvimento

1. **Setup inicial**: Criar estrutura de arquivos e ambiente virtual
2. **Backend base**: Implementar CRUD básico para intimações e prompts
3. **Integração OpenAI**: Criar serviço para chamadas da API
4. **Frontend MVP**: Páginas básicas funcionais
5. **Análise core**: Implementar comparação e cálculo de métricas
6. **Dashboard**: Criar visualizações e relatórios
7. **Exportação**: Implementar geração de CSV
8. **Testes**: Validar todas as funcionalidades
9. **Deploy**: Preparar para produção

## 11. Considerações de Custos

- Monitorar usage da OpenAI API
- Implementar limites de uso por sessão
- Log detalhado de chamadas para auditoria
- Opção para usar modelos mais baratos em testes

---

**Versão**: 1.0  
**Data**: Agosto 2025  
**Responsável**: [Seu nome/empresa]