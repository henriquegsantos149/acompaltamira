# Dashboard e geoportal do PMISB de Altamira: proposta para aprovação

Data: 05/11/2026. Situação: proposta; desenvolvimento não iniciado.

## Objetivo e uso

Criar uma aplicação para consultar o planejamento do PMISB, registrar seu acompanhamento e relacionar informações ao território. O usuário deve conseguir responder: o que está previsto, para qual local e período, qual evidência de execução existe e qual é a origem de cada informação.

Decisão de projeto proposta: primeira versão local, para um operador, acessada pelo navegador. Dados persistentes e documentos ficam dentro de `codex`. Publicação na internet, colaboração simultânea e autenticação ficam para uma etapa própria, depois de definir público e hospedagem. A aprovação desta proposta não publica automaticamente o sistema.

## O que já existe

Fonte: `../base_padronizada.json`, `../modelo_dados.json`, `../LEIA-ME.md` e PDF original em `../../documentos/PMISB-ALTAMIRA-APROVADO.pdf`.

| Conteúdo | Registros disponíveis |
|---|---:|
| Indicadores principais | 10 |
| Metas por âmbito/horizonte | 100, sendo 96 numéricas e 4 qualitativas |
| Indicadores adicionais de desempenho | 34 |
| Programas / projetos | 8 / 12 |
| Ações previstas | 95 |
| Intervenções físicas por medida/horizonte | 162 |
| Investimentos por linha/período | 124 |
| Medições reais / execução real / financeiro realizado | 0 / 0 / 0 |

Contagens de registros não equivalem a obras únicas. A base contém ainda diagnóstico, séries projetadas, referências de desempenho, contingências e pendências. A normalização é parcial por assunto, conforme a cobertura já documentada; inventário textual não equivale a dados semânticos prontos para cálculo.

Não foram localizados arquivos vetoriais ou rasters georreferenciados prontos na pasta de documentos ou na base. A tabela 20, p.118, contém dez pares E/N rotulados UTM22S; o datum não está indicado nessa tabela. A coordenada E do Parque Ipê é 262.642 m, diferente da faixa dos outros registros. Não corrigir nem atribuir EPSG automaticamente.

## Estrutura da aplicação

1. **Visão geral:** filtros de eixo, território, período e natureza do dado; metas publicadas, evidências disponíveis e atalhos para mapa, ações e pendências. Sem índice agregado fictício de cumprimento.
2. **Metas e indicadores:** ficha com definição, unidade, denominador, marcos publicados, histórico medido e fonte. Gráfico distingue meta de medição; não preenche anos sem meta nem conecta lacunas como resultado observado.
3. **Programas, projetos e ações:** lista e detalhe, cronograma planejado, atualizações comprovadas, quantidades físicas e evidências. Sem transformar registros de diferentes seções em obras únicas automaticamente.
4. **Investimentos:** previsto por eixo/horizonte; realizado em empenhado, liquidado e pago, separadamente. Pendências de soma e base monetária visíveis.
5. **Geoportal:** mapa amplo, catálogo de camadas, legenda, busca de objetos cadastrados, zoom, identificação de feição e ficha vinculada. Lista acessível acompanha o mapa. Objetos sem geometria permanecem no cadastro.
6. **Fontes e qualidade:** PDF na página de origem, dicionário, cobertura, divergências e histórico da referência escolhida para acompanhamento. Contingências consultáveis como catálogo de planejamento.
7. **Atualização de dados:** formulários e importação nos três modelos existentes, validação, confirmação, histórico e exportação. Sem substituição silenciosa da base do plano.

Layout proposto: cabeçalho institucional compacto; navegação lateral em desktop; filtros comuns; área de conteúdo; ficha lateral ou página de detalhe. No geoportal, o mapa ocupa a maior parte da tela, com camadas à esquerda e ficha à direita. No celular, camadas e ficha viram painéis recolhíveis. Seleções e filtros podem ser compartilhados por URL, sem incluir documentos ou dados sensíveis no endereço.

## Regras que a interface precisa preservar

- Separar diagnóstico, projeção, meta, medição, execução física e despesa realizada.
- Ausência significa **Sem informação**, nunca 0%, concluído ou atrasado automaticamente.
- Comparar apenas definição, universo, unidade, território e período compatíveis. Referência divergente não resolvida significa **Comparação pendente**.
- Não interpolar metas; em 2026, os marcos 2025 e 2029 podem ser exibidos, mas não produzem uma meta nova de 2026.
- Armazenar percentuais na escala 0–100; respeitar sentidos de melhoria e operadores originais. Redução de perdas não tem o mesmo sentido de aumento da cobertura.
- Não somar percentuais, estoques de anos distintos, totais com parcelas ou empenho com liquidação e pagamento.
- Não distribuir metas conjuntas dos distritos por bairro, ponto ou polígono sem regra explícita e validada.
- Toda atualização conserva autor informado, data de registro, competência e evidência. Autor informado em instalação local não equivale a identidade autenticada.
- Decisão sobre uma referência guarda responsável informado, data, justificativa e IDs de origem; nunca apaga a alternativa publicada.

