# Roteiro de Testes Manuais - Custo Modular

Este roteiro serve para validar o MVP sem depender de automacao.

## 1. Teste de instalacao local

Objetivo: confirmar que o sistema abre no computador do usuario.

Passos:

1. Abrir a pasta do projeto.
2. Executar `setup_windows.bat`.
3. Confirmar que a pasta `.venv` foi criada.
4. Confirmar que as dependencias foram instaladas sem erro.
5. Executar `run_app.bat`.
6. Confirmar que o navegador abre em `http://localhost:8501`.

Resultado esperado:

- app abre sem erro;
- menu lateral aparece;
- telas `Importar base`, `Nova previsao` e `Historico` aparecem.

## 2. Teste de importacao da planilha real

Objetivo: confirmar que a base historica e carregada corretamente.

Passos:

1. Abrir a tela `Importar base`.
2. Selecionar a planilha real.
3. Escolher `Substituir base historica atual` no primeiro teste controlado.
4. Clicar em `Importar planilha`.
5. Aguardar conclusao.
6. Verificar resumo exibido na tela.

Resultado esperado:

- importacao concluida sem erro;
- quantidade de linhas importadas faz sentido;
- quantidade de obras faz sentido;
- quantidade de itens no catalogo faz sentido.

Verificar tambem:

- arquivo copiado para `data/raw/planilhas_importadas`;
- banco `data/app.db` criado;
- app continua responsivo.

## 3. Teste de colunas obrigatorias

Objetivo: verificar se o sistema bloqueia planilhas invalidas.

Passos:

1. Criar uma copia de teste da planilha.
2. Remover uma coluna obrigatoria, por exemplo `num_obra`.
3. Tentar importar.

Resultado esperado:

- sistema nao importa;
- mensagem informa a coluna ausente;
- banco nao fica parcialmente contaminado.

## 4. Teste de nova previsao elegivel

Objetivo: testar um caso de Ramal Rural puro.

Descricao sugerida:

```text
CONSTRUCAO DE 1000M DE RDR MT 19,9KV COM INSTALACAO DE 01 TRAFO 15KVA
```

Passos:

1. Abrir `Nova previsao`.
2. Informar a descricao.
3. Clicar em `Analisar descricao`.
4. Conferir variaveis extraidas.
5. Corrigir campos se necessario.
6. Clicar em `Confirmar variaveis e gerar previsao`.

Resultado esperado:

- tipo previsto: `CONSTR. DE RAMAL RURAL`;
- extensao MT: proxima de 1000;
- tensao MT: proxima de 19.9;
- qtd trafo: 1;
- potencia trafo: 15;
- previsao gerada se houver base semelhante suficiente.

## 5. Teste de bloqueio por rede BT

Objetivo: confirmar que obra composta nao gera previsao automatica indevida.

Descricao sugerida:

```text
CONSTRUCAO DE 239M DE REDE MT 13,8KV E 561M DE REDE BT 380/220V COM INSTALACAO DE 01 TRAFO 15KVA
```

Resultado esperado:

- sistema detecta rede BT;
- previsao automatica e bloqueada;
- usuario entende o motivo do bloqueio.

## 6. Teste de bloqueio por excecao

Descricoes sugeridas:

```text
RECONDUTORAMENTO DE 540M DE REDE BT
DESLOCAMENTO DE 173M DE REDE MT 13,8KV
RETIRADA DE REDE MT COM TRANSFORMADOR
```

Resultado esperado:

- sistema identifica excecao;
- nao gera previsao automatica completa;
- classificacao e variaveis ainda aparecem quando possivel.

## 7. Teste de campos ausentes

Objetivo: verificar comportamento quando faltam dados obrigatorios.

Descricao sugerida:

```text
CONSTRUCAO DE RDR MT 19,9KV COM INSTALACAO DE TRAFO
```

Resultado esperado:

- extensao MT ausente deve ser sinalizada;
- potencia do transformador ausente deve ser sinalizada;
- usuario deve poder preencher manualmente;
- previsao so deve seguir apos correcao dos campos necessarios.

## 8. Teste de edicao da previsao

Objetivo: validar revisao humana.

Passos:

1. Gerar uma previsao elegivel.
2. Alterar quantidade final de um material.
3. Alterar valor unitario final.
4. Verificar se total final e recalculado.
5. Repetir para mao de obra e taxas.

Resultado esperado:

- valores sugeridos permanecem visiveis;
- valores finais editados sao usados no resumo;
- total geral reflete as edicoes.

## 9. Teste de exportacao Excel

Objetivo: confirmar que o arquivo final e gerado corretamente.

Passos:

1. Gerar previsao.
2. Editar algum item.
3. Clicar em `Exportar Excel`.
4. Abrir o arquivo baixado.

Resultado esperado:

- arquivo abre no Excel;
- abas existem:
  - Resumo;
  - Materiais;
  - Mao de obra;
  - Taxas;
  - Auditoria.
- totais fazem sentido.

## 10. Teste de salvamento no historico

Objetivo: confirmar persistencia da previsao.

Passos:

1. Gerar uma previsao.
2. Clicar em `Salvar previsao no banco local`.
3. Abrir a tela `Historico`.

Resultado esperado:

- previsao aparece na lista;
- tipo, score e status aparecem;
- nao ha erro no banco.

## 11. Registro dos resultados

Para cada teste, registrar:

- data do teste;
- descricao usada;
- resultado esperado;
- resultado obtido;
- erro encontrado;
- prioridade de correcao;
- observacoes do engenheiro.

Modelo:

| Data | Teste | Descricao | Resultado | Problema | Prioridade | Observacao |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |
