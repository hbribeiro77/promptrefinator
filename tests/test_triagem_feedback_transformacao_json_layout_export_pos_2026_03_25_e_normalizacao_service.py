"""Testes de layout de export (legacy vs pos_2026_03_25) e normalização do parâmetro layout."""

import json

import pytest

from services.triagem_feedback_transformacao_json_para_importacao_intimacoes_service import (
    LAYOUT_FEEDBACK_LEGACY,
    LAYOUT_FEEDBACK_POS_2026_03_25,
    extrair_regras_usuario_markdown_e_sanitizar_contexto,
    normalize_feedback_export_layout,
    prompt_window_pos_2026_03_25,
    transform_feedback_json_text,
    transform_item,
)


def test_normalize_feedback_export_layout_padrao_quando_ausente_ou_vazio():
    assert normalize_feedback_export_layout(None) == LAYOUT_FEEDBACK_LEGACY
    assert normalize_feedback_export_layout("") == LAYOUT_FEEDBACK_LEGACY
    assert normalize_feedback_export_layout("   ") == LAYOUT_FEEDBACK_LEGACY


def test_normalize_feedback_export_layout_valores_validos():
    assert normalize_feedback_export_layout("legacy") == LAYOUT_FEEDBACK_LEGACY
    assert normalize_feedback_export_layout(" pos_2026_03_25 ") == LAYOUT_FEEDBACK_POS_2026_03_25


def test_normalize_feedback_export_layout_valor_invalido_levanta():
    with pytest.raises(ValueError, match="layout inválido"):
        normalize_feedback_export_layout("outro_formato")


def _item_com_triagem_estruturada_sem_markdown_no_prompt():
    return {
        "feedback": {"sucesso": True},
        "triagem": {
            "intimacaoId": "ext-layout-pos-1",
            "status": "CONCLUIDO",
            "numeroProcesso": "0001-99.2024.8.01.0001",
            "orgaoJulgador": "1ª Vara Cível",
            "classe": "Apelação",
            "intimados": [{"nome": "Fulano"}, "Beltrano"],
            "prazo": 15,
            "nomeDefensor": "Dr. Silva",
            "contexto": "Contexto vindo do campo estruturado.",
            "triagemResultado": "ELABORAR_PECA",
            "informacaoAdicional": "Obs estruturada",
            "prompt": "",
        },
    }


def test_transform_item_pos_2026_03_25_prioriza_campos_estruturados_em_triagem():
    reg = transform_item(
        _item_com_triagem_estruturada_sem_markdown_no_prompt(),
        layout=LAYOUT_FEEDBACK_POS_2026_03_25,
    )
    assert reg["processo"] == "0001-99.2024.8.01.0001"
    assert reg["órgão julgador"] == "1ª Vara Cível"
    assert reg["Classe"] == "Apelação"
    assert reg["intimado"] == "Fulano; Beltrano"
    assert reg["prazo"] == "15"
    assert reg["nome do defensor"] == "Dr. Silva"
    assert reg["contexto da intimação"] == "Contexto vindo do campo estruturado."
    assert reg["classificação manual"] == "ELABORAR_PECA"
    assert reg["Informações adicionais"] == "Obs estruturada"
    assert reg["cor da etiqueta"] == "verde"


def test_transform_item_legacy_sem_prompt_nao_preenche_orgao_a_partir_de_triagem_estruturada():
    reg = transform_item(
        _item_com_triagem_estruturada_sem_markdown_no_prompt(),
        layout=LAYOUT_FEEDBACK_LEGACY,
    )
    assert reg["processo"] == "0001-99.2024.8.01.0001"
    assert reg["órgão julgador"] is None
    assert reg["Classe"] is None


def test_prompt_window_pos_2026_03_25_a_partir_de_user_remove_ai_e_corta_sentinela():
    prompt = """
====== [INICIO: SYSTEM] ======
lixo system
====== [FIM: SYSTEM] ======
====== [INICIO: USER] ======
- **Processo** : 9999-88.2024.8.01.0001
Narrativa do contexto da intimação aqui.
====== [INICIO: AI] ======
resposta modelo
====== [FIM: AI] ======
text='Triagem IA executada com sucesso para intimação' foo bar
"""
    win = prompt_window_pos_2026_03_25(prompt)
    assert win is not None
    assert "lixo system" not in win
    assert "resposta modelo" not in win
    assert "foo bar" not in win
    assert "text='Triagem" not in win
    assert "9999-88.2024.8.01.0001" in win
    assert "Narrativa do contexto" in win


