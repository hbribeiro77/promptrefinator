"""Testes para extract_intimados (rótulos Intimados / Intimados da intimação no prompt)."""

from services.triagem_feedback_transformacao_json_para_importacao_intimacoes_service import (
    extract_intimados,
)


def test_extract_intimados_classico_lista_com_hifen():
    prompt = """
**Processo** : 123
- **Intimados**:
- João Silva
- Maria Souza
## Fim
"""
    assert extract_intimados(prompt) == "João Silva; Maria Souza"


def test_extract_intimados_da_intimacao_com_prefixo_lista():
    prompt = """
- **Intimados da intimação**:
- Pedro Costa
- Ana Lima
"""
    assert extract_intimados(prompt) == "Pedro Costa; Ana Lima"


def test_extract_intimados_da_intimacao_bloco_multilinha():
    prompt = """**Intimados da intimação**:
- Fulano
- Ciclano
"""
    assert extract_intimados(prompt) == "Fulano; Ciclano"


def test_extract_intimados_fallback_campo_unico_intimados_da_intimacao():
    prompt = "algo - **Intimados da intimação**: José da Silva  - **Outro** : x"
    assert extract_intimados(prompt) == "José da Silva"


def test_extract_intimados_fallback_campo_unico_somente_intimados():
    prompt = "- **Intimados**: Apenas Um Nome  - **Classe** : y"
    assert extract_intimados(prompt) == "Apenas Um Nome"
