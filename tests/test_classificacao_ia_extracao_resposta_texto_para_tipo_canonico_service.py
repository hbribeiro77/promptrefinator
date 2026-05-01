"""Testes do extrator compartilhado de classificação a partir da resposta da IA."""
import pytest

from config import Config
from services.classificacao_ia_extracao_resposta_texto_para_tipo_canonico_service import (
    ALIASES_TRIAGEM_IA_PARA_CANONICO,
    classificacao_extracao_indica_falha_nucleo,
    extrair_classificacao_da_resposta_ia,
)


@pytest.fixture
def tipos():
    return list(Config.TIPOS_ACAO)


def test_resposta_vazia(tipos):
    assert extrair_classificacao_da_resposta_ia("", tipos) == "ERRO: Resposta vazia"
    assert extrair_classificacao_da_resposta_ia("   ", tipos) == "ERRO: Resposta vazia"


def test_json_triagem_com_alias_snake_case(tipos):
    raw = '{"triagem": "CONTATAR_ASSISTIDO"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "CONTATAR ASSISTIDO"


def test_json_triagem_canonico(tipos):
    raw = '{"triagem": "OCULTAR"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "OCULTAR"


def test_json_triagem_indeterminado(tipos):
    raw = '{"triagem": "INDETERMINADO"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "INDETERMINADO"


def test_json_triagem_alias_indeterminada(tipos):
    raw = '{"triagem": "INDETERMINADA"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "INDETERMINADO"


def test_json_triagem_alias_agendar_retorno(tipos):
    raw = '{"triagem": "AGENDAR_RETORNO"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "AGENDAR RETORNO"


def test_json_triagem_alias_devolver_a_institucional(tipos):
    raw = '{"triagem": "DEVOLVER_A_INSTITUCIONAL"}'
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "DEVOLVER À INSTITUCIONAL"


def test_json_triagem_analisar_curto_mapeia_analisar_processo(tipos):
    raw = (
        '{"triagem": "ANALISAR", "descricao": "x", "sugestao": "y"}'
    )
    assert extrair_classificacao_da_resposta_ia(raw, tipos) == "ANALISAR PROCESSO"


def test_substring_tipo_canonico(tipos):
    assert (
        extrair_classificacao_da_resposta_ia("A intimação é OCULTAR no sistema", tipos)
        == "OCULTAR"
    )


def test_alias_analisar_processo_no_texto(tipos):
    r = extrair_classificacao_da_resposta_ia("resultado ANALISAR_PROCESSO fim", tipos)
    assert r == "ANALISAR PROCESSO"


def test_falha_nucleo_prefixo(tipos):
    r = extrair_classificacao_da_resposta_ia("texto sem classificação conhecida xyz", tipos)
    assert classificacao_extracao_indica_falha_nucleo(r)
    assert "ERRO: Classificação não reconhecida" in r


def test_resposta_vazia_nao_eh_falha_nucleo_extracao():
    assert not classificacao_extracao_indica_falha_nucleo("ERRO: Resposta vazia")


def test_aliases_dict_cobre_chaves_upper():
    for k in ALIASES_TRIAGEM_IA_PARA_CANONICO:
        assert k == k.upper()
