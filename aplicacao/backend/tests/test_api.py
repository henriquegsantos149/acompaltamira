import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parents[4]

@pytest.fixture
def env(tmp_path):
    (tmp_path / 'codex').mkdir()
    shutil.copy(ROOT / 'codex/base_padronizada.json', tmp_path / 'codex/base_padronizada.json')
    return tmp_path, TestClient(create_app(tmp_path))

def row(id='m1', value=0):
    return dict(medicao_id=id, indicador_id='A1', ambito='Sede de Altamira', periodo_inicio='2025-01-01', periodo_fim='2025-12-31', numerador=value, denominador=100, valor_medido=value, unidade='%', evidencia_arquivo_ou_url='https://example.org/laudo', responsavel_informacao='Teste', data_registro='2026-11-05T10:00:00-03:00')

def enable(c):
    assert c.post('/api/session/write', json={'confirm_sync_paused': True}).status_code == 200

def preview(c, records):
    return c.post('/api/import/preview', json={'tipo':'medicoes','registros':records}).json()

def confirm(c,p):
    return c.post('/api/import/confirm',json={k:p[k] for k in ['preview_id','assinatura']})

def test_readonly_preview_and_persistence(env):
    root,c=env
    p=preview(c,[row()])
    assert p['valid']
    assert not (root/'codex/dados').exists()
    assert confirm(c,p).status_code == 403
    enable(c)
    p=preview(c,[row()])
    assert confirm(c,p).status_code==200
    assert confirm(c,p).status_code==409
    fresh=TestClient(create_app(root))
    assert fresh.get('/api/state').json()['medicoes'][0]['valor_medido']==0
    assert fresh.get('/api/state').json()['write_enabled'] is False

def test_invalid_atomic_stale_and_retification(env):
    _,c=env
    enable(c)
    bad=row('bad'); bad['indicador_id']='unknown'
    p=preview(c,[row(),bad])
    assert not p['valid']
    assert confirm(c,p).status_code==422
    assert not c.get('/api/state').json()['medicoes']
    p=preview(c,[row()]); stale=preview(c,[row('m2')])
    assert confirm(c,p).status_code==200
    assert confirm(c,stale).status_code==409
    r=row(value=None); r.update(revisao_esperada=1,justificativa_retificacao='Correção comprovada')
    assert confirm(c,preview(c,[r])).status_code==200
    state=c.get('/api/state').json()
    assert state['medicoes'][0]['valor_medido'] is None
    assert len(state['historico'])==2
    assert state['historico'][1]['antes']['valor_medido']==0

def test_security_validation_comparison(env):
    _,c=env
    assert c.post('/api/session/write',json={'confirm_sync_paused':True},headers={'origin':'https://evil.example'}).status_code==403
    enable(c)
    for field,value in [('valor_medido',101),('denominador',0),('unidade','m'),('evidencia_arquivo_ou_url','../../secret')]:
        r=row(); r[field]=value
        assert not preview(c,[r])['valid']
    assert confirm(c,preview(c,[row()])).status_code==200
    request={'meta_id':'T52_A1_2025','medicao_id':'m1','decisao_referencia_id':None}
    assert c.post('/api/comparar',json=request).json()['estado']=='referencia_pendente'
    d=dict(decisao_id='d1',indicador_id='A1',meta_id='T52_A1_2025',ambito='Sede de Altamira',responsavel='Teste',justificativa='Fonte selecionada',data_registro='2026-11-05T10:00:00-03:00')
    assert c.post('/api/decisoes',json=d).status_code==200
    request['decisao_referencia_id']='d1'
    assert c.post('/api/comparar',json=request).json()['classificacao']=='nao_atingida'
    request['meta_id']='T52_A1_2029'
    assert c.post('/api/comparar',json=request).json()['estado']!='comparavel'

