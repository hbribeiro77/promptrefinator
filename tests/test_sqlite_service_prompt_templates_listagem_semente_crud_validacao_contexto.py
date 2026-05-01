"""Testes: tabela prompt_templates, semente vazia, CRUD e validação de {CONTEXTO}."""

import uuid

import pytest

from services.sqlite_service import SQLiteService


@pytest.fixture()
def svc_empty(tmp_path):
    db = tmp_path / "t.db"
    return SQLiteService(db_path=str(db))


def test_list_semente_quando_vazio(svc_empty):
    rows = svc_empty.list_prompt_templates()
    assert len(rows) >= 1
    assert any("Triagem JSON" in (r.get("nome") or "") for r in rows)
    assert all("{CONTEXTO}" in (r.get("conteudo") or "") for r in rows)


def test_save_rejeita_sem_contexto(svc_empty):
    with pytest.raises(ValueError, match="CONTEXTO"):
        svc_empty.save_prompt_template(
            {"nome": "X", "conteudo": "sem placeholder", "ordem": 0}
        )


def test_crud_basico(svc_empty):
    tid = svc_empty.save_prompt_template(
        {
            "nome": "Meu T",
            "descricao": "d",
            "conteudo": "Olá {CONTEXTO}",
            "ordem": 5,
        }
    )
    assert uuid.UUID(tid).version == 4
    row = svc_empty.get_prompt_template(tid)
    assert row["nome"] == "Meu T"
    assert row["ordem"] == 5
    svc_empty.save_prompt_template(
        {
            "id": tid,
            "nome": "Meu T2",
            "descricao": None,
            "conteudo": "Oi {CONTEXTO}",
            "ordem": 1,
        }
    )
    row2 = svc_empty.get_prompt_template(tid)
    assert row2["nome"] == "Meu T2"
    assert row2["conteudo"] == "Oi {CONTEXTO}"
    assert svc_empty.delete_prompt_template(tid) is True
    assert svc_empty.get_prompt_template(tid) is None
