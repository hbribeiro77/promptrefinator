"""GET /analise?intimacao_ids= — filtro e checkbox já no HTML (servidor)."""

from unittest.mock import patch

import pytest


@pytest.fixture
def flask_client():
    import app as flask_app_module

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as c:
        yield c


def test_analise_deep_link_marca_linha_e_filtro_no_html(flask_client):
    intimacoes = [
        {
            "id": "aaa-111",
            "classificacao_manual": "URGÊNCIA",
            "defensor": "",
            "classe": "",
            "smart_context": False,
            "data_criacao": "2026-01-01",
            "observacoes": "",
            "regras_usuario_prioridade_alta": "",
            "area_id": "",
            "area_nome": "",
        },
        {
            "id": "bbb-222",
            "classificacao_manual": "NORMAL",
            "defensor": "",
            "classe": "",
            "smart_context": False,
            "data_criacao": "2026-01-02",
            "observacoes": "",
            "regras_usuario_prioridade_alta": "",
            "area_id": "",
            "area_nome": "",
        },
    ]
    with patch(
        "app.data_service.listar_intimacoes_resumo_sem_contexto_sem_analises_para_pagina_analise_ia",
        return_value=intimacoes,
    ):
        with patch("app.data_service.get_prompts_ativos", return_value=[]):
            with patch("app.data_service.get_config", return_value={}):
                with patch(
                    "app.data_service.get_mapeamento_classe_para_area",
                    return_value={},
                ):
                    r = flask_client.get("/analise?intimacao_ids=aaa-111")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'value="aaa-111"' in html or "value='aaa-111'" in html
    assert '__servidorAplicouDeepLinkIntimacao = true' in html
    assert 'data-intimacao-id="aaa-111"' in html
    assert "checked" in html.split('data-intimacao-id="aaa-111"')[1].split("<tr")[0]
    assert 'style="display:none"' in html.split('data-intimacao-id="bbb-222"')[0][-800:]


def test_analise_deep_link_id_inexistente_nao_quebra_lista(flask_client):
    intimacoes = [{"id": "only-one", "classificacao_manual": "X", "defensor": "", "classe": "", "smart_context": False, "data_criacao": "2026-01-01", "observacoes": "", "regras_usuario_prioridade_alta": "", "area_id": "", "area_nome": ""}]
    with patch(
        "app.data_service.listar_intimacoes_resumo_sem_contexto_sem_analises_para_pagina_analise_ia",
        return_value=intimacoes,
    ):
        with patch("app.data_service.get_prompts_ativos", return_value=[]):
            with patch("app.data_service.get_config", return_value={}):
                with patch(
                    "app.data_service.get_mapeamento_classe_para_area",
                    return_value={},
                ):
                    r = flask_client.get("/analise?intimacao_ids=nao-existe")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "__servidorAplicouDeepLinkIntimacao = false" in html
