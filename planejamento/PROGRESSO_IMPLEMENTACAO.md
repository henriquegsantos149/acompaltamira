# Execução do plano aprovado — 05/11/2026

Plano: PLANO_DE_IMPLEMENTACAO.md. Especificação: ESCOPO_E_IDENTIDADE.md. Aprovação do usuário: “Aprovado”.

- Implementado: backend, interface local e pública, cartografia, contratos, evidências, histórico, comparação, exportação e backup.
- Verificado: backend19 testes; interface24 testes; cartografia5 testes; empacotamento público7 testes; TypeScript e builds local/público aprovados. Revisão independente de backend, GIS, frontend e pacote público sem achados abertos após correções.
- Em andamento: publicação autorizada no GitHub e na Vercel e verificação HTTP/navegação do endereço público.
- Decisão: pasta não é repositório Git; implementar em nova pasta `codex/aplicacao`, sem criar worktree ou modificar outros projetos. Preservar arquivos de extração.
- Decisão: iniciar em consulta; habilitação da escrita exige confirmação do operador de que OneDrive foi pausado. Testes de persistência usam diretório descartável separado; nenhum dado fictício entra em produção.
- Decisão: Leaflet estável1.9.4 para compatibilidade e API documentada; sem adotar versão preliminar.
- Prévia: API8765 e frontend5173 em127.0.0.1, com proxy no desenvolvimento e frontend compilado servido pela API na entrega.
- Decisão posterior autorizada pelo usuário: repositório público `henriquegsantos149/acompaltamira` e hospedagem Vercel. Portal público é estático e somente consulta; backend de gestão continua local. Builds separados `dist` e `dist-public`, com lista permitida de publicação, sem SQLite, evidências ou backups.
- Correções verificadas: comparação conserva decisões de marcos diferentes; âmbito adicional e URL inválida validados; filtros de acompanhamento resolvem o eixo pelos vínculos de origem; ausência de investimento permanece nula; datas não usam separador de milhar; nenhum eixo de drenagem criado.
- Operação Windows: scripts PowerShell salvos UTF-8 com BOM para funcionar também no Windows PowerShell5; inicialização pelo atalho validada em consulta.
