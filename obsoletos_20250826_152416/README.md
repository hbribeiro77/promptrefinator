# Scripts Obsoletos

Este diretório contém scripts que foram marcados como obsoletos após a migração do sistema para SQLite.

## Por que foram movidos?

Estes scripts ainda referenciam arquivos JSON (`intimacoes.json`, `prompts.json`, `analises.json`) que foram removidos após a migração para SQLite.

## Scripts incluídos:

- `criar_prompt_teste.py` - Criava prompts de teste em JSON
- `recuperar_intimacoes_perdidas.py` - Recuperava intimações de arquivos JSON
- `script_atualizar_custos_analises_existentes.py` - Atualizava custos em JSON
- `script_limpar_todos_custos_estimados.py` - Limpava custos em JSON
- `script_recuperacao_analises_perdidas.py` - Recuperava análises de JSON
- `script_remover_custo_estimado_completo.py` - Removia custos de JSON
- `script_teste_exclusao_analise_debug.py` - Testes de exclusão em JSON
- `script_verificacao_perda_intimacoes.py` - Verificava perdas em JSON
- `teste_exclusao_massa_analises.py` - Testes de exclusão em massa
- `teste_cenario_usuario_exclusao_relatorio.py` - Testes de cenário
- `teste_prompts.py` - Testes de prompts em JSON
- `verificar_intimacoes_recuperadas.py` - Verificação de recuperação

## O que usar agora?

- **Dados**: Agora armazenados no banco SQLite (`data/database.db`)
- **Configurações**: Ainda em `data/config.json`
- **Backups**: Automáticos do banco SQLite
- **Consultas**: Use o SQLiteService para acessar dados

## Como acessar dados agora?

```python
from services.sqlite_service import SQLiteService

# Instanciar serviço
data_service = SQLiteService()

# Obter intimações
intimacoes = data_service.get_all_intimacoes()

# Obter prompts
prompts = data_service.get_all_prompts()

# Obter análises
analises = data_service.get_all_analises()
```

## Data da migração:
26/08/2025 15:24:16
