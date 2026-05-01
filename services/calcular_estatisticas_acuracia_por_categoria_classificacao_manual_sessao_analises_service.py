"""
Agrega acertos/erros a partir das análises de uma sessão.

- Modo padrão: uma linha por classificação manual (rótulo humano).
- Modo focado: duas faixas — manual = tipo alvo vs. manual ≠ alvo (esperado INDETERMINADO da IA).

Em ambos os casos usa o campo `acertou` já gravado (mesma regra da execução).
Cada linha pode incluir quebra por classe processual e por defensor (dados da intimação).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

_SEM_CLASSIFICACAO = "(Sem classificação manual)"
_SEM_CLASSE = "(Sem classe)"
_SEM_DEFENSOR = "(Sem defensor)"
_AMOSTRA_PEQUENA_LIMITE_PADRAO = 5


def _norm(s: Optional[str]) -> str:
    if s is None:
        return ""
    return str(s).strip().upper()


def _acertou_foi_avaliado(acertou: Any) -> bool:
    return acertou is not None


def _conta_como_acerto(acertou: Any) -> bool:
    if acertou is None:
        return False
    if isinstance(acertou, bool):
        return acertou
    try:
        return int(acertou) == 1
    except (TypeError, ValueError):
        return bool(acertou)


def _etiqueta_classe_intimacao_analise(a: Mapping[str, Any]) -> str:
    c = a.get("classe")
    s = (str(c).strip() if c is not None else "") or ""
    return s if s else _SEM_CLASSE


def _etiqueta_defensor_intimacao_analise(a: Mapping[str, Any]) -> str:
    d = a.get("defensor")
    if d is not None and str(d).strip():
        return str(d).strip()
    i = a.get("intimado")
    if i is not None and str(i).strip():
        return str(i).strip()
    return _SEM_DEFENSOR


def quebra_por_classe_e_defensor_sessao_analises(
    itens: Sequence[Mapping[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Para análises já filtradas (todas com acertou avaliado), distribui acertos/erros
    por classe processual e por defensor (ou intimado como fallback).
    """
    pc: MutableMapping[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "acertos": 0})
    pd: MutableMapping[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "acertos": 0})

    for a in itens:
        acertou = a.get("acertou")
        if not _acertou_foi_avaliado(acertou):
            continue
        cl = _etiqueta_classe_intimacao_analise(a)
        df = _etiqueta_defensor_intimacao_analise(a)
        ok = _conta_como_acerto(acertou)
        pc[cl]["total"] += 1
        pd[df]["total"] += 1
        if ok:
            pc[cl]["acertos"] += 1
            pd[df]["acertos"] += 1

    def _to_sorted_rows(m: MutableMapping[str, Dict[str, int]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for label, b in m.items():
            n = b["total"]
            ac = b["acertos"]
            out.append(
                {
                    "label": label,
                    "total": n,
                    "acertos": ac,
                    "erros": n - ac,
                    "taxa_pct": round(100.0 * ac / n, 1) if n else 0.0,
                }
            )
        out.sort(key=lambda x: (-x["total"], x["label"]))
        return out

    return {
        "por_classe": _to_sorted_rows(pc),
        "por_defensor": _to_sorted_rows(pd),
    }


def _montar_linha_resumo(
    *,
    categoria: str,
    total: int,
    acertos: int,
    limite_amostra_pequena: int,
    itens: Sequence[Mapping[str, Any]],
    subtitulo: Optional[str] = None,
) -> Dict[str, Any]:
    n = total
    taxa = round(100.0 * acertos / n, 1) if n else 0.0
    q = quebra_por_classe_e_defensor_sessao_analises(list(itens))
    row: Dict[str, Any] = {
        "categoria": categoria,
        "total": n,
        "acertos": acertos,
        "erros": n - acertos,
        "taxa_pct": taxa,
        "amostra_pequena": 0 < n < limite_amostra_pequena,
        "por_classe": q["por_classe"],
        "por_defensor": q["por_defensor"],
    }
    if subtitulo:
        row["subtitulo"] = subtitulo
    return row


def calcular_estatisticas_acuracia_por_categoria_classificacao_manual(
    analises: Sequence[Mapping[str, Any]],
    *,
    limite_amostra_pequena: int = _AMOSTRA_PEQUENA_LIMITE_PADRAO,
) -> Dict[str, Any]:
    """
    Retorna dict com:
      - linhas: lista ordenada (menor taxa primeiro) de totais por categoria
      - total_avaliadas: análises com acertou não nulo
      - sem_avaliacao: análises com acertou nulo (não entram na taxa)
    """
    por_categoria: MutableMapping[str, List[Mapping[str, Any]]] = defaultdict(list)
    sem_avaliacao = 0

    for a in analises:
        acertou = a.get("acertou")
        if not _acertou_foi_avaliado(acertou):
            sem_avaliacao += 1
            continue
        raw = a.get("classificacao_manual")
        cat = (str(raw).strip() if raw is not None else "") or _SEM_CLASSIFICACAO
        por_categoria[cat].append(a)

    linhas: List[Dict[str, Any]] = []
    for categoria, itens in por_categoria.items():
        n = len(itens)
        acertos = sum(1 for x in itens if _conta_como_acerto(x.get("acertou")))
        linhas.append(
            _montar_linha_resumo(
                categoria=categoria,
                total=n,
                acertos=acertos,
                limite_amostra_pequena=limite_amostra_pequena,
                itens=itens,
            )
        )

    linhas.sort(key=lambda x: (x["taxa_pct"], -x["total"], x["categoria"]))

    total_avaliadas = sum(len(v) for v in por_categoria.values())

    return {
        "vista": "classificacao_manual",
        "linhas": linhas,
        "total_avaliadas": total_avaliadas,
        "sem_avaliacao": sem_avaliacao,
    }


def calcular_estatisticas_acuracia_modo_focado_faixa_alvo_e_indeterminado(
    analises: Sequence[Mapping[str, Any]],
    tipo_alvo_focado: str,
    *,
    limite_amostra_pequena: int = _AMOSTRA_PEQUENA_LIMITE_PADRAO,
) -> Dict[str, Any]:
    """
    Modo focado: duas faixas — (1) manual = tipo alvo, acerto se IA = alvo;
    (2) manual ≠ alvo, acerto se IA = INDETERMINADO. Usa o campo `acertou` já gravado.
    """
    alvo_display = (tipo_alvo_focado or "").strip()
    alvo_n = _norm(alvo_display)
    if not alvo_n:
        return {
            "vista": "focado",
            "tipo_alvo_focado": "",
            "linhas": [],
            "total_avaliadas": 0,
            "sem_avaliacao": 0,
            "erro_config": "Tipo alvo vazio",
        }

    itens_alvo: List[Mapping[str, Any]] = []
    itens_demais: List[Mapping[str, Any]] = []
    sem_avaliacao = 0

    for a in analises:
        acertou = a.get("acertou")
        if not _acertou_foi_avaliado(acertou):
            sem_avaliacao += 1
            continue
        manual_n = _norm(a.get("classificacao_manual"))
        if not manual_n:
            sem_avaliacao += 1
            continue
        if manual_n == alvo_n:
            itens_alvo.append(a)
        else:
            itens_demais.append(a)

    na = len(itens_alvo)
    aa = sum(1 for x in itens_alvo if _conta_como_acerto(x.get("acertou")))
    nd = len(itens_demais)
    ad = sum(1 for x in itens_demais if _conta_como_acerto(x.get("acertou")))

    linhas = [
        _montar_linha_resumo(
            categoria=alvo_display,
            total=na,
            acertos=aa,
            limite_amostra_pequena=limite_amostra_pequena,
            itens=itens_alvo,
            subtitulo=(
                "Classificação manual igual ao tipo alvo — acerto quando a IA responde com o mesmo tipo."
            ),
        ),
        _montar_linha_resumo(
            categoria="INDETERMINADO",
            total=nd,
            acertos=ad,
            limite_amostra_pequena=limite_amostra_pequena,
            itens=itens_demais,
            subtitulo=(
                "Classificação manual diferente do alvo — acerto quando a IA responde INDETERMINADO."
            ),
        ),
    ]

    total_avaliadas = na + nd

    return {
        "vista": "focado",
        "tipo_alvo_focado": alvo_display,
        "linhas": linhas,
        "total_avaliadas": total_avaliadas,
        "sem_avaliacao": sem_avaliacao,
    }
