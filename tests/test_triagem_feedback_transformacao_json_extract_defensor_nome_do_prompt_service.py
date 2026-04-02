"""Testes para extract_defensor_name (frases 'triagem para' / 'triagem para o defensor (a)')."""

from services.triagem_feedback_transformacao_json_para_importacao_intimacoes_service import (
    extract_defensor_name,
)


def test_extract_defensor_legado_negrito():
    prompt = "Intro\nVocê está realizando a triagem para: **Dr. Maria Silva**\nMais texto"
    assert extract_defensor_name(prompt) == "Dr. Maria Silva"


def test_extract_defensor_para_o_defensor_a_com_negrito():
    prompt = (
        "Você está realizando a triagem para o defensor (a): **12345-M**\n"
        "- **Processo** : 1"
    )
    assert extract_defensor_name(prompt) == "12345-M"


def test_extract_defensor_para_o_defensor_a_sem_espaco_antes_parenteses():
    prompt = "Você está realizando a triagem para o defensor(a): **Ana Costa**"
    assert extract_defensor_name(prompt) == "Ana Costa"


def test_extract_defensor_para_o_defensor_a_mesma_linha_sem_negrito():
    prompt = "Você está realizando a triagem para o defensor (a): João Pedro\n## Próximo"
    assert extract_defensor_name(prompt) == "João Pedro"


def test_extract_defensor_novo_formato_tem_preferencia_sobre_legado_na_mesma_string():
    """Se ambos aparecerem (raro), o primeiro padrão que casa na ordem do código vence."""
    prompt = (
        "Você está realizando a triagem para o defensor (a): **Nome Novo**\n"
        "Você está realizando a triagem para: **Nome Legado**"
    )
    assert extract_defensor_name(prompt) == "Nome Novo"
