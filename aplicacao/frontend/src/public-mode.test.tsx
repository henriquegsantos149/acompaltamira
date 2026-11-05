// @vitest-environment jsdom
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import App from './App';
vi.mock('./Geoportal',()=>({default:()=>null}));
const base={fonte:{paginas:321,sha256:'fonte'},metas:[],indicadores_principais:[],acoes_previstas:[],investimentos_previstos:[],programas:[],projetos:[],indicadores_desempenho:[],pendencias:[],pendencias_contingencia:[],inventario_fonte:[],diagnostico:[],eventos_contingencia:[]};
beforeEach(()=>{history.replaceState(null,'','/');window.scrollTo=vi.fn();vi.stubGlobal('fetch',vi.fn((url)=>Promise.resolve({ok:true,json:()=>Promise.resolve(String(url).includes('/base')?base:{write_enabled:false,medicoes:[],execucoes:[],financeiro:[],decisoes:[],historico:[]})})))});
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
it('consulta pública não oferece administração e conserva navegação de consulta',async()=>{render(<App publicMode/>);await screen.findByText('Acompanhamento do PMISB de Altamira');expect(screen.getAllByText('Consulta pública').length).toBeGreaterThan(0);expect(screen.queryByRole('button',{name:'Atualização de dados'})).toBeNull();expect(screen.queryByRole('button',{name:'Gerenciar acompanhamento'})).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Metas e indicadores'}));expect(await screen.findByText('Catálogo de indicadores')).toBeTruthy()});
it('rota administrativa manipulada é substituída por fontes no modo público',async()=>{history.replaceState(null,'','/?modulo=atualizacao');render(<App publicMode/>);expect(await screen.findByText('Documento de referência',{exact:false})).toBeTruthy();expect(screen.queryByText('Registrar uma atualização')).toBeNull();expect(location.search).toContain('modulo=fontes');expect(fetch).toHaveBeenCalledTimes(2)});
