"""Testes do endpoint de conteúdo completo da análise por ID."""

from unittest.mock import patch

import pytest


@pytest.fixture
def flask_client():
    import app as flask_app_module

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as c:
        yield c


def test_api_analises_conteudos_completos_retorna_payload(flask_client):
    import app as m

    payload = {
        "id": "a1",
        "intimacao_id": "i1",
        "prompt_completo": "PROMPT_X",
        "resposta_completa": "RESP_X",
    }
    with patch.object(m.data_service, "get_analise_prompt_resposta_completa_por_id", return_value=payload):
        resp = flask_client.get("/api/analises/a1/conteudos-completos")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["analise_id"] == "a1"
    assert data["intimacao_id"] == "i1"
    assert data["prompt_completo"] == "PROMPT_X"
    assert data["resposta_completa"] == "RESP_X"


def test_api_analises_conteudos_completos_quando_nao_encontra(flask_client):
    import app as m

    with patch.object(m.data_service, "get_analise_prompt_resposta_completa_por_id", return_value=None):
        resp = flask_client.get("/api/analises/inexistente/conteudos-completos")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
