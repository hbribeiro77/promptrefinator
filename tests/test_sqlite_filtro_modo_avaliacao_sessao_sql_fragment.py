"""Sanidade: SQLite com json_extract para filtro de modo em sessoes_analise."""
import sqlite3

from services.sqlite_service import _sql_filtro_modo_avaliacao_sessao


def test_fragmento_focado_e_padrao():
    assert _sql_filtro_modo_avaliacao_sessao("focado") is not None
    assert _sql_filtro_modo_avaliacao_sessao("padrao") is not None
    assert _sql_filtro_modo_avaliacao_sessao("") is None
    assert _sql_filtro_modo_avaliacao_sessao(None) is None


def test_json_extract_filtra_focado_e_padrao():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sessoes_analise (configuracoes TEXT)")
    rows = [
        ('{"modo_avaliacao": "focado", "x": 1}',),
        ('{"modo_avaliacao": "padrao"}',),
        ('{}',),
        (None,),
    ]
    conn.executemany("INSERT INTO sessoes_analise VALUES (?)", rows)
    sql_f = _sql_filtro_modo_avaliacao_sessao("focado")
    sql_p = _sql_filtro_modo_avaliacao_sessao("padrao")
    n_f = conn.execute(f"SELECT COUNT(*) FROM sessoes_analise WHERE ({sql_f})").fetchone()[0]
    n_p = conn.execute(f"SELECT COUNT(*) FROM sessoes_analise WHERE ({sql_p})").fetchone()[0]
    assert n_f == 1
    assert n_p == 3
