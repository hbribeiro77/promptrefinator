"""Testes do agregador de acurácia por classificação manual na sessão."""

from services.calcular_estatisticas_acuracia_por_categoria_classificacao_manual_sessao_analises_service import (
    calcular_estatisticas_acuracia_modo_focado_faixa_alvo_e_indeterminado,
    calcular_estatisticas_acuracia_por_categoria_classificacao_manual,
    quebra_por_classe_e_defensor_sessao_analises,
)


def test_vazio():
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual([])
    assert r["vista"] == "classificacao_manual"
    assert r["linhas"] == []
    assert r["total_avaliadas"] == 0
    assert r["sem_avaliacao"] == 0


def test_ignora_acertou_nulo():
    analises = [
        {"classificacao_manual": "A", "acertou": None},
        {"classificacao_manual": "A", "acertou": True},
    ]
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual(analises)
    assert r["sem_avaliacao"] == 1
    assert r["total_avaliadas"] == 1
    assert len(r["linhas"]) == 1
    assert r["linhas"][0]["categoria"] == "A"
    assert r["linhas"][0]["taxa_pct"] == 100.0


def test_agrega_e_ordena_pior_taxa_primeiro():
    analises = [
        {"classificacao_manual": "FACIL", "acertou": True},
        {"classificacao_manual": "FACIL", "acertou": True},
        {"classificacao_manual": "DIFICIL", "acertou": False},
        {"classificacao_manual": "DIFICIL", "acertou": True},
    ]
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual(analises)
    assert [x["categoria"] for x in r["linhas"]] == ["DIFICIL", "FACIL"]
    assert r["linhas"][0]["taxa_pct"] == 50.0
    assert r["linhas"][1]["taxa_pct"] == 100.0


def test_sem_classificacao_manual_e_int_acertou():
    analises = [
        {"classificacao_manual": "", "acertou": 0},
        {"classificacao_manual": None, "acertou": 1},
    ]
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual(analises)
    assert len(r["linhas"]) == 1
    assert r["linhas"][0]["categoria"] == "(Sem classificação manual)"
    assert r["linhas"][0]["total"] == 2
    assert r["linhas"][0]["acertos"] == 1
    assert r["linhas"][0]["taxa_pct"] == 50.0


def test_amostra_pequena():
    analises = [{"classificacao_manual": "X", "acertou": True}]
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual(
        analises, limite_amostra_pequena=5
    )
    assert r["linhas"][0]["amostra_pequena"] is True


def test_modo_focado_duas_faixas_ordem_e_totais():
    analises = [
        {"classificacao_manual": "ALVO", "acertou": True},
        {"classificacao_manual": "ALVO", "acertou": False},
        {"classificacao_manual": "OUTRO", "acertou": True},
        {"classificacao_manual": "OUTRO", "acertou": False},
    ]
    r = calcular_estatisticas_acuracia_modo_focado_faixa_alvo_e_indeterminado(analises, "ALVO")
    assert r["vista"] == "focado"
    assert r["tipo_alvo_focado"] == "ALVO"
    assert len(r["linhas"]) == 2
    assert r["linhas"][0]["categoria"] == "ALVO"
    assert r["linhas"][0]["total"] == 2
    assert r["linhas"][0]["acertos"] == 1
    assert r["linhas"][0]["taxa_pct"] == 50.0
    assert r["linhas"][1]["categoria"] == "INDETERMINADO"
    assert r["linhas"][1]["total"] == 2
    assert r["linhas"][1]["acertos"] == 1
    assert r["sem_avaliacao"] == 0


def test_modo_focado_alvo_vazio():
    r = calcular_estatisticas_acuracia_modo_focado_faixa_alvo_e_indeterminado([], "  ")
    assert r["linhas"] == []
    assert r.get("erro_config")


def test_modo_focado_case_insensitive_manual():
    analises = [
        {"classificacao_manual": "contato peça", "acertou": 1},
    ]
    r = calcular_estatisticas_acuracia_modo_focado_faixa_alvo_e_indeterminado(
        analises, "CONTATO PEÇA"
    )
    assert r["linhas"][0]["total"] == 1
    assert r["linhas"][0]["acertos"] == 1
    assert r["linhas"][1]["total"] == 0


def test_linhas_incluem_quebra_por_classe_e_defensor():
    analises = [
        {
            "classificacao_manual": "A",
            "acertou": True,
            "classe": "Cível",
            "defensor": "Dr. Um",
        },
        {
            "classificacao_manual": "A",
            "acertou": False,
            "classe": "Cível",
            "defensor": "Dr. Dois",
        },
        {
            "classificacao_manual": "A",
            "acertou": True,
            "classe": "",
            "defensor": "",
            "intimado": "DP",
        },
    ]
    r = calcular_estatisticas_acuracia_por_categoria_classificacao_manual(analises)
    linha = r["linhas"][0]
    assert linha["categoria"] == "A"
    assert linha["total"] == 3
    por_c = {x["label"]: x for x in linha["por_classe"]}
    assert por_c["Cível"]["acertos"] == 1
    assert por_c["Cível"]["erros"] == 1
    assert por_c["(Sem classe)"]["total"] == 1
    por_d = {x["label"]: x for x in linha["por_defensor"]}
    assert por_d["Dr. Um"]["acertos"] == 1
    assert por_d["Dr. Dois"]["erros"] == 1
    assert por_d["DP"]["total"] == 1


def test_quebra_por_classe_e_defensor_vazio():
    q = quebra_por_classe_e_defensor_sessao_analises([])
    assert q["por_classe"] == []
    assert q["por_defensor"] == []
