# Adendo autorizado: publicação pública

Em05/11/2026, durante a implementação local aprovada, o usuário forneceu o repositório `https://github.com/henriquegsantos149/acompaltamira` e solicitou hospedagem pública via Vercel.

A entrega passa a incluir dois produtos derivados do mesmo frontend:

- Gestão local com sete módulos e API Python/SQLite, conforme o plano original.
- Consulta pública com seis módulos, gerada em `dist-public`, sem renderização de administração e sem backend de gravação hospedado.

A publicação usa `vercel.json` na raiz do repositório, com quatro reescritas exatas para arquivos públicos. Rotas de mutação não são implementadas na hospedagem. O histórico real, os arquivos comprobatórios privados, bancos e backups locais não fazem parte do pacote público.

A base pública inicial conserva o conteúdo documental do plano e contexto cartográfico oficial. Os três modelos de acompanhamento permanecem vazios. O empacotamento remove caminhos locais de metadados, verifica o PDF e mantém origem e data das camadas. Atualizações públicas futuras exigem nova versão revisada e publicação; não há sincronização automática do banco local.

O repositório inclui o código da gestão local e dados documentais públicos, mas `.gitignore` exclui dependências, segredos, estado de hospedagem, banco, evidências, backups e arquivos temporários. `.vercelignore` também limita o envio do projeto à hospedagem.

Verificação antes do primeiro envio:24 testes de interface,7 de empacotamento, TypeScript e build público aprovados; revisão independente sem achados abertos. A confirmação da URL final e do acesso anônimo será registrada na área local de verificação após o deploy.
