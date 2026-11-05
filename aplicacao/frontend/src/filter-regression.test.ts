import {describe,it,expect} from 'vitest';
import {axis,filterRows,cleanRecord,parseCSV} from './data';
describe('recortes por componente e CSV compatível',()=>{
 it('classifica E1 e E2 sem depender de nome',()=>{expect(axis({indicador_id:'E1'})).toBe('Esgotamento sanitário');expect(filterRows([{indicador_id:'E2'}],{eixo:'Esgotamento sanitário',territorio:'',periodo:''})).toHaveLength(1)});
 it('mapeia IDs adicionais e ações RSUT',()=>{expect(axis({indicador_id:'T98_01'})).toBe('Abastecimento de água');expect(axis({indicador_id:'T99_01'})).toBe('Esgotamento sanitário');expect(axis({indicador_id:'RSU_IND_01'})).toBe('Resíduos sólidos');expect(axis({acao_id:'RSUT_01'})).toBe('Resíduos sólidos')});
 it('conserva o eixo conjunto sem o atribuir somente a esgoto',()=>{expect(axis({eixo:'Água e esgoto'})).toBe('Água e esgoto · transversal')});
 it('aceita o marcador nulo das exportações sem criar número',()=>{expect(parseCSV('valor_pago;unidade\n__NULL__;R$')[0].valor_pago).toBeNull();expect(cleanRecord({valor_medido:'__NULL__'}).valor_medido).toBeNull()});
 it('filtra medições por competência sem inventar ano',()=>{expect(filterRows([{periodo_inicio:'2026-01-01',periodo_fim:'2026-12-31'}],{eixo:'',territorio:'',periodo:'2026'})).toHaveLength(1)});
});
