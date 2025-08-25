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
- **IA**: OpenAI API (GPT-3.5-turbo, GPT-4)
- **Armazenamento**: JSON (arquivos locais)
- **Exportação**: CSV, Excel
- **Variáveis de Ambiente**: python-dotenv

### **Estrutura de Diretórios**
```
promptrefinator2/
├── app.py                 # Aplicação principal Flask
├── config.py              # Configurações do sistema
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente (NOVO)
├── .gitignore            # Arquivos ignorados pelo Git (NOVO)
├── README.md             # Documentação do projeto (NOVO)
├── data/                  # Dados persistentes
│   ├── intimacoes.json   # Intimações cadastradas
│   ├── prompts.json      # Prompts de IA
│   ├── config.json       # Configurações do usuário
│   └── backups/          # Backups automáticos
├── services/             # Camada de serviços
│   ├── data_service.py   # Gerenciamento de dados
│   ├── openai_service.py # Integração OpenAI
│   └── export_service.py # Exportação de dados
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── dashboard.html    # Página inicial
│   ├── analise.html      # Interface de análise
│   ├── relatorios.html   # Relatórios e gráficos
│   ├── configuracoes.html # Configurações
│   ├── intimacoes.html   # Listagem de intimações
│   ├── prompts.html      # Listagem de prompts
│   └── partials/         # Componentes reutilizáveis
│       ├── tabela_analises.html
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
- `/prompts` - Gerenciamento de prompts
- `/analise` - Interface de análise de IA
- `/relatorios` - Relatórios e estatísticas
- `/configuracoes` - Configurações do sistema
- `/exportar` - Exportação de dados
- `/api/relatorios/pagina/<int:pagina>` - Paginação AJAX
- `/api/analises/excluir` - Exclusão de análises
- `/api/analise-progresso` - Server-Sent Events para progresso em tempo real (NOVO)
- `/api/precos-modelos` - API para obter preços dos modelos (NOVO)

**Funcionalidades Especiais:**
- Paginação AJAX para relatórios
- Sistema de backup automático
- Exportação em múltiplos formatos
- API REST para operações CRUD
- Sistema de variáveis de ambiente para chaves de API
- Persistência de configurações de colunas via localStorage
- **NOVO**: Sistema de progresso em tempo real com Server-Sent Events
- **NOVO**: Cálculo de custo real baseado em tokens e preços configurados
- **NOVO**: Tooltips de memória de cálculo com soma automática

### **2. Configurações (`config.py`)**

**Classes de Configuração:**
- `Config` - Configurações base
- `DevelopmentConfig` - Configurações para desenvolvimento
- `ProductionConfig` - Configurações para produção
- `TestingConfig` - Configurações para testes

**Configurações Principais:**
- Chaves de API OpenAI (agora via variáveis de ambiente)
- Modelos de IA disponíveis
- Tipos de ação para classificação
- Configurações de backup e paginação

### **3. Serviços**

#### **DataService (`services/data_service.py`)**
**Responsabilidades:**
- Gerenciamento completo de dados JSON
- CRUD para intimações, prompts e análises
- Sistema de backup automático
- Validação e integridade de dados
- **NOVO**: Substituição de placeholders por variáveis de ambiente

**Métodos Principais:**
- `get_all_intimacoes()` - Listar todas as intimações
- `save_intimacao()` - Salvar intimação
- `adicionar_analise_intimacao()` - Adicionar análise
- `get_config()` / `save_config()` - Gerenciar configurações
- **NOVO**: Substituição automática de `${VARIABLE}` por valores de ambiente

#### **OpenAIService (`services/openai_service.py`)**
**Responsabilidades:**
- Integração com API OpenAI
- Análise de intimações usando IA
- Tratamento de erros e retry
- Estimativa de custos
- **NOVO**: Priorização de variáveis de ambiente sobre config.json

**Funcionalidades:**
- Teste de conexão com OpenAI
- Análise de intimações com prompts customizados
- Extração de classificações da resposta da IA
- Sistema de retry para falhas de API
- **NOVO**: Carregamento seguro de chaves de API

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
- Migração para banco de dados relacional
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
- ✅ Integração eficiente com OpenAI
- ✅ Relatórios detalhados e gráficos
- ✅ Configuração flexível
- ✅ Exportação de dados completa
- ✅ Segurança aprimorada com variáveis de ambiente
- ✅ Persistência de configurações do usuário
- ✅ Sistema de modais reutilizáveis
- ✅ Paginação AJAX otimizada
- ✅ **NOVO**: Sistema de progresso em tempo real com Server-Sent Events
- ✅ **NOVO**: Cálculo de custo real baseado em tokens e preços
- ✅ **NOVO**: Tooltips de memória de cálculo com soma automática

**Tecnologias Utilizadas:**
- Python + Flask (Backend)
- Bootstrap 5 + Chart.js (Frontend)
- OpenAI API (IA)
- JSON (Persistência)
- AJAX (Interatividade)
- **NOVO**: python-dotenv (Variáveis de ambiente)

**Melhorias Recentes:**
- 🔐 Segurança da chave da API OpenAI via variáveis de ambiente
- 🎛️ Persistência de configurações de colunas via localStorage
- 🔄 Sistema de modais reutilizáveis para prompts e respostas
- 📊 Paginação AJAX sem mudança de URL
- 🗂️ Componentes modulares para melhor manutenibilidade
- 📝 Documentação completa com README.md
- ⚡ **NOVO**: Sistema de progresso em tempo real com Server-Sent Events
- 💰 **NOVO**: Cálculo de custo real baseado em tokens e preços configurados
- 🧮 **NOVO**: Tooltips de memória de cálculo com soma automática
- 🎯 **NOVO**: Barra de progresso dinâmica com cancelamento

O sistema está pronto para uso em produção e pode ser facilmente estendido com novas funcionalidades conforme necessário.
