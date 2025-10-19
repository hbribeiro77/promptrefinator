# 📋 Resumo Detalhado da Codebase - Sistema Prompt Refinator

## 🎯 **Visão Geral do Projeto**

O **Sistema Prompt Refinator** é uma aplicação web desenvolvida em Flask para análise e otimização de prompts de IA, especificamente voltada para a Defensoria Pública do Estado do Rio Grande do Sul (DPE/RS). O sistema permite criar, testar e analisar a eficácia de prompts para classificação automática de intimações jurídicas.

### **Objetivo Principal**
Automatizar e otimizar o processo de triagem de intimações jurídicas através de análise de IA, permitindo que defensores públicos foquem em casos mais complexos e urgentes.

---

## 🏗️ **Arquitetura do Sistema**

### **Tecnologias Utilizadas**
- **Backend**: Python 3.x + Flask
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5.3.0
- **Ícones**: Bootstrap Icons 1.10.0
- **Gráficos**: Chart.js
- **IA**: OpenAI API (GPT-3.5-turbo, GPT-4) + Azure OpenAI (GPT-4, GPT-35-turbo)
- **Armazenamento**: SQLite (NOVO) + JSON (legado)
- **Exportação**: CSV, Excel
- **Variáveis de Ambiente**: python-dotenv
- **Banco de Dados**: SQLite3 (NOVO)

### **Estrutura de Diretórios**
```
promptrefinator2/
├── app.py                 # Aplicação principal Flask
├── config.py              # Configurações do sistema
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Documentação do projeto
├── data/                  # Dados persistentes
│   ├── database.db       # Banco SQLite (NOVO)
│   ├── config.json       # Configurações do usuário
│   └── backups/          # Backups automáticos
├── models/               # Modelos de dados (NOVO)
│   ├── __init__.py
│   ├── intimacao.py
│   ├── prompt.py
│   └── analise.py
├── services/             # Camada de serviços
│   ├── data_service.py   # Gerenciamento de dados
│   ├── sqlite_service.py # Serviço SQLite (NOVO)
│   ├── openai_service.py # Integração OpenAI
│   ├── azure_service.py  # Integração Azure OpenAI (NOVO)
│   ├── ai_manager_service.py # Gerenciador de IA (NOVO)
│   ├── ai_service_interface.py # Interface de IA (NOVO)
│   ├── cost_calculation_service.py # Cálculo de custos (NOVO)
│   └── export_service.py # Exportação de dados
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── dashboard.html    # Página inicial
│   ├── analise.html      # Interface de análise
│   ├── relatorios.html   # Relatórios e gráficos
│   ├── configuracoes.html # Configurações
│   ├── intimacoes.html   # Listagem de intimações
│   ├── nova_intimacao.html # Nova intimação (NOVO)
│   ├── visualizar_intimacao.html # Visualizar intimação (NOVO)
│   ├── prompts.html      # Listagem de prompts
│   ├── novo_prompt.html  # Novo prompt (NOVO)
│   ├── visualizar_prompt.html # Visualizar prompt (NOVO)
│   ├── editar_prompt.html # Editar prompt (NOVO)
│   ├── historico.html    # Histórico de análises (NOVO)
│   ├── visualizar_sessao.html # Visualizar sessão (NOVO)
│   └── partials/         # Componentes reutilizáveis
│       ├── tabela_analises.html
│       ├── tabela_analises_avancada.html # Tabela avançada (NOVO)
│       ├── tabela_analises_com_card.html # Tabela com cards (NOVO)
│       ├── card_intimacao.html # Card de intimação (NOVO)
│       ├── card_intimacao_compact.html # Card compacto (NOVO)
│       └── modais_prompt_resposta.html
└── static/               # Arquivos estáticos
    ├── css/
    └── js/
```

---

## 🔧 **Componentes Principais**

### **1. Aplicação Principal (`app.py`)**

**Responsabilidades:**
- Configuração e inicialização do Flask
- Definição de todas as rotas da aplicação
- Orquestração entre serviços
- Geração de dados para gráficos
- **NOVO**: Carregamento de variáveis de ambiente

**Rotas Principais:**
- `/` - Dashboard principal
- `/intimacoes` - Gerenciamento de intimações
- `/intimacoes/nova` - Nova intimação (NOVO)
- `/intimacoes/<id>` - Visualizar intimação (NOVO)
- `/prompts` - Gerenciamento de prompts
- `/prompts/novo` - Novo prompt (NOVO)
- `/prompts/<id>` - Visualizar prompt (NOVO)
- `/prompts/<id>/editar` - Editar prompt (NOVO)
- `/prompts/<id>/copiar` - Copiar prompt (NOVO)
- `/prompts/<id>/excluir` - Excluir prompt (NOVO)
- `/analise` - Interface de análise de IA
- `/relatorios` - Relatórios e estatísticas
- `/configuracoes` - Configurações do sistema
- `/historico` - Histórico de análises (NOVO)
- `/historico/<session_id>` - Visualizar sessão (NOVO)
- `/exportar` - Exportação de dados
- `/api/relatorios/pagina/<int:pagina>` - Paginação AJAX
- `/api/analises/excluir` - Exclusão de análises
- `/api/analise-progresso` - Server-Sent Events para progresso em tempo real
- `/api/precos-modelos` - API para obter preços dos modelos
- `/api/prompts/<id>/excluir` - Excluir prompt via API (NOVO)
- `/api/historico/excluir-sessao` - Excluir sessão (NOVO)
- `/api/historico/exportar-sessao` - Exportar sessão (NOVO)
- `/api/historico/pagina/<int:pagina>` - Paginação AJAX do histórico (NOVO)
- `/api/filtros/analise` - API para obter filtros dinâmicos (defensores e classificações) (NOVO)
- `/api/intimacoes/taxa-acerto` - API para obter taxa de acerto global das intimações (NOVO)
- `/api/intimacoes/<intimacao_id>/prompts-acerto` - API para obter prompts e taxas de acerto por intimação (NOVO)

