# Resultados dos testes Locust — 22/09/2026

## Protocolo

A comparação principal executou V1 e V2 isoladamente com 1, 10 e 50 usuários, três repetições por combinação. Cada execução durou 300 segundos; os primeiros 60 segundos foram tratados como aquecimento. A ordem foi embaralhada com seed 42. A fase mista executou uma repetição com 1, 10 e 50 usuários, dividindo as chamadas entre V1 e V2.

Os percentis abaixo foram calculados sobre respostas válidas na janela estável, pelo método empírico nearest-rank. Intervalos representam o menor e o maior valor entre as três repetições, não uma média de percentis.

## Comparação principal

| Rota | Usuários | Requisições | Falhas | RPS por repetição | P95 (ms) | P99 (ms) |
|---|---:|---:|---:|---:|---:|---:|
| V1 | 1 | 297 | 0 | 0,40–0,42 | 448–523 | 668–817 |
| V1 | 10 | 2.904 | 0 | 3,96–4,10 | 472–779 | 815–2.903 |
| V1 | 50 | 13.374 | 0 | 18,55–18,59 | 503–518 | 919–2.072 |
| V2 | 1 | 298 | 0 | 0,41–0,42 | 452–495 | 556–2.117 |
| V2 | 10 | 2.955 | 0 | 4,08–4,14 | 493–535 | 595–666 |
| V2 | 50 | 6.634 | 3 HTTP 520 | 8,92–9,41 | 4.026–4.117 | 5.633–11.504 |

Todos os logins da matriz principal foram bem-sucedidos. Não houve HTTP 401. Em V2 com 50 usuários, duas das três repetições apresentaram, respectivamente, duas e uma respostas HTTP 520; a terceira não apresentou falhas. A taxa agregada desse cenário foi de 3/6.634, aproximadamente 0,045%. Os máximos das três repetições ficaram entre 24,7 e 40,3 segundos.

Com 50 usuários, V1 sustentou aproximadamente 18,6 predições/s, enquanto V2 sustentou de 8,9 a 9,4 predições/s. O P95 da V1 permaneceu próximo de 0,5 segundo; o da V2 ficou próximo de 4,1 segundos. Isso evidencia diferença de desempenho do serviço ao executar cada rota na infraestrutura testada. Não representa comparação da qualidade preditiva: MAE, RMSE e R² são métricas separadas, produzidas no conjunto de teste dos modelos.

Três execuções tiveram uma única amostra do contador de usuários abaixo do valor configurado no instante final, durante o encerramento do Locust. Todas observaram todos os usuários distintos e mantiveram o valor nominal nas outras 237 amostras da janela. Portanto, não houve evidência de redução sustentada da concorrência.

## Fase mista

| Usuários | Rota | Requisições | Falhas | RPS | P95 (ms) | P99 (ms) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | V1 | 38 | 0 | 0,16 | 723 | 865 |
| 1 | V2 | 47 | 0 | 0,20 | 1.987 | 19.675 |
| 10 | V1 | 402 | 0 | 1,68 | 2.092 | 6.306 |
| 10 | V2 | 478 | 0 | 1,99 | 2.276 | 7.058 |
| 50 | V1 | 1.640 | 0 | 6,83 | 2.020 | 11.431 |
| 50 | V2 | 1.611 | 0 | 6,71 | 2.381 | 3.184 |

A fase mista teve apenas uma repetição por carga e deve ser tratada como evidência complementar. Não houve falhas ou logins malsucedidos, e a concorrência foi mantida em todos os cenários. A cauda elevada com somente um usuário, sobretudo o P99 da V2, corresponde a uma amostra pequena e a um único valor extremo; não deve ser generalizada sem novas repetições.

## Diagnóstico dos 401

O teste controlado confirmou os seguintes comportamentos da versão revisada:

- token válido: HTTP 200;
- token ausente: HTTP 401, `missing_token`;
- token malformado: HTTP 401, `invalid_token`;
- token expirado: HTTP 401, `expired_token`;
- novo login após a expiração: HTTP 200.

Nenhum 401 ocorreu na nova bateria. O script original autenticava uma vez, não renovava o token de 30 minutos e continuava fazendo predições sem Authorization quando o login inicial falhava. Isso torna expiração e falha de login hipóteses plausíveis para as 179 falhas antigas, mas não permite determinar retrospectivamente qual delas ocorreu sem os arquivos brutos daquela execução.

## Evidência MLOps

Antes e depois da carga, a API informou o mesmo commit de deploy (`81d6fb252cbd1b64af485007896dee366c3977c1`), os mesmos hashes SHA-256 dos artefatos V1 e V2 e as mesmas previsões para a entrada de referência. Ambos os hashes também são iguais aos artefatos do commit original `9b2f7f8`. As duas rotas permaneceram disponíveis com HTTP 200.

Isso demonstra que a nova versão da API foi disponibilizada e rastreada sem substituir os dois artefatos de modelo anteriores. A evidência não deve ser descrita como um registry automatizado ou como avaliação de qualidade preditiva; trata-se de proveniência verificável dos artefatos incorporados ao deploy.

## Artefatos

- Matriz principal: `load_tests/results/20260922-150628-principal-81d6fb2`
- Fase mista: `load_tests/results/20260922-165420-misto-81d6fb2`
- Diagnóstico JWT: `load_tests/results/auth-20260922/auth-evidence.json`
- Evidência MLOps: `load_tests/results/mlops`

Cada diretório de bateria contém CSV bruto por requisição, CSV e histórico do Locust, manifesto, relatório HTML, resumo consolidado e gráficos de P95, P99, throughput e taxa de falhas.
