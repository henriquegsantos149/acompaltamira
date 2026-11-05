# PMISB Altamira — dashboard e geoportal local

## Abrir e encerrar

Abra `codex/Abrir painel.cmd`, ou execute `codex/aplicacao/Iniciar.ps1`. O endereço local é **http://127.0.0.1:8765**. A interface compilada é servida pela própria API; não é necessário abrir duas janelas de terminal. O serviço é acessível somente neste computador.

Para encerrar, finalize a sessão de escrita, gere o backup desejado e execute `codex/aplicacao/Parar.ps1`. O script desabilita gravações e aguarda seu encerramento antes de parar o processo registrado. Não feche o Windows durante uma importação ou backup.

Na primeira preparação de outro computador, instale Python e Node.js compatíveis, depois execute `codex/aplicacao/Instalar.ps1`. O script cria um ambiente Python dentro da aplicação, instala os requisitos fixados e compila a interface com o arquivo de dependências bloqueado. A instalação exige internet. O uso de camadas já salvas e dados locais não exige buscar o plano novamente; o fundo cartográfico online depende de conexão.

## Consulta e escrita

Ao iniciar, o sistema fica em **consulta**. A base extraída do plano não é editada. Sem medições, execução e despesas fornecidas, a interface informa ausência de acompanhamento; isso não significa execução zero.

Para cadastrar informações:

1. Pause a sincronização do OneDrive enquanto o banco estiver em uso para escrita. O painel não altera essa configuração do computador.
2. Na área de atualização, confirme a condição e habilite a sessão de escrita.
3. Cadastre a evidência e os campos do modelo apropriado; ou importe um lote.
4. Confira a prévia e os erros por linha. Somente um lote válido pode ser confirmado.
5. Gere backup, volte a consulta e encerre o servidor antes de retomar a sincronização.

Essa confirmação pertence à sessão do servidor, não é uma autenticação pessoal. A instalação foi concebida para um operador local. Não use a cópia do banco ativo sincronizada entre máquinas como banco compartilhado. Para uma equipe editar simultaneamente, será necessária a evolução para armazenamento central e controle de acesso.

## O que consultar

- **Visão geral:** panorama do planejamento, metas publicadas e disponibilidade de acompanhamento, com filtros comuns.
- **Metas e indicadores:** definição, abrangência, unidade, marcos de ano explícitos e fonte. Referências conflitantes exigem decisão documentada antes de uma classificação de cumprimento.
- **Programas e ações:** programas, projetos, atividades e intervenções físicas. Registros de seções diferentes não equivalem automaticamente a obras distintas.
- **Investimentos:** previsto separado de empenho, liquidação e pagamento. Observe se a linha é item ou total e se o período é relativo. Não some total e parcelas.
- **Geoportal:** limite oficial, catálogo e consulta territorial. Camadas documentais pendentes não representam instalações levantadas. O mapa mantém referência à fonte e ao ano.
- **Fontes e qualidade:** documento original, páginas de referência, pendências e catálogo de contingências planejadas.
- **Atualização:** informações reais, evidências, prévia de lotes, decisões de referência, histórico, exportação e backup.

Os filtros devem ser entendidos como seleção do âmbito declarado. Uma referência conjunta aos dois distritos não deve ser distribuída por bairro nem interpretada como valor individual de cada distrito. Ano de meta é diferente de período de execução ou data de atualização.

## Informações que podem ser adicionadas

Use os três modelos que acompanham a base, preservando seus nomes de campo:

| Tipo | Campos centrais | Evidência |
|---|---|---|
| Medição | ID, indicador, âmbito, competência, numerador/denominador, valor e unidade | Documento ou URL que comprove a medição |
| Execução física | ID, ação/projeto, local, data de referência, situação e quantidade executada | Registro que comprove a execução |
| Financeiro | ID, linha de investimento/ação, competência e valores por estágio | Documento que comprove a despesa |

Percentuais usam escala0–100: `73` representa73%. Célula vazia não é zero. Datas de intercâmbio usam `AAAA-MM-DD`. Para corrigir um registro, use o mecanismo de retificação com a revisão esperada e a justificativa; o histórico anterior permanece preservado. Não crie uma medição só para preencher o gráfico.

Comparações exigem definição, unidade, universo, âmbito e período compatíveis. Não existe meta interpolada de2026 apenas porque o documento contém2025 e2029. Redução de perdas e aumento de cobertura têm sentidos diferentes. A comparação pode permanecer pendente mesmo quando existem dois números, se as referências não forem compatíveis.

## Cartografia entregue e limitações

O limite municipal de Altamira foi obtido do serviço oficial do IBGE, período2022, e preparado em GeoJSON para exibição. Os dados originais e sua proveniência estão em `codex/dados/geoespaciais/`.

Os mapas de setores de abastecimento e bacias de esgoto do PMISB foram preparados como candidatos georreferenciados para conferência. A publicação dessas imagens como camadas exige validação absoluta independente. O erro de ajuste aos pontos de controle, por si só, não comprova a precisão da localização real. Esses candidatos ficam na área de verificação, separados das camadas publicadas.

O cadastro dos dez microssistemas conserva as coordenadas originais da tabela20, sem atribuir um datum presumido. A coordenada de Parque Ipê continua como publicada e pendente de conferência. O cadastro oficial confirma três distritos, mas não foram criados polígonos distritais substitutos. Consulte `codex/dados/geoespaciais/README.md` para metadados, métodos e pendências.

## Arquivos e recuperação

- Aplicação: `codex/aplicacao/`.
- Base de entrada preservada: `codex/base_padronizada.json` e arquivos de extração.
- Banco e registros: `codex/dados/runtime/`, criados quando a escrita é habilitada.
- Evidências: `codex/dados/evidencias/`.
- Geometrias e metadados: `codex/dados/geoespaciais/`.
- Backups: `codex/dados/backups/`.
- Testes e registros de verificação: `codex/verificacao/dashboard/`.

Backups utilizam a API do SQLite para produzir uma cópia consistente e incluem evidências, cartografia, metadados e manifesto com assinaturas. Não substitua esse procedimento por copiar somente o arquivo `.sqlite` enquanto a aplicação grava dados. A restauração deve ocorrer com o servidor parado, para um destino vazio, pela ferramenta documentada em `codex/aplicacao/backend/README.md`; confira assinaturas e arquivos antes de retomar o uso.

Exportações CSV preservam unidades e competência. Exportações JSON representam um conjunto versionado. Uma exportação filtrada não substitui o backup completo.

## Diagnóstico de operação

Se o painel não abrir, consulte `codex/verificacao/dashboard/servidor.stderr.log`. Se a porta8765 já estiver em uso por outro serviço, não encerre esse serviço indiscriminadamente. A inicialização verifica o servidor e o script de encerramento valida o processo registrado.

Se o mapa de fundo online falhar, as camadas locais e a lista de registros devem continuar disponíveis. Camadas pendentes não podem ser ativadas como se estivessem validadas. Se a consulta estiver vazia após um filtro, confira âmbito, ano e natureza antes de concluir que o plano não possui registros.

Esta entrega é local. Não há publicação na internet, autenticação de equipe nem conexão automática com sistemas de despesas, sensores ou cadastros executivos.