**Funcionalidades Especiais:**
- Paginação AJAX para relatórios
- Sistema de backup automático
- Exportação em múltiplos formatos
- API REST para operações CRUD
- Sistema de variáveis de ambiente para chaves de API
- Persistência de configurações de colunas via localStorage
- Sistema de progresso em tempo real com Server-Sent Events
- Cálculo de custo real baseado em tokens e preços configurados
- Tooltips de memória de cálculo com soma automática
- **NOVO**: Migração completa para SQLite
- **NOVO**: Sistema de sessões de análise
- **NOVO**: Suporte a Azure OpenAI
- **NOVO**: Gerenciador de IA unificado
- **NOVO**: CRUD completo de prompts (criar, editar, copiar, excluir)
- **NOVO**: CRUD completo de intimações
- **NOVO**: Histórico de análises com sessões
- **NOVO**: Visualização detalhada de sessões
- **NOVO**: Configuração de colunas na visualização de sessões
- **NOVO**: Campo "defensor" nas intimações
- **NOVO**: Campo "informação adicional" nas intimações
- **NOVO**: Regra de negócio exibida nas sessões
- **NOVO**: Link clicável para prompt nas sessões
- **NOVO**: Proporção de acertos nas estatísticas
- **NOVO**: Paginação AJAX para histórico de análises
- **NOVO**: Configuração de análises paralelas para Azure OpenAI
- **NOVO**: Correção de prompt_nome nas análises (resolvido problema "N/A")
- **NOVO**: Sistema de filtros dinâmicos na página de análise (defensor e classificação)
- **NOVO**: Popover customizado com taxa de acerto global por intimação
- **NOVO**: Tooltip interativo com detalhes dos prompts testados
- **NOVO**: Prompts clicáveis no popover para visualização detalhada
- **NOVO**: Delay configurável para exibição do popover (500ms)

### **2. Configurações (`config.py`)**

**Classes de Configuração:**
- `Config` - Configurações base
- `DevelopmentConfig` - Configurações para desenvolvimento
- `ProductionConfig` - Configurações para produção
- `TestingConfig` - Configurações para testes

**Configurações Principais:**
- Chaves de API OpenAI e Azure OpenAI (via variáveis de ambiente)
- Modelos de IA disponíveis (OpenAI + Azure)
- Tipos de ação para classificação
- Lista de defensores disponíveis (NOVO)
- Configurações de backup e paginação

### **3. Serviços**

#### **SQLiteService (`services/sqlite_service.py`) - NOVO**
**Responsabilidades:**
- Gerenciamento completo do banco SQLite
- CRUD para intimações, prompts, análises e sessões
- Sistema de backup automático
- Validação e integridade de dados
- Substituição de placeholders por variáveis de ambiente

**Métodos Principais:**
- `get_all_intimacoes()` - Listar todas as intimações
- `save_intimacao()` - Salvar intimação
- `get_all_prompts()` - Listar todos os prompts
- `save_prompt()` - Salvar prompt
- `delete_prompt()` - Excluir prompt
- `get_sessoes_analise()` - Listar sessões de análise com filtros e paginação
- `get_total_sessoes_analise()` - Contar total de sessões com filtros
- `get_sessao_analise()` - Obter sessão específica
- `criar_sessao_analise()` - Criar nova sessão
- `get_analises_por_sessao()` - Obter análises de uma sessão
- Substituição automática de `${VARIABLE}` por valores de ambiente

#### **DataService (`services/data_service.py`) - LEGADO**
**Responsabilidades:**
- Gerenciamento de dados JSON (mantido para compatibilidade)
- Migração gradual para SQLite

#### **AIManagerService (`services/ai_manager_service.py`) - NOVO**
**Responsabilidades:**
- Gerenciamento unificado de serviços de IA
- Integração com OpenAI e Azure OpenAI
- Seleção automática do melhor serviço
- Tratamento de erros e retry
- Análise de intimações usando IA

**Funcionalidades:**
- Teste de conexão com múltiplos provedores
- Análise de intimações com prompts customizados
- Extração de classificações da resposta da IA
- Sistema de retry para falhas de API
- Carregamento seguro de chaves de API

#### **OpenAIService (`services/openai_service.py`)**
**Responsabilidades:**
- Integração específica com API OpenAI
- Implementação da interface de IA
- Tratamento de erros específicos da OpenAI

#### **AzureService (`services/azure_service.py`) - NOVO**
**Responsabilidades:**
- Integração específica com Azure OpenAI
- Implementação da interface de IA
- Tratamento de erros específicos do Azure

#### **ExportService (`services/export_service.py`)**
**Responsabilidades:**
- Exportação de dados em múltiplos formatos
- Geração de relatórios personalizados
- Filtros e ordenação de dados

---

## 🎨 **Interface do Usuário**

### **Template Base (`templates/base.html`)**
- Layout responsivo com Bootstrap 5
- Sidebar de navegação
- Sistema de notificações (toasts)
- Integração com Chart.js para gráficos

### **Páginas Principais**

#### **Dashboard (`templates/dashboard.html`)**
- Visão geral do sistema
- Métricas principais
- Gráficos de performance
- Acesso rápido às funcionalidades

#### **Análise (`templates/analise.html`)**
- Interface para execução de análises
- Seleção de prompts e intimações
- Configurações de IA (modelo, temperatura)
- **NOVO**: Sistema de progresso em tempo real com Server-Sent Events (SSE)
- **NOVO**: Barra de progresso dinâmica com cancelamento
- **NOVO**: Cálculo de custo real baseado em tokens e preços configurados
- **NOVO**: Tooltips de memória de cálculo com soma automática
- Exibição de resultados em tempo real
- Modais para visualização completa de prompts/respostas
- Coluna "Informação Adicional" configurável
- Persistência de configurações de colunas

#### **Relatórios (`templates/relatorios.html`)**
- Gráficos de acurácia por período
- Distribuição de classificações
- Performance por prompt
- Tabela paginada de análises individuais
- Sistema de filtros avançados
- Configuração de colunas visíveis
- **NOVO**: Colunas "Prompt Completo" e "Resposta IA" com modais
- **NOVO**: Sistema de seleção e exclusão em lote
- **NOVO**: Paginação AJAX sem mudança de URL
- **NOVO**: Persistência de configurações de colunas via localStorage

