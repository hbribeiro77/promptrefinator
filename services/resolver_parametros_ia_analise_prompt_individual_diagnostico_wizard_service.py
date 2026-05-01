"""
Resolve provedor, modelo e parâmetros usados em /api/analisar-prompt-individual (wizard, diagnóstico).

Mantém uma única fonte de verdade com a rota em app.py para exibir na UI antes da chamada.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from config import Config

_MIN_TOKENS_SAIDA_WIZARD_CONFIG_PERSONALIZADA = 4096

_LABEL_PROVEDOR_PT: Dict[str, str] = {
    "azure": "Azure OpenAI",
    "openai": "OpenAI",
    "litellm": "LiteLLM",
}


def max_tokens_efetivo_analise_individual_com_config_personalizada(
    max_tokens_base: int,
    config_personalizada: Any,
) -> int:
    """Espelha app.py: prompt longo no wizard; sobe o teto mínimo quando há config personalizada."""
    mt = int(max_tokens_base)
    if config_personalizada and config_personalizada != {}:
        mt = max(mt, _MIN_TOKENS_SAIDA_WIZARD_CONFIG_PERSONALIZADA)
    return mt


def aplicar_modelo_diagnostico_wizard_override(
    provedor: str,
    modelo_resolvido: str,
    override: Any,
    modelos_disponiveis: Optional[List[Any]],
) -> str:
    """
    Se `override` for um modelo permitido para o provedor atual (lista da UI), retorna-o normalizado;
    caso contrário retorna `modelo_resolvido`.
    """
    if override is None:
        return modelo_resolvido
    if not isinstance(override, str):
        return modelo_resolvido
    raw = override.strip()
    if not raw:
        return modelo_resolvido
    opts_set = {str(m).strip() for m in (modelos_disponiveis or []) if str(m).strip()}
    if not opts_set:
        return modelo_resolvido
    p = (provedor or "").strip().lower()
    if raw not in opts_set:
        return modelo_resolvido
    if p == "openai":
        return raw
    if p == "azure":
        return Config.normalize_azure_deployment(raw)
    if p == "litellm":
        return Config.normalize_litellm_model(raw)
    return modelo_resolvido


def resolver_parametros_ia_analise_prompt_individual(
    config: Optional[Dict[str, Any]],
    provider_atual: str,
) -> Dict[str, Any]:
    """
    Retorna dict com ok, modelo, temperatura, max_tokens da config e rótulos.
    Se ok é False, inclui 'erro' (mensagem curta).
    """
    cfg = config or {}
    p = (provider_atual or "").strip().lower()

    if p == "azure":
        modelo = Config.normalize_azure_deployment(
            (cfg.get("azure_deployment") or "").strip() or Config.AZURE_OPENAI_DEFAULT_DEPLOYMENT
        )
        temperatura = cfg.get("azure_temperatura")
        max_tokens = cfg.get("azure_max_tokens")
    elif p == "openai":
        modelo = cfg.get("modelo_padrao")
        temperatura = cfg.get("temperatura_padrao")
        max_tokens = cfg.get("max_tokens_padrao")
    elif p == "litellm":
        modelo = Config.normalize_litellm_model(
            (cfg.get("litellm_default_model") or "").strip() or Config.LITELLM_DEFAULT_MODEL
        )
        temperatura = cfg.get("temperatura_padrao")
        max_tokens = cfg.get("max_tokens_padrao")
    else:
        return {
            "ok": False,
            "erro": f"Provedor não suportado: {provider_atual or '—'}",
            "provedor": p or "",
            "provedor_label": _LABEL_PROVEDOR_PT.get(p, provider_atual or ""),
            "modelo": None,
            "temperatura": None,
            "max_tokens_config": None,
        }

    if not modelo:
        return {
            "ok": False,
            "erro": f"Modelo não configurado para o provedor {p}",
            "provedor": p,
            "provedor_label": _LABEL_PROVEDOR_PT.get(p, p),
            "modelo": None,
            "temperatura": temperatura,
            "max_tokens_config": max_tokens,
        }
    if temperatura is None:
        return {
            "ok": False,
            "erro": f"Temperatura não configurada para o provedor {p}",
            "provedor": p,
            "provedor_label": _LABEL_PROVEDOR_PT.get(p, p),
            "modelo": modelo,
            "temperatura": None,
            "max_tokens_config": max_tokens,
        }
    if max_tokens is None:
        return {
            "ok": False,
            "erro": f"Max tokens não configurado para o provedor {p}",
            "provedor": p,
            "provedor_label": _LABEL_PROVEDOR_PT.get(p, p),
            "modelo": modelo,
            "temperatura": temperatura,
            "max_tokens_config": None,
        }

    try:
        mt_int = int(max_tokens)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "erro": "Max tokens inválido na configuração",
            "provedor": p,
            "provedor_label": _LABEL_PROVEDOR_PT.get(p, p),
            "modelo": modelo,
            "temperatura": temperatura,
            "max_tokens_config": max_tokens,
        }

    # No wizard, o front envia sempre `config_personalizada` com persona/checkboxes ao clicar em "Fazer diagnóstico";
    # o backend aplica o mesmo piso de 4096 que para qualquer objeto não vazio.
    mt_diag = max_tokens_efetivo_analise_individual_com_config_personalizada(
        mt_int,
        {"wizard": True},
    )

    return {
        "ok": True,
        "provedor": p,
        "provedor_label": _LABEL_PROVEDOR_PT.get(p, p),
        "modelo": modelo,
        "temperatura": temperatura,
        "max_tokens_config": mt_int,
        "max_tokens_efetivo_diagnostico_wizard": mt_diag,
    }
