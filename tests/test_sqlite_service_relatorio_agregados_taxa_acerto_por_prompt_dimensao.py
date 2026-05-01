"""Testes de agregação de relatório: taxa por dimensão e modo intimações comuns a todos os prompts."""

import os
import tempfile
import uuid

import pytest

from services.sqlite_service import SQLiteService


@pytest.fixture()
def svc_db_vazio():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        yield SQLiteService(db_path=path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _prompt(svc: SQLiteService, pid: str, nome: str) -> None:
    svc.save_prompt(
        {
            'id': pid,
            'nome': nome,
            'conteudo': 'x',
            'regra_negocio': '',
            'data_criacao': '2026-01-01T00:00:00',
        }
    )


def _intimacao(
    svc: SQLiteService,
    iid: str,
    *,
    classificacao_manual: str,
    classe: str = '',
    defensor: str = '',
) -> None:
    svc.save_intimacao(
        {
            'id': iid,
            'contexto': 'ctx',
            'classificacao_manual': classificacao_manual,
            'classe': classe,
            'defensor': defensor,
            'data_criacao': '2026-01-15T12:00:00',
        }
    )


def _analise(
    svc: SQLiteService,
    aid: str,
    intimacao_id: str,
    prompt_id: str,
    *,
    acertou: bool,
    data_analise: str = '2026-01-16T12:00:00',
) -> None:
    with svc.get_connection() as conn:
        conn.execute(
            '''
            INSERT INTO analises
            (id, intimacao_id, prompt_id, prompt_nome, data_analise, resultado_ia,
             acertou, temperatura, modo_avaliacao)
            VALUES (?, ?, ?, '', ?, '', ?, 0.7, 'padrao')
            ''',
            (aid, intimacao_id, prompt_id, data_analise, 1 if acertou else 0),
        )
        conn.commit()


def test_dimensao_invalida_levanta_value_error(svc_db_vazio):
    svc = svc_db_vazio
    p = str(uuid.uuid4())
    _prompt(svc, p, 'P')
    with pytest.raises(ValueError, match='dimensao'):
        svc.listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
            [p], 'dim_inexistente'
        )


def test_agregados_por_classificacao_manual_e_modo_casos_comuns(svc_db_vazio):
    svc = svc_db_vazio
    p1 = str(uuid.uuid4())
    p2 = str(uuid.uuid4())
    _prompt(svc, p1, 'Vanilla')
    _prompt(svc, p2, 'Vanilla mod')

    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    _intimacao(svc, i1, classificacao_manual='ELABORAR PEÇA')
    _intimacao(svc, i2, classificacao_manual='OCULTAR')

    _analise(svc, str(uuid.uuid4()), i1, p1, acertou=True)
    _analise(svc, str(uuid.uuid4()), i1, p2, acertou=False)
    _analise(svc, str(uuid.uuid4()), i2, p1, acertou=True)

    # Sem filtro "comuns": p1 tem 2 linhas (ELABORAR + OCULTAR), p2 só ELABORAR
    out_livre = svc.listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
        [p1, p2],
        'classificacao_manual',
        apenas_intimacoes_com_todos_prompts=False,
    )
    por_id = {x['prompt_id']: x for x in out_livre}
    assert len(por_id[p1]['linhas']) == 2
    assert len(por_id[p2]['linhas']) == 1

    # Comuns: só i1 tem ambos os prompts — p1 uma linha ELABORAR; p2 uma linha ELABORAR
    out_comum = svc.listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
        [p1, p2],
        'classificacao_manual',
        apenas_intimacoes_com_todos_prompts=True,
    )
    por_c = {x['prompt_id']: x for x in out_comum}
    assert len(por_c[p1]['linhas']) == 1
    assert por_c[p1]['linhas'][0]['label'] == 'ELABORAR PEÇA'
    assert por_c[p1]['linhas'][0]['total'] == 1
    assert por_c[p1]['linhas'][0]['acertos'] == 1
    assert len(por_c[p2]['linhas']) == 1
    assert por_c[p2]['linhas'][0]['total'] == 1
    assert por_c[p2]['linhas'][0]['acertos'] == 0


def test_agregados_por_defensor(svc_db_vazio):
    svc = svc_db_vazio
    p1 = str(uuid.uuid4())
    _prompt(svc, p1, 'P')
    i1 = str(uuid.uuid4())
    _intimacao(svc, i1, classificacao_manual='X', defensor='Maria')
    _analise(svc, str(uuid.uuid4()), i1, p1, acertou=True)

    out = svc.listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
        [p1],
        'defensor',
    )
    assert len(out) == 1
    assert out[0]['linhas'][0]['label'] == 'Maria'
    assert out[0]['linhas'][0]['taxa_pct'] == 100.0


def test_contar_intimacoes_cadastradas_por_dimensao_classificacao(svc_db_vazio):
    svc = svc_db_vazio
    _intimacao(svc, str(uuid.uuid4()), classificacao_manual='ALFA')
    _intimacao(svc, str(uuid.uuid4()), classificacao_manual='ALFA')
    _intimacao(svc, str(uuid.uuid4()), classificacao_manual='BETA')
    d = svc.contar_intimacoes_cadastradas_agrupadas_por_dimensao_relatorio(
        'classificacao_manual',
    )
    assert d['ALFA'] == 2
    assert d['BETA'] == 1
    d_f = svc.contar_intimacoes_cadastradas_agrupadas_por_dimensao_relatorio(
        'classificacao_manual',
        classificacao_manual_filtro='ALFA',
    )
    assert d_f.get('ALFA') == 2
    assert 'BETA' not in d_f


def test_total_intimacoes_distintas_duas_analises_mesma_intimacao(svc_db_vazio):
    svc = svc_db_vazio
    p1 = str(uuid.uuid4())
    _prompt(svc, p1, 'P')
    i1 = str(uuid.uuid4())
    _intimacao(svc, i1, classificacao_manual='OCULTAR')
    _analise(svc, str(uuid.uuid4()), i1, p1, acertou=True, data_analise='2026-01-16T10:00:00')
    _analise(svc, str(uuid.uuid4()), i1, p1, acertou=False, data_analise='2026-01-17T10:00:00')

    out = svc.listar_agregados_relatorio_taxa_acerto_por_prompt_ids_dimensao_com_filtros(
        [p1],
        'classificacao_manual',
    )
    lin = out[0]['linhas'][0]
    assert lin['total'] == 2
    assert lin['total_intimacoes_distintas'] == 1
