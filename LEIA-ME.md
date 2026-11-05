# Base padronizada do PMISB de Altamira

Extração realizada em 05/11/2026 a partir de **PMISB-ALTAMIRA-APROVADO.pdf**, 321 páginas, edição indicada na folha de rosto: agosto de 2022. A fonte original permanece em `../documentos/`. A assinatura SHA-256 consta em `extracao/manifesto_fonte.json`.

## Arquivos de uso

- `PMISB_Altamira_base_padronizada.xlsx`: base em tabelas filtráveis, dicionário e três modelos vazios para coleta futura. Não contém painel.
- `base_padronizada.json`: as mesmas entidades em formato estruturado. As entidades dos três modelos são listas vazias.
- `csv/`: uma tabela por arquivo, UTF-8 com BOM e separador ponto e vírgula. Números normalizados usam ponto decimal; ao importar em Excel, configure a localidade adequada ou use o XLSX, que já contém números tipados.
- `modelo_dados.json`: campos, tipos, granularidade e regras de ausência. Os tipos dos modelos vazios são propostas de estrutura, não dados extraídos.
- `cobertura_extracao.csv`: identificação das tabelas e quadros por página e tratamento.
- `extracao/`: transcrições estruturadas por assunto, inventário de tabelas/quadros, texto integral e texto por página.
- `verificacao/`: evidências de conferência, relatórios e imagens de tabelas.
- `scripts/`: rotinas de extração e montagem usadas nesta entrega. Algumas tabelas foram transcritas e conferidas nas imagens; os JSON temáticos são seus registros preservados.

## O modelo criado

O modelo mantém entidades diferentes em tabelas próprias, prontas para futura importação por um sistema de acompanhamento. Os nomes dos campos e identificadores internos são convenções desta padronização; não são códigos oficiais novos do município. Nomes, códigos oficiais e descrições originais são preservados nos campos correspondentes.

| Entidade | O que representa | Regra para o acompanhamento |
|---|---|---|
| Indicadores principais | Os dez indicadores A1–G2 da tabela 51 | Usar `indicador_id` como chave no catálogo principal |
| Metas | Indicador × âmbito × ano publicado | Não interpolar anos; G1/G2 são qualitativos sem valor anual |
| Metas de resíduos | Objetivos e metas da tabela 54 | Preservar o prazo categórico e eventuais conflitos |
| Diagnóstico | Uma medida histórica por tabela/categoria | Não interpretar como execução de 2026 |
| Projeções anuais | Uma medida projetada por tabela, local e ano | Conservar tabela e natureza; T57 é meta técnica de perdas |
| Intervenções previstas | Quantidades físicas por local e horizonte | Distinguir implantação, estoque instalado e substituição |
| Investimentos previstos | Item × período ou total publicado | Filtrar `tipo_linha` e `periodo_original` antes de somar |
| Programas e projetos | Estrutura de códigos da figura 107 | `projetos.programa_id` se relaciona a `programas.programa_id` |
| Ações previstas | Ações estratégicas, cronograma e atividades textuais | Seções distintas mantêm IDs distintos; não contar como obras únicas |
| Indicadores de desempenho | Definições das tabelas 98/99 e texto de resíduos | Não substituir automaticamente A1–G2 por indicadores de definição diferente |
| Referências de desempenho | Históricos, metas e parâmetros do capítulo 4 | Observar ano, operador e tipo de referência |
| Contingências | Evento/causa, medidas e vínculos | `vinculos_evento_medida` liga evento a medida; não somar vínculos como eventos |
| Pendências | Diferenças na publicação e limites da extração | Não constituem correções autorizadas do plano |

Os valores com referência conjunta a Castelo de Sonhos e Cachoeira da Serra permanecem conjuntos. Não foram duplicados ou rateados entre os distritos. O plano trata de água, esgoto e resíduos sólidos; nenhum eixo de drenagem foi criado como se constasse dos componentes do documento.

## Regras de padronização

1. **Origem por registro.** Página física do PDF, página impressa e tabela/quadro/seção identificam a fonte. Nas páginas numeradas consultadas, PDF e impresso coincidem. Títulos continuados mantêm um trecho por página. `arquivo_fonte` é único para toda a base, mesmo nas tabelas que não repetem esse campo em cada linha.
2. **Valor original e valor numérico.** O texto publicado permanece em `valor_original`; o campo numérico converte apenas a representação brasileira. Exemplo: `1.847.220,00` torna-se `1847220`. Comparadores, notas e fórmulas permanecem nos campos originais.
3. **Percentuais na escala 0–100.** `73` representa 73%, e não 0,73. Não aplicar o formato percentual do Excel diretamente a esses campos. A unidade `%` aparece em coluna própria. Valores são taxas em porcentagem; não representam variação em pontos percentuais.
4. **Ausência não é zero.** `null` em JSON e célula vazia em CSV/XLSX indicam ausência de valor. Traços, ND e referências qualitativas permanecem no campo original ou na observação. Zeros publicados foram preservados. Nenhuma lacuna foi estimada.
5. **Prazos preservados.** Intervalos civis foram normalizados somente quando explícitos. “Ano 01–05” da tabela 97 não foi associado automaticamente a 2022–2026. A fonte usa definições de curto/médio/longo prazo diferentes em alguns trechos; os conflitos estão nas pendências. A tabela populacional 47 estende-se até 2054, embora o horizonte geral seja 2051; os anos publicados foram preservados.
6. **Planejamento e execução separados.** Metas, custos estimados e projeções não são resultados medidos nem despesas realizadas. Os valores iniciais de 2022 nas tabelas 52/53 continuam identificados como valores iniciais no plano de metas.
7. **Sem correção silenciosa.** Totais incompatíveis, definições diferentes e fórmulas aparentemente incorretas foram mantidos. Operações aritméticas usadas para conferir somas aparecem nas pendências como conferência, sem substituir o valor da fonte.
8. **Não agregar universos diferentes.** Domicílios, população atendida, economias, ligações, incrementos e estoque instalado são medidas diferentes. Também não somar totais com parcelas, estoques de anos diferentes ou percentuais.
9. **Responsabilidade.** Campos de responsável ficam vazios quando não explícitos. Marcas de atores envolvidos nos quadros de contingência não foram transformadas em responsabilidade exclusiva.
10. **Normalização textual.** Foram consolidados espaços e quebras de linha em campos temáticos; conteúdo e sentido foram preservados. O texto integral mantém uma extração mais próxima do layout.