#### **Configurações (`templates/configuracoes.html`)**
- Configuração da API OpenAI
- Parâmetros padrão de IA
- Configurações de backup
- Teste de conexão
- **NOVO**: Campo de chave da API readonly (carregado de .env)
- **NOVO**: Instruções para configuração via variável de ambiente
- **NOVO**: Configuração de análises paralelas para Azure OpenAI
- **NOVO**: Campos de delay entre lotes para Azure OpenAI

#### **Histórico (`templates/historico.html`)**
- Listagem de sessões de análise
- Filtros por data, prompt, status, acurácia
- Visualização de estatísticas por sessão
- Ações: visualizar, copiar resumo, excluir
- **NOVO**: Paginação AJAX com 20 itens por página
- **NOVO**: Filtros integrados com paginação
- **NOVO**: Carregamento dinâmico sem recarregar página

### **Componentes Reutilizáveis**

#### **Tabela de Análises (`templates/partials/tabela_analises.html`)**
- Tabela paginada de análises
- Colunas configuráveis
- Botões de ação (excluir, visualizar)
- Integração com modais
- **NOVO**: Colunas "Prompt Completo" e "Resposta IA"
- **NOVO**: Badge de prompt clicável para modal
- **NOVO**: Sistema de checkboxes para seleção

#### **Modais de Prompt/Resposta (`templates/partials/modais_prompt_resposta.html`)**
- Modais reutilizáveis para exibir conteúdo completo
- Funcionalidade de cópia para clipboard
- Formatação adequada para código JSON
- **NOVO**: Componente centralizado para reutilização

---

## 📊 **Modelos de Dados**

### **Intimação**
```json
{
  "id": "uuid",
  "contexto": "Dados do processo jurídico",
  "classificacao_manual": "Tipo de ação",
  "informacoes_adicionais": "Observações",
  "data_criacao": "timestamp",
  "analises": [
    {
      "id": "uuid",
      "data_analise": "timestamp",
      "prompt_id": "uuid",
      "prompt_nome": "Nome do prompt",
      "resultado_ia": "Classificação da IA",
      "acertou": boolean,
      "tempo_processamento": float,
      "modelo": "Modelo usado",
      "temperatura": float,
      "tokens_usados": int,

      "prompt_completo": "Prompt enviado",
      "resposta_completa": "Resposta da IA"
    }
  ]
}
```

### **Prompt**
```json
{
  "id": "uuid",
  "nome": "Nome do prompt",
  "descricao": "Descrição",
  "template": "Template do prompt",
  "categoria": "Categoria",
  "tags": ["tag1", "tag2"],
  "data_criacao": "timestamp",
  "usos": [
    {
      "data_uso": "timestamp",
      "intimacao_id": "uuid",
      "resultado": "Classificação",
      "acertou": boolean
    }
  ]
}
```

### **Configuração**
```json
{
  "openai_api_key": "${OPENAI_API_KEY}",
  "modelo_padrao": "gpt-4",
  "temperatura_padrao": 0.7,
  "max_tokens_padrao": 500,
  "timeout_padrao": 30,
  "max_retries": 3
}
```

**NOVO**: O arquivo `config.json` agora usa placeholders `${VARIABLE}` que são substituídos automaticamente pelos valores das variáveis de ambiente.

---

## 🔄 **Fluxo de Trabalho**

### **1. Cadastro de Intimações**
1. Usuário acessa `/intimacoes/nova`
2. Preenche dados do processo jurídico
3. Define classificação manual esperada
4. Sistema salva no `intimacoes.json`

### **2. Criação de Prompts**
1. Usuário acessa `/prompts/novo`
2. Define template do prompt
3. Configura parâmetros de IA
4. Sistema salva no `prompts.json`

### **3. Análise de Intimações**
1. Usuário acessa `/analise`
2. Seleciona prompt e intimações
3. Configura parâmetros de IA
4. **NOVO**: Sistema inicia progresso em tempo real via Server-Sent Events
5. **NOVO**: Barra de progresso mostra "X de Y intimações" em tempo real
6. Sistema envia para OpenAI
7. Recebe e processa resposta
8. **NOVO**: Calcula custo real baseado em tokens e preços configurados
9. Salva análise no banco (incluindo prompt_completo, resposta_completa e custo_real)
10. Exibe resultados em tempo real
11. **NOVO**: Tooltips mostram memória de cálculo com soma automática

### **4. Relatórios e Estatísticas**
1. Usuário acessa `/relatorios`
2. Sistema carrega dados de análises
3. Gera gráficos e estatísticas
4. Exibe tabela paginada com AJAX
5. Permite filtros e exportação
6. **NOVO**: Configurações de colunas persistentes

---

## 🛠️ **Funcionalidades Avançadas**

### **Sistema de Backup**
- Backup automático antes de cada salvamento
- Limpeza automática de backups antigos
- Configuração de número máximo de backups

### **Paginação AJAX**
- Carregamento assíncrono de dados
- Manutenção de estado de filtros
- Configuração persistente de colunas
- **NOVO**: Não altera URL durante navegação

### **Configuração de Colunas**
- Sistema de persistência via localStorage
- Configuração em tempo real
- Aplicação automática após carregamento
- **NOVO**: Funciona com paginação AJAX
- **NOVO**: Configurações mantidas entre sessões

### **Exportação de Dados**
- Múltiplos formatos (CSV, Excel)
- Filtros aplicados na exportação
- Dados completos incluindo análises

### **Sistema de Modais**
- Modais reutilizáveis para conteúdo longo
- Funcionalidade de cópia para clipboard
- Escape adequado de caracteres especiais
- Componente centralizado para reutilização
- Uso de data-attributes para evitar problemas de escape

### **Sistema de Progresso em Tempo Real (NOVO)**
- Server-Sent Events (SSE) para atualizações em tempo real
- Barra de progresso dinâmica com percentual
- Descrições variadas durante o processamento
- Funcionalidade de cancelamento
- Integração com análise real de intimações

