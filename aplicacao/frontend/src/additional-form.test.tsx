// @vitest-environment jsdom
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import Update from './Update';
const scope='Município de Altamira; área de abrangência conforme indicador';
afterEach(cleanup);
it('oferece âmbito e unidade originais do indicador adicional selecionado',()=>{render(<Update state={{write_enabled:false,medicoes:[],execucoes:[],financeiro:[],decisoes:[],historico:[]}} base={{indicadores_principais:[{indicador_id:'A1',unidade:'%'}],indicadores_desempenho:[{indicador_id:'T98_01',ambito:scope,unidade_original:'%'}],metas:[{meta_id:'A1-2025',indicador_id:'A1',ambito:'Sede de Altamira'}],acoes_previstas:[],investimentos_previstos:[],projetos:[]}} reload={vi.fn()}/>);fireEvent.change(screen.getByLabelText('Indicador de origem'),{target:{value:'T98_01'}});expect((screen.getByLabelText('Âmbito exato') as HTMLSelectElement).value).toBe(scope);expect((screen.getByLabelText('Unidade') as HTMLInputElement).value).toBe('%');expect(screen.getByRole('option',{name:scope})).toBeTruthy()});