def test_backup_restore_and_untrusted_zip(env,tmp_path):
    from app.backup import restore_backup
    import zipfile
    root,c=env; enable(c)
    ev=c.post('/api/evidencias',files={'file':('laudo.txt',b'evidencia real de teste')}).json()
    r=row(); r['evidencia_arquivo_ou_url']=ev['url']
    assert confirm(c,preview(c,[r])).status_code==200
    b=c.post('/api/backup').json()
    archive=root/'codex/dados/backups'/b['nome']
    target=tmp_path/'restaurado'
    restore_backup(archive,target)
    restored=TestClient(create_app(target))
    assert len(restored.get('/api/state').json()['medicoes'])==1
    assert restored.get(ev['url']).content==b'evidencia real de teste'
    malicious=tmp_path/'evil.zip'
    with zipfile.ZipFile(malicious,'w') as z: z.writestr('../escape','evil')
    with pytest.raises(ValueError): restore_backup(malicious,tmp_path/'invalid')
    with zipfile.ZipFile(archive,'a') as z: z.writestr('extra.txt','tampered')
    with pytest.raises(ValueError): restore_backup(archive,tmp_path/'invalid2')


def test_transaction_rolls_back_on_mid_batch_failure(env,monkeypatch):
    import sqlite3
    _,c=env; enable(c)
    repo=c.app.state.repository
    original=repo.put
    def failure(connection,kind,record,links=()):
        result=original(connection,kind,record,links)
        if record.get('medicao_id')=='m2': raise sqlite3.IntegrityError('Simulated disk/constraint failure')
        return result
    monkeypatch.setattr(repo,'put',failure)
    p=preview(c,[row(),row('m2')])
    assert confirm(c,p).status_code==409
    assert c.get('/api/state').json()['medicoes']==[]
    assert c.get('/api/state').json()['historico']==[]
    monkeypatch.setattr(repo,'put',original)
    assert confirm(c,p).status_code==200
    assert len(c.get('/api/state').json()['medicoes'])==2


def test_all_models_and_foreign_keys(env):
    root,c=env; enable(c)
    base=c.get('/api/base').json()
    original=(root/'codex/base_padronizada.json').read_bytes()
    a=base['acoes_previstas'][0]; inv=base['investimentos_previstos'][0]
    shared=dict(responsavel_informacao='Teste',evidencia_arquivo_ou_url='https://example.org/comprovante')
    execution=dict(**shared,execucao_id='e1',acao_id=a['acao_id'],projeto_id=None,localidade=a['localidade'],data_referencia='2026-11-05',situacao_informada='Em execução',quantidade_executada=0,unidade='m')
    finance=dict(**shared,despesa_id='f1',linha_investimento_id=inv['linha_id'],localidade=inv['localidade'],periodo_inicio='2026-01-01',periodo_fim='2026-11-05',valor_empenhado=100,valor_liquidado=None,valor_pago=0,unidade_monetaria='R$')
    for kind,r in [('execucoes',execution),('financeiro',finance)]:
        p=c.post('/api/import/preview',json={'tipo':kind,'registros':[r]}).json()
        assert p['valid'],p
        assert confirm(c,p).status_code==200
    assert c.get('/api/export/financeiro').json()[0]['valor_liquidado'] is None
    assert '__NULL__' in c.get('/api/export/financeiro?formato=csv').text
    assert (root/'codex/base_padronizada.json').read_bytes()==original
    repo=c.app.state.repository
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        with repo.transaction() as connection:
            connection.execute("INSERT INTO links VALUES ('medicoes','missing','metas','missing')")