## Modelos vazios para alimentar o acompanhamento

Os três modelos foram criados como estrutura proposta. Contêm cabeçalhos e uma linha visual vazia no Excel, que não é um registro. Nenhuma medição, execução, responsável ou despesa foi preenchida.

- **Modelo medicoes:** uma observação por indicador, âmbito e período, com numerador, denominador, valor medido, unidade e evidência. `indicador_id` deve corresponder ao catálogo escolhido. Indicadores A1–G2, T98/T99 e RSU têm definições próprias. Não calcular um percentual com denominador diferente do original.
- **Modelo execucao:** uma atualização real vinculada a `acao_id` e/ou `projeto_id`, com data de referência, quantidade executada, unidade, situação informada e evidência. Não usar o prazo previsto para preencher situação ou conclusão real.
- **Modelo financeiro:** uma despesa real por competência, com vínculo a `linha_id` dos investimentos e/ou `acao_id`. Empenho, liquidação e pagamento são estágios distintos; não devem ser somados entre si. Não há atualização monetária ou índice de inflação presumido.

Datas futuras devem usar `AAAA-MM-DD` nos formatos de intercâmbio. Para comparar previsto e realizado, será necessário selecionar uma referência coerente nas pendências, confirmar âmbito, unidade, período e evidência. Os modelos não impõem frequência ou regra de cumprimento que não conste da fonte.

## Cobertura e limites

O texto foi extraído das **321 páginas**, e o inventário identifica **99 números de tabelas e 12 números de quadros**, em **120 trechos por página**. Esse arquivo de texto também contém prosa após algumas tabelas até o próximo título ou fim da página; não deve ser interpretado automaticamente como uma tabela limpa. Textos incorporados exclusivamente em figuras e mapas podem não aparecer na extração textual. Estruturas usadas no acompanhamento, como a figura 107 e quadros de contingência, foram transcritas separadamente.

A normalização semântica abrange:

- Diagnóstico: tabelas 18, 19, 21–23, 30–35 e 38–43.
- Metas e indicadores: tabelas 51–54 e 98–99, indicadores textuais de resíduos e ações da seção 3.5.4.
- Séries anuais: tabelas 47, 48, 50, 57–60, 65 e 81–83.
- Intervenções por horizonte: tabelas 66–79, 84–87, 89–91 e 93–95. Totais e linhas de referência de 2021 dessas tabelas permanecem na extração original; a tabela padronizada de intervenções contém os três horizontes, sem duplicar totais.
- Investimentos: todas as linhas das tabelas 80, 96 e 97, incluindo itens e totais identificados.
- Programas, projetos e ações: quadros 2–4, figura 107 e atividades selecionadas dos projetos educacionais e de regulação, conforme seção e página de cada registro.
- Contingências e riscos: quadros 5–12.

As demais tabelas permanecem no inventário e na extração textual, incluindo caracterização municipal, equipamentos específicos e estruturas auxiliares. **Não se afirma que todas as tabelas do PDF tenham sido transformadas em medidas normalizadas.** Mapas e desenhos não foram vetorizados ou georreferenciados. Não foram consultadas fontes externas para completar a publicação.

As principais incompatibilidades incluem metas diferentes entre os capítulos 3 e 4, diferenças de definições dos indicadores, custos totais diferentes das parcelas da tabela 97, referência de perda dos distritos incompatível entre tabelas, vazão/reservação da sede no ano de 2051 na tabela 65 e o estoque de rede no longo prazo da tabela 72. Consulte os registros específicos antes de fazer comparações.

## Conferência

Foram conferidos identificadores, conversões numéricas, presença dos valores nas páginas informadas e amostras das relações entre linhas e colunas. Tabelas principais de metas, indicadores, custos e contingências foram verificadas também por imagem. A revisão independente e seus limites estão em `verificacao/revisao_extracao.md` e nos relatórios finais de verificação. A validação automatizada não substitui uma revisão de todas as células do documento nem resolve as divergências da própria fonte.
