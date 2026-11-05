export type Row = Record<string, any>;
export type Filters = {eixo:string;territorio:string;periodo:string};
export const normalize=(v:unknown)=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function axis(r:Row):string {
 const explicit=normalize(r.eixo||'');const id=String(r.indicador_id||r.acao_id||'');const v=explicit||normalize(r.nome_original||'');
 if(explicit.includes('agua')&&explicit.includes('esgot'))return 'Água e esgoto · transversal';
 if(/^RSU/.test(id)||v.includes('residu')||v.includes('limpeza')||/^R\d/.test(id))return 'Resíduos sólidos';
 if(/^E\d|^T99_/.test(id)||v.includes('esgot'))return 'Esgotamento sanitário';
 if(/^A\d|^T98_/.test(id)||v.includes('agua'))return 'Abastecimento de água';
 return 'Gestão e integração';
}
export function filterRows(rows:Row[],f:Filters){return rows.filter(r=>{
 const scope=r.ambito||r.localidade||r.local||'';let period=true;
 if(f.periodo){const start=r.periodo_inicio||r.data_referencia;const end=r.periodo_fim||start;
 period=r.ano!=null?String(r.ano)===f.periodo:r.ano_inicio!=null&&r.ano_fim!=null?Number(f.periodo)>=r.ano_inicio&&Number(f.periodo)<=r.ano_fim:start&&end?Number(f.periodo)>=Number(String(start).slice(0,4))&&Number(f.periodo)<=Number(String(end).slice(0,4)):String(r.periodo_original||'')===f.periodo;
 }return (!f.eixo||axis(r)===f.eixo)&&(!f.territorio||scope===f.territorio)&&period;
 })}
export const formatValue=(v:unknown)=>v===null||v===undefined||v===''?'Sem informação':typeof v==='number'?v.toLocaleString('pt-BR',{maximumFractionDigits:2}):String(v);
export const money=(v:unknown)=>typeof v==='number'?v.toLocaleString('pt-BR',{style:'currency',currency:'BRL'}):'Sem informação';
export const investmentSum=(rows:Row[]):number|null=>{const values=rows.filter(r=>normalize(r.tipo_linha)==='item'&&normalize(r.periodo_original)!=='total'&&typeof r.valor==='number'&&Number.isFinite(r.valor)).map(r=>r.valor);return values.length?values.reduce((sum,v)=>sum+v,0):null};
export function enrichAccompaniment(rows:Row[],base:Row):Row[]{return rows.map(r=>{const investment=(base.investimentos_previstos||[]).find((i:Row)=>i.linha_id===r.linha_investimento_id);const action=(base.acoes_previstas||[]).find((a:Row)=>a.acao_id===r.acao_id);return {...r,eixo:r.eixo??investment?.eixo??action?.eixo}})}
export async function request(url:string,body?:unknown){const r=await fetch(url,body!==undefined?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:undefined);const t=await r.json();if(!r.ok)throw new Error(typeof t.detail==='string'?t.detail:JSON.stringify(t.detail));return t}
export function download(rows:Row[],name:string,format:'csv'|'json'='csv'){const keys=[...new Set(rows.flatMap(Object.keys))];const content=format==='json'?JSON.stringify(rows,null,2):'\uFEFF'+keys.join(';')+'\n'+rows.map(r=>keys.map(k=>'"'+(r[k]==null?'__NULL__':typeof r[k]==='object'?JSON.stringify(r[k]):String(r[k])).replace(/"/g,'""')+'"').join(';')).join('\n');const url=URL.createObjectURL(new Blob([content],{type:format==='json'?'application/json':'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name+'.'+format;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
export function parseCSV(text:string):Row[]{const separator=text.split(/\r?\n/)[0].includes(';')?';':',';const lines:string[][]=[];let row:string[]=[],cell='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===separator&&!quoted){row.push(cell);cell=''}else if(c==='\n'&&!quoted){row.push(cell.replace(/\r$/,''));if(row.some(Boolean))lines.push(row);row=[];cell=''}else cell+=c}if(quoted)throw Error('CSV com aspas não fechadas.');row.push(cell.replace(/\r$/,''));if(row.some(Boolean))lines.push(row);const headers=(lines.shift()||[]).map(s=>s.replace(/^\uFEFF/,''));return lines.map(values=>Object.fromEntries(headers.map((h,i)=>[h,values[i]===''||values[i]==='__NULL__'||values[i]===undefined?null:values[i]])))}
export const modelFields:Record<string,string[]>={medicoes:'medicao_id indicador_id ambito periodo_inicio periodo_fim numerador denominador valor_medido unidade evidencia_arquivo_ou_url pagina_evidencia responsavel_informacao data_registro observacao'.split(' '),execucoes:'execucao_id acao_id projeto_id localidade data_referencia situacao_informada quantidade_executada unidade inicio_real conclusao_real responsavel_informacao evidencia_arquivo_ou_url pagina_evidencia observacao'.split(' '),financeiro:'despesa_id linha_investimento_id acao_id localidade periodo_inicio periodo_fim valor_empenhado valor_liquidado valor_pago unidade_monetaria data_base responsavel_informacao evidencia_arquivo_ou_url pagina_evidencia observacao'.split(' ')};
export function cleanRecord(r:Row){return Object.fromEntries(Object.entries(r).map(([k,v])=>{
 if(v===''||v==='__NULL__')return [k,null];
 if(k==='data_registro'&&typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v))return [k,new Date(v+'T12:00:00').toISOString()];
 if(['numerador','denominador','valor_medido','quantidade_executada','valor_empenhado','valor_liquidado','valor_pago','pagina_evidencia','revisao_esperada'].includes(k)&&typeof v==='string'){
 const n=Number(v.replace(',','.'));return [k,Number.isFinite(n)?n:v];
 }return [k,v];
 }))}
export function expenseSum(rows:Row[],field:string):number|null{const values=rows.map(r=>r[field]).filter(v=>typeof v==='number'&&Number.isFinite(v));return values.length?values.reduce((sum,v)=>sum+v,0):null}
