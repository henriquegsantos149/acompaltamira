import {describe,it,expect} from 'vitest';
import {investmentSum,enrichAccompaniment,filterRows} from './data';
describe('ausência e vínculos de acompanhamento',()=>{
 it('investimento ausente não vira zero',()=>{expect(investmentSum([])).toBeNull();expect(investmentSum([{tipo_linha:'item',periodo_original:'CURTO',valor:null}])).toBeNull();expect(investmentSum([{tipo_linha:'item',periodo_original:'CURTO',valor:0}])).toBe(0)});
 it('filtra despesa pelo eixo da linha vinculada sem mutar o registro',()=>{const records=[{despesa_id:'D1',linha_investimento_id:'L1',valor_pago:0}];const enriched=enrichAccompaniment(records,{investimentos_previstos:[{linha_id:'L1',eixo:'Abastecimento de água'}],acoes_previstas:[]});expect(filterRows(enriched,{eixo:'Abastecimento de água',territorio:'',periodo:''})).toHaveLength(1);expect(records[0]).not.toHaveProperty('eixo')});
 it('filtra execução pelo eixo da ação e preserva o transversal',()=>{const rows=enrichAccompaniment([{acao_id:'A1'}],{acoes_previstas:[{acao_id:'A1',eixo:'Água e esgoto'}],investimentos_previstos:[]});expect(filterRows(rows,{eixo:'Água e esgoto · transversal',territorio:'',periodo:''})).toHaveLength(1);expect(filterRows(rows,{eixo:'Esgotamento sanitário',territorio:'',periodo:''})).toHaveLength(0)});
});
