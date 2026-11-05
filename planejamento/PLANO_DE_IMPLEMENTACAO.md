# Plano de Implementação: dashboard e geoportal do PMISB de Altamira

> Execução futura: implementar as tarefas deste plano com autoria e revisão separadas, usando o fluxo de execução de planos ou desenvolvimento por subagentes disponível. Os itens abaixo são pendentes. Este documento não autoriza iniciar desenvolvimento antes da aprovação do usuário.

**Objetivo:** entregar um dashboard com geoportal para consultar o PMISB e registrar acompanhamento com evidência, mantendo sua identidade visual e a origem dos dados.

**Arquitetura proposta:** aplicação web local, com frontend separado de uma API local e armazenamento persistente. A base extraída do plano será importada como versão imutável; registros de acompanhamento e decisões de referência serão mantidos em entidades próprias. Geometrias validadas e documentos serão arquivos associados por identificador.

**Tecnologias propostas:** React + TypeScript + Vite na interface, Leaflet no geoportal, componentes de gráficos acessíveis com tabelas equivalentes; Python + FastAPI na API, SQLite para persistência local. QGIS/GDAL, quando necessários, na preparação de cartografia, sem exigir QGIS aberto para consultar o painel. Versões serão fixadas no início da implementação após conferir compatibilidade e documentação oficial.

**Especificação:** [ESCOPO_E_IDENTIDADE.md](ESCOPO_E_IDENTIDADE.md). Os dois documentos formam a proposta para aprovação.

**Situação:** aguardando aprovação. Em05/11/2026 foram produzidos somente planejamento, inventário e evidências visuais; nenhuma aplicação, instalação, banco ou publicação foi criada nesta etapa.

## Condições gerais

- Todas as novas entregas ficarão dentro de `codex`, com dados e evidências separados do código.
- Os arquivos existentes de extração não serão sobrescritos pela aplicação.
- Interface em português brasileiro, apresentação numérica brasileira e datas de competência explícitas. Datas/horas de registro mantêm fuso; não confundir atualização do sistema com competência do dado.
- O operador local será o público inicial proposto. O serviço escuta apenas em `127.0.0.1`; não haverá exposição na rede ou internet nesta entrega.
- A aplicação não produzirá resultados atuais enquanto os modelos de acompanhamento estiverem vazios.
- Ausências, divergências e falta de geometria são estados previstos do produto, não erros a preencher com dados demonstrativos.
- SQLite será usado por uma instância local. Como o destino está dentro do OneDrive, a operação em escrita exige sincronização pausada durante o uso do banco e seus arquivos auxiliares; depois do encerramento limpo, o operador pode retomá-la. A aplicação não pausará o OneDrive sem ação do operador. Se essa rotina for inadequada, a alternativa a aprovar é armazenamento central em servidor antes de habilitar escrita. O manual tratará cópias do banco ativo sincronizadas pelo OneDrive como inadequadas para recuperação; somente backups consistentes, com evidências e manifesto, serão pontos de restauração.
- O cadastro de acompanhamento deve persistir no disco e sobreviver ao fechamento do navegador. Armazenamento apenas na memória ou no navegador não atende ao aceite.

## Foco da revisão

1. Valor ausente e zero legítimo precisam produzir estados diferentes em tela, cálculo, importação e exportação.
2. Fonte conflitante, universo distinto ou ano não publicado não podem produzir comparação de cumprimento.
3. Territórios conjuntos, registros duplicados por seção e totais financeiros não podem gerar contagens ou somas indevidas.
4. SRC desconhecido, coordenada suspeita ou esquema sem escala não podem virar feições geográficas validadas.
5. Importação inválida, fechamento da aplicação ou erro de gravação não podem apagar a versão anterior nem deixar lote parcialmente gravado.

## Organização proposta para a implementação

Esta árvore é uma proposta de arquivos futuros, não pastas de produto já criadas:

