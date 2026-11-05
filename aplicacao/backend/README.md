# API local PMISB Altamira

Executar nesta pasta com Python 3.13:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
python -m pytest --basetemp ../../verificacao/dashboard/backend_tmp -q
python -m compileall -q app tests
```

As versões efetivamente verificadas estão em `requirements.txt`. Para instalar numa máquina nova, criar ambiente virtual local e usar `python -m pip install -r requirements.txt`; não instalar globalmente. Uma instância apenas. Não usar `--reload`, múltiplos workers ou exposição na rede durante operação real. `PMISB_ROOT` pode apontar para uma cópia isolada do workspace; não altera os caminhos internos. A API serve `frontend/dist` quando compilado. Os ativos históricos ficam em `../assets`.

## Operação e persistência

O estado inicial é consulta e os três modelos estão vazios. Nenhum arquivo é criado pelo startup, consulta ou prévia. Pause manualmente o OneDrive antes de confirmar a escrita. `POST /api/session/write` com `{"confirm_sync_paused":true}` cria o snapshot assinado e o banco sob `codex/dados`; a confirmação não controla o OneDrive. O modo não persiste após reinício. Para encerrar, envie `{"confirm_sync_paused":false}` na mesma rota, feche o servidor e só então retome a sincronização. A troca para consulta aguarda gravações pendentes sob o mesmo bloqueio. As conexões são fechadas após cada operação e o SQLite usa journal de rollback, sem WAL.

Não manipular nem sincronizar cópia ativa de `pmisb.sqlite` como ponto de restauração. Alterações da base são recusadas quando a assinatura diverge do banco; a API nunca reescreve `codex/base_padronizada.json`. Snapshots ficam em `dados/snapshots/<prefixo-sha256>` e armazenam a assinatura completa no manifesto. A ausência de medição não significa zero. JSON conserva `null`; CSV utiliza o marcador explícito `__NULL__`, separador `;` e UTF-8 com BOM.

## Contrato e roteiro de integração

O contrato público está em `../CONTRATO.md`; `/openapi.json` expõe os parâmetros HTTP e `/docs` a documentação interativa. Smoke sem escrita: consultar `/api/health`, `/api/base`, `/api/state`, `/api/geo/catalog`, `/api/documento`, `/api/export/completo`. Conferir saúde `write_enabled:false`, listas de acompanhamento vazias e base integral. A ausência inicial de catálogo retorna `{"layers":[]}`.

As rotas de mutação exigem origem local, JSON `application/json` e confirmação de escrita, exceto prévia/comparação que não alteram armazenamento. Evidências usam multipart `file`; backup aceita POST sem corpo ou JSON vazio. URLs de evidência `http(s)` são referências e nunca são baixadas automaticamente. Um arquivo local precisa antes ser enviado em `/api/evidencias`; usar o ID retornado ou sua URL `/api/evidencias/<id>`. Limite de upload 25 MB, nome simples sem caminho. O arquivo é servido como anexo por ID e conservado com SHA-256.

Importação: enviar `{"tipo":"medicoes","registros":[...]}` para `/api/import/preview`; analisar `valid`, `erros` por linha/campo e `registros` normalizados. Somente `preview_id` e `assinatura` são necessários em `/api/import/confirm`. Prévia expira em 30 minutos, só pode ser consumida uma vez e qualquer alteração de versão exige nova prévia. Confirmação escreve o lote inteiro numa única transação; falha reverte também histórico e vínculos. IDs já existentes não são substituídos silenciosamente. Para retificação, repetir o ID com `revisao_esperada` igual à revisão atual e `justificativa_retificacao` não vazia. A revisão anterior continua no histórico (`antes`, `depois`, responsável informado e data).

Decisões em `/api/decisoes` usam os campos do contrato e data com fuso. Uma nova decisão recebe ID novo e preserva as anteriores; para a mesma meta, somente a mais recente pode classificar. Comparação em `/api/comparar` não exige escrita. Exige referência explícita, definição/unidade/âmbito iguais, competência anual integral correspondente ao marco publicado, evidência e denominador positivo. A2 melhora por redução; A1/A3/E1/E2/R1/R2/R3 por aumento. G1/G2 permanecem qualitativos. Não se inventa marco em2026 nem se desagrega território conjunto. Indicadores adicionais continuam com suas definições originais e não recebem direção presumida.

Os testes em `tests/test_api.py` são também fixtures de integração dos três modelos. Todos os valores de teste são fictícios e somente são escritos nas pastas temporárias de `codex/verificacao/dashboard/backend_tmp`, jamais no banco real. `create_app(root)` permite apontar outros testes para raiz descartável contendo a cópia da base.

## Backup e restauração

`POST /api/backup` retorna nome, SHA-256 e URL de download. Antes de confirmar importações e decisões, um backup automático preserva a versão anterior. O pacote inclui SQLite obtido pela [API oficial de backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup), base, snapshots, evidências, PDF original quando presente, catálogo/camadas GIS processadas e ativos documentais. Cada arquivo tem tamanho e SHA-256 no manifesto; geometrias originais não processadas não são arquivos referenciados pela aplicação e não entram no pacote.

Com serviço fechado e sincronização pausada, restaurar sempre para pasta NOVA:

```powershell
python -m app.backup "CAMINHO/pmisb-ID.zip" "CAMINHO/nova-copia" --confirm-sync-paused
```

A CLI recusa destinos existentes, caminhos externos, membros duplicados, links simbólicos, arquivos cifrados, conteúdo sem manifesto ou fora do escopo e assinaturas divergentes. Verifica integridade SQLite, chaves estrangeiras, versão da base e cada evidência antes de disponibilizar a cópia. Não há endpoint de upload/restauração de ZIP. O pacote contém dados/documentos; use o mesmo código da aplicação com `PMISB_ROOT` apontando para a cópia restaurada. Confira as evidências e camadas antes de escolher essa cópia para operação. O arquivo `manifesto_restauracao.json` conserva a relação verificada.

## Evidências de verificação

Suite cobre persistência após novo processo lógico, consulta sem alteração de bytes, nulo versus zero, validação dos três modelos, IDs órfãos/FK, lote inválido, rollback de falha no meio da transação, prévia desatualizada, retificação com histórico, redução de perdas, período sem interpolação, origem externa, backup/restauração e rejeição de ZIP adulterado. Referências técnicas: [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/) e [SQLite Python](https://docs.python.org/3/library/sqlite3.html). Não há dependência de QGIS no servidor.
