"""Comparação conservadora: não cria meta nem desagrega território."""


def comparar(base,state,meta_id,medicao_id,decisao_id):
    meta=next((m for m in base['metas'] if m['meta_id']==meta_id),None)
    med=next((m for m in state['medicoes'] if m['medicao_id']==medicao_id),None)
    origins=[dict(tipo='meta',registro=meta)] if meta else []
    if med: origins.append(dict(tipo='medicao',registro=med))
    def result(status,reason,**kwargs):
        return dict(estado=status,diferenca=None,unidade=meta.get('unidade') if meta else None,motivo=reason,origens=origins,**kwargs)
    if meta is None: return result('referencia_pendente','Meta não publicada para o identificador; sem interpolação.')
    if not med or med['valor_medido'] is None: return result('sem_medicao','Sem medição real informada.')
    if meta.get('valor_numerico') is None or meta.get('ano') is None: return result('incompativel','Meta qualitativa ou período não publicado.')
    for field in ['indicador_id','ambito','unidade']:
        if med.get(field)!=meta.get(field): return result('incompativel','Definição, âmbito ou unidade incompatível: '+field)
    year=meta['ano']
    if med['periodo_inicio']!=f'{year}-01-01' or med['periodo_fim']!=f'{year}-12-31':
        return result('incompativel','Competência difere do ano publicado; não interpolar ou equiparar períodos parciais.')
    if not med.get('evidencia_arquivo_ou_url'): return result('incompativel','Evidência obrigatória ausente.')
    if med.get('denominador') is None or med['denominador']<=0: return result('incompativel','Denominador da definição ausente ou inválido.')
    decision=next((d for d in state['decisoes'] if d['decisao_id']==decisao_id),None)
    if not decision or any(decision.get(f)!=meta.get(f) for f in ['meta_id','indicador_id','ambito']):
        return result('referencia_pendente','Decisão explícita compatível de referência obrigatória; alternativas publicadas preservadas.')
    matching=[d for d in state['decisoes'] if d['meta_id']==meta['meta_id'] and d['indicador_id']==meta['indicador_id'] and d['ambito']==meta['ambito']]
    if matching and matching[-1]['decisao_id']!=decision['decisao_id']:
        return result('referencia_pendente','Referência substituída por decisão posterior; consulte histórico.')
    # Os dez indicadores da tabela51 são percentuais; A2 mede perdas.
    directions={id:'aumentar' for id in ['A1','A3','E1','E2','R1','R2','R3']}
    directions['A2']='reduzir'
    direction=directions.get(meta['indicador_id'])
    if not direction: return result('referencia_pendente','Sentido/operador não validado para este indicador.')
    difference=med['valor_medido']-meta['valor_numerico']
    achieved=difference<=0 if direction=='reduzir' else difference>=0
    return dict(estado='comparavel',diferenca=difference,unidade=meta['unidade'],motivo='Referência adotada explicitamente; competência, âmbito, unidade e evidência compatíveis.',origens=origins+[dict(tipo='decisao',registro=decision)],classificacao='atingida' if achieved else 'nao_atingida')
