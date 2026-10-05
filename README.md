# Solução do desafio de desenvolvimento

Este projeto resolve os três exercícios do arquivo `desafio_dev.docx`: calcular comissões por vendedor, registrar entradas e saídas de estoque e calcular juros por atraso. A implementação usa Python e apenas sua biblioteca padrão, sem pacotes externos.

## Como executar

1. Instale Python 3.10 ou superior, caso ainda não esteja instalado.
2. Extraia o ZIP para uma pasta em que você tenha permissão de escrita.
3. No Windows, dê dois cliques em `INICIAR.bat` para abrir o menu.

Também é possível abrir um terminal na pasta do projeto e executar:

```console
python main.py
```

No menu, escolha `1` para comissões, `2` para estoque ou `3` para juros. Digite `0` para voltar ou encerrar. Se o comando `python` não estiver disponível no Windows, use `py -3` no lugar dele.

## Exercício 1 — Comissões

O programa lê `dados/vendas.json`, aplica a faixa a **cada venda** e soma as comissões por vendedor.

| Valor da venda | Comissão |
| --- | ---: |
| Menor que R$ 100,00 | 0% |
| De R$ 100,00 até menos de R$ 500,00 | 1% |
| A partir de R$ 500,00 | 5% |

Os valores monetários são calculados com `Decimal`. Como o enunciado não define o arredondamento, a solução arredonda a comissão de cada venda para dois decimais antes de somar, elevando meio centavo ao centavo seguinte (`ROUND_HALF_UP`). Por exemplo, R$ 100,50 × 1% = R$ 1,005, pago como R$ 1,01.

Para as 36 vendas fornecidas no enunciado:

| Vendedor | Comissão |
| --- | ---: |
| João Silva | R$ 495,69 |
| Maria Souza | R$ 465,96 |
| Carlos Oliveira | R$ 379,38 |
| Ana Lima | R$ 404,99 |
| **Total** | **R$ 1.746,02** |

Execução independente, com o arquivo padrão ou outro JSON no mesmo formato:

```console
python comissoes.py
python comissoes.py "caminho/novas_vendas.json"
```

## Exercício 2 — Estoque

O primeiro uso importa os cinco produtos de `dados/estoque.json`. Os saldos e o histórico são salvos em `dados/estoque.sqlite3`. Ao reabrir o programa, o estoque continua do saldo anterior; o JSON inicial não substitui os saldos já movimentados.

Cada movimentação registra:

- Identificador numérico único, gerado pelo banco e mantido entre execuções.
- Código do produto, tipo (`entrada` ou `saida`) e descrição informada pelo usuário.
- Quantidade, saldo anterior, saldo final e data com fuso horário.

Quantidades devem ser inteiras e positivas. Produtos inexistentes, descrições vazias e saídas maiores que o saldo são recusados. Uma movimentação é salva integralmente em uma transação: uma falha não altera o saldo nem cria um registro parcial. Escritas simultâneas são serializadas pelo SQLite.

Exemplo: a Caneta Azul (101) começa com 150 unidades. Uma entrada de 20 gera saldo 170; uma saída de 10 gera saldo 160. O programa exibe o identificador e o saldo final imediatamente após cada operação.

Execução independente:

```console
python estoque.py
python estoque.py listar
python estoque.py movimentar 101 entrada 20 "Compra de mercadoria"
python estoque.py movimentar 101 saida 10 "Venda ao cliente"
python estoque.py historico
```

Os exemplos de movimentação acima alteram o estoque salvo. Para usar um banco separado, informe a opção antes do comando:

```console
python estoque.py --banco "dados/exemplo.sqlite3" movimentar 101 entrada 20 "Compra"
```

A opção `--arquivo` permite escolher outro JSON de estoque inicial. Ele só é importado quando o banco ainda não contém produtos.

## Exercício 3 — Juros

O programa recebe o valor original e a data de vencimento. A data do cálculo é obtida automaticamente do relógio local do computador a cada execução.

O enunciado usa os termos juros e multa e não especifica capitalização. A solução adota **juros simples de 2,5% por dia corrido de atraso**, sem multa adicional:

```text
dias de atraso = máximo entre 0 e (hoje − vencimento)
juros = valor original × 0,025 × dias de atraso
total = valor original + juros
```

No vencimento ou antes dele, os juros são zero. O primeiro dia de atraso é o dia seguinte ao vencimento. Os juros são arredondados para centavos ao final do cálculo, com `ROUND_HALF_UP`.

São aceitas datas em `DD/MM/AAAA` ou `AAAA-MM-DD` e valores sem separador de milhar, com ponto ou vírgula decimal. Exemplos: `1000`, `1000.50` ou `1000,50`. Valores negativos e datas inexistentes são recusados.

```console
python juros.py
python juros.py 1000 02/10/2026
```

**Exemplo com data de cálculo em 05/10/2026:** valor R$ 1.000,00, vencimento 02/10/2026, três dias de atraso, juros R$ 75,00 e total R$ 1.075,00. Em outra data, o resultado muda conforme os dias transcorridos.

## Testes

Na pasta do projeto:

```console
python -m unittest -v
```

Os testes cobrem as fronteiras de R$ 100,00 e R$ 500,00, arredondamento, totais do JSON original, entradas e saídas, saldo zero, rejeição sem alteração do banco, identificadores e histórico entre execuções, duas saídas simultâneas, datas atuais e futuras, ano bissexto e entradas inválidas. Os testes de estoque usam bancos temporários e não alteram o estoque de uso do programa.

## Arquivos

| Arquivo | Função |
| --- | --- |
| `main.py` | Menu para acessar os três exercícios |
| `comissoes.py` | Leitura de vendas e cálculo das comissões |
| `estoque.py` | Movimentações, consulta e histórico persistente |
| `juros.py` | Cálculo do atraso, dos juros e do valor total |
| `util.py` | Validação de valores e formatação monetária |
| `test_desafio.py` | Testes automatizados |
| `dados/vendas.json` | Vendas originais do enunciado |
| `dados/estoque.json` | Estoque inicial original do enunciado |
| `INICIAR.bat` | Abertura do menu no Windows |

Não é necessário executar `pip install`. O arquivo de banco é criado automaticamente na primeira abertura do estoque.
