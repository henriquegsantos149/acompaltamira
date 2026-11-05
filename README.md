# Acompanha Altamira — PMISB

Dashboard e geoportal para consultar o Plano Municipal Integrado de Saneamento Básico de Altamira, edição de agosto de2022. A interface segue a identidade visual do próprio documento e conserva a referência de origem de cada informação.

## Duas formas de uso

| Versão | Finalidade | Dados e acesso |
|---|---|---|
| Consulta pública — Vercel | Planejamento, metas, ações, investimentos, mapa e fontes | Site estático. Não hospeda API de gravação, banco, backups ou arquivos privados |
| Gestão local — Python | Alimentação de medições, execução e despesas com evidências e histórico | API em127.0.0.1, SQLite local, sessão de escrita explícita e backup consistente |

Não existem resultados atuais preenchidos nesta base inicial. Ausência de acompanhamento não representa execução zero. Metas conflitantes permanecem identificadas, anos ausentes não são interpolados e nenhum ponto de infraestrutura foi criado sem localização validada.

## Publicar na Vercel

Importe este repositório usando a raiz como Root Directory. O arquivo `vercel.json` define os comandos e a pasta de saída:

```text
Install Command: npm --prefix aplicacao/frontend ci
Build Command: npm run build
Output Directory: aplicacao/frontend/dist-public
```

O build público usa `VITE_PUBLIC_MODE=true`, presente em `.env.public`, sem segredos. Não são necessárias variáveis de banco, tokens ou funções Python para a versão pública. O mesmo código conserva a versão local com sete módulos; a versão pública oferece seis módulos e não disponibiliza administração, upload, gravação ou backup.

Preparação local do pacote público:

```powershell
python scripts/preparar_publicacao.py
npm --prefix aplicacao/frontend ci
npm run build
```

O pacote usa uma lista permitida de arquivos e não lê banco de acompanhamento nem pastas de evidências ou backups. Na cópia original de trabalho, o PDF é localizado em `../documentos/`; num clone do repositório, utiliza-se a cópia pública já versionada em `aplicacao/frontend/public/documentos/`.

Os endpoints de consulta `/api/base`, `/api/state`, `/api/geo/catalog` e `/api/documento` são reescritos para arquivos estáticos. Não existe backend mutável na hospedagem. A alteração do parâmetro de URL não habilita a gestão local no site público.

Atualizações de dados públicos devem ser preparadas como uma nova versão revisada, verificadas e publicadas pelo repositório. Registros de acompanhamento não são enviados automaticamente do computador para a Vercel.

## Abrir a gestão local

No Windows, execute `aplicacao/Instalar.ps1` para preparar o ambiente quando necessário. Depois abra `Abrir painel.cmd`. O endereço é `http://127.0.0.1:8765`.

Inicialmente a aplicação funciona em consulta. Como os dados estão em pasta OneDrive, pause a sincronização antes de habilitar escrita; encerre a sessão e o servidor antes de retomá-la. O aplicativo não altera a configuração do OneDrive. Uma equipe com edição simultânea exige banco central e autenticação, fora desta versão local.

Instruções de operação: [manual](entregas/MANUAL_DE_OPERACAO.md). Backend e restauração: [documentação da API](aplicacao/backend/README.md).

## Dados e cartografia

- [Guia de extração e padronização](LEIA-ME.md).
- [Modelo de dados](modelo_dados.json).
- [Cobertura da extração](cobertura_extracao.csv).
- [Plano aprovado](planejamento/PLANO_DE_IMPLEMENTACAO.md).
- [Cartografia, metadados e limites](dados/geoespaciais/README.md).

O limite municipal publicado provém da API oficial do IBGE, período2022. As referências a redes, instalações e mapas históricos que ainda precisam de validação geográfica permanecem no catálogo como pendentes. Cadastros de microssistemas não foram convertidos em pontos com datum presumido.

Fonte documental original: [PMISB aprovado — Prefeitura de Altamira](https://altamira.pa.gov.br/wp-content/uploads/2023/03/PMISB-ALTAMIRA-APROVADO.pdf). A marca e as fotografias utilizadas pertencem ao documento de2022; sua presença identifica a fonte histórica, sem presumir identidade da gestão atual.

## Verificação

```powershell
npm test
npm run typecheck
cd aplicacao/backend
python -m pytest --basetemp ../../verificacao/dashboard/backend_tmp -q
```

Os testes usam diretórios isolados e nunca alimentam o banco de produção. Dependências, dados runtime, evidências, backups e artefatos temporários são excluídos do Git por `.gitignore`. A pasta pública é gerada por lista permitida; não acrescente evidências privadas a ela.
