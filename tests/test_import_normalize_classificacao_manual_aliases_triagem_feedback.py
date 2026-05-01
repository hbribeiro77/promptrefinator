"""Aliases de classificação na importação em lote (_import_normalize_classificacao)."""

import app as app_module


def test_encaminhar_intimacao_curto_mapeia_para_canonico():
    assert (
        app_module._import_normalize_classificacao("ENCAMINHAR_INTIMACAO")
        == "ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR"
    )


def test_encaminhar_intimacao_com_espacos():
    assert (
        app_module._import_normalize_classificacao("encaminhar intimacao")
        == "ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR"
    )


def test_encaminhar_intimacao_para_outro_defensor_snake_continua_ok():
    assert (
        app_module._import_normalize_classificacao("ENCAMINHAR_INTIMACAO_PARA_OUTRO_DEFENSOR")
        == "ENCAMINHAR INTIMAÇÃO PARA OUTRO DEFENSOR"
    )


def test_devolver_a_institucional_snake_mapeia_para_canonico():
    assert (
        app_module._import_normalize_classificacao("DEVOLVER_A_INSTITUCIONAL")
        == "DEVOLVER À INSTITUCIONAL"
    )
