from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS importacoes_base (
                id_importacao INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_arquivo TEXT NOT NULL,
                data_importacao TEXT NOT NULL,
                versao_importacao TEXT NOT NULL,
                qtd_linhas INTEGER,
                qtd_obras INTEGER,
                status TEXT NOT NULL,
                mensagem_validacao TEXT
            );

            CREATE TABLE IF NOT EXISTS obras_historicas (
                id_obra INTEGER PRIMARY KEY AUTOINCREMENT,
                id_importacao INTEGER NOT NULL,
                num_projeto TEXT,
                num_obra TEXT NOT NULL,
                descricao_original TEXT,
                descricao_normalizada TEXT,
                tipo_servico_real TEXT,
                tip_servico TEXT,
                extensao_mt_m REAL,
                extensao_bt_m REAL,
                tensao_mt_kv REAL,
                tensao_bt_v TEXT,
                possui_trafo INTEGER,
                qtd_trafo INTEGER,
                potencia_trafo_kva REAL,
                fase TEXT,
                possui_rede_mt INTEGER,
                possui_rede_bt INTEGER,
                possui_rdu INTEGER,
                rede_rural_indicador INTEGER,
                possui_retirada INTEGER,
                possui_recondutoramento INTEGER,
                possui_deslocamento INTEGER,
                possui_trifaseamento INTEGER,
                elegivel_previsao INTEGER,
                ordem_obra_importacao INTEGER,
                FOREIGN KEY(id_importacao) REFERENCES importacoes_base(id_importacao)
            );

            CREATE TABLE IF NOT EXISTS itens_obra_historica (
                id_item_obra INTEGER PRIMARY KEY AUTOINCREMENT,
                id_obra INTEGER NOT NULL,
                id_importacao INTEGER NOT NULL,
                num_obra TEXT NOT NULL,
                tip_item_obra TEXT,
                cod_item_obra TEXT,
                des_item_obra TEXT,
                qtd_item_obra REAL,
                val_unitario REAL,
                val_total REAL,
                tuc TEXT,
                tb TEXT,
                ordem_linha_importacao INTEGER,
                FOREIGN KEY(id_obra) REFERENCES obras_historicas(id_obra),
                FOREIGN KEY(id_importacao) REFERENCES importacoes_base(id_importacao)
            );

            CREATE TABLE IF NOT EXISTS catalogo_itens (
                cod_item_obra TEXT PRIMARY KEY,
                des_item_obra TEXT,
                tip_item_obra TEXT,
                unidade_medida_inferida TEXT,
                grupo_item TEXT,
                subgrupo_item TEXT,
                ativo INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS previsoes (
                id_previsao INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao_input TEXT NOT NULL,
                tipo_servico_previsto TEXT,
                score_classificacao REAL,
                status_previsao TEXT,
                data_criacao TEXT NOT NULL,
                data_exportacao TEXT
            );

            CREATE TABLE IF NOT EXISTS variaveis_previsao (
                id_previsao INTEGER PRIMARY KEY,
                extensao_mt_m REAL,
                extensao_bt_m REAL,
                tensao_mt_kv REAL,
                tensao_bt_v TEXT,
                qtd_trafo INTEGER,
                potencia_trafo_kva REAL,
                fase TEXT,
                alertas TEXT,
                campos_pendentes TEXT,
                FOREIGN KEY(id_previsao) REFERENCES previsoes(id_previsao)
            );

            CREATE TABLE IF NOT EXISTS itens_previsao (
                id_item_previsao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_previsao INTEGER NOT NULL,
                cod_item_obra TEXT,
                des_item_obra TEXT,
                tip_item_obra TEXT,
                unidade_medida_inferida TEXT,
                qtd_sugerida_sistema REAL,
                val_unitario_sugerido REAL,
                val_total_sugerido REAL,
                qtd_final_engenheiro REAL,
                val_unitario_final REAL,
                val_total_final REAL,
                origem_item TEXT,
                acao_usuario TEXT,
                FOREIGN KEY(id_previsao) REFERENCES previsoes(id_previsao)
            );

            CREATE INDEX IF NOT EXISTS idx_obras_tipo ON obras_historicas(tipo_servico_real);
            CREATE INDEX IF NOT EXISTS idx_obras_num ON obras_historicas(num_obra);
            CREATE INDEX IF NOT EXISTS idx_itens_obra ON itens_obra_historica(id_obra);
            CREATE INDEX IF NOT EXISTS idx_itens_cod ON itens_obra_historica(cod_item_obra);
            """
        )


def resetar_base_historica(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM itens_obra_historica")
    conn.execute("DELETE FROM obras_historicas")
    conn.execute("DELETE FROM catalogo_itens")
    conn.execute("DELETE FROM importacoes_base")


def tabela_para_df(query: str, params: Iterable | None = None) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params or [])


def carregar_obras_historicas() -> pd.DataFrame:
    return tabela_para_df("SELECT * FROM obras_historicas")


def carregar_catalogo() -> pd.DataFrame:
    return tabela_para_df("SELECT * FROM catalogo_itens WHERE ativo = 1 ORDER BY des_item_obra")


def resumo_base() -> dict:
    with get_connection() as conn:
        linhas = conn.execute("SELECT COUNT(*) FROM itens_obra_historica").fetchone()[0]
        obras = conn.execute("SELECT COUNT(*) FROM obras_historicas").fetchone()[0]
        itens = conn.execute("SELECT COUNT(*) FROM catalogo_itens").fetchone()[0]
        importacoes = conn.execute("SELECT COUNT(*) FROM importacoes_base").fetchone()[0]
    return {"linhas": linhas, "obras": obras, "itens": itens, "importacoes": importacoes}


def salvar_previsao(
    descricao_input: str,
    tipo_servico_previsto: str,
    score_classificacao: float,
    status_previsao: str,
    variaveis: dict,
    itens: pd.DataFrame,
) -> int:
    from datetime import datetime
    import json

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO previsoes
            (descricao_input, tipo_servico_previsto, score_classificacao, status_previsao, data_criacao)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                descricao_input,
                tipo_servico_previsto,
                float(score_classificacao or 0),
                status_previsao,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        id_previsao = cur.lastrowid
        conn.execute(
            """
            INSERT INTO variaveis_previsao
            (id_previsao, extensao_mt_m, extensao_bt_m, tensao_mt_kv, tensao_bt_v, qtd_trafo,
             potencia_trafo_kva, fase, alertas, campos_pendentes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_previsao,
                variaveis.get("extensao_mt_m"),
                variaveis.get("extensao_bt_m"),
                variaveis.get("tensao_mt_kv"),
                variaveis.get("tensao_bt_v"),
                variaveis.get("qtd_trafo"),
                variaveis.get("potencia_trafo_kva"),
                variaveis.get("fase"),
                json.dumps(variaveis.get("alertas", []), ensure_ascii=False),
                json.dumps(variaveis.get("campos_ausentes", []), ensure_ascii=False),
            ),
        )

        if itens is not None and not itens.empty:
            registros = []
            for _, row in itens.iterrows():
                registros.append(
                    (
                        id_previsao,
                        str(row.get("cod_item_obra", "")),
                        str(row.get("des_item_obra", "")),
                        str(row.get("tip_item_obra", "")),
                        str(row.get("unidade_medida_inferida", "")),
                        float(row.get("qtd_sugerida_sistema", 0) or 0),
                        float(row.get("val_unitario_sugerido", 0) or 0),
                        float(row.get("val_total_sugerido", 0) or 0),
                        float(row.get("qtd_final_engenheiro", 0) or 0),
                        float(row.get("val_unitario_final", 0) or 0),
                        float(row.get("val_total_final", 0) or 0),
                        str(row.get("origem_item", "automatico")),
                        str(row.get("acao_usuario", "mantido")),
                    )
                )
            conn.executemany(
                """
                INSERT INTO itens_previsao
                (id_previsao, cod_item_obra, des_item_obra, tip_item_obra, unidade_medida_inferida,
                 qtd_sugerida_sistema, val_unitario_sugerido, val_total_sugerido, qtd_final_engenheiro,
                 val_unitario_final, val_total_final, origem_item, acao_usuario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                registros,
            )
        return int(id_previsao)


def carregar_historico_previsoes() -> pd.DataFrame:
    return tabela_para_df("SELECT * FROM previsoes ORDER BY id_previsao DESC")
