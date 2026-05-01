"""Testes dos métodos SQL leves dos relatórios e conteúdo completo sob demanda."""

import os
import tempfile
import uuid

import pytest

from services.sqlite_service import SQLiteService


@pytest.fixture()
def svc_db_vazio():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        yield SQLiteService(db_path=path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _seed_prompt(svc: SQLiteService, pid: str, nome: str) -> None:
    svc.save_prompt(
        {
            "id": pid,
            "nome": nome,
            "conteudo": "c",
            "regra_negocio": "r",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )


def _seed_intimacao(svc: SQLiteService, iid: str, classificacao_manual: str) -> None:
    svc.save_intimacao(
        {
            "id": iid,
            "contexto": "contexto",
            "classificacao_manual": classificacao_manual,
            "informacao_adicional": "info",
            "processo": "proc",
            "orgao_julgador": "orgao",
            "intimado": "intimado",
            "status": "pendente",
            "prazo": "5 dias",
            "disponibilizacao": "2026-01-10",
            "data_criacao": "2026-01-01T00:00:00",
        }
    )


def _seed_analise(
    svc: SQLiteService,
    aid: str,
    iid: str,
    pid: str,
    *,
    data_analise: str,
    acertou: bool,
    prompt_completo: str,
    resposta_completa: str,
) -> None:
    svc.save_analise(
        {
            "id": aid,
            "intimacao_id": iid,
            "prompt_id": pid,
            "prompt_nome": "Prompt A",
            "data_analise": data_analise,
            "resultado_ia": "ELABORAR PEÇA",
            "acertou": acertou,
            "modelo": "gpt-4",
            "temperatura": 0.0,
            "tempo_processamento": 1.5,
            "tokens_input": 10,
            "tokens_output": 20,
            "custo_real": 0.1234,
            "prompt_completo": prompt_completo,
            "resposta_completa": resposta_completa,
        }
    )


def test_relatorios_count_e_paginacao_com_filtro_classificacao(svc_db_vazio):
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _seed_prompt(svc, pid, "Prompt A")
    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    _seed_intimacao(svc, i1, "ALFA")
    _seed_intimacao(svc, i2, "BETA")
    _seed_analise(
        svc,
        str(uuid.uuid4()),
        i1,
        pid,
        data_analise="2026-01-11T10:00:00",
        acertou=True,
        prompt_completo="P1",
        resposta_completa="R1",
    )
    _seed_analise(
        svc,
        str(uuid.uuid4()),
        i2,
        pid,
        data_analise="2026-01-12T10:00:00",
        acertou=False,
        prompt_completo="P2",
        resposta_completa="R2",
    )

    total = svc.contar_analises_relatorios_filtradas(classificacao_manual="ALFA")
    assert total == 1
    page = svc.listar_analises_relatorios_paginadas(
        pagina=1,
        itens_por_pagina=10,
        classificacao_manual="ALFA",
    )
    assert len(page) == 1
    assert page[0]["classificacao_manual"] == "ALFA"


def test_relatorios_agregados_e_busca_conteudo_completo_por_id(svc_db_vazio):
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _seed_prompt(svc, pid, "Prompt A")
    iid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    _seed_intimacao(svc, iid, "ALFA")
    _seed_analise(
        svc,
        aid,
        iid,
        pid,
        data_analise="2026-01-13T09:00:00",
        acertou=True,
        prompt_completo="PROMPT_LONGO",
        resposta_completa="RESPOSTA_LONGA",
    )

    agg = svc.obter_agregados_relatorios_filtrados()
    assert agg["total_analises"] == 1
    assert agg["acertos"] == 1
    assert agg["distribuicao_manual"]["ALFA"] == 1
    assert agg["dados_graficos"]["classificacoes_manuais"]["labels"] == ["ALFA"]

    conteudo = svc.get_analise_prompt_resposta_completa_por_id(aid)
    assert conteudo is not None
    assert conteudo["prompt_completo"] == "PROMPT_LONGO"
    assert conteudo["resposta_completa"] == "RESPOSTA_LONGA"
