import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=async name=>JSON.parse(await fs.readFile(path.join(root,'extracao',name),'utf8'));
const m=await read('metas_indicadores.json'), i=await read('investimentos_acoes.json'), d=await read('diagnostico.json');
const p=await read('projecoes_anuais.json'), e=await read('intervencoes_planejadas.json'), inv=await read('inventario_tabelas.json'), manifest=await read('manifesto_fonte.json');
const pending=[...m.divergencias.map(x=>({pendencia_id:x.divergencia_id,tema:x.tema,descricao:x.descricao,paginas_pdf:x.paginas_pdf,tratamento:x.tratamento})),...i.pendencias.map(x=>({...x,paginas_pdf:String(x.pagina_pdf??''),tratamento:'Preservado conforme publicação. Resolver com o gestor antes de consolidar.'})),...d.divergencias.map(x=>({pendencia_id:x.id,descricao:x.descricao,paginas_pdf:x.paginas_pdf,tratamento:'Preservado conforme publicação. Não consolidar automaticamente.'})),
{pendencia_id:'EST-01',tema:'Reservação no fim do plano',descricao:'Tabela 65, 2051: vazão máxima diária 13,52 L/s e reservação necessária 389,38 m³. Diferem da tendência da própria tabela e da vazão máxima diária 334,97 L/s da tabela 58. Números preservados.',paginas_pdf:'234; 228',tratamento:'Validar a linha de 2051 com o gestor. Não corrigir automaticamente.'},
{pendencia_id:'EST-02',tema:'Rede de Castelo de Sonhos',descricao:'Tabela 72: coluna ATUAL + INCREMENTO, longo prazo, 1.701,00 m. Tabela 71: rede instalada no longo prazo 39.351,00 m. Rótulos e valores preservados.',paginas_pdf:'242; 243',tratamento:'Validar se a coluna expressa incremento ou estoque antes de agregar.'},
{pendencia_id:'EST-03',tema:'Cobertura da normalização',descricao:'Extração textual de todas as 321 páginas e inventário das 99 tabelas. A normalização semântica concentra-se no acompanhamento: metas, indicadores, diagnóstico selecionado, projeções, intervenções, programas, ações, investimentos e contingências. Demais tabelas permanecem no arquivo textual/inventário, sem afirmar normalização integral.',paginas_pdf:'1–321',tratamento:'Consultar LEIA-ME e cobertura por tabela.'}];
const datasets=[];
function add(sheet,key,records,grain,keys=null){datasets.push({sheet,key,records:records.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v===''?null:v]))),grain,keys});}
add('Metas','metas',m.metas_horizontes,'Uma meta por indicador, âmbito e ano; qualitativas G1/G2 sem ano.');
add('Indicadores principais','indicadores_principais',m.indicadores_metas,'Um indicador da tabela 51.');
add('Metas residuos','metas_residuos',m.metas_residuos_t54,'Uma meta qualitativa da tabela 54.');
add('Diagnostico','diagnostico',d.dados,'Uma medida, categoria e referência histórica do diagnóstico.');
add('Projecoes anuais','projecoes_anuais',p,'Uma medida por tabela, ano e localidade. Inclui meta técnica de perdas da tabela 57.');
add('Intervencoes previstas','intervencoes_previstas',e,'Uma medida por intervenção, localidade e horizonte.');
add('Investimentos previstos','investimentos_previstos',i.investimentos,'Um valor monetário por linha e período, incluindo totais explicitamente identificados.');
add('Programas','programas',i.programas,'Um programa com seu código original.');
add('Projetos','projetos',i.projetos,'Um projeto com seu código original e vínculo ao programa.');
add('Acoes previstas','acoes_previstas',[...i.acoes,...m.acoes_residuos_textuais.map(r=>({...r,descricao_original:r.acao_original,tipo_registro:'ação textual de resíduos'}))],'Uma ação/atividade por seção de origem. Repetições entre seções não são a mesma chave.');
add('Indicadores desempenho','indicadores_desempenho',[...m.indicadores_desempenho,...m.indicadores_residuos],'Uma definição de indicador. Fórmulas e unidades preservadas como texto.');
add('Referencias desempenho','referencias_desempenho',m.referencias_desempenho,'Uma referência histórica, meta ou parâmetro de desempenho.');
try {
  const c=await read('contingencias.json');
  const names={medidas_acionamento:'Medidas contingencia',eventos_contingencia:'Eventos contingencia',vinculos_evento_medida:'Vinculos contingencia',acoes_preventivas:'Acoes preventivas',riscos_trabalho:'Riscos trabalho',acoes_emergenciais:'Acoes emergenciais',pendencias:'Pendencias contingencia'};
  for(const [k,v] of Object.entries(c))if(Array.isArray(v)&&v.length&&typeof v[0]==='object')add(names[k]??k.slice(0,31),k==='pendencias'?'pendencias_contingencia':k,v,'Um registro transcrito do respectivo quadro de contingência ou risco.');
} catch(err){if(err.code!=='ENOENT')throw err;}
add('Pendencias','pendencias',pending,'Uma divergência ou limitação a resolver.');
add('Inventario fonte','inventario_fonte',inv.map(({texto_original,...r})=>r),'Um trecho de tabela/quadro por página. Texto completo no JSON de extração.');