### **Sistema de Cálculo de Custos (NOVO)**
- Cálculo real baseado em tokens de entrada e saída
- Preços configuráveis por modelo e provedor
- Tooltips de memória de cálculo com soma automática
- Integração com preços do Azure OpenAI e OpenAI
- Exibição de custo total e individual

### **Sistema de Variáveis de Ambiente**
- Carregamento automático de `.env`
- Substituição de placeholders `${VARIABLE}`
- Priorização de variáveis de ambiente sobre config.json
- Interface de configuração atualizada
- Segurança aprimorada para chaves de API

---

## 🔒 **Segurança e Configuração**

### **Configurações de Segurança**
- Chave secreta configurável
- Validação de entrada de dados
- Escape de caracteres especiais
- Tratamento de erros robusto
- **NOVO**: Chaves de API em variáveis de ambiente
- **NOVO**: Arquivo `.env` no .gitignore

### **Configurações de Ambiente**
- Suporte a variáveis de ambiente
- Configurações separadas por ambiente
- Sistema de configuração hierárquico
- **NOVO**: Carregamento automático de `.env`
- **NOVO**: Substituição de placeholders

### **Arquivos de Configuração (NOVOS)**
- `.env` - Variáveis de ambiente (não versionado)
- `.gitignore` - Arquivos ignorados pelo Git
- `README.md` - Documentação do projeto

---

## 📈 **Métricas e Performance**

### **Métricas Coletadas**
- Acurácia por período (últimos 6 meses)
- Distribuição de classificações manuais
- Distribuição de resultados da IA
- Performance por prompt
- Tempo de processamento
- Tokens utilizados (entrada e saída)
- **NOVO**: Custo real baseado em tokens e preços configurados
- **NOVO**: Memória de cálculo detalhada por análise

### **Otimizações Implementadas**
- Sistema de cache para dados
- Paginação para grandes volumes
- Lazy loading de componentes
- Compressão de dados JSON
- **NOVO**: Carregamento seguro de configurações
- **NOVO**: Persistência de preferências do usuário

---

## 🚀 **Deploy e Manutenção**

### **Requisitos de Sistema**
- Python 3.8+
- Dependências listadas em `requirements.txt`
- Acesso à API OpenAI
- Espaço em disco para dados e backups
- **NOVO**: Arquivo `.env` configurado

### **Configuração de Produção**
- Configuração de chaves de API via variáveis de ambiente
- Backup automático configurado
- Logs de erro habilitados
- Monitoramento de performance
- **NOVO**: Configuração segura de chaves de API

### **Configuração Inicial (NOVO)**
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Crie o arquivo `.env` na raiz do projeto
4. Configure `OPENAI_API_KEY=sk-...` no arquivo `.env`
5. Execute `python app.py`

---

## 🆕 **Melhorias Recentes Implementadas (2025)**

### **Migração para SQLite**
- ✅ Migração completa de JSON para SQLite
- ✅ Estrutura de banco otimizada
- ✅ Backup automático do banco
- ✅ Performance melhorada

### **Sistema de Sessões de Análise**
- ✅ Agrupamento de análises por sessão
- ✅ Histórico de sessões com estatísticas
- ✅ Visualização detalhada de sessões
- ✅ Exportação de sessões completas

### **CRUD Completo de Prompts**
- ✅ Criação de prompts com regra de negócio
- ✅ Edição de prompts existentes
- ✅ Cópia de prompts com sufixo "(Cópia)"
- ✅ Exclusão de prompts com confirmação
- ✅ Visualização detalhada de prompts

### **CRUD Completo de Intimações**
- ✅ Criação de intimações com defensor
- ✅ Campo "informação adicional"
- ✅ Visualização detalhada de intimações
- ✅ Edição e exclusão de intimações

### **Melhorias na Interface**
- ✅ Configuração de colunas na visualização de sessões
- ✅ Coluna "Informação Adicional" nas análises
- ✅ Regra de negócio exibida nas sessões
- ✅ Link clicável para prompt nas sessões
- ✅ Proporção de acertos nas estatísticas (13/20)
- ✅ Layout otimizado das configurações

### **Suporte a Azure OpenAI**
- ✅ Integração com Azure OpenAI
- ✅ Gerenciador unificado de IA
- ✅ Seleção automática do melhor serviço
- ✅ Interface padronizada para múltiplos provedores
- ✅ Configuração de análises paralelas para Azure OpenAI
- ✅ Campos de delay entre lotes para Azure OpenAI

### **Paginação e Performance**
- ✅ Paginação AJAX para histórico de análises
- ✅ Filtros integrados com paginação
- ✅ Carregamento dinâmico sem recarregar página
- ✅ Performance otimizada com 20 itens por página

### **Correções e Melhorias**
- ✅ Correção de prompt_nome nas análises (resolvido problema "N/A")
- ✅ Remoção de "informação adicional" do prompt enviado à IA
- ✅ Correção de templating de prompts em análises paralelas

### **Sistema de Filtros Dinâmicos**
- ✅ Filtros por defensor e classificação na página de análise
- ✅ Carregamento dinâmico de opções do banco de dados
- ✅ Checkboxes "Todos" que controlam seleções individuais
- ✅ Filtros aplicados apenas em intimações visíveis
- ✅ Seleção inteligente de "Selecionar Todas" apenas em itens visíveis

### **Popover Customizado com Taxa de Acerto**
- ✅ Taxa de acerto global exibida para cada intimação
- ✅ Popover customizado com hover inteligente
- ✅ Delay de 500ms para exibição do popover
- ✅ Detalhes dos prompts testados com taxas individuais
- ✅ Prompts clicáveis para visualização detalhada
- ✅ Efeitos visuais e transições suaves
- ✅ API dedicada para buscar dados de prompts por intimação

---

## 🔮 **Funcionalidades Futuras**

### **Melhorias Planejadas**
- Sistema de usuários e autenticação
- API REST completa
- Integração com sistemas externos
- Machine Learning para otimização automática
- Dashboard em tempo real
- Notificações push
- Sistema de versionamento de prompts