## Identidade visual observada no documento

Referências inspecionadas: capa, p.1; aberturas dos capítulos, pp.184 e279; mapas pp.106 e124. Evidências em `referencias_visuais/`.

| Elemento | Evidência | Aplicação proposta |
|---|---|---|
| Verde-petróleo da capa | Cor raster dominante RGB 0,68,69, aproximadamente `#004445` | Cabeçalho, navegação ativa e destaque institucional |
| Verde escuro da faixa inferior da capa | Cor raster dominante RGB 1,52,53, aproximadamente `#013435` | Rodapé e profundidade visual |
| Verde dos rodapés internos | Preenchimento vetorial aproximadamente `#01393A` | Divisórias e títulos de seção |
| Branco e preto | Fundos e texto do documento | Base clara, leitura e contraste |
| Arial | Fonte mais frequente na extração: ArialMT; títulos Arial-BoldMT | Arial, com alternativa sem serifa do sistema |
| Brasão e marca municipal | Presença na capa e nos cabeçalhos | Usar somente ativo fiel extraído ou original fornecido, associado à edição de2022 |

As amostras de cor são medições do arquivo, não um manual oficial. Não usar a marca da Ambiental Pro nem criar logotipo novo. A marca e o slogan da gestão retratada em2022 não devem fazer a aplicação parecer uma comunicação institucional atual: a identificação principal será **PMISB Altamira**, com indicação **Plano de2022**. A marca histórica pode acompanhar a referência documental.

Adaptações propostas para a tela: cinza claro `#F3F5F5` para superfícies, cinza `#667579` para apoio, foco visível e ícones acompanhados de texto. Esses valores são escolhas de interface, não cores extraídas. Tabelas e gráficos terão números legíveis, unidades, legenda e equivalentes tabulares. Cores temáticas de água/esgoto/resíduos serão auxiliares e identificadas por legenda; não disputarão com a identidade institucional nem indicarão cumprimento sem dado.

## Estratégia cartográfica

Três origens separadas no catálogo: **contexto oficial**, **PMISB2022** e **acompanhamento validado**. Uma base cartográfica atual não altera a data nem os limites usados no planejamento de2022.

Primeiro carregar o limite municipal obtido de fonte oficial, com edição, licença, SRC e transformação documentados. Limites de distritos/unidades de análise só entram com geometria correspondente; não usar bairros ou limites aproximados como substitutos. O mapa continua útil com contexto e catálogo de objetos sem coordenadas, sem fabricar instalações.

As figuras36 p.106 e53 p.124 têm grades e referência SIRGAS2000 visíveis; são candidatas a sobreposições históricas georreferenciadas. A primeira menciona projeção UTM, zona22S. A legenda de uma figura não comprova o datum da tabela20. Para cada mapa: conferir legenda em resolução adequada, registrar recorte e pontos de controle, calcular e revisar resíduos, verificar alinhamento e escala da fonte e aprovar o resultado antes de exibir como camada georreferenciada. Resíduo baixo de ajuste não comprova precisão do levantamento original. Vetores derivados conservarão a identificação **derivado de mapa do PMISB2022**, sem aparência de cadastro executivo.

Metadados mínimos de camada/feição: ID, objeto vinculado, origem, arquivo/página ou URL, data da fonte, data da preparação, método, SRC original, transformação aplicada, precisão/escala conhecida, situação de validação e responsável informado. GeoJSON de exibição será preparado em coordenadas geográficas WGS84, com ordem longitude/latitude. O mapa pode usar Web Mercator para navegação; isso não autoriza medições de engenharia diretamente na tela.

Não inventar geometrias para redes, ecopontos ou obras. Os esquemas das pp.239 e259 não são traçados executivos. Incertezas ficam no cadastro e no catálogo de pendências; registros sem geometria válida não ganham marcadores no centro do município.

## Limites da primeira entrega

Aplicação local com persistência de acompanhamento, dashboard, geoportal, fontes e exportação. Sem publicação, sem colaboração simultânea, sem aplicativo nativo, sem integrações automáticas com sistemas de despesas ou sensores, sem monitoramento de incidentes em tempo real. Mapas históricos e cadastro de ativos dependem da validação espacial descrita; camadas sem esse requisito permanecem indisponíveis, com motivo explícito.

## Referências técnicas consultadas em05/11/2026

- [Leaflet: referência de GeoJSON, camadas e atribuição](https://leafletjs.com/reference).
- [Vite: construção para produção](https://vite.dev/guide/build).
- [FastAPI: bases SQL e exemplo SQLite](https://fastapi.tiangolo.com/tutorial/sql-databases/).
- [IBGE: Malha Municipal e referência SIRGAS2000](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html).
- [OpenStreetMap: política do serviço de imagens de mapa](https://operations.osmfoundation.org/policies/tiles/). Se usado, conservar atribuição e respeitar limites/cache; não fazer download em massa. O mapa deverá manter camadas locais e mensagem de indisponibilidade se o fundo online falhar.
