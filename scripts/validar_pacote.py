"""Read-only verification of exported workbook, CSVs and JSON. Does not author XLSX."""
import csv, json, math, hashlib
from pathlib import Path
import openpyxl

root=Path(__file__).resolve().parents[1]
base=json.loads((root/'base_padronizada.json').read_text(encoding='utf8'))
model=json.loads((root/'modelo_dados.json').read_text(encoding='utf8'))
wb=openpyxl.load_workbook(root/'PMISB_Altamira_base_padronizada.xlsx',data_only=False)
errors=[]; checks=[]; cells=0
def equivalent(a,b):
    if a is None and b in (None,''): return True
    if isinstance(a,(dict,list)): a=json.dumps(a,ensure_ascii=False,separators=(',',':'))
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)
    if isinstance(a,str) and a.startswith('=') and b=="'"+a:return True
    return a==b
for t in model['tabelas']:
    data=base[t['nome']];sh=wb[t['aba']]; cols=t['colunas']
    if list(next(sh.iter_rows(min_row=1,max_row=1,max_col=len(cols),values_only=True)))!=cols:errors.append(t['nome']+': cabeçalho XLSX diferente')
    for rn,record in enumerate(data,2):
        for cn,col in enumerate(cols,1):
            cells+=1;a=record.get(col);b=sh.cell(rn,cn).value
            if not equivalent(a,b):errors.append(f'{t["nome"]}!{rn},{col}: {a!r} != {b!r}')
    with (root/'csv'/(t['nome']+'.csv')).open(encoding='utf-8-sig',newline='') as f: rows=list(csv.reader(f,delimiter=';'))
    if rows[0]!=cols or len(rows)-1!=len(data):errors.append(t['nome']+': CSV cabeçalho/contagem diferente')
    for rr,record in zip(rows[1:],data):
        for val,col in zip(rr,cols):
            original=record.get(col)
            expected='' if original is None else json.dumps(original,ensure_ascii=False,separators=(',',':')) if isinstance(original,(dict,list)) else str(original)
            if isinstance(original,(int,float)):
                if not math.isclose(float(val),original,rel_tol=1e-12,abs_tol=1e-9):errors.append(t['nome']+': CSV valor diferente')
            elif val!=expected:errors.append(t['nome']+': CSV texto diferente')
    if t['nome'].startswith('modelo_'):
        if data or any(cell.value is not None for row in sh.iter_rows(min_row=2) for cell in row):errors.append(t['nome']+': modelo contém dados')
    checks.append({'tabela':t['nome'],'registros_json_csv_xlsx':len(data),'colunas':len(cols)})
formulas=[f'{s.title}!{c.coordinate}' for s in wb for row in s for c in row if c.data_type=='f']
if formulas:errors.append('Fórmulas executáveis inesperadas: '+str(formulas[:10]))
principal={r['indicador_id'] for r in base['indicadores_principais']}
if any(r['indicador_id'] not in principal for r in base['metas']):errors.append('Meta sem indicador principal')
programs={r['programa_id'] for r in base['programas']}
if any(r['programa_id'] not in programs for r in base['projetos']):errors.append('Projeto sem programa')
events={r['evento_id'] for r in base['eventos_contingencia']};measures={r['medida_id'] for r in base['medidas_acionamento']}
if any(r['evento_id'] not in events or r['medida_id'] not in measures for r in base['vinculos_evento_medida']):errors.append('Vínculo de contingência inválido')
original=root.parent/'documentos'/'PMISB-ALTAMIRA-APROVADO.pdf'
if hashlib.sha256(original.read_bytes()).hexdigest()!=base['fonte']['sha256']:errors.append('Assinatura da fonte diferente')
result={'data':'2026-11-05','resultado':'Aprovado nos testes executados' if not errors else 'Falhas','abas':len(wb.sheetnames),'celulas_comparadas':cells,'registros':sum(t['registros'] for t in model['tabelas']),'formulas_executaveis':len(formulas),'comparacoes':checks,'erros':errors,'limites':'Comparação dos formatos exportados; não comprova a correção externa dos dados do plano. Conferência semântica e visual descrita nos relatórios de revisão.'}
(root/'verificacao'/'validacao_pacote.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='comparacoes'},ensure_ascii=False))
if errors:raise SystemExit(1)