def test_readonly_cannot_change_existing_storage(env):
    root,c=env; enable(c)
    assert confirm(c,preview(c,[row()])).status_code==200
    assert c.post('/api/session/write',json={'confirm_sync_paused':False}).status_code==200
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert c.post('/api/backup').status_code==403
    assert c.post('/api/evidencias',files={'file':('x.txt',b'x')}).status_code==403
    assert confirm(c,preview(c,[row('m2')])).status_code==403
    c.get('/api/state'); c.get('/api/base'); c.get('/api/export/completo')
    after={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before==after


def test_reduction_period_scope_and_missing_measurement(env):
    _,c=env; enable(c)
    b=c.get('/api/base').json()
    meta=next(m for m in b['metas'] if m['indicador_id']=='A2' and m['ano']==2025)
    r=row(); r.update(indicador_id='A2',ambito=meta['ambito'],valor_medido=0,numerador=0)
    assert confirm(c,preview(c,[r])).status_code==200
    d=dict(decisao_id='d2',indicador_id='A2',meta_id=meta['meta_id'],ambito=meta['ambito'],responsavel='Teste',justificativa='Adotada tabela52',data_registro='2026-11-05T10:00:00-03:00')
    assert c.post('/api/decisoes',json=d).status_code==200
    request=dict(meta_id=meta['meta_id'],medicao_id='m1',decisao_referencia_id='d2')
    assert c.post('/api/comparar',json=request).json()['classificacao']=='atingida'
    r.update(periodo_inicio='2026-01-01',periodo_fim='2026-12-31',revisao_esperada=1,justificativa_retificacao='Competência corrigida')
    assert confirm(c,preview(c,[r])).status_code==200
    assert c.post('/api/comparar',json=request).json()['estado']=='incompativel'
    request['medicao_id']='missing'
    assert c.post('/api/comparar',json=request).json()['estado']=='sem_medicao'


def test_backup_includes_sources_layers_and_detects_changed_hash(env,tmp_path):
    import zipfile
    from app.backup import restore_backup
    root,c=env
    (root/'documentos').mkdir(); (root/'documentos/PMISB-ALTAMIRA-APROVADO.pdf').write_bytes(b'%PDF-test-source')
    geo=root/'codex/dados/geoespaciais/processados'; geo.mkdir(parents=True)
    (geo/'catalogo.json').write_text('{"layers":[]}',encoding='utf-8')
    (geo/'limite.geojson').write_text('{"type":"FeatureCollection","features":[]}',encoding='utf-8')
    enable(c)
    b=c.post('/api/backup').json(); archive=root/'codex/dados/backups'/b['nome']
    restored=restore_backup(archive,tmp_path/'restored')
    assert (restored/'documentos/PMISB-ALTAMIRA-APROVADO.pdf').read_bytes()==b'%PDF-test-source'
    assert (restored/'codex/dados/geoespaciais/processados/limite.geojson').read_bytes()==(geo/'limite.geojson').read_bytes()
    altered=tmp_path/'altered.zip'
    with zipfile.ZipFile(archive) as src,zipfile.ZipFile(altered,'w') as dst:
        for name in src.namelist():
            data=src.read(name)
            if name.endswith('limite.geojson'): data=b'tampered'
            dst.writestr(name,data)
    with pytest.raises(ValueError,match='Assinatura'): restore_backup(altered,tmp_path/'rejected')


@pytest.mark.parametrize('name',[
    'codex/dados/evidencias/.. /escape',
    'codex/dados/evidencias/CON.txt',
    'codex/dados/evidencias/NUL',
    'codex/dados/evidencias/dado. ',
])
def test_windows_zip_names_rejected(name):
    from app.backup import safe_member
    with pytest.raises(ValueError): safe_member(name)


def test_decisions_for_other_year_do_not_supersede_reference(env):
    _,c=env; enable(c)
    assert confirm(c,preview(c,[row()])).status_code==200
    for year in [2025,2029]:
        d=dict(decisao_id=str(year),indicador_id='A1',meta_id=f'T52_A1_{year}',ambito='Sede de Altamira',responsavel='Teste',justificativa='Referência do respectivo marco',data_registro='2026-11-05T10:00:00-03:00')
        assert c.post('/api/decisoes',json=d).status_code==200
    p=dict(meta_id='T52_A1_2025',medicao_id='m1',decisao_referencia_id='2025')
    assert c.post('/api/comparar',json=p).json()['estado']=='comparavel'


@pytest.mark.parametrize('value',['0',True,False])
def test_numbers_require_numeric_json_type(env,value):
    _,c=env
    r=row(); r['valor_medido']=value
    assert not preview(c,[r])['valid']


def test_additional_indicator_cannot_invent_scope(env):
    _,c=env
    ind=c.get('/api/base').json()['indicadores_desempenho'][0]
    r=row(); r.update(indicador_id=ind['indicador_id'],unidade=ind['unidade_original'],ambito='Bairro inventado')
    p=preview(c,[r])
    assert not p['valid']
    assert any(e['campo']=='ambito' for e in p['erros'])
    r['ambito']=ind['ambito']
    assert preview(c,[r])['valid']


def test_malformed_evidence_url_is_line_error(env):
    _,c=env
    r=row(); r['evidencia_arquivo_ou_url']='http://['
    response=c.post('/api/import/preview',json={'tipo':'medicoes','registros':[r]})
    assert response.status_code==200
    p=response.json()
    assert not p['valid']
    assert any(e['campo']=='evidencia_arquivo_ou_url' for e in p['erros'])