### **Escalabilidade**
- Sistema de cache distribuído
- Load balancing
- Microserviços

---

## 📝 **Conclusão**

O Sistema Prompt Refinator é uma solução completa e robusta para análise e otimização de prompts de IA, especificamente desenvolvida para o contexto jurídico da DPE/RS. Com arquitetura modular, interface intuitiva e funcionalidades avançadas, o sistema oferece uma base sólida para automação de processos jurídicos através de inteligência artificial.

**Principais Pontos Fortes:**
- ✅ Arquitetura modular e escalável
- ✅ Interface responsiva e intuitiva
- ✅ Sistema robusto de backup
- ✅ Integração eficiente com OpenAI e Azure OpenAI
- ✅ Relatórios detalhados e gráficos
- ✅ Configuração flexível
- ✅ Exportação de dados completa
- ✅ Segurança aprimorada com variáveis de ambiente
- ✅ Persistência de configurações do usuário
- ✅ Sistema de modais reutilizáveis
- ✅ Paginação AJAX otimizada
- ✅ Sistema de progresso em tempo real com Server-Sent Events
- ✅ Cálculo de custo real baseado em tokens e preços
- ✅ Tooltips de memória de cálculo com soma automática
- ✅ **NOVO**: Banco de dados SQLite otimizado
- ✅ **NOVO**: Sistema de sessões de análise
- ✅ **NOVO**: CRUD completo de prompts e intimações
- ✅ **NOVO**: Histórico detalhado de análises
- ✅ **NOVO**: Configuração de colunas personalizável
- ✅ **NOVO**: Gerenciador unificado de IA

**Tecnologias Utilizadas:**
- Python + Flask (Backend)
- Bootstrap 5 + Chart.js (Frontend)
- OpenAI API + Azure OpenAI (IA)
- SQLite (Persistência principal)
- JSON (Persistência legado)
- AJAX (Interatividade)
- python-dotenv (Variáveis de ambiente)

**Melhorias Recentes (2025):**
- 🗄️ Migração completa para SQLite
- 📊 Sistema de sessões de análise
- 🔄 CRUD completo de prompts e intimações
- 📈 Histórico detalhado de análises
- ⚙️ Configuração de colunas personalizável
- 🤖 Gerenciador unificado de IA (OpenAI + Azure)
- 📋 Campo "defensor" e "informação adicional" nas intimações
- 📝 Regra de negócio exibida nas sessões
- 🔗 Link clicável para prompt nas sessões
- 📊 Proporção de acertos nas estatísticas
- 🎨 Layout otimizado das configurações
- ⚡ Paginação AJAX para histórico de análises
- 🔧 Configuração de análises paralelas para Azure OpenAI
- 🐛 Correção de prompt_nome nas análises (resolvido "N/A")
- 🚫 Remoção de "informação adicional" do prompt enviado à IA
- 🔍 Sistema de filtros dinâmicos na página de análise
- 📊 Popover customizado com taxa de acerto global
- 🎯 Tooltip interativo com detalhes dos prompts
- 🔗 Prompts clicáveis para visualização detalhada
- ⏱️ Delay configurável para exibição do popover (500ms)

O sistema está pronto para uso em produção e pode ser facilmente estendido com novas funcionalidades conforme necessário.

### **Sistema Completo de Configuração de Colunas na Tabela de Intimações**
- ✅ Modal de configuração com checkboxes para cada coluna
- ✅ Colunas adicionais: Defensor e Classe da Intimação
- ✅ Botão "Colunas" na interface de análise
- ✅ Persistência no localStorage
- ✅ Reset para configuração padrão
- ✅ Colunas disponíveis: Card, Defensor, Classe, Classificação, Informações, Taxa, Data, Ações

### **Floating Button de Voltar ao Topo**
- ✅ Botão flutuante disponível em todas as páginas
- ✅ Aparece após rolar 300px para baixo
- ✅ Scroll suave ao clicar
- ✅ Design moderno com gradiente e sombra
- ✅ Efeito hover com escala
- ✅ Posicionamento fixo no canto inferior direito

### **Modal "Ver Informações Adicionais" na Página de Visualizar Prompt**
- ✅ Botão "Ver Informações Adicionais" na tabela "Histórico nas Intimações"
- ✅ Modal reutilizável com contexto e informações adicionais
- ✅ Funciona apenas com intimações selecionadas
- ✅ Botões para copiar informações individuais ou em lote
- ✅ API endpoint dedicada para buscar dados das intimações
- ✅ Integração completa com sistema de filtros

### **Correções e Melhorias de Interface**
- ✅ Correção de erros de lint no arquivo visualizar_intimacao.html
- ✅ Separação de dados JSON e JavaScript para evitar conflitos
- ✅ Correção de seletor CSS inválido em filtros com caracteres especiais
- ✅ Função de escape CSS para nomes com parênteses e caracteres especiais
- ✅ Checkbox "Selecionar Todas" funciona apenas com intimações filtradas/visíveis
- ✅ Estado inteligente do checkbox (marcado/indeterminado/desmarcado)
- ✅ Sincronização automática com filtros aplicados

### **Sistema de Comparação de Prompts**
- ✅ Página de comparação de prompts selecionados
- ✅ Checkboxes no popover de taxa de acerto para seleção múltipla
- ✅ Botão "Comparar Prompts Selecionados" habilitado com 2+ prompts
- ✅ Navegação para página de comparação com intimação de origem
- ✅ Exibição da intimação que originou a comparação
- ✅ Taxa de acerto de cada prompt com a intimação específica
- ✅ Nomes de prompts clicáveis para visualização detalhada
- ✅ Conteúdo do prompt colapsado por padrão
- ✅ Layout responsivo ocupando toda largura disponível

