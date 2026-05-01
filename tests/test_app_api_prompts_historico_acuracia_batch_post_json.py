"""Testes de POST /api/prompts/historico-acuracia-batch."""

from unittest.mock import patch

import pytest


@pytest.fixture
def flask_client():
    import app as flask_app_module

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as c:
        yield c


def test_batch_retorna_por_prompt(flask_client):
    fake = {
        "p1": [{"acuracia_media": 81.5}],
        "p2": [],
    }
    with patch(
        "app.data_service.get_historico_acuracia_prompt_multi",
        return_value=fake,
    ):
        r = flask_client.post(
            "/api/prompts/historico-acuracia-batch",
            json={"prompt_ids": ["p1", "p2", "p1"]},
        )
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["por_prompt"]["p1"][0]["acuracia_media"] == 81.5
    assert data["por_prompt"]["p2"] == []


def test_batch_rejeita_prompt_ids_invalido(flask_client):
    r = flask_client.post(
        "/api/prompts/historico-acuracia-batch",
        json={"prompt_ids": "não-lista"},
    )
    assert r.status_code == 400
