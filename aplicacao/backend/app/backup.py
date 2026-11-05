"""Pacotes verificáveis e restauração somente em diretório novo."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from .repository import now


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def create_backup(repo):
    directory=repo.root/'codex/dados/backups'
    directory.mkdir(parents=True,exist_ok=True)
    name='pmisb-'+uuid.uuid4().hex+'.zip'
    final=directory/name
    with tempfile.TemporaryDirectory(prefix='pacote-',dir=directory) as temporary:
        stage=Path(temporary)
        db=stage/'pmisb.sqlite'
        source=repo.connect()
        destination=sqlite3.connect(db)
        try: source.backup(destination)
        finally:
            source.close(); destination.close()
        files={'codex/dados/runtime/pmisb.sqlite':db,'codex/base_padronizada.json':repo.base_path}
        for relative in ['codex/dados/evidencias','codex/dados/geoespaciais/processados','codex/dados/snapshots','codex/aplicacao/assets']:
            folder=repo.root/relative
            if folder.exists():
                for path in folder.rglob('*'):
                    if path.is_file():
                        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()): raise ValueError('Arquivo associado fora da pasta permitida.')
                        files[path.relative_to(repo.root).as_posix()]=path
        pdf=repo.root/'documentos/PMISB-ALTAMIRA-APROVADO.pdf'
        if pdf.exists(): files['documentos/PMISB-ALTAMIRA-APROVADO.pdf']=pdf
        manifest=dict(versao=1,criado_em=now(),base_sha256=repo.digest,files={name:dict(sha256=sha256(path),size=path.stat().st_size) for name,path in files.items()})
        partial=directory/(name+'.partial')
        try:
            with zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED) as z:
                for relative,path in files.items(): z.write(path,relative)
                z.writestr('manifesto.json',json.dumps(manifest,ensure_ascii=False,indent=2))
            os.replace(partial,final)
        finally: partial.unlink(missing_ok=True)
    return dict(nome=name,sha256=sha256(final),url='/api/backups/'+name)


def safe_member(name):
    path=PurePosixPath(name)
    reserved={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    windows_unsafe=any(part.rstrip(' .')!=part or part.split('.')[0].upper() in reserved or any(ord(char)<32 for char in part) for part in path.parts)
    if not name or '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or str(path)!=name or windows_unsafe:
        raise ValueError('Caminho inseguro no pacote.')
    allowed=('codex/dados/runtime/','codex/dados/evidencias/','codex/dados/geoespaciais/processados/','codex/dados/snapshots/','codex/aplicacao/assets/')
    if name not in ('codex/base_padronizada.json','documentos/PMISB-ALTAMIRA-APROVADO.pdf') and not name.startswith(allowed):
        raise ValueError('Arquivo fora do escopo do backup.')
    if name.startswith('codex/dados/runtime/') and name!='codex/dados/runtime/pmisb.sqlite': raise ValueError('Arquivo runtime inesperado.')


def restore_backup(archive,target):
    archive=Path(archive).resolve(); target=Path(target).resolve()
    if target.exists(): raise ValueError('Destino deve ser novo e inexistente; não sobrescrever instalação.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        names=[i.filename for i in entries]
        if len(names)!=len(set(names)) or 'manifesto.json' not in names: raise ValueError('Manifesto ausente ou membros duplicados.')
        if len(entries)>20000 or sum(i.file_size for i in entries)>2*1024**3: raise ValueError('Pacote excede limite de restauração.')
        for i in entries:
            if i.flag_bits&1 or (i.external_attr>>16)&0o170000==0o120000: raise ValueError('Links e arquivos cifrados não são aceitos.')
            if i.filename!='manifesto.json': safe_member(i.filename)
        try:
            manifest=json.loads(z.read('manifesto.json'))
            if manifest['versao']!=1 or set(manifest['files'])!=set(names)-{'manifesto.json'}: raise ValueError('Conteúdo não corresponde ao manifesto.')
            if not {'codex/dados/runtime/pmisb.sqlite','codex/base_padronizada.json'}<=set(manifest['files']): raise ValueError('Banco/base ausentes.')
        except (KeyError,TypeError,json.JSONDecodeError) as e: raise ValueError('Manifesto inválido.') from e
        with tempfile.TemporaryDirectory(prefix='restauracao-',dir=target.parent) as temporary:
            stage=Path(temporary)/'conteudo'; stage.mkdir()
            for name,metadata in manifest['files'].items():
                if not isinstance(metadata,dict) or not isinstance(metadata.get('size'),int) or not isinstance(metadata.get('sha256'),str): raise ValueError('Metadados inválidos no manifesto.')
                path=stage/name; path.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as src,path.open('wb') as dst: shutil.copyfileobj(src,dst)
                if path.stat().st_size!=metadata.get('size') or sha256(path)!=metadata.get('sha256'): raise ValueError('Assinatura/tamanho incorreto: '+name)
            base_hash=sha256(stage/'codex/base_padronizada.json')
            if base_hash!=manifest.get('base_sha256'): raise ValueError('Snapshot difere do manifesto.')
            db=stage/'codex/dados/runtime/pmisb.sqlite'
            c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
            try:
                c.execute('PRAGMA trusted_schema=OFF')
                if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall(): raise ValueError('Banco inválido.')
                if c.execute("SELECT value FROM metadata WHERE key='base_sha256'").fetchone()[0]!=base_hash: raise ValueError('Versão da base incompatível.')
                for id,name,hash,file in c.execute('SELECT * FROM evidence'):
                    if Path(file).name!=file or sha256(stage/'codex/dados/evidencias'/file)!=hash: raise ValueError('Evidência ausente ou assinatura divergente.')
            finally: c.close()
            (stage/'manifesto_restauracao.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(stage,target)
    return target


def main():
    p=argparse.ArgumentParser(description='Restaura backup validado em NOVA pasta; feche o serviço e pause a sincronização.')
    p.add_argument('pacote',type=Path); p.add_argument('destino',type=Path)
    p.add_argument('--confirm-sync-paused',action='store_true',required=True)
    args=p.parse_args()
    try: print('Restaurado em:',restore_backup(args.pacote,args.destino))
    except (ValueError,OSError,sqlite3.Error,zipfile.BadZipFile) as e: p.exit(1,'Restauração recusada: '+str(e)+'\n')


if __name__=='__main__': main()
