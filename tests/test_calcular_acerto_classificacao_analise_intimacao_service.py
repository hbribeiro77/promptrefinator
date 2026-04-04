"""Testes do cálculo de acerto padrão vs modo focado."""
import pytest

from services.calcular_acerto_classificacao_analise_intimacao_service import (
    MODO_FOCADO,
    MODO_PADRAO,
    calcular_acerto_classificacao,
)


def test_padrao_acerto():
    assert (
        calcular_acerto_classificacao(
            "RENUNCIAR PRAZO",
            "renunciar prazo",
            modo_avaliacao=MODO_PADRAO,
            tipo_alvo_focado=None,
            calcular_acuracia=True,
        )
        is True
    )


def test_padrao_erro():
    assert (
        calcular_acerto_classificacao(
            "RENUNCIAR PRAZO",
            "OCULTAR",
            modo_avaliacao=MODO_PADRAO,
            tipo_alvo_focado=None,
            calcular_acuracia=True,
        )
        is False
    )


def test_sem_calcular_acuracia():
    assert (
        calcular_acerto_classificacao(
            "X",
            "X",
            modo_avaliacao=MODO_PADRAO,
            tipo_alvo_focado=None,
            calcular_acuracia=False,
        )
        is None
    )


def test_sem_classificacao_manual():
    assert (
        calcular_acerto_classificacao(
            None,
            "X",
            modo_avaliacao=MODO_PADRAO,
            tipo_alvo_focado=None,
            calcular_acuracia=True,
        )
        is None
    )


def test_focado_vp():
    assert (
        calcular_acerto_classificacao(
            "RENUNCIAR PRAZO",
            "RENUNCIAR PRAZO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is True
    )


def test_focado_vn():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "INDETERMINADO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is True
    )


def test_focado_fn_manual_alvo_ia_indeterminado():
    assert (
        calcular_acerto_classificacao(
            "RENUNCIAR PRAZO",
            "INDETERMINADO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is False
    )


def test_focado_fp_manual_outro_ia_alvo():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "RENUNCIAR PRAZO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is False
    )


def test_focado_ia_fora_do_conjunto():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "ELABORAR PEÇA",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is False
    )


def test_focado_erro_extracao():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "ERRO: Classificação não reconhecida",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="RENUNCIAR PRAZO",
            calcular_acuracia=True,
        )
        is False
    )


def test_focado_sem_tipo_alvo_retorna_none():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "INDETERMINADO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado=None,
            calcular_acuracia=True,
        )
        is None
    )


def test_focado_tipo_alvo_vazio_retorna_none():
    assert (
        calcular_acerto_classificacao(
            "OCULTAR",
            "INDETERMINADO",
            modo_avaliacao=MODO_FOCADO,
            tipo_alvo_focado="   ",
            calcular_acuracia=True,
        )
        is None
    )
