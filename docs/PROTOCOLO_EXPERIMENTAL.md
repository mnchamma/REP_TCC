# Reexecução dos experimentos do TCC

## Perguntas e limites

1. Como concorrência afeta P50/P90/P95/P99, taxa de erros e throughput de V1 e V2?
2. Os 401 decorrem de login inicial malsucedido, expiração, assinatura inválida ou ausência de token?
3. É possível rastrear o artefato de cada versão e continuar usando V1 depois de disponibilizar V2?

Latência e throughput medem o serviço completo (rede, autenticação, inferência e gravação no MongoDB). Não medem isoladamente o algoritmo. MAE/RMSE/R² pertencem à avaliação preditiva em dados de teste e não devem ser interpretados a partir de latência. A otimização dos modelos continua fora do escopo.

## Evidência histórica

O script original `load_tests/locustfile.py` foi preservado. Ele autentica uma vez por usuário, continua sem Authorization quando o login falha e não renova tokens. A API original usa expiração de 30 minutos. Esses comportamentos são hipóteses verificáveis; não demonstram retrospectivamente a causa das 179 falhas. Guardar os CSV/HTML/logs originais, se disponíveis. Sem eles, declarar que a causa histórica não pôde ser determinada.

## Ambiente a registrar

- URL, commit efetivamente publicado, data/hora UTC e região do Render.
- Tipo de instância, CPU, memória, número de processos/workers e configuração de autoscaling.
- Provedor/região/plano de PostgreSQL e MongoDB; latência pode incluir ambos.
- Máquina/rede do gerador, versões de Python e Locust, CPU do gerador durante teste.
- Artefatos e hashes, seed, payload, espera de 1 a 3 segundos, taxa de entrada de 1 usuário/s.
- Reinícios, cold start e alterações de infraestrutura. Não misturar cold start à janela estável.

Não fazer deploy nem mudar configuração durante uma bateria comparativa.

## Sequência

1. Preflight: disponibilidade, login e uma predição válida em cada versão. Se falhar, resolver antes da carga.
2. Piloto de 1 usuário: conferir registros e relatórios.
3. Matriz principal: 1, 10, 50 usuários × V1 isolada, V2 isolada e mista × 3 repetições. Execuções sequenciais com ordem embaralhada por seed registrada. Cada execução dura 360 segundos; descartar os primeiros 60 segundos. Tempo nominal total: 162 minutos, além de finalização.
4. Conferir se todos os usuários autenticaram. Falha de login que encerra usuário reduz carga efetiva: sinalizar a execução e não tratá-la como evidência de capacidade no nível nominal.
5. Diagnóstico de expiração separado: `no_renew` e `renew`, 1 usuário, 2100 segundos cada, mantendo TTL real de 30 minutos. Correlacionar 401 com tempo restante do token. Testes locais com token expirado validam o mecanismo, mas não substituem essa evidência em nuvem.
6. Diagnóstico de comportamento legado: `legacy` mantém chamadas sem token após falha de login, como o original. Comparar motivos de erro. Não provocar alteração de senhas/chaves de produção.
7. Preservar CSV bruto, histórico Locust, HTML, manifesto e logs. Analisar falhas mesmo que o processo termine com código 1; não transformar falhas em sucesso para obter relatório limpo.

## Execução no PowerShell (a partir de tcc-api)

O ambiente de testes fica em `../.venv-tools`, separado do runtime Docker Python 3.10 da API. As credenciais são lidas de TEST_USERNAME/TEST_PASSWORD ou do teste local original, nunca de argumentos de linha de comando.

```powershell
../.venv-tools/Scripts/python.exe load_tests/preflight.py
../.venv-tools/Scripts/python.exe load_tests/run_matrix.py --host https://rep-tcc.onrender.com --users 1 --versions mixed --repeats 1 --seconds 90 --warmup 30 --label piloto-COMMIT
../.venv-tools/Scripts/python.exe load_tests/run_matrix.py --host https://rep-tcc.onrender.com --label revisada-COMMIT
../.venv-tools/Scripts/python.exe load_tests/run_matrix.py --host https://rep-tcc.onrender.com --users 1 --versions mixed --repeats 1 --seconds 2100 --warmup 60 --auth no_renew --label expiracao-COMMIT
../.venv-tools/Scripts/python.exe load_tests/run_matrix.py --host https://rep-tcc.onrender.com --users 1 --versions mixed --repeats 1 --seconds 2100 --warmup 60 --auth renew --label renovacao-COMMIT
../.venv-tools/Scripts/python.exe load_tests/analyze.py load_tests/results/PASTA_DA_BATERIA
```

## Métricas e interpretação

`summary.csv` separa endpoint, cenário e repetição. Inclui P50/P90/P95/P99 de sucessos e de todas as respostas, máximo, requisições/s totais, sucessos/s, erros, códigos HTTP e motivos. Percentis calculados pelo método empírico nearest-rank com tempos brutos; os percentis nativos do Locust usam histogramas e podem diferir por arredondamento. A janela analítica inclui apenas requisições iniciadas e concluídas na janela estável; requisições que atravessam seus limites ficam preservadas no CSV bruto e no relatório integral do Locust.

Gráficos mostram cada repetição; não fazer média de percentis como se fosse percentil global. P99 de amostra pequena deve ser interpretado com cautela. Comparação isolada identifica diferenças por rota; comparação mista avalia disputa pelos mesmos recursos. O modelo fechado do Locust, com espera entre chamadas, reduz a taxa de chegada quando respostas ficam lentas; usuários simultâneos não são uma taxa de requisições fixa.

Para causa dos 401, contar separadamente `missing_token`, `expired_token`, `invalid_token`, `invalid_subject` e falhas de login. `invalid_token` não prova chave divergente: inclui token malformado e outras falhas de validação. Correlacionar idade do token e logs do deploy. Nunca registrar token, senha ou SECRET_KEY.

## Demonstração MLOps

O endpoint autenticado `/api/v1/models` informa hashes dos arquivos realmente presentes, nome do modelo, rotas, métricas preditivas já existentes e commit de deploy. Novas predições persistidas incluem hash e commit. Isso permite rastreabilidade; não constitui sozinho um registry com promoção automática.

Capturar antes/depois do deploy: commit, hashes e predições de V1 e V2 com a mesma entrada. V1 deve manter o hash e resposta (tolerância numérica definida), enquanto V2 permanece acessível por rota própria. Manter arquivos separados e revisar diff antes do deploy. O treinador original sobrescreve ambos os arquivos: não executá-lo para publicar uma nova versão sem alterar sua política de saída. Para uma futura V3, criar um novo arquivo/rota e metadados sem sobrescrever V1/V2. Demonstrar rollback pelo commit anterior apenas em janela controlada, sem misturá-lo à carga.

## Referências operacionais

- https://docs.locust.io/en/stable/configuration.html
- https://render.com/docs/free
- https://render.com/docs/deploys

O Render documenta suspensão de serviços gratuitos após inatividade e expiração do PostgreSQL gratuito. Verificar o estado real no painel; não atribuir indisponibilidade a uma dessas causas sem logs.
