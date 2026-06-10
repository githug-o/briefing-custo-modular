# Roadmap - Custo Modular

## Diretriz geral

Priorizar seguranca, validacao e estabilidade antes de sofisticacao.

Ordem correta:

1. Fazer rodar local.
2. Fazer importar a planilha real.
3. Fazer extrair variaveis corretamente.
4. Fazer classificar tipos com score.
5. Fazer bloquear corretamente o que nao e elegivel.
6. Fazer recomendar Ramal Rural puro.
7. Fazer editar e exportar Excel.
8. Depois melhorar IA, modelo e UX.

## Fase 1 - Rodar localmente

Objetivo: abrir o sistema no navegador local.

Tarefas:

- validar Python instalado;
- criar ambiente virtual;
- instalar dependencias;
- rodar `streamlit run app.py`;
- validar abertura em `http://localhost:8501`;
- testar `setup_windows.bat` e `run_app.bat`.

Status atual: parcialmente implementado.

## Fase 2 - Importar planilha real

Objetivo: validar ingestao do Excel real.

Tarefas:

- testar upload da planilha real;
- validar colunas obrigatorias;
- melhorar mensagens de erro;
- converter valores numericos brasileiros;
- testar celulas vazias, formulas e valores negativos;
- confirmar se `num_obra` e a chave correta;
- validar se descricoes repetem dentro da mesma obra;
- confirmar modo substituir e modo versionar.

Status atual: implementacao basica existente.

## Fase 3 - Normalizar base historica

Objetivo: transformar linhas de item em obras consolidadas.

Tarefas:

- agrupar por `num_obra`;
- extrair variaveis por obra;
- popular `obras_historicas`;
- popular `itens_obra_historica`;
- popular `catalogo_itens`;
- revisar unidades inferidas;
- revisar comportamento dos itens.

Status atual: implementacao basica existente.

## Fase 4 - Extracao tecnica

Objetivo: extrair variaveis confiaveis de descricoes curtas.

Tarefas:

- criar testes com descricoes reais;
- melhorar extensao MT e BT;
- tratar descricoes com km;
- melhorar tensao MT e BT;
- melhorar quantidade e potencia de transformadores;
- detectar obras compostas;
- detectar excecoes como retirada, deslocamento, recondutoramento e trifaseamento;
- exibir campos ausentes e alertas de forma clara.

Status atual: parcial.

## Fase 5 - Classificacao de servico

Objetivo: prever `tipo_servico_descricao`.

Tarefas:

- avaliar classificador nos tipos reais;
- criar matriz de confusao;
- calibrar limiar de confianca;
- persistir modelo em `models/`;
- evitar treino a cada analise;
- restringir IA externa a lista real de tipos;
- validar resposta da IA com schema.

Status atual: baseline implementado.

## Fase 6 - Elegibilidade do MVP

Objetivo: separar casos elegiveis de excecoes.

Tarefas:

- validar regra de Ramal Rural puro;
- bloquear rede BT/RDU;
- bloquear obras compostas;
- bloquear baixa confianca;
- bloquear base historica insuficiente;
- orientar usuario sobre o motivo do bloqueio;
- permitir correcao manual de campos obrigatorios.

Status atual: parcial.

## Fase 7 - Motor de recomendacao

Objetivo: gerar previsao para Ramal Rural puro.

Tarefas:

- filtrar por tipo, tensao, potencia e extensao;
- usar ate 20 obras semelhantes;
- exigir minimo de 5 obras;
- calcular frequencia de itens;
- separar automaticos e opcionais;
- calcular quantidade sugerida;
- usar maior valor unitario;
- validar resultados com engenheiro.

Status atual: implementacao inicial existente.

## Fase 8 - Editor e exportacao

Objetivo: permitir revisao humana e gerar Excel.

Tarefas:

- melhorar tabelas editaveis;
- permitir adicionar item manual;
- permitir remover item;
- implementar selecao real de opcionais;
- recalcular totais;
- exportar Excel;
- salvar previsao;
- preservar diferenca entre sugestao do sistema e versao final.

Status atual: parcial.

## Fase 9 - Auditoria, backup e operacao local

Objetivo: reduzir risco operacional.

Tarefas:

- criar backup manual do banco;
- salvar criterios usados na recomendacao;
- salvar obras de referencia;
- criar logs basicos;
- adicionar confirmacao antes de substituir base;
- criar tela de detalhe de previsao salva;
- documentar roteiro de recuperacao.

Status atual: pouco implementado.

## Fase 10 - Evolucao futura

Possiveis proximos passos apos validar Ramal Rural:

- expandir para `EXTENSAO REDE sem PE - GRUPO B`;
- expandir para `EXT RD + EQUIP + MELHORIA`;
- enriquecer catalogo de itens;
- aprender com edicoes dos engenheiros;
- criar login simples local se necessario;
- avaliar PostgreSQL local se houver concorrencia real;
- manter diretriz sem Azure enquanto custo recorrente for restricao.
