"""Garante que histórico de acurácia por prompt seja agrupado por modelo + condições."""

import os
import tempfile
import uuid

import pytest

from services.sqlite_service import SQLiteService


@pytest.fixture()
def svc_db_temporario():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        yield SQLiteService(db_path=path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _salvar_prompt(svc: SQLiteService, pid: str, nome: str = "Prompt A") -> None:
    svc.save_prompt(
        {
            "id": pid,
            "nome": nome,
            "conteudo": "conteudo",
            "regra_negocio": "",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )


def test_historico_acuracia_agrupar_por_modelo_na_mesma_condicao(svc_db_temporario):
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)

    # Mesmas condições de intimações e temperatura, mas modelos distintos.
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=30,
        modelo="gpt-4o-mini",
        temperatura=0.2,
        acuracia=80.0,
        session_id=str(uuid.uuid4()),
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=30,
        modelo="gpt-4o-mini",
        temperatura=0.2,
        acuracia=100.0,
        session_id=str(uuid.uuid4()),
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=30,
        modelo="gpt-4o",
        temperatura=0.2,
        acuracia=50.0,
        session_id=str(uuid.uuid4()),
    )

    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 2

    por_modelo = {h["modelo"]: h for h in historico}
    assert "gpt-4o-mini" in por_modelo
    assert "gpt-4o" in por_modelo

    mini = por_modelo["gpt-4o-mini"]
    assert mini["numero_intimacoes"] == 30
    assert mini["temperatura"] == 0.2
    assert mini["total_analises"] == 2
    assert mini["acuracia_media"] == 90.0
    assert mini["acuracia_minima"] == 80.0
    assert mini["acuracia_maxima"] == 100.0

    full = por_modelo["gpt-4o"]
    assert full["total_analises"] == 1
    assert full["acuracia_media"] == 50.0


def test_historico_acuracia_sem_modelo_retorna_nd(svc_db_temporario):
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)

    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=10,
        temperatura=0.7,
        acuracia=75.0,
        session_id=str(uuid.uuid4()),
    )

    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 1
    assert historico[0]["modelo"] == "N/D"


def test_salvar_historico_prefere_modelo_das_analises_quando_parametro_vazio(svc_db_temporario):
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)
    iid = str(uuid.uuid4())
    svc.save_intimacao(
        {
            "id": iid,
            "contexto": "ctx",
            "classificacao_manual": "X",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )
    session_id = str(uuid.uuid4())
    svc.save_analise(
        {
            "id": str(uuid.uuid4()),
            "intimacao_id": iid,
            "prompt_id": prompt_id,
            "prompt_nome": "P",
            "data_analise": "2026-01-02T12:00:00",
            "acertou": True,
            "modelo": "gpt-4o-mini",
            "temperatura": 0.7,
            "session_id": session_id,
        }
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=1,
        temperatura=0.7,
        acuracia=100.0,
        session_id=session_id,
        modelo="",
    )
    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 1
    assert historico[0]["modelo"] == "gpt-4o-mini"


def test_salvar_historico_prefere_analises_a_parametro_inconsistente(svc_db_temporario):
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)
    iid = str(uuid.uuid4())
    svc.save_intimacao(
        {
            "id": iid,
            "contexto": "ctx",
            "classificacao_manual": "X",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )
    session_id = str(uuid.uuid4())
    svc.save_analise(
        {
            "id": str(uuid.uuid4()),
            "intimacao_id": iid,
            "prompt_id": prompt_id,
            "prompt_nome": "P",
            "data_analise": "2026-01-02T12:00:00",
            "acertou": True,
            "modelo": "gpt-4o",
            "temperatura": 0.2,
            "session_id": session_id,
        }
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=1,
        temperatura=0.2,
        acuracia=80.0,
        session_id=session_id,
        modelo="outro-modelo-errado",
    )
    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 1
    assert historico[0]["modelo"] == "gpt-4o"


def test_get_historico_mostra_modelo_da_sessao_quando_linha_historico_sem_modelo(
    svc_db_temporario,
):
    """API de histórico deve enriquecer modelo via sessoes_analise (dados legados)."""
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)
    session_id = str(uuid.uuid4())
    assert svc.criar_sessao_analise(
        session_id=session_id,
        prompt_id=prompt_id,
        prompt_nome="P",
        modelo="modelo-da-sessao-xyz",
        temperatura=0.4,
        max_tokens=500,
        timeout=30,
        total_intimacoes=3,
        configuracoes=None,
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=3,
        temperatura=0.4,
        acuracia=88.0,
        session_id=session_id,
        modelo="",
    )
    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 1
    assert historico[0]["modelo"] == "modelo-da-sessao-xyz"


def test_salvar_historico_varios_modelos_na_sessao_concatena_ordenado(svc_db_temporario):
    svc = svc_db_temporario
    prompt_id = str(uuid.uuid4())
    _salvar_prompt(svc, prompt_id)
    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    svc.save_intimacao(
        {
            "id": i1,
            "contexto": "a",
            "classificacao_manual": "X",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )
    svc.save_intimacao(
        {
            "id": i2,
            "contexto": "b",
            "classificacao_manual": "Y",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )
    session_id = str(uuid.uuid4())
    svc.save_analise(
        {
            "id": str(uuid.uuid4()),
            "intimacao_id": i1,
            "prompt_id": prompt_id,
            "prompt_nome": "P",
            "data_analise": "2026-01-02T12:00:00",
            "acertou": True,
            "modelo": "gpt-4o-mini",
            "temperatura": 0.5,
            "session_id": session_id,
        }
    )
    svc.save_analise(
        {
            "id": str(uuid.uuid4()),
            "intimacao_id": i2,
            "prompt_id": prompt_id,
            "prompt_nome": "P",
            "data_analise": "2026-01-02T13:00:00",
            "acertou": False,
            "modelo": "gpt-4o",
            "temperatura": 0.5,
            "session_id": session_id,
        }
    )
    svc.salvar_historico_acuracia(
        prompt_id=prompt_id,
        numero_intimacoes=2,
        temperatura=0.5,
        acuracia=50.0,
        session_id=session_id,
        modelo="",
    )
    historico = svc.get_historico_acuracia_prompt(prompt_id)
    assert len(historico) == 1
    assert historico[0]["modelo"] == "gpt-4o, gpt-4o-mini"