// Empty future data-entry templates: no measured values or implementation status is fabricated.
const templates=[
{sheet:'Modelo medicoes',key:'modelo_medicoes',columns:['medicao_id','indicador_id','ambito','periodo_inicio','periodo_fim','numerador','denominador','valor_medido','unidade','evidencia_arquivo_ou_url','pagina_evidencia','responsavel_informacao','data_registro','observacao'],grain:'Uma medição real por indicador, âmbito e período. Informar evidência e manter denominador da definição original.'},
{sheet:'Modelo execucao',key:'modelo_execucao',columns:['execucao_id','acao_id','projeto_id','localidade','data_referencia','situacao_informada','quantidade_executada','unidade','inicio_real','conclusao_real','responsavel_informacao','evidencia_arquivo_ou_url','pagina_evidencia','observacao'],grain:'Um evento real de execução física, identificado pela ação e data de referência.'},
{sheet:'Modelo financeiro',key:'modelo_financeiro',columns:['despesa_id','linha_investimento_id','acao_id','localidade','periodo_inicio','periodo_fim','valor_empenhado','valor_liquidado','valor_pago','unidade_monetaria','data_base','responsavel_informacao','evidencia_arquivo_ou_url','pagina_evidencia','observacao'],grain:'Uma despesa comprovada por período e vínculo ao item previsto. Não somar empenhado, liquidado e pago entre si.'}
];
for(const t of templates)add(t.sheet,t.key,[],t.grain,t.columns);
const desc={
valor_original:'Conteúdo literal da fonte; preserva traços, ND, vírgulas e comparadores.',valor_numerico:'Conversão decimal do valor original, sem estimativa. Percentuais em escala 0–100.',valor_numero:'Conversão decimal do valor original, sem estimativa.',valor:'Valor monetário numérico em reais quando explicitamente informado.',pagina_pdf:'Página física do arquivo PDF, contando a capa como 1.',pagina_impressa:'Número de página impresso, quando identificado.',tabela:'Número original da tabela; quadros permanecem identificados no campo próprio.',ano:'Ano civil explicitamente apresentado na fonte.',ano_inicio:'Primeiro ano civil do intervalo explícito; vazio quando fonte usa apenas Ano 01–05.',ano_fim:'Último ano civil do intervalo explícito.',unidade:'Unidade de medida da fonte; não converter entre domicílios, economias e população.',indicador_id:'Identificador do catálogo correspondente. T98/T99 são mantidos separados de A1–G2.',ambito:'Abrangência territorial da fonte. Distritos em conjunto não foram desagregados.',tipo_linha:'Distingue item, subtotal e total; não somar subtotais/totais com os itens.',valor_medido:'Resultado real a inserir posteriormente, com unidade e evidência. Vazio nesta entrega.',acao_id:'Identificador da ação na base; prefixos preservam seção de origem.',linha_investimento_id:'Vínculo a linha_id de Investimentos previstos; não ao registro longo do período.',situacao_informada:'Situação real a informar posteriormente; não derivar de datas planejadas.',periodo_inicio:'Início real da competência, formato AAAA-MM-DD.',periodo_fim:'Fim real da competência, formato AAAA-MM-DD.',data_referencia:'Data real a que se refere a informação, formato AAAA-MM-DD.',evidencia_arquivo_ou_url:'Documento comprobatório do dado real. Não usar o plano como evidência de execução.',numerador:'Quantidade medida conforme a definição do indicador.',denominador:'Universo medido conforme a definição do indicador. Zero não equivale a ausência.',quantidade_executada:'Quantidade real comprovada; nenhuma quantidade foi preenchida.',valor_empenhado:'Despesa empenhada comprovada em reais.',valor_liquidado:'Despesa liquidada comprovada em reais.',valor_pago:'Despesa paga comprovada em reais.'
};
const model=[];
const priority=['meta_id','indicador_id','id','id_registro','investimento_id','linha_id','acao_id','programa_id','projeto_id','pendencia_id','natureza_registro','tipo_registro','natureza','eixo','ambito','localidade','local','ano','ano_inicio','ano_fim','periodo_original','medida','nome_original','descricao_original','valor_original','valor_numerico','valor_numero','valor','unidade'];
function cols(ds){const all=ds.keys??[...new Set(ds.records.flatMap(r=>Object.keys(r)))];return ds.keys??[...priority.filter(k=>all.includes(k)),...all.filter(k=>!priority.includes(k))];}
for(const ds of datasets){ds.columns=cols(ds);for(const col of ds.columns){const non=ds.records.map(r=>r[col]).filter(v=>v!==null&&v!==undefined);const typ=non.length?(typeof non[0]==='number'?'number':typeof non[0]==='object'?'json':'string'):(/(valor|numerador|denominador|quantidade)/.test(col)?'number':'string');model.push({tabela:ds.key,aba:ds.sheet,campo:col,tipo:typ,descricao:desc[col]??col.replaceAll('_',' '),granularidade:ds.grain,ausencia:'null no JSON; vazio no CSV/XLSX; não equivale a zero'});}}
await fs.mkdir(path.join(root,'csv'),{recursive:true});
const csvval=x=>{const s=x==null?'':typeof x==='object'?JSON.stringify(x):String(x);return /[;\n\r"]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;};
for(const ds of datasets){await fs.writeFile(path.join(root,'csv',ds.key+'.csv'),'\uFEFF'+[ds.columns,...ds.records.map(r=>ds.columns.map(k=>r[k]))].map(row=>row.map(csvval).join(';')).join('\r\n'),'utf8');}
await fs.writeFile(path.join(root,'base_padronizada.json'),JSON.stringify({fonte:manifest,regras:{nulos:'Ausente, não zero',percentuais:'Escala 0–100',medicoes_atuais:'Não fornecidas',data_extracao:'2026-11-05'},...Object.fromEntries(datasets.map(ds=>[ds.key,ds.records]))},null,2));
await fs.writeFile(path.join(root,'modelo_dados.json'),JSON.stringify({tabelas:datasets.map(ds=>({nome:ds.key,aba:ds.sheet,registros:ds.records.length,granularidade:ds.grain,colunas:ds.columns})),campos:model},null,2));
const catalog=inv.map(r=>({tipo:r.tipo,numero:r.numero,titulo_original:r.titulo_original,pagina_pdf:r.pagina_pdf,tratamento:(r.tipo==='Quadro'&&r.numero>=2&&r.numero<=12)||(r.tipo==='Tabela'&&[18,19,21,22,23,30,31,32,33,34,35,38,39,40,41,42,43,47,48,50,51,52,53,54,57,58,59,60,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,89,90,91,93,94,95,96,97,98,99].includes(r.numero))?'Dados normalizados; conferir tabela específica na base':'Extração textual preservada; consultar JSON/texto'}));
await fs.writeFile(path.join(root,'cobertura_extracao.csv'),'\uFEFF'+[Object.keys(catalog[0]),...catalog.map(Object.values)].map(row=>row.map(csvval).join(';')).join('\r\n'));
const wb=Workbook.create();
const guide=wb.worksheets.add('Como usar');guide.showGridLines=false;
const guideRows=[['PMISB de Altamira','Base para acompanhamento'],['Fonte','PMISB-ALTAMIRA-APROVADO.pdf, agosto de 2022.'],['Conteúdo','Dados do plano extraídos e padronizados; sem resultados atuais.'],['Metas','Uma linha por indicador, âmbito e ano explícito. G1/G2 são qualitativos.'],['Percentuais','73 significa 73%. Os valores são números na escala 0–100.'],['Ausências','Células vazias significam ausência. Zero somente quando publicado.'],['Distritos','Tabelas conjuntas não foram repartidas por distrito.'],['Prazos','Horizontes originais preservados. Ano 01–05 não virou ano civil.'],['Investimentos','Separar itens de subtotais/totais. Não somar períodos com a coluna TOTAL.'],['Execução futura','Preencher as três abas Modelo somente com comprovação externa.'],['Evidências','Cada valor do plano possui página e tabela/seção de origem.'],['Divergências','Consultar Pendencias antes de escolher metas ou agregar valores.'],['Cobertura','Arquivo cobertura_extracao.csv identifica tabelas normalizadas e textuais.'],['Limite','As 321 páginas e 99 tabelas têm extração textual. Nem todas as tabelas têm normalização semântica.'],['Modelo de dados','Dicionario descreve os campos; LEIA-ME.md documenta relações e limites.'],['Documento original','A assinatura SHA-256 está no manifesto_fonte.json e base_padronizada.json.']];
guide.getRange('A1:B16').values=guideRows;guide.getRange('A1:B16').format.font={name:'Arial',size:11};guide.getRange('A1:B16').format.wrapText=true;guide.getRange('A1:A16').format.columnWidth=24;guide.getRange('B1:B16').format.columnWidth=100;guide.getRange('A1:B16').format.rowHeight=34;guide.getRange('A1:B1').format.font={name:'Arial',bold:true,size:15};guide.getRange('A2:A16').format.font={name:'Arial',bold:true,size:11};
const all=[...datasets,{sheet:'Dicionario',key:'dicionario',records:model,columns:Object.keys(model[0])}];
let count=0;
for(const ds of all){
 const sh=wb.worksheets.add(ds.sheet);sh.showGridLines=false;
 const headers=ds.columns, rows=ds.records.map(r=>headers.map(k=>{let v=r[k]??null;if(v&&typeof v==='object')v=JSON.stringify(v);return typeof v==='string'&&v.startsWith('=')?"'"+v:v;}));
 const nr=Math.max(2,rows.length+1), nc=headers.length;
 sh.getRangeByIndexes(0,0,1,nc).values=[headers];
 if(rows.length)sh.getRangeByIndexes(1,0,rows.length,nc).values=rows;
 const rng=sh.getRangeByIndexes(0,0,nr,nc);rng.format.font={name:'Arial',size:10,color:'#202C39'};rng.format.verticalAlignment='top';rng.format.wrapText=true;rng.format.rowHeight=42;
 sh.getRangeByIndexes(0,0,1,nc).format={fill:'#234B3D',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:34,verticalAlignment:'center'};
 for(let c=0;c<nc;c++){
  const k=headers[c], texts=ds.records.map(r=>String(r[k]??'')), max=Math.max(k.length,...texts.map(x=>x.length));
  const width=/descricao|formula|observacao|original|texto|tratamento|granularidade/.test(k)&&max>60?78:max>30?38:Math.max(16,Math.min(32,max+3));
  const col=sh.getRangeByIndexes(0,c,nr,1);col.format.columnWidth=width;
  if(ds.records.some(r=>typeof r[k]==='number'))sh.getRangeByIndexes(1,c,nr-1,1).setNumberFormat(k==='valor'?'#,##0.00':'General');
 }
 // Fit wrapped descriptions to their content; preserve all text for normal scrolling.
 for(let r=0;r<rows.length;r++){
   const lines=Math.max(...rows[r].map((x,c)=>{const width=/descricao|formula|observacao|original|texto|tratamento|granularidade/.test(headers[c])&&String(x??'').length>60?78:38;return Math.ceil(String(x??'').length/(width*0.95));}));
   if(lines>2)sh.getRangeByIndexes(r+1,0,1,nc).format.rowHeight=Math.min(409,Math.max(42,lines*15));
 }
 sh.tables.add(sh.getRangeByIndexes(0,0,nr,nc),true,'Dados_'+(++count));sh.freezePanes.freezeRows(1);
 if(ds.key.startsWith('modelo_')){sh.getRangeByIndexes(1,0,1,nc).format.fill='#FFF3CD';}
}
wb.recalculate();
await fs.mkdir(path.join(root,'verificacao','planilha'),{recursive:true});
console.log((await wb.inspect({kind:'table',range:'Metas!A1:H5',include:'values,formulas',tableMaxRows:5,tableMaxCols:8,maxChars:1400})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(root,'PMISB_Altamira_base_padronizada.xlsx'));
for(const name of ['Como usar',...all.map(d=>d.sheet)]){
 const img=await wb.render({sheetName:name,range:name==='Como usar'?'A1:B8':'A1:E5',scale:1,format:'png'});
 await fs.writeFile(path.join(root,'verificacao','planilha',name.replaceAll(' ','_')+'.png'),new Uint8Array(await img.arrayBuffer()));
}
await fs.writeFile(path.join(root,'verificacao','contagens.json'),JSON.stringify(datasets.map(ds=>({tabela:ds.key,aba:ds.sheet,registros:ds.records.length,colunas:ds.columns.length})),null,2));
console.log(JSON.stringify({arquivo:'PMISB_Altamira_base_padronizada.xlsx',abas:all.length+1,registros:datasets.reduce((s,x)=>s+x.records.length,0)}));
