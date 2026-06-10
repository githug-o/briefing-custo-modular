# Regras de Negocio - Custo Modular

## Objetivo do sistema

O Custo Modular e um assistente local de pre-orcamento para obras eletricas de distribuicao.

O sistema deve apoiar o engenheiro de planejamento na geracao inicial de materiais, mao de obra e taxas a partir de:

- uma descricao curta da obra;
- uma base historica em Excel;
- regras locais de extracao, classificacao e recomendacao.

O sistema nao deve fechar orcamento automaticamente. Toda previsao precisa de revisao humana.

## Fluxo principal

1. O usuario importa uma planilha historica em Excel.
2. O sistema valida as colunas obrigatorias.
3. O sistema grava obras, itens e catalogo no SQLite local.
4. O usuario informa uma descricao curta de nova obra.
5. O sistema normaliza o texto.
6. O sistema extrai variaveis tecnicas.
7. O sistema classifica o tipo de servico.
8. O usuario valida ou corrige as variaveis.
9. O sistema gera previsao somente se o caso for elegivel.
10. O engenheiro edita quantidades e valores.
11. O sistema exporta Excel e pode salvar a previsao no banco local.

## Escopo do MVP

A previsao automatica completa esta habilitada somente para:

```text
CONSTR. DE RAMAL RURAL
```

Regra inicial para considerar Ramal Rural puro:

```text
construcao + rede MT + transformador + sem rede BT/RDU
```

Outros tipos de servico devem ser classificados e ter variaveis extraidas, mas a previsao automatica deve ser bloqueada no MVP.

## Bloqueios obrigatorios

O sistema deve bloquear a previsao automatica quando:

- a confianca da classificacao for baixa;
- o tipo de servico nao for elegivel no MVP;
- faltar extensao MT quando ela for obrigatoria;
- faltar potencia do transformador quando ela for obrigatoria;
- houver rede BT ou RDU no caso de Ramal Rural puro;
- houver excecoes como retirada, deslocamento, recondutoramento ou trifaseamento;
- houver menos de 5 obras semelhantes na base historica.

## Criterios de obras semelhantes

Para gerar recomendacao, o sistema deve buscar obras historicas semelhantes usando:

- mesmo tipo de servico;
- mesma tensao MT;
- mesma potencia de transformador;
- faixa de extensao MT;
- ate 20 obras de referencia.

Tolerancia adaptativa inicial:

- ate 500 m: +/- 30%;
- de 501 m a 1500 m: +/- 25%;
- acima de 1500 m: +/- 20%;
- fallback ate +/- 50% se a base for insuficiente.

Regra minima:

```text
minimo de 5 obras semelhantes
```

## Criterios de itens

Itens devem ser separados em:

- MATERIAL;
- MAO-DE-OBRA;
- TAXAS.

Regras iniciais:

- frequencia historica >= 40%: item automatico;
- frequencia entre 15% e 39%: item opcional;
- frequencia abaixo de 15%: ignorar no MVP;
- valor unitario sugerido: maior valor unitario entre as obras semelhantes;
- quantidade final e valor final sempre podem ser editados pelo engenheiro.

O sistema deve preservar:

- sugestao original do sistema;
- versao final editada pelo engenheiro.

## Calculo de quantidade

Itens proporcionais a extensao:

```text
quantidade_sugerida = mediana(quantidade_historica / extensao_historica) * extensao_nova
```

Itens proporcionais ao transformador:

```text
quantidade_sugerida = mediana(quantidade_historica / qtd_trafo_historica) * qtd_trafo_nova
```

Itens fixos, taxas e administrativos:

```text
quantidade_sugerida = mediana historica da quantidade
```

## Premissas importantes

- A planilha historica esta no nivel de item de obra.
- Uma obra pode ter varias linhas.
- `num_obra` e a chave de agrupamento da obra.
- `cod_item_obra` e tratado como identificador confiavel do item.
- A planilha nao possui unidade de medida formal.
- Unidade e comportamento dos itens precisam ser inferidos e validados.
- SQLite e suficiente para o MVP local com poucos usuarios.
- IA externa e fallback opcional, nao motor principal.
- O projeto deve permanecer local-first, sem Azure no MVP.

## Pontos que precisam validacao de engenharia

- Regra de Ramal Rural puro.
- Lista de excecoes bloqueadas.
- Tolerancias de extensao.
- Minimo de 5 obras semelhantes.
- Frequencia de 40% para itens automaticos.
- Frequencia de 15% a 39% para opcionais.
- Uso do maior valor unitario como criterio conservador.
- Unidade dos principais itens.
- Comportamento dos itens: por metro, por trafo ou fixo.
- Tratamento de TAXAS.
- Codigos de transformador por potencia.