### **Análise de Diferenças com IA**
- ✅ Botão "Analisar com IA" no cabeçalho da comparação
- ✅ Sistema de configuração de prompt de análise personalizável
- ✅ Modal de configuração com persona, instruções e opções
- ✅ Opções para incluir contexto da intimação e gabarito
- ✅ Botão "Ver Prompt" para visualizar prompt completo
- ✅ Modal com estatísticas detalhadas (caracteres, palavras, linhas)
- ✅ Botão "Copiar Prompt" para área de transferência
- ✅ Análise JSON estruturada com diferenças e recomendações
- ✅ API endpoint dedicada para análise de diferenças
- ✅ Integração com AIManagerService para múltiplos provedores

### **Organização de Código JavaScript**
- ✅ Arquivo JavaScript dedicado: `static/js/comparar_prompts.js`
- ✅ Separação completa entre template HTML e lógica JavaScript
- ✅ Dados da intimação passados via JSON seguro
- ✅ Funções organizadas e reutilizáveis
- ✅ Código limpo e fácil de manter
- ✅ Eliminação de scripts inline gigantes
- ✅ Melhor performance com cache do navegador

### **Sistema de Configuração Persistente**
- ✅ Configurações salvas automaticamente no localStorage
- ✅ Carregamento automático das configurações ao inicializar
- ✅ Configuração padrão como fallback seguro
- ✅ Merge inteligente entre configurações salvas e padrão
- ✅ Tratamento de erros com fallback para configuração padrão
- ✅ Persistência entre sessões do navegador
- ✅ Simplificação da interface com campo único "Persona + Instruções"

### **Melhorias na Análise de Diferenças**
- ✅ Campo único "Persona + Instruções de Análise" no modal de configuração
- ✅ Instruções integradas ao persona para simplificar a interface
- ✅ Configuração padrão com instruções completas de análise
- ✅ Persistência das configurações personalizadas
- ✅ Textarea expandida (6 linhas) para acomodar persona + instruções
- ✅ Remoção de campo separado de instruções para evitar confusão

### **Correções Críticas de Funcionamento (Janeiro 2025)**
- ✅ **Correção de erro de encoding com emojis**: Implementada remoção automática de emojis no frontend
- ✅ **Correção de JavaScript quebrado**: Resolvido erro de sintaxe que impedia funcionamento dos botões
- ✅ **Eliminação de alucinação da IA**: Implementado uso de taxas de acerto reais dos prompts
- ✅ **Configuração completa do Azure OpenAI**: Adicionadas configurações necessárias (modelo, temperatura, tokens)
- ✅ **Sistema de taxas de acerto**: Frontend agora envia taxas reais para o backend
- ✅ **Prompt estruturado**: Backend usa taxas reais no formato "CONJUNTO A - NOME (Taxa: X%)"
- ✅ **Temperatura 0.0**: Configurado para eliminar alucinação da IA
- ✅ **Modelo GPT-4o**: Configurado para máxima precisão
- ✅ **16k tokens**: Configurado para respostas completas
- ✅ **Sistema robusto**: Todos os botões funcionando perfeitamente

### **Sistema de Análise Individual de Prompts (Janeiro 2025)**
- ✅ **Seção "Prompts Usados com Taxa de Acerto"**: Nova seção na página de visualizar intimação
- ✅ **Tabela ordenável**: Colunas clicáveis para ordenação (taxa de acerto, última análise, análises, modelo)
- ✅ **Ordenação padrão**: Por análise mais recente (descendente)
- ✅ **Botão "Analisar"**: Para cada prompt na tabela
- ✅ **Modal de configuração**: Sistema de configuração separado para análise individual
- ✅ **Configuração persistente**: localStorage com chave 'configPromptIndividual'
- ✅ **Persona personalizada**: Especializada em análise de eficácia de prompts
- ✅ **Opções de contexto**: Incluir contexto da intimação e gabarito
- ✅ **Instruções de resposta**: Formato JSON estruturado para análise
- ✅ **Modal "Ver Prompt"**: Visualização do prompt completo com contexto
- ✅ **Análise com IA**: Execução da análise usando configurações personalizadas
- ✅ **Resultado em Markdown**: Renderização adequada com estilos CSS
- ✅ **Botão "Testar Triagem"**: Teste da intimação com regras sugeridas pela IA
- ✅ **Configuração de quantidade**: Usuário pode especificar número de testes (1-50, padrão 10)
- ✅ **Tempo estimado**: Cálculo automático do tempo estimado baseado na quantidade
- ✅ **Textarea para regras**: Campo para colar regras de negócio sugeridas
- ✅ **Botão "Tentar Extrair Automaticamente"**: Extração automática das regras da análise
- ✅ **Modal de resultado**: Exibição de modelo, temperatura, tokens e resposta completa
- ✅ **Tooltip de resposta**: Badge com tooltip mostrando resposta completa da IA
- ✅ **Resultado consolidado**: Tabela com todos os testes executados
- ✅ **Botões de ação**: "Ver Prompt Combinado" e "Testar com Regras Combinadas"
- ✅ **Botão "Copiar Regras"**: Copia as regras utilizadas para área de transferência
- ✅ **Combinação de regras**: Regras originais do prompt + regras testadas
- ✅ **Modal de prompt combinado**: Visualização do prompt final com regras combinadas
- ✅ **Teste com regras combinadas**: Execução de testes usando regras originais + testadas
- ✅ **Sistema completo**: Análise → Sugestão → Teste → Combinação → Iteração

### **Correções de Taxa de Acerto (Janeiro 2025)**
- ✅ **Problema identificado**: Taxa de acerto inconsistente entre tabela e modais
- ✅ **Modal de análise individual**: Taxa de acerto agora calculada usando dados da linha da tabela
- ✅ **Modal "Ver Prompt"**: Taxa de acerto corrigida para usar dados da linha da tabela
- ✅ **Botão "Analisar com IA"**: Taxa de acerto corrigida para usar dados da linha da tabela
- ✅ **Função `analisarPromptIndividual()`**: Agora recebe parâmetros `(promptId, promptNome, acertos, total)`
- ✅ **Função `visualizarPromptAnaliseIndividual()`**: Agora recebe parâmetros `(promptId, promptNome, acertos, total)`
- ✅ **Função `executarAnaliseIndividual()`**: Agora recebe parâmetros `(promptId, promptNome, acertos, total)`
- ✅ **Cálculo direto**: Taxa calculada como `((acertos / total) * 100).toFixed(1)`
- ✅ **Backend atualizado**: Endpoint `/api/analisar-prompt-individual` agora usa dados do frontend
- ✅ **Consistência total**: Mesma taxa de acerto em tabela, modais e análises
- ✅ **Performance melhorada**: Sem requisições extras à API
- ✅ **Dados sincronizados**: Fonte única de dados da linha da tabela
- ✅ **Logs de debug**: Adicionados para facilitar investigação de problemas
- ✅ **Fallback seguro**: Backend mantém busca na API como fallback
- ✅ **Interface unificada**: Todas as interfaces mostram taxa de acerto idêntica

