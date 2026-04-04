"""Testes das tabelas areas / area_classe e do mapeamento classe → área."""

import os
import tempfile

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


def test_seed_quatro_areas(svc_db_vazio):
    areas = svc_db_vazio.get_areas()
    ids = {a['id'] for a in areas}
    assert ids == {'civel', 'familia', 'crime', 'violencia_domestica'}
    assert all('nome' in a and 'ordem' in a for a in areas)


def test_mapeamento_replace_e_lookup(svc_db_vazio):
    svc_db_vazio.replace_mapeamento_classes_areas(
        {'Apelação Cível': 'civel', 'Ação Penal': 'crime'}
    )
    m = svc_db_vazio.get_mapeamento_classe_para_area()
    assert m['Apelação Cível']['id'] == 'civel'
    assert m['Apelação Cível']['nome'] == 'Cível'
    assert m['Ação Penal']['id'] == 'crime'
    mid = svc_db_vazio.get_mapeamento_classe_para_area_id()
    assert mid['Apelação Cível'] == 'civel'


def test_replace_remove_tudo_com_mapa_vazio(svc_db_vazio):
    svc_db_vazio.replace_mapeamento_classes_areas({'X': 'familia'})
    svc_db_vazio.replace_mapeamento_classes_areas({'X': None})
    assert svc_db_vazio.get_mapeamento_classe_para_area() == {}


def test_area_invalida_levanta_value_error(svc_db_vazio):
    with pytest.raises(ValueError, match='inválida'):
        svc_db_vazio.replace_mapeamento_classes_areas({'Y': 'nao_existe'})
