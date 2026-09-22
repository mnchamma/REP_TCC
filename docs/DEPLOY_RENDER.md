# Retomada do deploy existente

Serviço: REP_TCC, `srv-d8g3vs6q1p3s73ctl8gg`.
URL: https://rep-tcc.onrender.com
Repositório: https://github.com/mnchamma/REP_TCC
Commit original observado: `9b2f7f8`.

## Estado observado nesta preparação

Em 22/09/2026, duas consultas GET de 90 segundos expiraram sem resposta. O navegador mostrou a página intermediária do Render, “Application loading”. Os logs autenticados do Render, às 08:43:10 no horário exibido pelo painel, confirmaram encerramento durante a importação de `app.database.mongo`: `pymongo.errors.ConfigurationError: The DNS query name does not exist: _mongodb._tcp.cluster0.nh4s3c3.mongodb.net.` O rótulo Live refere-se ao último deploy bem-sucedido, de cerca de quatro meses atrás, e não comprova que a instância atual inicializou. Falta verificar no Atlas se o cluster está pausado, removido ou se a URI mudou. A falha DNS atual não explica retrospectivamente os 179 erros 401.

## Verificação e publicação

Verificação posterior no Atlas: `Cluster0` estava automaticamente pausado por inatividade. Após a autorização do usuário para acessar e retomar o cluster, o painel passou a indicar provisionamento; plano FREE, AWS São Paulo (sa-east-1), MongoDB 8.0.24. A restauração terminou e o painel passou a mostrar conexões. A aplicação então avançou além da inicialização do MongoDB e falhou no PostgreSQL.

Às 08:53:14 (horário exibido pelo Render), os logs indicaram `OperationalError: failed to resolve host 'dpg-d8g3isuk1jcs73d5mivg-a'`, seguido de `Application startup failed`. O banco não apareceu no inventário/busca do Render. A conexão externa usando a configuração local também falhou, com encerramento inesperado de SSL. Foi preparado, sem criação até autorização, um substituto chamado `tcc-postgres-retest`: plano FREE, 1 GB, região Oregon, projeto existente/Production. O plano gratuito expira em 30 dias e não recupera cadastros do banco anterior.

1. No painel do serviço, consultar Events e Logs. Procurar falha de conexão PostgreSQL no startup, importação de dependências, falta de arquivos de modelos ou reinício por memória. Não compartilhar tokens/chaves: a versão original imprime esses segredos em logs de autenticação.
2. Conferir presença de SECRET_KEY, POSTGRES_URL e MONGO_URL sem revelar valores. Manter a mesma SECRET_KEY entre workers e deploys, salvo rotação planejada. Verificar se o PostgreSQL está ativo e se MongoDB Atlas permite acesso do serviço.
3. Usar o Dockerfile existente (Python 3.10), com os dois arquivos joblib. Não treinar modelos no build. `.dockerignore` exclui ambientes locais, credenciais .env e resultados de carga.
4. Rodar testes e preflight. Capturar evidência pré-deploy se o serviço original estiver disponível.
5. Revisar diff, publicar os arquivos revisados no repositório e acompanhar o deploy do commit exato no Render. Nenhuma alteração de plano pago é necessária por padrão.
6. Configurar `/health` como health check após disponibilização da rota. Esse endpoint indica que o processo está pronto; não é uma verificação contínua dos bancos.
7. Abrir `/`, `/docs`, testar login e predições V1/V2, consultar `/api/v1/models` autenticado e capturar evidência pós-deploy.
8. Somente iniciar a bateria após esses passos. Não alterar recursos, variáveis nem commit durante a medição.

## Alterações preparadas

- Frontend servido pela própria API e URLs relativas, evitando chamadas ao localhost em produção.
- Motivos de autenticação diferenciados, sem logar segredos.
- Endpoint autenticado de proveniência de modelos e hash/commit nas novas predições persistidas.
- Harness Locust separado, mantendo o original local para análise histórica.

## Recuperação concluída em 22/09/2026

- PostgreSQL criado com autorização: `tcc-postgres-retest`, ID `dpg-dap6pregekts7380d14g-a`, PostgreSQL 18, plano gratuito, Oregon, expiração informada em 22/10/2026.
- POSTGRES_URL atualizado no Render para conexão interna do novo banco. O arquivo `.env` antigo local não foi alterado; suas credenciais PostgreSQL não representam mais o banco atual.
- Commit revisado `81d6fb252cbd1b64af485007896dee366c3977c1` publicado e deploy `dep-dap7phe7bikc73bh90rg` confirmado Live.
- O Atlas continha somente um IP antigo na lista de acesso. As faixas informadas pelo painel do Render, `74.220.48.0/24` e `74.220.56.0/24`, foram adicionadas com autorização explícita. As faixas são compartilhadas por serviços Render da região; autenticação e TLS permanecem exigidos.
- Antes da liberação de rede, predições retornavam HTTP 500 após aproximadamente 30 segundos, com `ServerSelectionTimeoutError` e falha de handshake TLS. Após a liberação, login e predições V1/V2 retornaram HTTP 200. Evidências: `load_tests/results/preflight-before-network-fix.json` e `preflight.json`.
- Usuário de carga criado. Credenciais ficam somente em `.env.loadtest`, ignorado pelo Git e pelo Docker.
- Evidência MLOps em `load_tests/results/mlops`: hashes dos artefatos do commit original iguais aos atuais e aos retornados pela API; ambas as rotas respondem com seus respectivos modelos.

Os tempos de preflight não são resultados de desempenho. O piloto e a bateria Locust produzem diretórios próprios. Os testes locais com servidor simulado validam somente o instrumento de coleta.
