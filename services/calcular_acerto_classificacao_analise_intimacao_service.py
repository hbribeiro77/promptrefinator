"""Cálculo de acerto (boolean) entre classificação manual e resultado da IA na análise em lote."""
from typing import Optional

MODO_PADRAO = "padrao"
MODO_FOCADO = "focado"
INDETERMINADO_NORMALIZADO = "INDETERMINADO"


def _norm(s: Optional[str]) -> str:
    if s is None:
        return ""
    return str(s).strip().upper()


def calcular_acerto_classificacao(
    classificacao_manual: Optional[str],
    resultado_ia: Optional[str],
    *,
    modo_avaliacao: str,
    tipo_alvo_focado: Optional[str],
    calcular_acuracia: bool,
) -> Optional[bool]:
    """
    Retorna None se não deve calcular acerto; True/False caso contrário.

    Modo padrão: acerto = manual normalizado == IA normalizado (com classificação manual e flag).
    Modo focado: IA deve estar em {tipo_alvo, INDETERMINADO}; fora disso => False.
    """
    if not calcular_acuracia:
        return None
    if not (classificacao_manual and str(classificacao_manual).strip()):
        return None

    manual_n = _norm(classificacao_manual)
    ia_n = _norm(resultado_ia)
    modo = (modo_avaliacao or MODO_PADRAO).strip().lower()

    if modo == MODO_FOCADO:
        alvo_n = _norm(tipo_alvo_focado)
        if not alvo_n:
            return None
        permitidos = {alvo_n, INDETERMINADO_NORMALIZADO}
        if ia_n not in permitidos:
            return False
        if manual_n == alvo_n:
            return ia_n == alvo_n
        return ia_n == INDETERMINADO_NORMALIZADO

    # padrao
    return manual_n == ia_n
