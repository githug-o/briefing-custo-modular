# Matriz de Acompanhamento - MVP Custo Modular

Legenda:

- Sim: existe implementacao funcional basica.
- Parcial: existe base inicial, mas precisa ajuste ou validacao.
- Nao: ainda nao implementado.

## Prioridades imediatas

| Area | Item | Status | Arquivos principais | Proximo passo | Prioridade |
| --- | --- | --- | --- | --- | --- |
| Instalacao/local | Rodar localmente com Streamlit | Sim | `setup_windows.bat`, `run_app.bat`, `app.py` | Testar em maquina real do usuario | Alta |
| Importacao | Upload e leitura de Excel | Sim | `app.py`, `src/importacao_excel.py` | Testar com planilha real completa | Alta |
| Importacao | Validacao de colunas | Parcial | `src/importacao_excel.py` | Melhorar mensagens e validar campos vazios | Alta |
| Importacao | Conversao numerica brasileira | Parcial | `src/normalizacao_texto.py` | Criar testes para valores reais | Alta |
| Banco | Schema SQLite principal | Sim | `src/database.py` | Comparar com campos planejados | Alta |
| Normalizacao | Padronizar texto tecnico | Parcial | `src/normalizacao_texto.py` | Expandir abreviacoes e tratar km | Alta |
| Extracao | Extrair extensao, tensao e trafo | Parcial | `src/extracao_variaveis.py` | Criar testes com descricoes reais | Alta |
| Classificacao | Classificar tipo de servico | Parcial | `src/classificador_servico.py` | Avaliar desempenho nos 29 tipos | Alta |
| Elegibilidade | Bloquear casos fora do MVP | Parcial | `src/recomendador.py`, `app.py` | Explicitar excecoes e mensagens | Alta |
| Recomendacao | Gerar itens para Ramal Rural | Parcial | `src/recomendador.py` | Validar com engenheiro | Alta |
| Edicao | Editar tabelas no Streamlit | Parcial | `app.py` | Melhorar adicionar/remover/opcionais | Media |
| Exportacao | Gerar Excel | Sim | `src/exportador_excel.py` | Validar abas e layout com usuario | Media |
| Historico | Salvar previsao | Parcial | `src/database.py`, `app.py` | Salvar criterios e obras de referencia | Alta |
| IA externa | Fallback OpenAI | Parcial | `src/ia_fallback.py` | Validar schema e lista de tipos | Media |
| Testes | Testes automatizados | Nao | `tests/` | Criar testes de normalizacao e extracao | Alta |
| Backup | Backup local do banco | Nao | `src/database.py`, `app.py` | Criar botao de backup | Alta |
| Documentacao | Regras, roadmap e testes | Parcial | `docs/` | Manter atualizado a cada decisao | Media |

## Lacunas importantes

1. Testes automatizados ainda nao existem.
2. A extracao tecnica precisa ser validada com descricoes reais.
3. A recomendacao precisa validacao de engenharia.
4. O app ainda nao salva criterios usados nem obras de referencia.
5. Ainda nao existe backup manual do banco.
6. Ainda nao existe confirmacao extra antes de substituir a base.
7. Itens opcionais aparecem em aba, nao em modal ou fluxo de selecao.
8. O classificador treina em tempo de uso e nao persiste modelo.
9. A IA externa nao recebe lista controlada dos 29 tipos.
10. Algumas mensagens de bloqueio ainda nao orientam claramente a acao do usuario.

## Risco central

O maior risco do projeto nao esta na interface ou no banco. Esta na qualidade da extracao tecnica e na validacao das regras de recomendacao com engenharia.

## Ordem recomendada de execucao

1. Testar app localmente.
2. Importar planilha real.
3. Criar testes de normalizacao e extracao.
4. Corrigir extracao tecnica com base nos testes.
5. Validar 5 a 10 casos reais de Ramal Rural puro.
6. Ajustar recomendacao.
7. Implementar auditoria mais forte.
8. Implementar backup.
9. Melhorar UX.
10. Evoluir classificador e IA.
