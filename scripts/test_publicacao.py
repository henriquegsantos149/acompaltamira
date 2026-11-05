import copy
import importlib.util
import json
import hashlib
from pathlib import Path

import pytest

SPEC=importlib.util.spec_from_file_location('publicacao',Path(__file__).with_name('preparar_publicacao.py'))
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


@pytest.fixture
def source(tmp_path):
    root=tmp_path/'codex'; root.mkdir()
    base={'fonte':{'arquivo':r'C:\Users\operador\documentos\PMISB-ALTAMIRA-APROVADO.pdf'},'metas':[{'meta_id':'m','valor_numerico':0,'unidade':'%','observacao':None}],'modelo_medicoes':[{'secret':'private'}],'modelo_execucao':[{'secret':'private'}],'modelo_financeiro':[{'secret':'private'}]}
    (root/'base_padronizada.json').write_text(json.dumps(base),encoding='utf-8')
    geo=root/'dados/geoespaciais/processados'; geo.mkdir(parents=True)
    (geo/'catalogo.json').write_text(json.dumps({'layers':[{'id':'limite','status':'validada','type':'geojson','url':'/geo/limite.geojson','source':'IBGE'},{'id':'historico','status':'pendente','type':'image','url':'/geo/candidato.tif','source':'PMISB'},{'id':'pdf','status':'pendente','type':'document','url':'/api/documento#page=118','source':'PMISB'}]}),encoding='utf-8')
    (geo/'limite.geojson').write_text('{"type":"FeatureCollection","features":[]}',encoding='utf-8')
    (geo/'candidato.tif').write_bytes(b'NEVER PUBLISH')
    for file in ['microssistemas_candidatos.json','distritos_cadastro_ibge.json']:
        (geo/file).write_text('{"records":[{"geometry":null,"source":"/api/documento#page=118"}]}',encoding='utf-8')
    (root/'aplicacao/assets').mkdir(parents=True)
    (root/'aplicacao/assets/marca-pmisb.png').write_bytes(b'original asset')
    (root/'aplicacao/assets/secret.txt').write_text('secret')
    for name in ['runtime/pmisb.sqlite','evidencias/privado.pdf','backups/privado.zip']:
        p=root/'dados'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'PRIVATE')
    docs=root.parent/'documentos';docs.mkdir();(docs/'PMISB-ALTAMIRA-APROVADO.pdf').write_bytes(b'%PDF original')
    return root,base


def test_exact_allowlist_and_values(source):
    root,base=source
    manifest=mod.prepare(root)
    public=root/'aplicacao/frontend/public'
    names={p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()}
    assert names=={'data/base.json','data/state.json','data/catalogo.json','geo/limite.geojson','geo/microssistemas_candidatos.json','geo/distritos_cadastro_ibge.json','assets/marca-pmisb.png','documentos/PMISB-ALTAMIRA-APROVADO.pdf'}
    expected=copy.deepcopy(base);expected['fonte']['arquivo']='PMISB-ALTAMIRA-APROVADO.pdf'
    for key in ['modelo_medicoes','modelo_execucao','modelo_financeiro']: expected[key]=[]
    assert json.loads((public/'data/base.json').read_text(encoding='utf-8'))==expected
    state=json.loads((public/'data/state.json').read_text())
    assert state==dict(write_enabled=False,medicoes=[],execucoes=[],financeiro=[],decisoes=[],historico=[])
    layers=json.loads((public/'data/catalogo.json').read_text(encoding='utf-8'))['layers']
    assert 'url' not in layers[1]
    assert layers[2]['url']=='/documentos/PMISB-ALTAMIRA-APROVADO.pdf#page=118'
    for entry in manifest['arquivos']:
        p=public/entry['caminho']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
        assert len(p.read_bytes())==entry['tamanho_bytes']
        assert not str(root) in json.dumps(entry)
    all_text=''.join(p.read_text(encoding='utf-8') for p in public.rglob('*.json'))
    assert 'C:\\' not in all_text and 'PRIVATE' not in all_text and 'private' not in all_text


def test_reproducible_and_pdf_fallback(source):
    root,_=source
    first=mod.prepare(root)
    (root.parent/'documentos/PMISB-ALTAMIRA-APROVADO.pdf').unlink()
    second=mod.prepare(root)
    assert first==second
    assert (root/'aplicacao/frontend/public/documentos/PMISB-ALTAMIRA-APROVADO.pdf').read_bytes()==b'%PDF original'


def test_catalog_traversal_is_rejected(source):
    root,_=source
    path=root/'dados/geoespaciais/processados/catalogo.json'
    path.write_text('{"layers":[{"status":"validada","type":"geojson","url":"/geo/../../runtime/pmisb.sqlite"}]}',encoding='utf-8')
    with pytest.raises(ValueError): mod.prepare(root)


def test_unexpected_public_file_blocks_packaging(source):
    root,_=source
    mod.prepare(root)
    (root/'aplicacao/frontend/public/private.sqlite').write_bytes(b'private')
    with pytest.raises(ValueError,match='não autorizado'): mod.prepare(root)


def test_pdf_hash_must_match_base(source):
    root,_=source
    base_path=root/'base_padronizada.json'
    base=json.loads(base_path.read_text())
    base['fonte']['sha256']='0'*64
    base_path.write_text(json.dumps(base),encoding='utf-8')
    with pytest.raises(ValueError,match='assinatura'): mod.prepare(root)


def test_pending_cadastre_never_publishes_geometry(source):
    root,_=source
    (root/'dados/geoespaciais/processados/microssistemas_candidatos.json').write_text('{"records":[{"geometry":{"type":"Point","coordinates":[0,0]}}]}',encoding='utf-8')
    with pytest.raises(ValueError,match='geometria'): mod.prepare(root)


def test_real_public_snapshot_preserves_plan_and_provenance():
    root=Path(__file__).resolve().parents[1]
    public=root/'aplicacao/frontend/public'
    original=json.loads((root/'base_padronizada.json').read_text(encoding='utf-8'))
    snapshot=json.loads((public/'data/base.json').read_text(encoding='utf-8'))
    expected=copy.deepcopy(original)
    expected['fonte']['arquivo']='PMISB-ALTAMIRA-APROVADO.pdf'
    for name in ['modelo_medicoes','modelo_execucao','modelo_financeiro']: expected[name]=[]
    assert snapshot==expected
    assert len(snapshot['metas'])==100
    assert len(snapshot['indicadores_principais'])==10
    assert len(snapshot['indicadores_desempenho'])==34
    assert len(snapshot['acoes_previstas'])==95
    assert len(snapshot['investimentos_previstos'])==124
    assert hashlib.sha256((public/'documentos/PMISB-ALTAMIRA-APROVADO.pdf').read_bytes()).hexdigest()==original['fonte']['sha256']
    records=[]
    for name in ['microssistemas_candidatos.json','distritos_cadastro_ibge.json']:
        records+=json.loads((public/'geo'/name).read_text(encoding='utf-8'))['records']
    assert len(records)==13
    assert all(r['geometry'] is None for r in records)
    manifest=json.loads((root/'verificacao/dashboard/PUBLICACAO_MANIFESTO.json').read_text(encoding='utf-8'))
    assert len(manifest['arquivos'])==12
    actual={p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()}
    assert actual=={entry['caminho'] for entry in manifest['arquivos']}