```text
codex/
  planejamento/                  proposta, inventário e referências visuais
  aplicacao/
    frontend/src/
      app/                       navegação, filtros e seleção global
      design/                    cores, tipografia e componentes comuns
      features/indicadores/      metas, medições e comparação
      features/acoes/            programas, projetos e execução
      features/financeiro/       previsto, despesas e reconciliação
      features/geoportal/        mapa, camadas e ficha de feição
      features/fontes/           documento, pendências e referências
      features/atualizacao/      formulários, importação e confirmação
      tests/                     regras da interface e testes de navegação
    backend/app/
      main.py                    API local e configuração
      schemas.py                 contratos e validação dos registros
      repository.py              transações, consultas e versões
      comparacao.py              regras de meta versus medição
      importacao.py              prévia, validação e gravação de lotes
      arquivos.py                documentos, caminhos e metadados
      backup.py                  cópia consistente e restauração
    backend/tests/               persistência, contratos e regras
  dados/
    snapshots/                   versões de entrada com assinatura e manifesto
    runtime/pmisb.sqlite         banco local criado na implementação
    geoespaciais/originais/      arquivos GIS recebidos ou oficiais
    geoespaciais/processados/    camadas prontas e seus metadados
    evidencias/                  documentos comprobatórios cadastrados
    backups/                     banco e manifesto consistentes
  entregas/                      exportações e instruções de operação
  verificacao/dashboard/        resultados de teste e conferência visual
```

## Etapas e critérios de aceite

### 1. Contrato de dados e preservação da fonte

Arquivos futuros: `backend/app/schemas.py`, `repository.py`, `backend/tests/test_importacao_base.py`, `dados/snapshots/`.

Consome: base e dicionário existentes. Produz: snapshot identificável, contratos tipados e consulta por ID de origem.

- [ ] Definir os contratos de indicador, meta, território, ação, intervenção, investimento, medição, atualização de execução, despesa, evidência e decisão de referência.
- [ ] Escrever testes para nulo versus zero, IDs repetidos, tipos numéricos, percentuais0–100, vínculo inexistente e unidade incompatível; comprovar falha antes da implementação.
- [ ] Implementar importação transacional do snapshot e catálogo de origens. Não deduplicar por nome; qualquer correspondência entre seções será relação explícita e revisada.
- [ ] Validar contagens por entidade contra o snapshot, assinaturas dos arquivos e ausência de execução inventada. Manter o PDF acessível à API por caminho permitido, sem cópias dispersas.
- [ ] Revisão independente do contrato e da migração antes de ligar gráficos.

Aceite: todos os registros importados têm a mesma origem, valor, unidade e significado do consolidado; ausências continuam ausentes. Importar novamente a mesma versão não duplica registros.

### 2. Identidade e navegação

Arquivos futuros: `frontend/src/design/`, `frontend/src/app/`, `frontend/src/tests/navigation.test.tsx`.

Consome: contrato da etapa1 e identidade da especificação. Produz: estrutura navegável e filtros compartilhados.

- [ ] Preparar referências de tela para visão geral, ficha e geoportal, usando as amostras do PDF; revisar legibilidade e hierarquia antes de aplicar aos demais módulos.
- [ ] Implementar cabeçalho, navegação, filtros, estados de carregamento/ausência/erro e detalhe de origem.
- [ ] Verificar teclado, foco, contraste, textos sem cortes e alternativas aos gráficos em larguras de360,768 e1440px.
- [ ] Confirmar que marca histórica e data do plano estão contextualizadas; nenhum slogan será tratado como marca atual presumida.

Aceite: navegação e filtros coerentes em todas as telas; conteúdo consultável sem depender exclusivamente de cor ou de interação com o mapa.

### 3. Motor de comparação e dashboard

Arquivos futuros: `backend/app/comparacao.py`, `backend/tests/test_comparacao.py`, `frontend/src/features/indicadores/`.

Interface proposta: `comparar(meta_id, medicao_id, decisao_referencia_id) → estado, diferenca, unidade, motivo, origens`. Estados: `sem_medicao`, `referencia_pendente`, `incompativel` ou `comparavel`. Somente `comparavel` pode receber classificação conforme operador e sentido validados do indicador.

- [ ] Testar: meta ausente em2026; medição vazia; zero publicado; denominador zero; indicador qualitativo; melhoria por redução; referência conflitante; território conjunto versus individual; períodos distintos.
- [ ] Implementar comparação somente entre dados compatíveis e referência explicitamente adotada. Não escolher automaticamente um capítulo como verdadeiro.
- [ ] Montar visão geral e fichas de indicadores com marcos de metas, série real, data/competência e acesso à fonte. Os dez indicadores principais serão o catálogo inicial; os adicionais ficam identificados como definições próprias.
- [ ] Revisar gráficos para que projeções e metas não pareçam medições. Sem interpolação de marcos nem percentual global de conclusão.

