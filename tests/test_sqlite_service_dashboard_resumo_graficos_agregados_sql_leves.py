"""Agregações leves para o dashboard (sem get_all_intimacoes)."""

import os
import tempfile
import uuid

import pytest

from services.sqlite_service import SQLiteService


@pytest.fixture()
def svc_db_vazio():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        yield SQLiteService(db_path=path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def test_dashboard_resumo_vazio(svc_db_vazio):
    r = svc_db_vazio.get_dashboard_resumo_graficos()
    assert r['distribuicao_classificacao'] == {}
    assert r['status_analises']['Pendente'] == 0
    assert r['status_analises']['Concluída'] == 0
    assert r['status_analises']['Erro'] == 0


def test_dashboard_resumo_distribuicao_e_pendente(svc_db_vazio):
    pid = str(uuid.uuid4())
    svc_db_vazio.save_prompt({'id': pid, 'nome': 'P', 'conteudo': 'x'})

    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    svc_db_vazio.save_intimacao(
        {
            'id': i1,
            'contexto': 'c' * 50,
            'classificacao_manual': 'RECURSO',
        }
    )
    svc_db_vazio.save_intimacao(
        {
            'id': i2,
            'contexto': 'd' * 50,
            'classificacao_manual': '',
        }
    )

    svc_db_vazio.save_analise(
        {
            'intimacao_id': i1,
            'prompt_id': pid,
            'acertou': True,
        }
    )

    r = svc_db_vazio.get_dashboard_resumo_graficos()
    assert r['distribuicao_classificacao']['RECURSO'] == 1
    assert r['distribuicao_classificacao']['Não classificada'] == 1
    assert r['status_analises']['Concluída'] == 1
    assert r['status_analises']['Pendente'] == 1
    assert r['status_analises']['Erro'] == 0
