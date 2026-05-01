"""Testes do resolver de modelo/tokens do diagnóstico (wizard análise individual)."""

from services.resolver_parametros_ia_analise_prompt_individual_diagnostico_wizard_service import (
    aplicar_modelo_diagnostico_wizard_override,
    max_tokens_efetivo_analise_individual_com_config_personalizada,
    resolver_parametros_ia_analise_prompt_individual,
)


def test_max_tokens_com_config_personalizada_aumenta_piso():
    assert max_tokens_efetivo_analise_individual_com_config_personalizada(500, {"a": 1}) == 4096
    assert max_tokens_efetivo_analise_individual_com_config_personalizada(8000, {"a": 1}) == 8000


def test_max_tokens_sem_config_ignora_piso():
    assert max_tokens_efetivo_analise_individual_com_config_personalizada(500, {}) == 500
    assert max_tokens_efetivo_analise_individual_com_config_personalizada(500, None) == 500


def test_resolver_openai_ok():
    cfg = {
        "modelo_padrao": "gpt-4",
        "temperatura_padrao": 0.2,
        "max_tokens_padrao": 1000,
    }
    r = resolver_parametros_ia_analise_prompt_individual(cfg, "openai")
    assert r["ok"] is True
    assert r["modelo"] == "gpt-4"
    assert r["max_tokens_config"] == 1000
    assert r["max_tokens_efetivo_diagnostico_wizard"] == 4096


def test_resolver_provedor_invalido():
    r = resolver_parametros_ia_analise_prompt_individual({}, "xyz")
    assert r["ok"] is False


def test_aplicar_override_openai_somente_se_estiver_na_lista():
    base = "gpt-4"
    opts = ["gpt-4", "gpt-5-mini"]
    assert aplicar_modelo_diagnostico_wizard_override("openai", base, "gpt-5-mini", opts) == "gpt-5-mini"
    assert aplicar_modelo_diagnostico_wizard_override("openai", base, "gpt-99", opts) == base
    assert aplicar_modelo_diagnostico_wizard_override("openai", base, "", opts) == base
    assert aplicar_modelo_diagnostico_wizard_override("openai", base, None, opts) == base


def test_aplicar_override_azure_normaliza_se_na_lista():
    from config import Config

    base = Config.AZURE_OPENAI_MODELS[0]
    opts = list(Config.AZURE_OPENAI_MODELS)
    assert aplicar_modelo_diagnostico_wizard_override("azure", base, base, opts) == base


def test_aplicar_override_lista_vazia_ignora():
    assert aplicar_modelo_diagnostico_wizard_override("openai", "gpt-4", "gpt-5", []) == "gpt-4"