Aceite: base inicial produz ausência de acompanhamento atual, conservando toda a consulta ao planejado. Nenhuma classificação é criada apenas porque um prazo já passou.

### 4. Programas, ações e investimentos

Arquivos futuros: `frontend/src/features/acoes/`, `frontend/src/features/financeiro/`, `backend/tests/test_agregacao.py`.

Consome: IDs e relações da etapa1; comparação da etapa3 quando aplicável. Produz: fichas físicas/financeiras e exportações filtradas.

- [ ] Testar soma de itens sem subtotal/total, período relativo da tabela97, estoques e incrementos distintos e despesas em estágios diferentes.
- [ ] Implementar consulta por programa, projeto, ação, eixo, território e horizonte, mantendo códigos conflitantes e relações ainda não resolvidas.
- [ ] Exibir investimento previsto separado de empenho, liquidação e pagamento. Não atualizar moeda sem data-base e regra acordada.
- [ ] Exibir divergências das tabelas80/96/97 e evitar que o total publicado seja substituído silenciosamente por uma soma recalculada.
- [ ] Disponibilizar contingências planejadas como catálogo consultável; não criar incidentes reais a partir dos eventos hipotéticos.

Aceite: registros são contados pelo seu tipo; valores financeiros reconciliam com a regra de agregação selecionada e os conflitos permanecem visíveis.

### 5. Base geográfica e geoportal

Arquivos futuros: `dados/geoespaciais/`, `frontend/src/features/geoportal/`, `backend/tests/test_geometrias.py`, `frontend/src/tests/map.test.tsx`.

Consome: [INVENTARIO_CARTOGRAFICO.csv](INVENTARIO_CARTOGRAFICO.csv), IDs territoriais e metadados de origem. Produz: catálogo GIS, camadas validadas e vínculo explícito entre objeto e geometria. Um objeto pode ter zero ou mais geometrias; ausência não gera ponto artificial.

- [ ] Obter limite municipal oficial e metadados da edição escolhida. Camada atual e referência territorial de2022 recebem identificação temporal própria.
- [ ] Testar geometria inválida, coordenada fora do território esperado, ordem longitude/latitude trocada, SRC desconhecido, ausência de geometria e objeto sem correspondência exata.
- [ ] Preparar limite municipal e demais camadas oficiais disponíveis. Carregar dados locais no mapa, com legenda, atribuição, ajuste à extensão, busca e identificação.
- [ ] Avaliar e preparar sobreposições históricas das figuras36 p.106 e53 p.124 quando os pontos de controle e a validação forem suficientes; conservar relatório de georreferenciamento. Resultado reprovado permanece como imagem documental, fora do mapa.
- [ ] Extrair o cadastro de microssistemas da tabela20 como candidato, sem transformar coordenadas antes de confirmar o datum/SRC. Manter Parque Ipê em pendência. Geometrias originais confiáveis serão preferidas à vetorização de figuras.
- [ ] Implementar seleção bidirecional entre ficha e mapa, vinculada ao nível territorial real. Um filtro não pode transformar dado municipal em dado de bairro.
- [ ] Validar desempenho com as camadas reais e conferir alinhamento em diferentes escalas. Se o fundo online falhar, conservar camadas locais e lista acessível com aviso.

Aceite: geoportal utilizável com contexto oficial e dados geográficos efetivamente validados. Exibir somente geometria com origem e método conhecidos. O aceite não exige inventar ativos nem depende da confirmação de todos os microssistemas. Camadas pendentes permanecem identificadas no catálogo.

### 6. Alimentação, evidências, histórico e backup

Arquivos futuros: `backend/app/importacao.py`, `arquivos.py`, `backup.py`, `frontend/src/features/atualizacao/`, testes correspondentes.

Interfaces propostas: prévia de lote retorna erros por linha e alterações previstas; confirmação recebe o ID e assinatura da prévia e grava tudo numa transação. Exportação retorna snapshot e manifesto, sem alterar a base do plano.

