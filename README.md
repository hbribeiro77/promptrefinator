# Sistema Prompt Refinator

Sistema para análise e otimização de prompts de IA para a Defensoria Pública do Estado do Rio Grande do Sul (DPE/RS).

## Configuração

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar chave da API OpenAI

Crie um arquivo `.env` na raiz do projeto com sua chave da API:

```env
OPENAI_API_KEY=sua-chave-da-api-aqui
```

**Exemplo:**
```env
OPENAI_API_KEY=sk-proj-abc123...
```

### 3. Executar o sistema
```bash
python app.py
```

O sistema estará disponível em: http://127.0.0.1:5000

## Segurança

- A chave da API OpenAI é carregada do arquivo `.env`
- O arquivo `.env` está no `.gitignore` e não será commitado
- Nunca compartilhe ou commite sua chave da API

## Funcionalidades

- Cadastro de intimações jurídicas
- Criação e teste de prompts de IA
- Análise automática de intimações
- Relatórios e estatísticas
- Exportação de dados

## Estrutura

```
promptrefinator2/
├── app.py                 # Aplicação principal
├── .env                   # Variáveis de ambiente (criar)
├── data/                  # Dados persistentes
├── services/              # Serviços
├── templates/             # Templates HTML
└── static/                # Arquivos estáticos
```
