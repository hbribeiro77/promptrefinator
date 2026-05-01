"""Testes do preview de /api/analisar-prompt-individual: bloco conteúdo do cadastro no wizard."""

from unittest.mock import patch

import pytest


@pytest.fixture
def flask_client():
    import app as flask_app_module

    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as c:
        yield c


def test_preview_com_flag_inclui_conteudo_apos_identificacao_e_antes_triagem(flask_client):
    import app as m

    prompt_row = {
        "id": 1,
        "conteudo": "TEXTO_CONTEUDO_CADASTRO",
        "regra_negocio": "REGRAS_NEGOCIO",
    }

    with patch.object(m.data_service, "get_prompt_by_id", return_value=prompt_row):
        with patch.object(m.data_service, "get_intimacao_by_id", return_value=None):
            r = flask_client.post(
                "/api/analisar-prompt-individual",
                json={
                    "prompt_id": 1,
                    "prompt_nome": "Nome Teste",
                    "intimacao_id": None,
                    "preview_only": True,
                    "config_personalizada": {
                        "persona": "PERSONA_X",
                        "incluirContextoIntimacao": False,
                        "incluirInformacaoAdicional": False,
                        "incluirIdentificacaoPromptDesempenho": True,
                        "incluirConteudoPromptCadastrado": True,
                        "incluirTriagemFeitaPelaIa": True,
                    },
                    "dados_analise_original": None,
                },
            )

    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    full = data["prompt_completo"]
    assert "=== IDENTIFICAÇÃO DO PROMPT E DESEMPENHO ===" in full
    assert "=== CONTEÚDO DO PROMPT (CADASTRO) ===" in full
    assert "TEXTO_CONTEUDO_CADASTRO" in full
    assert "=== TRIAGEM FEITA PELA IA ===" in full
    idx_id = full.index("=== IDENTIFICAÇÃO DO PROMPT E DESEMPENHO ===")
    idx_ct = full.index("=== CONTEÚDO DO PROMPT (CADASTRO) ===")
    idx_tr = full.index("=== TRIAGEM FEITA PELA IA ===")
    assert idx_id < idx_ct < idx_tr


def test_preview_sem_flag_nao_inclui_titulo_conteudo_cadastro(flask_client):
    import app as m

    prompt_row = {
        "id": 1,
        "conteudo": "TEXTO_CONTEUDO_CADASTRO",
        "regra_negocio": "REGRAS_NEGOCIO",
    }

    with patch.object(m.data_service, "get_prompt_by_id", return_value=prompt_row):
        with patch.object(m.data_service, "get_intimacao_by_id", return_value=None):
            r = flask_client.post(
                "/api/analisar-prompt-individual",
                json={
                    "prompt_id": 1,
                    "prompt_nome": "Nome Teste",
                    "intimacao_id": None,
                    "preview_only": True,
                    "config_personalizada": {
                        "persona": "PERSONA_X",
                        "incluirContextoIntimacao": False,
                        "incluirInformacaoAdicional": False,
                        "incluirIdentificacaoPromptDesempenho": True,
                        "incluirConteudoPromptCadastrado": False,
                        "incluirTriagemFeitaPelaIa": False,
                    },
                    "dados_analise_original": None,
                },
            )

    assert r.status_code == 200
    full = r.get_json()["prompt_completo"]
    assert "=== CONTEÚDO DO PROMPT (CADASTRO) ===" not in full
    assert "TEXTO_CONTEUDO_CADASTRO" not in full


def test_preview_conteudo_vazio_usa_placeholder(flask_client):
    import app as m

    prompt_row = {"id": 1, "conteudo": "   ", "regra_negocio": "R"}

    with patch.object(m.data_service, "get_prompt_by_id", return_value=prompt_row):
        with patch.object(m.data_service, "get_intimacao_by_id", return_value=None):
            r = flask_client.post(
                "/api/analisar-prompt-individual",
                json={
                    "prompt_id": 1,
                    "prompt_nome": "X",
                    "intimacao_id": None,
                    "preview_only": True,
                    "config_personalizada": {
                        "persona": "P",
                        "incluirContextoIntimacao": False,
                        "incluirInformacaoAdicional": False,
                        "incluirIdentificacaoPromptDesempenho": False,
                        "incluirConteudoPromptCadastrado": True,
                        "incluirTriagemFeitaPelaIa": False,
                    },
                },
            )

    assert r.status_code == 200
    full = r.get_json()["prompt_completo"]
    assert "(conteúdo do prompt vazio no cadastro)" in full
