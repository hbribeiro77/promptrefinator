"""Testes de /api/analisar-prompt-individual com modeloDiagnosticoOverride (wizard)."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def flask_client():
    import app as flask_app_module

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as c:
        yield c


def test_diagnostico_chama_ia_com_modelo_override_valido(flask_client):
    import app as m

    prompt_row = {
        "id": 1,
        "conteudo": "",
        "regra_negocio": "REGRAS",
    }
    parametros_capturados = {}

    def side_analisar(_ctx, _tmpl, parametros):
        parametros_capturados.update(parametros)
        return "IND", '{"analise":"ok"}', {}

    with patch.object(m.data_service, "get_prompt_by_id", return_value=prompt_row):
        with patch.object(m.data_service, "get_intimacao_by_id", return_value=None):
            with patch.object(
                m.data_service,
                "get_config",
                return_value={
                    "modelo_padrao": "gpt-4",
                    "temperatura_padrao": 0.2,
                    "max_tokens_padrao": 2000,
                },
            ):
                with patch("app.AIManagerService") as MockAIM:
                    inst = MockAIM.return_value
                    inst.get_current_service.return_value = MagicMock()
                    inst.get_current_provider.return_value = "openai"
                    inst.get_available_models.return_value = ["gpt-4", "gpt-5-mini"]
                    inst.analisar_intimacao.side_effect = side_analisar

                    r = flask_client.post(
                        "/api/analisar-prompt-individual",
                        json={
                            "prompt_id": 1,
                            "prompt_nome": "P",
                            "intimacao_id": None,
                            "preview_only": False,
                            "config_personalizada": {
                                "persona": "X",
                                "incluirContextoIntimacao": False,
                                "incluirInformacaoAdicional": False,
                                "incluirIdentificacaoPromptDesempenho": False,
                                "incluirConteudoPromptCadastrado": False,
                                "incluirTriagemFeitaPelaIa": False,
                                "modeloDiagnosticoOverride": "gpt-5-mini",
                            },
                        },
                    )

    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert parametros_capturados.get("model") == "gpt-5-mini"
    assert data.get("modelo_diagnostico_usado") == "gpt-5-mini"


def test_diagnostico_ignora_override_fora_da_lista(flask_client):
    import app as m

    prompt_row = {"id": 1, "conteudo": "", "regra_negocio": "R"}
    parametros_capturados = {}

    def side_analisar(_ctx, _tmpl, parametros):
        parametros_capturados.update(parametros)
        return "IND", "{}", {}

    with patch.object(m.data_service, "get_prompt_by_id", return_value=prompt_row):
        with patch.object(m.data_service, "get_intimacao_by_id", return_value=None):
            with patch.object(
                m.data_service,
                "get_config",
                return_value={
                    "modelo_padrao": "gpt-4",
                    "temperatura_padrao": 0.2,
                    "max_tokens_padrao": 2000,
                },
            ):
                with patch("app.AIManagerService") as MockAIM:
                    inst = MockAIM.return_value
                    inst.get_current_service.return_value = MagicMock()
                    inst.get_current_provider.return_value = "openai"
                    inst.get_available_models.return_value = ["gpt-4", "gpt-5-mini"]
                    inst.analisar_intimacao.side_effect = side_analisar

                    r = flask_client.post(
                        "/api/analisar-prompt-individual",
                        json={
                            "prompt_id": 1,
                            "prompt_nome": "P",
                            "intimacao_id": None,
                            "preview_only": False,
                            "config_personalizada": {
                                "persona": "X",
                                "incluirContextoIntimacao": False,
                                "incluirInformacaoAdicional": False,
                                "incluirIdentificacaoPromptDesempenho": False,
                                "incluirConteudoPromptCadastrado": False,
                                "incluirTriagemFeitaPelaIa": False,
                                "modeloDiagnosticoOverride": "modelo-inexistente",
                            },
                        },
                    )

    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert parametros_capturados.get("model") == "gpt-4"
    assert data.get("modelo_diagnostico_usado") == "gpt-4"
