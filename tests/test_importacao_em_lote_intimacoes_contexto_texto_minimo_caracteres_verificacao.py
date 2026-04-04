"""Verificação de tamanho mínimo do contexto na importação em lote (_import_montar_intimacao)."""

from unittest.mock import patch

import pytest

import app as app_module


def _reg_valido_contexto(n_chars: int) -> dict:
    return {
        'contexto': 'A' * n_chars,
        'classificação manual': 'ELABORAR PEÇA',
        'nome do defensor': 'Dr Unit Test',
    }


@patch.object(app_module, 'obter_defensores_disponiveis', return_value=['Dr Unit Test'])
def test_import_montar_rejeita_contexto_com_menos_de_200_caracteres(_mock_def):
    with pytest.raises(ValueError, match='mínimo exigido na importação em lote é 200'):
        app_module._import_montar_intimacao(_reg_valido_contexto(199))


@patch.object(app_module, 'obter_defensores_disponiveis', return_value=['Dr Unit Test'])
def test_import_montar_aceita_contexto_com_200_caracteres(_mock_def):
    out = app_module._import_montar_intimacao(_reg_valido_contexto(200))
    assert len(out['contexto']) == 200
    assert out['classificacao_manual'] == 'ELABORAR PEÇA'
