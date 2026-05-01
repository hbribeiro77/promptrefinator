"""Testes de agrupamento em lote de análises (get_all_intimacoes) e listagem paginada/stats no SQLite."""

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


def _prompt_minimo(svc: SQLiteService, pid: str) -> None:
    svc.save_prompt(
        {
            'id': pid,
            'nome': 'Prompt teste',
            'conteudo': 'x',
            'regra_negocio': '',
            'data_criacao': '2026-01-01T00:00:00',
        }
    )


def _intimacao_minima(svc: SQLiteService, iid: str, contexto: str, classe_manual: str = 'OCULTAR') -> None:
    svc.save_intimacao(
        {
            'id': iid,
            'contexto': contexto,
            'classificacao_manual': classe_manual,
            'data_criacao': '2026-01-15T12:00:00',
        }
    )


def _insert_analise_sem_session_id(
    svc: SQLiteService,
    aid: str,
    intimacao_id: str,
    prompt_id: str,
    *,
    acertou: bool,
    temperatura: float = 0.7,
    data_analise: str = '2026-01-16T00:00:00',
) -> None:
    """INSERT compatível com schema inicial (sem colunas opcionais de migrações antigas)."""
    with svc.get_connection() as conn:
        conn.execute(
            '''
            INSERT INTO analises
            (id, intimacao_id, prompt_id, prompt_nome, data_analise, resultado_ia,
             acertou, temperatura, modo_avaliacao)
            VALUES (?, ?, ?, '', ?, '', ?, ?, 'padrao')
            ''',
            (aid, intimacao_id, prompt_id, data_analise, 1 if acertou else 0, temperatura),
        )
        conn.commit()


def test_get_all_intimacoes_usa_agrupamento_analises_duas_queries(svc_db_vazio):
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _prompt_minimo(svc, pid)
    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    _intimacao_minima(svc, i1, 'contexto um')
    _intimacao_minima(svc, i2, 'contexto dois')
    _insert_analise_sem_session_id(svc, str(uuid.uuid4()), i1, pid, acertou=True, temperatura=0.7)
    _insert_analise_sem_session_id(
        svc,
        str(uuid.uuid4()),
        i1,
        pid,
        acertou=False,
        temperatura=0.7,
        data_analise='2026-01-17T00:00:00',
    )
    todas = svc.get_all_intimacoes()
    por_id = {x['id']: x for x in todas}
    assert len(por_id[i1]['analises']) == 2
    assert len(por_id[i2]['analises']) == 0
    assert por_id[i1]['analises'][0]['data_analise'] >= por_id[i1]['analises'][1]['data_analise']


def test_stats_e_listagem_filtrada_por_busca(svc_db_vazio):
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _prompt_minimo(svc, pid)
    i1 = str(uuid.uuid4())
    i2 = str(uuid.uuid4())
    _intimacao_minima(svc, i1, 'marca_busca_xyz alpha')
    _intimacao_minima(svc, i2, 'outro contexto sem marca')
    stats = svc.stats_intimacoes_listagem(busca='marca_busca_xyz')
    assert stats['total'] == 1
    assert stats['com_classificacao'] == 1
    page = svc.list_intimacoes_listagem_pagina(busca='marca_busca_xyz', pagina=1, itens_por_pagina=10)
    assert len(page) == 1
    assert page[0]['id'] == i1


def test_listagem_ordenacao_taxa_desc(svc_db_vazio):
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _prompt_minimo(svc, pid)
    low = str(uuid.uuid4())
    high = str(uuid.uuid4())
    _intimacao_minima(svc, low, 'low taxa')
    _intimacao_minima(svc, high, 'high taxa')
    for _ in range(3):
        _insert_analise_sem_session_id(
            svc, str(uuid.uuid4()), low, pid, acertou=False, temperatura=0.5
        )
    for _ in range(4):
        _insert_analise_sem_session_id(
            svc, str(uuid.uuid4()), high, pid, acertou=True, temperatura=0.5
        )
    page = svc.list_intimacoes_listagem_pagina(
        ordenacao='taxa_acerto_desc',
        prompt_especifico=pid,
        temperatura_especifica='0.5',
        pagina=1,
        itens_por_pagina=10,
    )
    ids_ordem = [r['id'] for r in page]
    assert ids_ordem[0] == high


def test_stats_cards_classificacao_elaborar_peca(svc_db_vazio):
    svc = svc_db_vazio
    i1 = str(uuid.uuid4())
    _intimacao_minima(svc, i1, 'x', classe_manual='ELABORAR PEÇA')
    st = svc.stats_intimacoes_listagem()
    assert st['count_elaborar_peca'] >= 1


def test_resumo_para_pagina_analise_ia_sem_contexto_sem_analises(svc_db_vazio):
    """Página /analise: lista leve versus get_all_intimacoes completo."""
    svc = svc_db_vazio
    pid = str(uuid.uuid4())
    _prompt_minimo(svc, pid)
    i1 = str(uuid.uuid4())
    ctx_grande = 'CORPO_' + ('z' * 8000)
    _intimacao_minima(svc, i1, ctx_grande)
    _insert_analise_sem_session_id(svc, str(uuid.uuid4()), i1, pid, acertou=True)

    todas = svc.get_all_intimacoes()
    resumo = svc.listar_intimacoes_resumo_sem_contexto_sem_analises_para_pagina_analise_ia()

    por_get = next(x for x in todas if x['id'] == i1)
    por_resumo = next(x for x in resumo if x['id'] == i1)

    assert por_get['contexto'] == ctx_grande
    assert por_resumo['contexto'] == ''
    assert len(por_get['analises']) >= 1
    assert por_resumo['analises'] == []
