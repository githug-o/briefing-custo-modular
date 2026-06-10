# Orçamento de Obras - MVP Local

Sistema local em Python + Streamlit + SQLite para importar uma base Excel, interpretar descrições curtas de obras e gerar uma previsão editável de materiais, mão de obra e taxas.

## Escopo desta primeira versão

- Roda localmente no notebook ou em máquina interna.
- Importa planilha Excel histórica.
- Permite escolher entre substituir a base ou criar nova versão.
- Extrai variáveis técnicas da descrição.
- Classifica o tipo de serviço com modelo local e fallback opcional de IA.
- Gera previsão automática completa apenas para `CONSTR. DE RAMAL RURAL` puro.
- Para outros tipos, classifica e bloqueia previsão automática completa.
- Exibe tabelas editáveis para materiais, mão de obra e taxas.
- Exporta Excel com abas de resumo, materiais, mão de obra, taxas e auditoria.
- Salva previsões no banco SQLite local.

## Estrutura

```text
orcamento_obras_local/
├── app.py
├── requirements.txt
├── setup_windows.bat
├── run_app.bat
├── .env.example
├── data/
│   ├── app.db
│   ├── raw/planilhas_importadas/
│   └── backups/
├── exports/orcamentos/
├── models/
├── logs/
└── src/
    ├── classificador_servico.py
    ├── database.py
    ├── exportador_excel.py
    ├── extracao_variaveis.py
    ├── ia_fallback.py
    ├── importacao_excel.py
    ├── normalizacao_texto.py
    ├── recomendador.py
    └── utils.py
```

## Instalação rápida no Windows

1. Instale Python 3.11 ou superior.
2. Extraia este projeto em uma pasta simples, por exemplo:

```text
C:\Projetos\orcamento_obras_local
```

3. Dê dois cliques em:

```text
setup_windows.bat
```

4. Depois dê dois cliques em:

```text
run_app.bat
```

5. O sistema abrirá no navegador em:

```text
http://localhost:8501
```

## Instalação manual

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois rode novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## IA externa

O uso de IA externa é opcional.

Para usar OpenAI como fallback:

1. Copie `.env.example` para `.env`.
2. Preencha:

```text
OPENAI_API_KEY=sua_chave_aqui
```

Sem chave, o sistema continua funcionando com regras locais e modelo local.

## Primeiro teste recomendado

1. Abra o app.
2. Vá em `Importar base`.
3. Faça upload da planilha histórica.
4. Escolha `Substituir base histórica atual` no primeiro teste.
5. Vá em `Nova previsão`.
6. Teste a descrição:

```text
CONSTRUÇÃO DE 1000M DE RDR MT 19,9KV COM INSTALAÇÃO DE 01 TRAFO 15KVA
```

7. Valide as variáveis extraídas.
8. Gere a previsão.
9. Edite algum valor.
10. Exporte Excel.

## Observações importantes

- O banco local fica em `data/app.db`.
- As planilhas importadas são copiadas para `data/raw/planilhas_importadas`.
- O sistema ainda é MVP; as regras de extração e recomendação serão ajustadas conforme testes reais.
- Não use o Excel exportado como orçamento final sem revisão do engenheiro.