### **Sistema de Wizard para Análise de Prompts (Janeiro 2025)**
- ✅ **Refatoração completa**: Modal única com wizard de 5 etapas
- ✅ **Etapa 1 - Configuração**: Persona, instruções de análise e opções
- ✅ **Etapa 2 - Análise IA**: Execução e exibição da análise com IA
- ✅ **Etapa 3 - Teste Triagem**: Configuração de regras e quantidade de testes
- ✅ **Etapa 4 - Resultado**: Exibição consolidada dos testes com estatísticas
- ✅ **Etapa 5 - Teste Combinado**: Teste com regras originais + sugeridas
- ✅ **Navegação híbrida**: Badges superiores para navegação livre entre etapas já visitadas
- ✅ **Fluxo sequencial**: Botões inferiores para progressão e execução de testes
- ✅ **Indicadores visuais**: Badges coloridos (verde=concluída, azul=atual, azul claro=disponível, cinza=bloqueada)
- ✅ **Barra de progresso**: Indicador visual do percentual de conclusão
- ✅ **Textos contextuais**: Botões com textos que explicam a ação ("Fazer diagnóstico", "Executar Teste", etc.)
- ✅ **Preservação de dados**: Todos os resultados salvos em `window.wizardData`
- ✅ **Navegação livre**: Clique nos badges para revisar etapas já concluídas
- ✅ **Validação inteligente**: Etapas liberadas apenas após conclusão das anteriores
- ✅ **Regra testada visível**: Seção mostrando a regra em teste nas Etapas 4 e 5
- ✅ **Botão copiar regra**: Botões para copiar a regra testada nas Etapas 4 e 5
- ✅ **Configuração de quantidade**: Campo para definir número de testes combinados (1-50, padrão 10)
- ✅ **Tempo estimado**: Cálculo automático do tempo para teste combinado
- ✅ **Botão "Executar Novo Teste"**: Substitui botão "Ver Teste Combinado" para re-execução
- ✅ **Navegação superior**: Usar badges para visualizar resultados existentes
- ✅ **UX otimizada**: Fluxo claro entre execução (botões) e visualização (badges)

### **Sistema de Ordenação e Interface Avançada (Janeiro 2025)**
- ✅ **Ordenação por Taxa de Acerto**: Coluna "Taxa de Acerto" ordenável na tabela principal
- ✅ **Ícone de ordenação**: Indicador visual de direção da ordenação (ascendente/descendente)
- ✅ **CSS otimizado**: Ícone inline para evitar "pulo" visual durante carregamento
- ✅ **Popover customizado**: Taxa de acerto com popover interativo e detalhado
- ✅ **Posicionamento fixo**: Popover sempre visível na tela com posicionamento inteligente
- ✅ **Botão fixo**: Botão "Comparar Prompts Selecionados" fixo no rodapé do popover
- ✅ **Borda azul**: Contorno diferenciado para destacar o popover da página
- ✅ **Efeito hover**: Sombra e transição suave ao passar o mouse
- ✅ **Padding otimizado**: Espaçamento adequado para evitar sobreposição do botão
- ✅ **Scroll interno**: Modal wizard com scroll interno limitado ao cabeçalho
- ✅ **Altura ajustável**: Modal com altura maior (80vh) para melhor aproveitamento
- ✅ **Canaleta de scroll**: Sistema de scroll com canaleta de 50vh para etapas 3, 4 e 5
- ✅ **Conteúdo completo**: Etapa 4 mostra todo conteúdo com scroll funcional
- ✅ **Interface responsiva**: Adaptação automática a diferentes tamanhos de tela

### **Sistema de Taxa de Acerto na Página de Intimações (Janeiro 2025)**
- ✅ **Coluna Taxa de Acerto**: Implementada na página de intimações com popover interativo
- ✅ **Componente reutilizável**: JavaScript e CSS centralizados em arquivos separados
- ✅ **Popover inteligente**: Posicionamento automático e delay de 500ms
- ✅ **Filtro por prompt específico**: Dropdown para selecionar prompt e filtrar intimações
- ✅ **API dedicada**: Endpoints para taxa de acerto geral e por prompt específico
- ✅ **Performance por temperatura**: Exibição de todas as temperaturas usadas pelo prompt
- ✅ **Nome do prompt**: Exibição do nome real do prompt no popover
- ✅ **Prompts clicáveis**: Links para visualização detalhada dos prompts
- ✅ **Sem duplicação de código**: Componente único reutilizado entre páginas
- ✅ **Event listeners unificados**: Mouse hover e leave funcionando corretamente
- ✅ **CSS centralizado**: Estilos do popover em arquivo separado
- ✅ **JavaScript modular**: Funções organizadas e reutilizáveis
- ✅ **Integração completa**: Funciona com filtros existentes da página

### **Sistema de Filtros Avançados e Ordenação (Janeiro 2025)**
- ✅ **Filtro por temperatura**: Dropdown para filtrar por temperatura específica
- ✅ **Filtros combinados**: Prompt específico + temperatura funcionando em conjunto
- ✅ **Ordenação backend**: Taxa de acerto ordenada considerando filtros aplicados
- ✅ **Preservação de filtros**: Filtros mantidos durante paginação
- ✅ **API endpoints**: `/api/intimacoes/taxa-acerto-prompt-temperatura/<prompt_id>/<temperatura>`
- ✅ **Backend sorting**: Função `calcular_taxa_acerto_intimacao_filtrada` para ordenação correta
- ✅ **Tolerância de float**: Comparação de temperatura com tolerância para evitar problemas de precisão
- ✅ **URLs de paginação**: Parâmetros de filtro incluídos em todos os links de paginação

