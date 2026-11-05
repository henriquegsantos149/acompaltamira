# Contrato de integração — versão 1

Aplicação local aprovada em05/11/2026. API e frontend usam o mesmo host em produção; Vite faz proxy de `/api`, `/geo` e `/assets` em desenvolvimento. Backend porta8765, frontend5173, bind127.0.0.1. Não publicar.

- `GET /api/health` → `{status:"ok",version:"1.0",write_enabled:false}`.
- `GET /api/base` → conteúdo integral de `codex/base_padronizada.json`, sem modificar valores/campos.
- `GET /api/state` → `{write_enabled:boolean,medicoes:[],execucoes:[],financeiro:[],decisoes:[],historico:[]}`. Nomes das colunas dos registros seguem os três modelos da base; metadados de revisão podem ser adicionados.
- `POST /api/session/write` JSON `{confirm_sync_paused:true}` → habilita escrita apenas na sessão do servidor; não pausa OneDrive automaticamente. `false` volta a consulta.
- `POST /api/import/preview` JSON `{tipo:"medicoes"|"execucoes"|"financeiro",registros:[...]}` → `{preview_id,assinatura,valid:boolean,erros:[{linha,campo,mensagem}],quantidade,registros}`. Nenhuma escrita em disco.
- `POST /api/import/confirm` JSON `{preview_id,assinatura}` → lote atômico, exige modo escrita e prévia válida e fresca. Resposta `{ok:true,quantidade}`; erro422 inválido,409 desatualizado/duplicado,403 consulta.
- `POST /api/decisoes` → decisão de referência para indicador/âmbito, com `decisao_id,indicador_id,meta_id,ambito,responsavel,justificativa,data_registro`. Validar vínculos; histórico preservado.
- `POST /api/comparar` JSON `{meta_id,medicao_id,decisao_referencia_id}` → `{estado,diferenca,unidade,motivo,origens,classificacao?}`. Sem interpolação, sem comparar âmbitos/períodos/unidades diferentes; decisão explícita obrigatória para classificar.
- `POST /api/evidencias` multipart com `file` → `{evidencia_id,nome,sha256,url}`. Exige escrita, arquivo dentro da pasta permitida; URLs externas de evidência podem ser informadas sem download automático.
- `GET /api/evidencias/{id}` → arquivo seguro identificado por ID, não caminho arbitrário.
- `GET /api/export/{tipo}?formato=json|csv` → registros reais dos tipos aceitos ou `completo`; preservar nulos e unidade.
- `POST /api/backup` → `{nome,sha256,url}`; pacote restaurável com SQLite via backup API, evidências, geometrias, metadados e manifesto. Modo escrita obrigatório. Restauração via CLI, não aceitar ZIP arbitrário sem validação.
- `GET /api/geo/catalog` → `{layers:[{id,title,status:"validada"|"pendente",type:"geojson"|"image"|"document",url?,bounds?:[[sul,oeste],[norte,leste]],source,source_page?,year?,description,feature_count?,reason?}]}`.
- `/geo/*` → somente arquivos processados de `codex/dados/geoespaciais/processados`.
- `GET /api/documento` → PDF original; links usam `#page=N`.
- `/assets/*` → ativos próprios extraídos do PDF em `codex/aplicacao/assets`.

Erros retornam `detail` legível em português. Requisições mutáveis JSON usam `Content-Type: application/json`; rejeitar origens externas. Todo teste com dados fictícios usa armazenamento descartável em `codex/verificacao/dashboard`, nunca banco de produção.

Frontend pode filtrar o snapshot localmente. Biblioteca gráfica não é obrigatória: SVG acessível e tabela equivalente são adequados. Estado inicial é ausência de execução atual. Filtros não repartem registros conjuntos por distrito. Registros de tabela97 usam períodos relativos sem presumir anos.