- [ ] Escrever testes para duplicata, ID órfão, arquivo sem evidência obrigatória, importação malformada, tentativa de caminho externo, falha de gravação e restauração de backup.
- [ ] Implementar formulários nos três modelos existentes, registro de evidência, validação e confirmação de lotes. A ficha conserva valor original informado e dados normalizados.
- [ ] Preservar histórico de inclusão, retificação e decisão de referência. Atualizações incorretas serão retificadas com histórico, sem apagar a origem.
- [ ] Gerar backup consistente pela API de backup do SQLite, antes de importações/alterações de estrutura e sob comando do operador. O pacote inclui banco, evidências, geometrias e metadados referenciados, identificação do snapshot de origem e manifesto com assinaturas. Não copiar simplesmente o arquivo ativo nem seus sidecars. Restaurar numa cópia de teste e conferir assinaturas, documentos e camadas.
- [ ] Exportar dados filtrados em CSV e conjunto versionado em JSON, incluindo unidade, competência e origem. Exportar GeoJSON apenas das camadas validadas e respeitando suas condições de uso.

Aceite: dados permanecem após reiniciar aplicação e navegador; lote inválido não altera nada; backup restaurado reproduz registros, decisões e os próprios documentos de evidência. O operador local mantém os arquivos originais do plano. A rotina de sincronização pausada durante escrita e encerramento limpo deve estar descrita e testada na homologação, sem presumir que o OneDrive respeita bloqueios do banco.

### 7. Homologação e entrega local

Arquivos futuros: `verificacao/dashboard/`, `entregas/MANUAL_DE_OPERACAO.md`, instruções de inicialização e dependências fixadas.

- [ ] Executar testes do backend, testes da interface, compilação TypeScript e build de produção. Comandos de projeto previstos: `python -m pytest`, `npm run test`, `npm run typecheck` e `npm run build`, a definir nos scripts durante a implementação.
- [ ] Navegar em navegador real: filtrar, abrir origem, consultar mapa, registrar atualização, importar lote válido/inválido, exportar, reiniciar e restaurar backup numa cópia.
- [ ] Conferir amostras do dashboard e mapa contra PDF/base, incluindo divergências e ausência de execução inicial.
- [ ] Revisar aplicação por agente independente e corrigir falhas antes da entrega.
- [ ] Entregar instruções de instalação/inicialização, estrutura de dados, cobertura cartográfica, limitações e procedimento de atualização.

Aceite: um usuário consegue iniciar a aplicação local, consultar o PMISB, carregar apenas evidências reais, fechar/reabrir sem perder dados e localizar a origem de cada informação. Sem publicação externa nesta etapa.

## Sequência e dependências

Etapa1 → etapa2 → etapas3 e4 → etapa5 → etapa6 → etapa7. O levantamento e a preparação GIS podem ocorrer em paralelo à construção das telas depois do contrato de IDs; a publicação de cada camada continua dependente da validação espacial.

Marcos revisáveis: **M1** contrato e identidade; **M2** dashboard com dados do plano; **M3** geoportal com camadas validadas; **M4** atualização persistente e backup; **M5** aplicação homologada. Esses marcos são etapas de entrega, não datas de calendário prometidas. O esforço GIS depende de acesso às fontes e da qualidade dos mapas; nenhuma data de conclusão foi presumida.

## Evolução posterior, fora da primeira versão

Publicação privada ou pública; autenticação e perfis; colaboração simultânea; banco central com PostgreSQL/PostGIS quando necessário; atualização automática de fontes oficiais; novas camadas executivas; mapas de cobertura calculada somente com dados espaciais adequados. A arquitetura local permite migrar os dados, mas a publicação exige adequar persistência, acesso, serviço de mapas e infraestrutura; não é apenas enviar o frontend estático.

## O que a aprovação confirma

1. Escopo das sete áreas da aplicação e prioridade do dashboard integrado ao geoportal.
2. Identidade derivada do documento de2022, conforme as referências salvas.
3. Primeira versão local, para um operador, com persistência, evidências e backup.
4. Uso da base existente e aquisição de contexto cartográfico oficial com metadados; mapas do PDF serão usados geograficamente apenas quando validados.
5. Manutenção de lacunas e referências conflitantes até decisão documentada; nenhuma invenção de execução ou localização.

Após essa aprovação começa o desenvolvimento. Caso a intenção seja acesso imediato por equipe ou pela população, esse ponto altera o escopo inicial e deve constar da aprovação antes de escolher a infraestrutura.