### **Sistema de Histórico de Acurácia por Condições (Janeiro 2025)**
- ✅ **Tabela de histórico**: Exibição de acurácia por número de intimações e temperatura
- ✅ **Agrupamento inteligente**: Médias calculadas para mesmas condições (intimações + temperatura)
- ✅ **Colunas abreviadas**: Títulos compactos para melhor visualização
- ✅ **Formato de data**: DD/MM/YYYY para melhor legibilidade
- ✅ **Posicionamento**: Seção movida para sidebar direita, abaixo de "Estatísticas de Performance"
- ✅ **API endpoints**: `/api/prompts/<id>/historico-acuracia` e `/api/prompts/<id>/acuracia-condicoes/<int>/<float>`
- ✅ **Banco de dados**: Tabela `historico_acuracia` para armazenar dados históricos
- ✅ **Salvamento automático**: Histórico salvo automaticamente após cada análise

### **Sistema de Acurácia na Listagem de Prompts (Janeiro 2025)**
- ✅ **Coluna Acurácia**: Nova coluna na página `/prompts` mostrando acurácia mais recente
- ✅ **Popover de histórico**: Hover na coluna mostra todas as acurácias históricas
- ✅ **Critério de seleção**: Ordenação por `numero_intimacoes DESC, temperatura ASC, ultima_analise DESC`
- ✅ **Componente reutilizável**: Popover reutilizado da página de intimações
- ✅ **API integrada**: Endpoint `/api/prompts/<id>/historico-acuracia` para dados históricos
- ✅ **Carregamento dinâmico**: Dados carregados via AJAX para melhor performance

### **Sistema de Cores Configuráveis (Janeiro 2025)**
- ✅ **Escala de cores personalizável**: Configuração de thresholds para cada cor na página de configurações
- ✅ **Preview em tempo real**: Visualização das cores conforme configuração
- ✅ **Configuração persistente**: Valores salvos no banco de dados
- ✅ **API de configuração**: Endpoint `/api/config/cores` para carregar configurações
- ✅ **JavaScript modular**: Classe `ConfigCoresManager` para gerenciar configurações
- ✅ **Integração completa**: Cores aplicadas em todas as interfaces (badges, popovers, etc.)
- ✅ **Fallback seguro**: Cores padrão quando configuração não disponível

### **Sistema de Select Customizado com Badges (Janeiro 2025)**
- ✅ **Componente customizado**: Select HTML/CSS/JS personalizado para superar limitações do browser
- ✅ **Badges coloridos**: Acurácia exibida com badges coloridos dentro das opções
- ✅ **Configuração de cores**: Badges seguem escala configurável (verde/amarelo/vermelho/cinza)
- ✅ **API de dados**: Carregamento de acurácia histórica para cada prompt
- ✅ **Sincronização**: Select customizado sincronizado com select original para formulários
- ✅ **Eventos**: Disparo correto de eventos `change` e `input` no select original
- ✅ **Performance**: Carregamento assíncrono de dados de acurácia
- ✅ **Fallback**: Badge cinza quando dados não disponíveis

### **Correções de Bugs Críticos (Janeiro 2025)**
- ✅ **Erro `NoneType`**: Corrigido problema de `int()` com valores `None` no backend
- ✅ **Fallbacks robustos**: Valores padrão para `max_tokens`, `temperatura` e `timeout`
- ✅ **Sincronização de select**: Função `syncValue()` para garantir valores corretos
- ✅ **Debug logs**: Sistema de logs detalhado para troubleshooting
- ✅ **Performance**: Remoção de logs excessivos que causavam lentidão
- ✅ **Configuração de cores**: Correção de problema de salvamento de `cores_ativadas`
- ✅ **Backend robusto**: Tratamento de valores `true`/`false` e `'on'` para checkboxes

### **Sistema de Debug de Prompts (Janeiro 2025)**
- ✅ **Botão Debug**: Adicionado no passo 2 do wizard de análise individual
- ✅ **Modal de debug**: Exibição completa do prompt enviado para a IA
- ✅ **Prompt completo**: Backend retorna o prompt exato usado na análise
- ✅ **Cópia de prompt**: Funcionalidade para copiar o prompt para área de transferência
- ✅ **API atualizada**: Endpoint `/api/analisar-prompt-individual` retorna `prompt_completo`
- ✅ **Armazenamento**: Prompt completo salvo em `window.wizardData.promptCompleto`
- ✅ **Visibilidade condicional**: Botão aparece apenas após execução da análise
- ✅ **Formatação**: Prompt exibido com formatação monospace para melhor legibilidade
- ✅ **Scroll interno**: Modal com scroll para prompts longos
- ✅ **Integração completa**: Funciona com dados da análise original da intimação

### **Sistema de Destaque de Intimações (Janeiro 2025)**
- ✅ **Sistema completo**: Funcionalidade para destacar/remover destaque de intimações
- ✅ **Componente reutilizável**: Botão e CSS centralizados em arquivos separados
- ✅ **Persistência**: Estado salvo no banco SQLite com campo `destacada`
- ✅ **Visual**: Cards ficam amarelos quando destacados
- ✅ **Funcionalidade**: Botão alterna corretamente (destacar/remover)
- ✅ **Filtros**: "Apenas destacadas" em todas as páginas
- ✅ **Compatibilidade**: Funciona em todas as páginas (intimações, análise, histórico)
- ✅ **API endpoint**: `/api/intimacoes/<id>/destacar` para atualizar estado
- ✅ **JavaScript defensivo**: Prevenção de múltiplas inicializações
- ✅ **Correção de tipos**: JavaScript reconhece tanto `"true"` quanto `"1"`
- ✅ **Integração completa**: Sistema funciona em todas as interfaces do sistema
