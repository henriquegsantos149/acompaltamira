import {describe,it,expect} from 'vitest';
import {cleanRecord,expenseSum} from './data';
describe('atualizações e financeiro',()=>{
 it('não converte número inválido em ausência',()=>{expect(cleanRecord({valor_medido:'texto'}).valor_medido).toBe('texto')});
 it('preserva booleano para rejeição pela API',()=>{expect(cleanRecord({valor_medido:true}).valor_medido).toBe(true)});
 it('aplica fuso à data de registro informada',()=>{expect(cleanRecord({data_registro:'2026-11-05'}).data_registro).toMatch(/T.*Z$/)});
 it('nulo financeiro permanece ausente e zero é legítimo',()=>{expect(expenseSum([{valor_pago:null}],'valor_pago')).toBeNull();expect(expenseSum([{valor_pago:0}],'valor_pago')).toBe(0);expect(expenseSum([],'valor_pago')).toBeNull()});
});
