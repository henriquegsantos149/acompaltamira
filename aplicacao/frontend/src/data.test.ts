import {describe,it,expect} from 'vitest';
import {filterRows,formatValue,investmentSum,parseCSV} from './data';
describe('preservação da fonte',()=>{
 it('distingue zero e ausência',()=>{expect(formatValue(0)).toBe('0');expect(formatValue(null)).toBe('Sem informação')});
 it('não reparte âmbito conjunto',()=>{expect(filterRows([{ambito:'Castelo dos Sonhos e Cachoeira da Serra'}],{eixo:'',territorio:'Castelo dos Sonhos',periodo:''})).toEqual([])});
 it('não interpola meta para 2026',()=>{expect(filterRows([{ano:2025},{ano:2029}],{eixo:'',territorio:'',periodo:'2026'})).toEqual([])});
 it('soma apenas itens em períodos não totais',()=>{expect(investmentSum([{tipo_linha:'item',periodo_original:'CURTO',valor:5},{tipo_linha:'total',periodo_original:'CURTO',valor:5},{tipo_linha:'item',periodo_original:'TOTAL',valor:5}])).toBe(5)});
 it('lê CSV com aspas e preserva nulos',()=>{expect(parseCSV('a;b\n"um;dois";\n')[0]).toEqual({a:'um;dois',b:null})});
});
