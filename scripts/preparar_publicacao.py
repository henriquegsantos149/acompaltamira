"""Empacotamento público por lista explícita; não publica acompanhamento privado."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT=Path(__file__).resolve().parents[1]
PDF='PMISB-ALTAMIRA-APROVADO.pdf'
PDF_URL='/documentos/'+PDF
ASSETS=('marca-pmisb.png','capa-foto.png','capa-original.jpeg','origens.json')
CADASTROS=('microssistemas_candidatos.json','distritos_cadastro_ibge.json')
STATE=dict(write_enabled=False,medicoes=[],execucoes=[],financeiro=[],decisoes=[],historico=[])
CATALOG_FIELDS={'id','title','status','type','url','bounds','source','source_page','year','description','feature_count','reason'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def check_public_json(value):
    if isinstance(value,dict):
        for child in value.values(): check_public_json(child)
    elif isinstance(value,list):
        for child in value: check_public_json(child)
    elif isinstance(value,str):
        if re.search(r'(?i)(?:(?<![a-z])[a-z]:[\\/]|\\\\[^\\]+\\|/Users/|/home/)',value):
            raise ValueError('Caminho local absoluto detectado; publicação recusada.')


def document_links(value):
    if isinstance(value,dict): return {key:document_links(child) for key,child in value.items()}
    if isinstance(value,list): return [document_links(child) for child in value]
    if isinstance(value,str) and value.startswith('/api/documento'):
        return PDF_URL+value.removeprefix('/api/documento')
    return value


def safe_source(folder,name):
    path=PurePosixPath(name)
    if not name or len(path.parts)!=1 or path.name!=name or '\\' in name or ':' in name or name.rstrip(' .')!=name:
        raise ValueError('Nome de arquivo público inseguro: '+str(name))
    candidate=folder/name
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(folder.resolve()) or not candidate.is_file():
        raise ValueError('Fonte ausente ou fora da pasta permitida: '+name)
    return candidate


def prepare(root=ROOT):
    root=Path(root).resolve()
    public=root/'aplicacao/frontend/public'
    geo=root/'dados/geoespaciais/processados'
    outputs={}
    origins={}
    def add(relative,data,source,source_data=None):
        outputs[relative]=data
        origins[relative]=dict(origem=source,sha256_origem=digest(source_data if source_data is not None else data))
    def add_json(relative,data,source,source_data=None):
        check_public_json(data)
        add(relative,encode(data),source,source_data)

    base_bytes=(root/'base_padronizada.json').read_bytes()
    base=copy.deepcopy(json.loads(base_bytes))
    base['fonte']['arquivo']=PureWindowsPath(base['fonte']['arquivo']).name
    for key in ['modelo_medicoes','modelo_execucao','modelo_financeiro']: base[key]=[]
    add_json('data/base.json',base,'base_padronizada.json',base_bytes)
    add_json('data/state.json',STATE,'estado público vazio: sem acompanhamento')

    catalog_bytes=(geo/'catalogo.json').read_bytes()
    catalog=json.loads(catalog_bytes)
    layers=[]
    for original in catalog['layers']:
        layer=document_links({key:copy.deepcopy(value) for key,value in original.items() if key in CATALOG_FIELDS})
        if layer.get('status') not in {'validada','pendente'}: raise ValueError('Situação cartográfica não reconhecida.')
        url=layer.get('url','')
        if url.startswith('/geo/'):
            name=url.removeprefix('/geo/')
            # Somente GeoJSON validado: nenhum TIFF, imagem candidata ou caminho arbitrário.
            if layer.get('status')=='validada' and layer.get('type')=='geojson':
                if not name.endswith('.geojson'): raise ValueError('Camada validada deve ser GeoJSON explícito.')
                source=safe_source(geo,name)
                raw=source.read_bytes(); data=json.loads(raw)
                check_public_json(data)
                add('geo/'+name,raw,'dados/geoespaciais/processados/'+name)
            else:
                layer.pop('url',None)
        elif url and not url.startswith(PDF_URL):
            layer.pop('url',None)
        layers.append(layer)
    add_json('data/catalogo.json',dict(layers=layers),'dados/geoespaciais/processados/catalogo.json',catalog_bytes)

    for name in CADASTROS:
        source=safe_source(geo,name)
        raw=source.read_bytes(); data=json.loads(raw)
        if any(record.get('geometry') is not None for record in data.get('records',[])):
            raise ValueError('Cadastro pendente não pode publicar geometria: '+name)
        add_json('geo/'+name,document_links(data),'dados/geoespaciais/processados/'+name,raw)
    metadata=geo/'limite_altamira_ibge_metadados.json'
    if metadata.exists():
        raw=safe_source(geo,metadata.name).read_bytes()
        add_json('geo/'+metadata.name,json.loads(raw),'dados/geoespaciais/processados/'+metadata.name,raw)

    for name in ASSETS:
        source=root/'aplicacao/assets'/name
        if not source.exists(): continue
        raw=safe_source(source.parent,name).read_bytes()
        if name.endswith('.json'): check_public_json(json.loads(raw))
        add('assets/'+name,raw,'aplicacao/assets/'+name)

    original=root.parent/'documentos'/PDF
    fallback=public/'documentos'/PDF
    pdf=(original if original.exists() else fallback)
    if not pdf.is_file() or pdf.is_symlink(): raise ValueError('PDF original ausente; é obrigatório para publicação.')
    pdf_bytes=pdf.read_bytes()
    expected_hash=base.get('fonte',{}).get('sha256')
    if expected_hash and digest(pdf_bytes)!=expected_hash: raise ValueError('PDF difere da assinatura da fonte da base.')
    add('documentos/'+PDF,pdf_bytes,'../documentos/'+PDF)

    # Arquivos inesperados no staging interrompem o build, evitando exposição acidental.
    if public.exists():
        for path in public.rglob('*'):
            if path.is_symlink(): raise ValueError('Link simbólico não permitido no diretório público.')
            if path.is_file() and path.relative_to(public).as_posix() not in outputs:
                raise ValueError('Arquivo não autorizado já existente em public: '+path.relative_to(public).as_posix())
    manifest=dict(versao=1,escopo='Consulta pública: PMISB 2022 e contexto oficial; sem acompanhamento real',base_sha256_origem=digest(base_bytes),arquivos=[dict(caminho=name,tamanho_bytes=len(data),sha256=digest(data),**origins[name]) for name,data in sorted(outputs.items())])
    for relative,data in outputs.items():
        path=public/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()==data: continue
        temp=path.with_name(path.name+'.tmp')
        temp.write_bytes(data); temp.replace(path)
    manifest_path=root/'verificacao/dashboard/PUBLICACAO_MANIFESTO.json'
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    manifest_path.write_bytes(encode(manifest))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT,help='Raiz do repositório codex; padrão relativo ao script.')
    args=parser.parse_args()
    manifest=prepare(args.root)
    print(f"Preparados {len(manifest['arquivos'])} arquivos públicos; manifesto verificacao/dashboard/PUBLICACAO_MANIFESTO.json")


if __name__=='__main__': main()
