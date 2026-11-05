"""Prévias sem escrita; confirmação verifica versão e assinatura sob bloqueio."""
import hashlib
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import ValidationError

from .repository import encode, now
from .schemas import MODELS, IDS


def references(tipo,r):
    if tipo=='medicoes': return [('indicadores_principais' if not r['indicador_id'].startswith('T') else 'indicadores_desempenho',r['indicador_id'])]
    if tipo=='execucoes': return [('acoes_previstas',r['acao_id'])]+([('projetos',r['projeto_id'])] if r.get('projeto_id') else [])
    b=[('linhas_investimento',r['linha_investimento_id'])]
    if r.get('acao_id'): b.append(('acoes_previstas',r['acao_id']))
    return b


def validate(repo,tipo,records):
    errors=[]; normalized=[]; seen=set()
    existing={r[IDS[tipo]]:r for r in repo.records(tipo)}
    base=repo.base
    known={key:{str(r[field]) for r in base[key]} for key,field in [('indicadores_principais','indicador_id'),('indicadores_desempenho','indicador_id'),('acoes_previstas','acao_id'),('projetos','projeto_id')]}
    known['linhas_investimento']={r['linha_id'] for r in base['investimentos_previstos']}
    for line,raw in enumerate(records,1):
        def error(field,message): errors.append(dict(linha=line,campo=field,mensagem=message))
        try:
            r=MODELS[tipo].model_validate(raw).model_dump(mode='json')
        except ValidationError as exc:
            translations={'missing':'Campo obrigatório ausente.','extra_forbidden':'Campo desconhecido para este modelo.','string_type':'Informe texto.','string_too_short':'Texto obrigatório está vazio.','date_from_datetime_parsing':'Informe data válida no formato AAAA-MM-DD.','greater_than':'Valor deve ser maior que zero.','greater_than_equal':'Valor não pode ser negativo.','literal_error':'Valor fora das opções permitidas.'}
            for e in exc.errors():
                message=translations.get(e['type'],str(e['msg']).removeprefix('Value error, '))
                error('.'.join(map(str,e['loc'])) or 'registro',message)
            continue
        id=r[IDS[tipo]]
        if id in seen: error(IDS[tipo],'ID repetido no lote.')
        seen.add(id)
        old=existing.get(id)
        if old:
            if r.get('revisao_esperada')!=old['revisao'] or not (r.get('justificativa_retificacao') or '').strip(): error(IDS[tipo],'ID existente: retificação exige revisao_esperada e justificativa_retificacao.')
        elif r.get('revisao_esperada') is not None: error('revisao_esperada','Registro a retificar não existe.')
        for key,value in references(tipo,r):
            if value not in known[key]: error(key,'Vínculo inexistente: '+value)
        evidence=r['evidencia_arquivo_ou_url']
        try:
            parsed=urlparse(evidence)
            valid_url=parsed.scheme in ('http','https') and bool(parsed.hostname) and not parsed.username
            parsed.port  # Valida também portas malformadas.
        except ValueError:
            valid_url=False
        local_id=evidence.removeprefix('/api/evidencias/')
        exists=False
        if repo.db.exists():
            with repo.connect() as c:
                entry=c.execute('SELECT file FROM evidence WHERE id=?',(local_id,)).fetchone()
                exists=bool(entry and (repo.root/'codex/dados/evidencias'/entry[0]).is_file())
        if not valid_url and not exists: error('evidencia_arquivo_ou_url','Use URL http(s) ou evidência já cadastrada por ID/URL da API.')
        if tipo=='medicoes':
            ind=next((i for i in base['indicadores_principais']+base['indicadores_desempenho'] if i['indicador_id']==r['indicador_id']),None)
            if ind and ind.get('unidade',ind.get('unidade_original'))!=r['unidade']: error('unidade','Unidade difere da definição original.')
            scopes={m['ambito'] for m in base['metas'] if m['indicador_id']==r['indicador_id']}
            if not scopes and ind and ind.get('ambito'): scopes={ind['ambito']}
            if scopes and r['ambito'] not in scopes: error('ambito','Âmbito difere dos âmbitos publicados para o indicador.')
            if r['unidade']=='%' and r['valor_medido'] is not None and not 0<=r['valor_medido']<=100: error('valor_medido','Percentual exige escala 0 a 100.')
            if r['numerador'] is not None and r['denominador'] is not None and r['valor_medido'] is not None:
                if r['unidade']=='%' and abs(r['numerador']/r['denominador']*100-r['valor_medido'])>0.01: error('valor_medido','Percentual difere de numerador / denominador × 100.')
        elif tipo=='execucoes':
            a=next((a for a in base['acoes_previstas'] if a['acao_id']==r['acao_id']),None)
            if a and a.get('localidade') and a['localidade']!=r['localidade']: error('localidade','Não desagregue a localidade da ação sem vínculo validado.')
        else:
            investment=[a for a in base['investimentos_previstos'] if a['linha_id']==r['linha_investimento_id']]
            if investment and not any(a['localidade']==r['localidade'] for a in investment): error('localidade','Localidade incompatível com a linha prevista.')
        r['data_registro']=r.get('data_registro') or now()
        normalized.append(r)
    return normalized,errors


class Imports:
    def __init__(self,repo):
        self.repo=repo
        self.previews={}

    def preview(self,tipo,records):
        if not isinstance(tipo,str) or tipo not in MODELS or not isinstance(records,list) or not records or len(records)>10000:
            raise HTTPException(422,'Informe tipo válido e lote de 1 a 10000 registros.')
        normalized,errors=validate(self.repo,tipo,records)
        id=secrets.token_urlsafe(24)
        signature=hashlib.sha256(encode({'tipo':tipo,'registros':normalized,'versao':self.repo.revision(),'base':self.repo.digest}).encode()).hexdigest()
        result=dict(preview_id=id,assinatura=signature,valid=not errors,erros=errors,quantidade=len(records),registros=normalized)
        if len(self.previews)>=100: self.previews.pop(next(iter(self.previews)))
        self.previews[id]=dict(result=result,tipo=tipo,revision=self.repo.revision(),created=datetime.now(timezone.utc),used=False)
        return result

    def confirm(self,id,signature):
        if not isinstance(id,str) or not isinstance(signature,str):
            raise HTTPException(422,'Informe preview_id e assinatura textuais.')
        p=self.previews.get(id)
        if not p or p['used'] or signature!=p['result']['assinatura']:
            raise HTTPException(409,'Prévia desconhecida, assinatura incorreta ou lote já confirmado.')
        if not p['result']['valid']: raise HTTPException(422,'Lote inválido; corrija os erros e gere nova prévia.')
        if (datetime.now(timezone.utc)-p['created']).total_seconds()>1800: raise HTTPException(409,'Prévia expirada; gere nova prévia.')
        with self.repo.transaction() as c:
            if p['revision']!=self.repo.revision(c): raise HTTPException(409,'Prévia desatualizada; consulte o estado e gere nova prévia.')
            for r in p['result']['registros']:
                self.repo.put(c,p['tipo'],r,references(p['tipo'],r))
        p['used']=True
        return dict(ok=True,quantidade=p['result']['quantidade'])
