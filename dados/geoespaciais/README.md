# Cartografia preparada

Reprodução: `python codex/scripts/preparar_cartografia.py`, da raiz do projeto. Verificação independente dos artefatos: `python codex/verificacao/dashboard/cartografia/test_cartografia.py`.

O catálogo servido por `/api/geo/catalog` está em `processados/catalogo.json`. Apenas `limite-altamira-ibge` tem geometria liberada, em `/geo/limite_altamira_ibge.geojson`. As demais15 entradas conservam referência, página do PDF e motivo da pendência, sem marcadores artificiais.

## Limite oficial

Fonte: [API IBGE Malhas v3](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3), município1500602, período2022, qualidade máxima. A resposta representa uma **malha simplificada**, adequada ao contexto do mapa. A edição2022 foi escolhida explicitamente, coerente com o período do plano; a tentativa2024 retornou HTTP500, preservada em `originais/ibge_erro_2024_*`. Não se afirma que2022 seja a edição mais recente.

O nome e código foram conferidos na [API Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios/1500602). A malha de origem usa SIRGAS2000 geográfico, segundo as [informações técnicas2022](https://biblioteca.ibge.gov.br/visualizacao/livros/liv101998.pdf), preservadas localmente. A resposta GeoJSON da API não declara um membro `crs`; a preparação explicita a referência da malha de origem e aplica `pyproj` EPSG4674→4326, sempre longitude/latitude. Transformação escolhida pelo PROJ e precisão declarada estão em `processados/limite_altamira_ibge_metadados.json`. Não se presume precisão cadastral a partir dessa operação.

A geometria é válida, contém a sede e tem área geodésica compatível com a área oficial. Os SHA256 dos originais, PDF e derivados constam no manifesto/metadados. Não foi feita correção de divisas ou simplificação adicional. Atribuição: IBGE. Nenhuma licença adicional foi presumida; documentação de uso preservada.

## Mapas históricos: preparação concluída, liberação pendente

Figuras36 (p106) e53 (p124) foram extraídas dos objetos967 e1052 do PDF, sem reamostragem prévia. Os arquivos em `codex/verificacao/dashboard/cartografia/` incluem imagens com linhas de controle, GCPs/eixos de referência, recorte, matriz afim, resíduos, PNG WGS84 north-up com alfa, bounds Leaflet e GeoTIFF no SRC original. Não são servidos por `/geo` enquanto pendentes.

Figura36: cruzetas e tiques de moldura, SIRGAS2000 UTM22S (EPSG31982), escala impressa1:50.000. Resíduo máximo aproximado1,70m, pixel5,67m, barra2000m reconstruída2002,84m. Figura53: centros dos rótulos da moldura, SIRGAS2000 geográfico (EPSG4674), escala impressa1:60.000. Resíduo máximo aproximado2,78m, pixel6,96m, barra2000m reconstruída2003,40m. Os valores são consistência de leitura/ajuste e **não precisão do levantamento**. Os rótulos da figura53 são âncoras menos fortes que tiques explícitos; isso reforça a necessidade de validação externa.

Foi feita inspeção visual das grades de controle e teste das barras gráficas. Falta validar posição absoluta contra imagem de referência independente ou pontos de campo com SRC comprovado. O limite municipal não fornece essa validação urbana. A tabela20 não a fornece porque omite datum. Sem isso, o catálogo permite abrir o documento histórico, mas não desenha essas imagens como camadas validadas. Para liberar: registrar base independente/data, pontos e divergências observadas, responsável e decisão de validação; revisar bounds e PNG resultantes antes de adicionar URL de imagem ao catálogo.

## Cadastros sem geometria

`microssistemas_candidatos.json` transcreve os dez registros da tabela20, p118. Datum/EPSG/geometria são nulos, zona textual UTM22S preservada. Parque Ipê conserva E262642, sem correção; sua divergência de faixa é explícita. Endereços não foram geocodificados.

`distritos_cadastro_ibge.json` registra os três códigos/nomes da API Localidades: Altamira150060205, Cachoeira da Serra150060206 e Castelo dos Sonhos150060207. Essa consulta não informa edição histórica. A consulta de malha municipal com `intrarregiao=distrito` devolveu HTTP400 (“parâmetro intrarregiao NÃO aceita valores”), preservado. Não foi obtida geometria distrital; os nomes atuais não substituem as unidades históricas das pp186–189.

Os demais objetos (ETAs, ETE, elevatórias, redes, aterros, propostas etc.) conservam páginas e pendências do inventário aprovado. Quantidades, fotos e esquemas não foram convertidos em posições ou traçados. Nenhum ponto ou linha artificial foi criado.

## Ambiente

O script remove apenas de seu processo as variáveis `PROJ_LIB`, `PROJ_DATA` e `GDAL_DATA` herdadas para evitar usar o `proj.db` antigo do PostGIS com o rasterio atual. Não altera configuração do sistema nem projeto QGIS do usuário. Os arquivos originais baixados são reutilizados para reprodução offline; apagá-los causa novo download. Responsável técnico pela validação absoluta: não informado.
