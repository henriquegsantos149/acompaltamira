# Revisão independente do plano de implementação

Data: 05/11/2026. Documentos revisados: `PLANO_DE_IMPLEMENTACAO.md`, `ESCOPO_E_IDENTIDADE.md` e `INVENTARIO_CARTOGRAFICO.csv`. Revisão realizada em contexto separado da autoria. Nenhuma aplicação foi desenvolvida nesta revisão.

## Parecer

**Aprovado para apresentação ao usuário como proposta, com condições operacionais explícitas.** As ressalvas de persistência e recuperação foram incorporadas ao plano e conferidas em uma segunda leitura limitada aos trechos alterados. O escopo é coerente com uma primeira versão local de acompanhamento integrada ao geoportal. Não há impedimento para o usuário avaliar o plano. A aprovação desta revisão não substitui a aprovação solicitada ao usuário e não autoriza iniciar desenvolvimento.

A decisão de aplicação local para um operador está identificada como proposta, consta entre os pontos que a aprovação confirma e tem limites de evolução explícitos. React, FastAPI e SQLite são escolhas técnicas propostas; não exigem uma pergunta separada antes de apresentar o plano. Acesso imediato por equipe ou público, se solicitado, altera a arquitetura e precisa ser resolvido antes da implementação. O documento já explica essa diferença.

## Pontos confirmados

- As contagens de indicadores, metas, programas, projetos, ações, intervenções e investimentos correspondem à base existente. Os três modelos de acompanhamento permanecem sem registros reais. Contagem de registros não é apresentada como contagem de obras únicas.
- Diagnóstico, projeção, meta, medição, execução física e despesas possuem tratamentos distintos. A proposta impede interpolação de metas, inferência de atraso pelo calendário, escolha silenciosa entre referências conflitantes e agregações indevidas.
- A identidade distingue elementos observados no PDF de adaptações propostas para a interface. A identificação como plano de 2022 evita apresentar marca e slogan históricos como comunicação institucional atual. As medições de cores não são tratadas como manual oficial.
- O geoportal admite objetos sem geometria e bloqueia pontos artificiais, redes interpoladas e coordenadas com SRC desconhecido. A referência SIRGAS2000 de uma figura não é estendida à tabela 20. Parque Ipê continua pendente.
- As referências cartográficas amostradas conferem com o texto do PDF: setores p.105/106; redes p.114; bacias p.124; aterro e distritos pp.154–156; unidades territoriais pp.186–189; esquemas pp.239/259; ecopontos sem localização definida p.270. A existência de uma figura é tratada como origem documental, sem afirmar que já existe geometria validada.
- Camadas oficiais atuais terão edição e metadados próprios, preservando a referência histórica do plano. Precisão do mapa original e qualidade do ajuste de georreferenciamento são conceitos separados na especificação.
- Etapas, dependências, testes e aceites são concretos. Há validação transacional, prevenção de duplicatas, reinício da aplicação, restauração em cópia de teste, revisão independente e consulta à origem. Marcos não são datas prometidas.

## Ressalvas incorporadas e condições de implementação

### 1. Banco ativo dentro da árvore OneDrive

O caminho proposto `codex/dados/runtime/pmisb.sqlite` está dentro da pasta OneDrive. A versão revisada exige sincronização pausada pelo operador durante o uso em escrita do banco e de seus arquivos auxiliares, com retomada somente após encerramento limpo. A aplicação não altera o OneDrive por conta própria. A rotina deverá constar do manual e ser testada na homologação, sem presumir que o sincronizador respeite bloqueios do banco. Se essa operação for inadequada para o usuário, armazenamento central deverá ser aprovado antes de habilitar escrita. Não foi autorizada mudança silenciosa de pasta ou infraestrutura.

O plano revisado especifica a API de backup do SQLite e proíbe usar simples cópia do arquivo ativo ou de seus sidecars como ponto de recuperação. Essa definição atende à ressalva de planejamento. A documentação oficial explica os riscos de copiar um banco durante transação e oferece a API de backup para snapshots consistentes. [SQLite: causas de corrupção](https://www.sqlite.org/howtocorrupt.html), [SQLite: API de backup](https://sqlite.org/backup.html).

Essa condição é uma precaução operacional sobre a pasta sincronizada indicada, não uma afirmação de que OneDrive necessariamente corromperá o banco local. Está resolvida como requisito do plano; a implementação e os testes continuam pendentes. O usuário deve ter ciência dessa rotina ao aprovar a proposta local.

### 2. Restauração de evidências junto com os registros

O plano revisado exige pacote contendo banco, arquivos de evidência, geometrias, metadados referenciados, identificação do snapshot de origem e manifesto com assinaturas. O aceite de restauração abrange registros, decisões e os próprios documentos, com conferência de assinaturas, documentos e camadas em uma cópia de teste. Isso atende à ressalva de planejamento. Um banco íntegro apontando para documentos ausentes continua sem cumprir o aceite. A execução desse teste permanece pendente da implementação.

### 3. Dependência cartográfica explícita

A aquisição de malha oficial e a preparação de sobreposições são tarefas futuras. A entrega do geoportal deve registrar a edição efetivamente obtida e seus limites. Se uma fonte necessária não estiver disponível ou uma sobreposição falhar na validação, a aplicação precisa continuar com as camadas aprovadas e apresentar o motivo da ausência; isso já está previsto e deve ser mantido durante a execução.

## Limites da revisão

Esta revisão avalia a coerência e a executabilidade do plano. Não testa aplicação, banco, autenticação, desempenho, acessibilidade ou georreferenciamento, porque esses produtos ainda não existem. As figuras das páginas 106 e 124 foram verificadas visualmente pela autoria; a revisão independente confrontou referências e cautelas com o texto e o inventário, sem refazer o levantamento cartográfico. Não valida a atualidade de fatos territoriais, institucionais ou operacionais do documento de 2022.

Não foram alterados os documentos de proposta nem criado código de produto nesta revisão. A segunda leitura confirmou apenas a política OneDrive, o mecanismo e o conteúdo do backup e o aceite de restauração incorporados pela autoria. Essas condições são requisitos para executar e homologar a proposta, sem transformar decisões futuras em fatos aprovados.
