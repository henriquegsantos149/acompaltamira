"""API local PMISB. Iniciar: python -m uvicorn app.main:app --host 127.0.0.1 --port 8765."""
import csv
import hashlib
import io
import json
import os
import sqlite3
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response

from .backup import create_backup
from .comparacao import comparar
from .importacao import Imports
from .repository import Repository, now
from .schemas import Decisao, IDS


def create_app(root=None):
    root=Path(root or os.environ.get('PMISB_ROOT') or Path(__file__).resolve().parents[4]).resolve()
    repo=Repository(root)
    imports=Imports(repo)
    app=FastAPI(title='PMISB Altamira — Plano de 2022',version='1.0')
    app.state.write_enabled=False
    app.state.repository=repo
    lock=threading.RLock()

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        return JSONResponse(status_code=422,content={'detail':'Requisição inválida: confira campos e tipos obrigatórios.'})

    @app.exception_handler(sqlite3.Error)
    async def database_error(request,exc):
        return JSONResponse(status_code=409,content={'detail':'Operação de banco recusada; lote revertido. Confira vínculos, duplicatas e disponibilidade do disco.'})

    @app.exception_handler(OSError)
    async def filesystem_error(request,exc):
        return JSONResponse(status_code=409,content={'detail':'Não foi possível acessar ou gravar os arquivos. Verifique espaço, permissões e sincronização; tente novamente.'})

    @app.middleware('http')
    async def local_only(request,call_next):
        hostname=request.url.hostname
        if hostname not in {'127.0.0.1','localhost','testserver','::1'}:
            return JSONResponse(status_code=403,content={'detail':'Host não autorizado. Use o serviço local.'})
        if request.method in {'POST','PUT','PATCH','DELETE'}:
            origin=request.headers.get('origin')
            allowed={'http://127.0.0.1:8765','http://localhost:8765','http://127.0.0.1:5173','http://localhost:5173','http://testserver'}
            if origin and origin not in allowed:
                return JSONResponse(status_code=403,content={'detail':'Origem externa não autorizada.'})
            if request.headers.get('sec-fetch-site')=='cross-site':
                return JSONResponse(status_code=403,content={'detail':'Requisição externa não autorizada.'})
            if request.url.path not in {'/api/evidencias','/api/backup'} and request.headers.get('content-type','').split(';')[0]!='application/json':
                return JSONResponse(status_code=415,content={'detail':'Use Content-Type: application/json.'})
        return await call_next(request)

    def writable():
        if not app.state.write_enabled: raise HTTPException(403,'Modo consulta. Pause a sincronização e confirme antes de escrever.')

    def safe_file(folder,relative):
        folder=folder.resolve(); path=(folder/relative).resolve()
        if not path.is_relative_to(folder) or not path.is_file(): raise HTTPException(404,'Arquivo não encontrado ou caminho não permitido.')
        return path

    @app.get('/api/health')
    def health(): return dict(status='ok',version='1.0',write_enabled=app.state.write_enabled)

    @app.get('/api/base')
    def base(): return repo.base

    @app.get('/api/state')
    def state(): return dict(write_enabled=app.state.write_enabled,**repo.state())

    @app.post('/api/session/write')
    def write_session(payload:dict):
        if type(payload.get('confirm_sync_paused')) is not bool: raise HTTPException(422,'Confirme explicitamente confirm_sync_paused: true ou false.')
        with lock:
            if payload['confirm_sync_paused']:
                try: repo.initialize()
                except ValueError as e: raise HTTPException(409,str(e))
            app.state.write_enabled=payload['confirm_sync_paused']
        return dict(write_enabled=app.state.write_enabled)

    @app.post('/api/import/preview')
    def preview(payload:dict):
        with lock: return imports.preview(payload.get('tipo'),payload.get('registros'))

    @app.post('/api/import/confirm')
    def confirm(payload:dict):
        with lock:
            writable()
            # Backup consistente preserva a versão anterior de toda tentativa de importação.
            create_backup(repo)
            return imports.confirm(payload.get('preview_id'),payload.get('assinatura'))

    @app.post('/api/decisoes')
    def decisions(payload:Decisao):
        with lock:
            writable(); r=payload.model_dump(mode='json')
            meta=next((m for m in repo.base['metas'] if m['meta_id']==r['meta_id']),None)
            if not meta or any(meta.get(f)!=r[f] for f in ['indicador_id','ambito']): raise HTTPException(422,'Decisão com indicador, meta ou âmbito incompatível.')
            if any(d['decisao_id']==r['decisao_id'] for d in repo.records('decisoes')): raise HTTPException(409,'ID de decisão já registrado; crie nova decisão preservando o histórico.')
            create_backup(repo)
            with repo.transaction() as c:
                saved=repo.put(c,'decisoes',r,[('metas',r['meta_id']),('indicadores_principais',r['indicador_id'])])
            return saved

    @app.post('/api/comparar')
    def compare(payload:dict):
        return comparar(repo.base,repo.state(),payload.get('meta_id'),payload.get('medicao_id'),payload.get('decisao_referencia_id'))

    @app.post('/api/evidencias')
    def evidence(file:UploadFile=File(...)):
        with lock:
            writable()
            name=file.filename or 'evidencia'
            if Path(name).name!=name or '/' in name or '\\' in name or ':' in name or name in {'.','..'}: raise HTTPException(422,'Nome de arquivo inseguro.')
            data=file.file.read(25*1024*1024+1)
            if not data or len(data)>25*1024*1024: raise HTTPException(422,'Arquivo vazio ou maior que 25 MB.')
            id=uuid.uuid4().hex; filename=id+'.bin'; digest=hashlib.sha256(data).hexdigest()
            folder=root/'codex/dados/evidencias'; folder.mkdir(parents=True,exist_ok=True)
            path=folder/filename
            path.write_bytes(data)
            try:
                with repo.transaction() as c:
                    c.execute('INSERT INTO evidence VALUES(?,?,?,?)',(id,name,digest,filename))
                    c.execute("UPDATE metadata SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            except BaseException:
                path.unlink(missing_ok=True); raise
            return dict(evidencia_id=id,nome=name,sha256=digest,url='/api/evidencias/'+id)

    @app.get('/api/evidencias/{id}')
    def read_evidence(id:str):
        if not repo.db.exists(): raise HTTPException(404,'Evidência inexistente.')
        with repo.connect() as c: r=c.execute('SELECT name,file FROM evidence WHERE id=?',(id,)).fetchone()
        if not r: raise HTTPException(404,'Evidência inexistente.')
        return FileResponse(safe_file(root/'codex/dados/evidencias',r[1]),filename=r[0],media_type='application/octet-stream')

    @app.get('/api/export/{tipo}')
    def export(tipo:str,formato:str='json'):
        if tipo not in {*IDS,'completo'} or formato not in {'json','csv'}: raise HTTPException(422,'Tipo ou formato de exportação inválido.')
        if tipo=='completo':
            if formato!='json': raise HTTPException(422,'Exportação completa disponível em JSON.')
            return dict(versao='1.0',exportado_em=now(),base_sha256=repo.digest,base=repo.base,**repo.state())
        records=repo.records(tipo)
        if formato=='json': return records
        stream=io.StringIO(newline='')
        columns=list(dict.fromkeys(k for r in records for k in r))
        if not columns:
            from .schemas import MODELS
            columns=list(MODELS[tipo].model_fields) if tipo in MODELS else list(Decisao.model_fields)
        writer=csv.DictWriter(stream,fieldnames=columns,delimiter=';'); writer.writeheader()
        # Marcador explícito preserva ausência; zero continua 0.
        writer.writerows({k:'__NULL__' if v is None else v for k,v in r.items()} for r in records)
        return Response('\ufeff'+stream.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{tipo}.csv"'})

    @app.post('/api/backup')
    def backup(payload:dict={}):
        with lock:
            writable(); return create_backup(repo)

    @app.get('/api/backups/{nome}')
    def download_backup(nome:str):
        if not nome.startswith('pmisb-') or not nome.endswith('.zip') or Path(nome).name!=nome: raise HTTPException(404,'Backup inexistente.')
        return FileResponse(safe_file(root/'codex/dados/backups',nome),filename=nome,media_type='application/zip')

    @app.get('/api/geo/catalog')
    def catalog():
        path=root/'codex/dados/geoespaciais/processados/catalogo.json'
        if not path.exists(): return dict(layers=[])
        data=json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data,dict) else dict(layers=data)

    @app.get('/api/documento')
    def document(): return FileResponse(safe_file(root/'documentos','PMISB-ALTAMIRA-APROVADO.pdf'),media_type='application/pdf')

    @app.get('/geo/{relative:path}')
    def geo(relative:str): return FileResponse(safe_file(root/'codex/dados/geoespaciais/processados',relative))

    @app.get('/assets/{relative:path}')
    def assets(relative:str):
        own=root/'codex/aplicacao/assets'
        frontend=root/'codex/aplicacao/frontend/dist/assets'
        path=(own/relative).resolve()
        if path.is_relative_to(own.resolve()) and path.is_file(): return FileResponse(path)
        return FileResponse(safe_file(frontend,relative))

    @app.get('/{relative:path}')
    def frontend(relative:str):
        if relative.startswith(('api/','geo/')): raise HTTPException(404,'Rota não encontrada.')
        folder=root/'codex/aplicacao/frontend/dist'
        path=(folder/relative).resolve()
        if not path.is_relative_to(folder.resolve()): raise HTTPException(404,'Caminho não permitido.')
        if path.is_file(): return FileResponse(path)
        return FileResponse(safe_file(folder,'index.html'))

    return app


app=create_app()
