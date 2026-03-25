"""Extrai texto legível da mensagem `assistant` em respostas chat.completions (SDK OpenAI / compat)."""
from typing import Any


def texto_mensagem_assistente(message: Any) -> str:
    """Suporta content str, None, lista de blocos (multimodal/proxy) e refusal quando existir."""
    if message is None:
        return ""
    refusal = getattr(message, "refusal", None)
    if refusal:
        return str(refusal).strip()
    raw = getattr(message, "content", None)
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block.get("text", "")))
            else:
                t = getattr(block, "text", None)
                parts.append(str(t) if t is not None else str(block))
        return "".join(parts).strip()
    return str(raw).strip()
