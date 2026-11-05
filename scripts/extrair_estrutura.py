import json, re, hashlib
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'codex'
PDF = ROOT / 'documentos/PMISB-ALTAMIRA-APROVADO.pdf'
doc = fitz.open(PDF)
def save(name, data):
    (OUT/'extracao'/name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
def num(s):
    if s.strip() in ['-', '–', '']: return None
    return float(s.replace('.', '').replace(',', '.').replace('%',''))

# Archive all pages and all titled table/board segments, without implying semantic validation.
pages=[]; tables=[]; segments=[]
for i,p in enumerate(doc):
    txt=p.get_text(sort=True)
    pages.append({'pagina_pdf':i+1,'pagina_impressa':i+1 if i>=13 else None,'texto':txt})
    if i<16: continue
    matches=list(re.finditer(r'(?m)^\s*(Tabela|Quadro)\s+(\d+)\s*[:–-]\s*([^\n]+)',txt))
    for j,m in enumerate(matches):
        end=matches[j+1].start() if j+1<len(matches) else len(txt)
        block=txt[m.start():end]
        tid=f'{m[1][0]}{int(m[2]):03d}-P{i+1:03d}'
        tables.append({'id_trecho':tid,'tipo':m[1],'numero':int(m[2]),'titulo_original':m[3].strip(),'pagina_pdf':i+1,'pagina_impressa':i+1,'texto_original':block,'status':'Extração textual; inclui notas/prosa após a tabela até o próximo título ou fim da página'})
        for k,line in enumerate(block.splitlines()):
            if line.strip(): segments.append({'id_linha':f'{tid}-L{k+1:03d}','id_trecho':tid,'pagina_pdf':i+1,'linha_trecho':k+1,'texto_original':line.strip()})
save('paginas_layout.json',pages); save('inventario_tabelas.json',tables); save('linhas_tabelas.json',segments)
(OUT/'extracao'/'texto_integral_layout.txt').write_text('\n\n'.join(f'=== PÁGINA PDF {p["pagina_pdf"]} ===\n{p["texto"]}' for p in pages),encoding='utf-8')

# Explicit source headers, same sequence as the annual numeric rows in the source.
schemas={
47: [('populacao_urbana_sede','hab'),('populacao_castelo_sonhos','hab'),('populacao_cachoeira_serra','hab'),('populacao_urbana_total','hab'),('taxa_crescimento_aritmetico','%'),('populacao_rural','hab'),('populacao_total_municipio','hab')],
48:[('ano_projeto','ano de projeto'),('populacao_urbana_sede','hab'),('rsd_diario','t/dia'),('rsd_anual','t/ano'),('rsd_volume','m³')],
50:[('ano_projeto','ano de projeto'),('populacao_urbana_distritos','hab'),('rsd_diario','t/dia'),('rsd_anual','t/ano'),('rsd_volume','m³')],
57:[('perda_sede','%'),('perda_distritos','%')],
}
agua=[('populacao_atendida','hab'),('consumo_per_capita','L/hab.dia'),('vazao_media_sem_perda','L/s'),('perda_total_projetada','%'),('vazao_media_com_perda','L/s'),('vazao_maxima_diaria','L/s'),('vazao_maxima_horaria','L/s')]
esgoto=[('populacao_atendida','hab'),('consumo_per_capita','L/hab.dia'),('vazao_media','L/s'),('extensao_rede_coletora','km'),('taxa_infiltracao','L/s.km'),('vazao_infiltracao','L/s'),('vazao_media_com_infiltracao','L/s'),('vazao_maxima_com_infiltracao','L/s'),('volume_medio_diario','m³/dia')]
for t in [58,59,60]: schemas[t]=agua
for t in [81,82,83]: schemas[t]=esgoto
schemas[65]=[('vazao_maxima_diaria','L/s'),('reservacao_necessaria','m³'),('reservacao_existente','m³'),('reservacao_excedente','m³')]
loc={47:'Município de Altamira (componentes nas medidas)',48:'Sede de Altamira',50:'Distritos de Castelo de Sonhos e Cachoeira da Serra (conjunto)',57:'Sede e distritos (componentes nas medidas)',58:'Sede de Altamira',59:'Castelo de Sonhos',60:'Cachoeira da Serra',81:'Sede de Altamira',82:'Castelo de Sonhos',83:'Cachoeira da Serra'}
annual=[]; issues=[]
loc[65]='Sede de Altamira'
token_re=r'(?<!\S)(?:\d[\d.,]*%?|[-–])(?!\S)'
for table in tables:
    t=table['numero']
    if table['tipo']!='Tabela' or t not in schemas: continue
    for line in table['texto_original'].splitlines():
        # Restrict to rows whose nonnumeric content is only horizon labels.
        rest=re.sub(token_re,' ',line)
        if re.sub(r'CURTO|MÉDIO|LONGO|\s','',rest): continue
        tokens=re.findall(token_re,line)
        years=[k for k,x in enumerate(tokens) if re.fullmatch(r'20\d\d',x)]
        if len(years)!=1: continue
        idx=years[0]; year=int(tokens[idx]); vals=tokens[idx+1:]
        if len(vals)!=len(schemas[t]):
            issues.append({'tabela':t,'pagina_pdf':table['pagina_pdf'],'ano':year,'linha_original':line,'problema':f'Esperadas {len(schemas[t])} medidas; encontradas {len(vals)}. Não normalizada.'}); continue
        for (metric,unit),raw in zip(schemas[t],vals):
            annual.append({'id_registro':f'T{t}-P{table["pagina_pdf"]}-{year}-{metric}','natureza':'Projeção do plano' if t!=57 else 'Meta técnica do plano','tabela':t,'pagina_pdf':table['pagina_pdf'],'pagina_impressa':table['pagina_pdf'],'localidade':loc[t],'ano':year,'ano_projeto_original':int(tokens[idx-1]) if idx>0 else None,'medida':metric,'unidade':unit,'valor_original':raw,'valor_numerico':num(raw),'situacao_valor':'Ausente na fonte (traço)' if raw in ['-','–'] else 'Informado','linha_original':line.strip()})
save('projecoes_anuais.json',annual)

# Engineering horizons remain independent records, and original ordered values are retained.
engineering=[]
for table in tables:
    t=table['numero']
    if table['tipo']!='Tabela' or t not in list(range(65,80))+list(range(84,96)): continue
    for line in table['texto_original'].splitlines():
        m=re.match(r'\s*(2022|2026|2037)\s+a\s+(2025|2036|2051)\s+(Curto|Médio|Longo)\s+Prazo\s+(.+)',line)
        if not m: continue
        vals=re.findall(token_re,m[4])
        engineering.append({'id_registro':f'T{t}-{m[1]}-{m[2]}','tabela':t,'pagina_pdf':table['pagina_pdf'],'pagina_impressa':table['pagina_pdf'],'titulo_original':table['titulo_original'],'ano_inicio':int(m[1]),'ano_fim':int(m[2]),'horizonte_original':m[3]+' Prazo','valores_ordenados_originais':vals,'linha_original':line.strip(),'status':'Valores em ordem da fonte; cabeçalhos no trecho original. Não usar como medidas nomeadas antes de mapear colunas.'})
save('intervencoes_horizontes_brutas.json',engineering)

# Column mapping verified against each table header. Period totals and final stocks remain different measures.
eng_schema={}
for t in [66,71,75]: eng_schema[t]=[('implantacao_rede_distribuicao','m'),('extensao_rede_distribuicao_instalada','m')]
for t in [67,72,76,86,91,95]: eng_schema[t]=[('extensao_rede_atual','m'),('rede_atual_mais_incremento','m'),('substituicao_rede','m')]
for t in [68,77]: eng_schema[t]=[('incremento_ligacoes_agua','unid.'),('ligacoes_agua_totais','unid.')]
for t in [69,73,78]: eng_schema[t]=[('instalacao_hidrometros','unid.'),('hidrometros_instalados_totais','unid.')]
for t in [70,74,79]: eng_schema[t]=[('substituicao_hidrometros','unid.'),('substituicao_hidrometros_acumulada','unid.')]
for t in [84,89,93]: eng_schema[t]=[('implantacao_ligacoes_esgoto','unid.'),('ligacoes_esgoto_instaladas','unid.')]
for t in [85,90,94]: eng_schema[t]=[('implantacao_rede_coletora','m'),('rede_coletora_instalada','m')]
eng_schema[87]=[('implantacao_estacoes_elevatorias','unid.'),('estacoes_elevatorias_implantadas','unid.')]
# Table 89 wraps the year range across three lines; reconstruct only the printed ranges.
t89=next(t for t in tables if t['tipo']=='Tabela' and t['numero']==89)
for start,end,h in [(2022,2025,'Curto'),(2026,2036,'Médio'),(2037,2051,'Longo')]:
    m=re.search(rf'{start}\s+a\s+{h}\s+Prazo\s+([-\d.,]+)\s+([-\d.,]+)\s+{end}',t89['texto_original'])
    if m: engineering.append({'id_registro':f'T89-{start}-{end}','tabela':89,'pagina_pdf':262,'pagina_impressa':262,'ano_inicio':start,'ano_fim':end,'horizonte_original':h+' Prazo','valores_ordenados_originais':[m[1],m[2]],'linha_original':m[0]})
eng_norm=[]
for r in engineering:
    t=r['tabela']; schema=eng_schema.get(t)
    if not schema or len(schema)!=len(r['valores_ordenados_originais']):
        issues.append({'tabela':t,'pagina_pdf':r['pagina_pdf'],'problema':'Linha de engenharia não mapeada'}); continue
    place='Sede de Altamira' if t in [66,67,68,69,70,84,85,86,87] else ('Castelo de Sonhos' if t in [71,72,73,74,89,90,91] else 'Cachoeira da Serra')
    for (metric,unit),raw in zip(schema,r['valores_ordenados_originais']):
        eng_norm.append({'id_registro':r['id_registro']+'-'+metric,'natureza':'Intervenção prevista no plano','eixo':'Água' if t<80 else 'Esgoto','localidade':place,'tabela':t,'pagina_pdf':r['pagina_pdf'],'pagina_impressa':r['pagina_pdf'],'ano_inicio':r['ano_inicio'],'ano_fim':r['ano_fim'],'horizonte_original':r['horizonte_original'],'medida':metric,'unidade':unit,'valor_original':raw,'valor_numerico':num(raw),'situacao_valor':'Ausente na fonte (traço)' if raw=='-' else 'Informado','linha_original':r['linha_original']})
save('intervencoes_planejadas.json',eng_norm)
save('pendencias_extracao_estrutura.json',issues)
save('manifesto_fonte.json',{'arquivo':str(PDF),'nome':PDF.name,'sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'paginas':len(doc),'data_documento_original':'Agosto - 2022','pagina_data_documento':3,'data_extracao':'2026-11-05','contagens':{'trechos_tabelas_quadros':len(tables),'linhas_textuais':len(segments),'medidas_anuais':len(annual),'linhas_intervencoes_brutas':len(engineering),'pendencias':len(issues)}})
print(json.dumps({'trechos':len(tables),'medidas_anuais':len(annual),'engenharia_bruta':len(engineering),'pendencias':issues},ensure_ascii=False))