def test_transform_item_pos_2026_03_25_fallback_prompt_usa_janela_user():
    item = {
        "feedback": {"sucesso": True},
        "triagem": {
            "intimacaoId": "ext-pwin-1",
            "status": "OK",
            "triagemResultado": "ELABORAR_PECA",
            "prompt": """
====== [INICIO: USER] ======
- **Processo** : 1111-22.2024.8.01.0001
- **Órgão Julgador** : 2ª Vara
- **Classe** : Civel
Corpo útil.
====== [INICIO: AI] ======
x
====== [FIM: AI] ======
Triagem IA executada com sucesso para intimação trailing
""",
        },
    }
    reg = transform_item(item, layout=LAYOUT_FEEDBACK_POS_2026_03_25)
    assert reg["processo"] == "1111-22.2024.8.01.0001"
    assert reg["órgão julgador"] == "2ª Vara"
    assert reg["contexto da intimação"] is not None
    assert "Corpo útil" in reg["contexto da intimação"]
    assert "trailing" not in reg["contexto da intimação"]
    assert "resposta" not in (reg["contexto da intimação"] or "").lower()


def test_extrair_regras_markdown_remove_corpo_mantem_cabecalho_regras():
    raw = """Intro
# Regras do Usuário (PRIORIDADE ALTA)
linha regra um
linha regra dois
# Informações da Intimação
Resto do contexto."""
    novo, regras = extrair_regras_usuario_markdown_e_sanitizar_contexto(raw)
    assert regras == "linha regra um\nlinha regra dois"
    assert "# Regras do Usuário (PRIORIDADE ALTA)" in novo
    assert "linha regra um" not in novo
    assert "# Informações da Intimação" in novo
    assert "Resto do contexto" in novo


def test_transform_item_pos_extrai_regras_markdown_do_contexto_user():
    bloco = """# Regras do Usuário (PRIORIDADE ALTA)
Sempre priorizar o assistido.
# Informações da Intimação
Conteúdo da intimação aqui."""
    prompt = "====== [INICIO: USER] ======\n" + bloco
    item = {
        "feedback": {"sucesso": True},
        "triagem": {
            "intimacaoId": "ext-regras-md",
            "status": "OK",
            "triagemResultado": "ELABORAR_PECA",
            "prompt": prompt,
        },
    }
    reg = transform_item(item, layout=LAYOUT_FEEDBACK_POS_2026_03_25)
    assert reg.get("regras_usuario_prioridade_alta") == "Sempre priorizar o assistido."
    ctx = reg.get("contexto da intimação") or ""
    assert "Sempre priorizar o assistido." not in ctx
    assert "# Regras do Usuário (PRIORIDADE ALTA)" in ctx
    assert "# Informações da Intimação" in ctx
    assert "Conteúdo da intimação aqui" in ctx


def test_transform_item_prioriza_regras_estruturadas_na_triagem_sobre_markdown():
    bloco = """# Regras do Usuário (PRIORIDADE ALTA)
Do markdown
# Informações da Intimação
X"""
    item = {
        "feedback": {"sucesso": True},
        "triagem": {
            "intimacaoId": "ext-regras-tr",
            "status": "OK",
            "triagemResultado": "ELABORAR_PECA",
            "regras_usuario_prioridade_alta": "Do campo estruturado",
            "prompt": "====== [INICIO: USER] ======\n" + bloco,
        },
    }
    reg = transform_item(item, layout=LAYOUT_FEEDBACK_POS_2026_03_25)
    assert reg.get("regras_usuario_prioridade_alta") == "Do campo estruturado"


def test_transform_feedback_json_text_repasse_layout_sem_issues_obrigatorios():
    data = {"content": [_item_com_triagem_estruturada_sem_markdown_no_prompt()]}
    payload, issues = transform_feedback_json_text(
        json.dumps(data, ensure_ascii=False),
        origem="teste_unitario",
        layout=LAYOUT_FEEDBACK_POS_2026_03_25,
    )
    assert payload["total_registros"] == 1
    assert payload["registros"][0]["órgão julgador"] == "1ª Vara Cível"
    obrig = [i for i in issues if "obrigatório" in i.mensagem.casefold()]
    assert not obrig
