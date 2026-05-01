"""Testes da coluna observacoes em intimacoes (SQLiteService.save_intimacao / get_intimacao_by_id)."""

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


def test_save_intimacao_persiste_observacoes(svc_db_vazio):
    iid = str(uuid.uuid4())
    svc_db_vazio.save_intimacao(
        {
            'id': iid,
            'contexto': 'Texto de contexto suficiente para cadastro de teste.',
            'classificacao_manual': 'OCULTAR',
            'observacoes': 'Nota: revisar remição e prazo.',
            'data_criacao': '2026-01-01T00:00:00',
        }
    )
    row = svc_db_vazio.get_intimacao_by_id(iid)
    assert row is not None
    assert row.get('observacoes') == 'Nota: revisar remição e prazo.'
