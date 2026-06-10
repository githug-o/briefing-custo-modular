from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from .database import BASE_DIR, get_connection, init_db, resetar_base_historica
from .extracao_variaveis import extrair_variaveis_tecnicas
from .normalizacao_texto import parse_float
from .utils import inferir_unidade_medida

COLUNAS_OBRIGATORIAS = [
    "num_projeto",
    "num_obra",
    "descricao",
    "tip_servico",
    "tipo_servico_descricao",
    "tip_item_obra",
    "cod_item_obra",
    "des_item_obra",
    "qtd_item_obra",
    "val_unitario",
    "val_total",
]


def validar_colunas(df: pd.DataFrame) -> list[str]:
    colunas = set(df.columns)
    return [col for col in COLUNAS_OBRIGATORIAS if col not in colunas]


def importar_planilha(caminho_excel: str | Path, modo: str = "versionar") -> dict:
    """
    modo:
      - versionar: mantém importações anteriores e cria nova versão.
      - substituir: remove base histórica anterior e importa de novo.
    """
    init_db()
    caminho_excel = Path(caminho_excel)
    df = pd.read_excel(caminho_excel)
    df.columns = [str(c).strip() for c in df.columns]

    faltantes = validar_colunas(df)
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(faltantes)}")

    df = df.copy()
    df["ordem_linha_importacao"] = range(1, len(df) + 1)
    for col in ["qtd_item_obra", "val_unitario", "val_total"]:
        df[col] = df[col].apply(parse_float)

    agora = datetime.now()
    versao = f"importacao_{agora:%Y%m%d_%H%M%S}"

    raw_dir = BASE_DIR / "data" / "raw" / "planilhas_importadas"
    raw_dir.mkdir(parents=True, exist_ok=True)
    destino_raw = raw_dir / f"{versao}_{caminho_excel.name}"
    try:
        shutil.copy2(caminho_excel, destino_raw)
    except shutil.SameFileError:
        pass

    with get_connection() as conn:
        if modo == "substituir":
            resetar_base_historica(conn)

        cur = conn.execute(
            """
            INSERT INTO importacoes_base
            (nome_arquivo, data_importacao, versao_importacao, qtd_linhas, qtd_obras, status, mensagem_validacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                caminho_excel.name,
                agora.isoformat(timespec="seconds"),
                versao,
                int(len(df)),
                int(df["num_obra"].nunique()),
                "PROCESSANDO",
                "",
            ),
        )
        id_importacao = cur.lastrowid

        obras = []
        for ordem, (num_obra, grupo) in enumerate(df.groupby("num_obra", sort=False), start=1):
            primeira = grupo.iloc[0]
            extracao = extrair_variaveis_tecnicas(primeira.get("descricao"))
            elegivel = int(
                primeira.get("tipo_servico_descricao") == "CONSTR. DE RAMAL RURAL"
                and extracao.get("acao_principal") == "construcao"
                and extracao.get("extensao_mt_m") is not None
                and extracao.get("possui_trafo")
                and extracao.get("potencia_trafo_kva") is not None
                and not extracao.get("possui_rede_bt")
                and not extracao.get("possui_rdu")
            )
            obras.append(
                (
                    id_importacao,
                    str(primeira.get("num_projeto", "")),
                    str(num_obra),
                    str(primeira.get("descricao", "")),
                    extracao.get("descricao_normalizada"),
                    str(primeira.get("tipo_servico_descricao", "")),
                    str(primeira.get("tip_servico", "")),
                    extracao.get("extensao_mt_m"),
                    extracao.get("extensao_bt_m"),
                    extracao.get("tensao_mt_kv"),
                    extracao.get("tensao_bt_v"),
                    int(bool(extracao.get("possui_trafo"))),
                    extracao.get("qtd_trafo"),
                    extracao.get("potencia_trafo_kva"),
                    extracao.get("fase"),
                    int(bool(extracao.get("possui_rede_mt"))),
                    int(bool(extracao.get("possui_rede_bt"))),
                    int(bool(extracao.get("possui_rdu"))),
                    int(bool(extracao.get("rede_rural_indicador"))),
                    int(bool(extracao.get("possui_retirada"))),
                    int(bool(extracao.get("possui_recondutoramento"))),
                    int(bool(extracao.get("possui_deslocamento"))),
                    int(bool(extracao.get("possui_trifaseamento"))),
                    elegivel,
                    ordem,
                )
            )

        conn.executemany(
            """
            INSERT INTO obras_historicas
            (id_importacao, num_projeto, num_obra, descricao_original, descricao_normalizada,
             tipo_servico_real, tip_servico, extensao_mt_m, extensao_bt_m, tensao_mt_kv, tensao_bt_v,
             possui_trafo, qtd_trafo, potencia_trafo_kva, fase, possui_rede_mt, possui_rede_bt,
             possui_rdu, rede_rural_indicador, possui_retirada, possui_recondutoramento,
             possui_deslocamento, possui_trifaseamento, elegivel_previsao, ordem_obra_importacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            obras,
        )

        mapa_obras = {
            row["num_obra"]: row["id_obra"]
            for row in conn.execute("SELECT id_obra, num_obra FROM obras_historicas WHERE id_importacao = ?", (id_importacao,))
        }

        itens = []
        catalogo = {}
        for _, row in df.iterrows():
            num_obra = str(row["num_obra"])
            cod = str(row.get("cod_item_obra", "")).strip()
            desc = str(row.get("des_item_obra", "")).strip()
            tipo = str(row.get("tip_item_obra", "")).strip()
            itens.append(
                (
                    mapa_obras[num_obra],
                    id_importacao,
                    num_obra,
                    tipo,
                    cod,
                    desc,
                    row.get("qtd_item_obra"),
                    row.get("val_unitario"),
                    row.get("val_total"),
                    str(row.get("tuc", "")) if "tuc" in row else "",
                    str(row.get("tb", "")) if "tb" in row else "",
                    int(row.get("ordem_linha_importacao")),
                )
            )
            if cod and cod not in catalogo:
                catalogo[cod] = (
                    cod,
                    desc,
                    tipo,
                    inferir_unidade_medida(desc, tipo),
                    None,
                    None,
                    1,
                )

        conn.executemany(
            """
            INSERT INTO itens_obra_historica
            (id_obra, id_importacao, num_obra, tip_item_obra, cod_item_obra, des_item_obra,
             qtd_item_obra, val_unitario, val_total, tuc, tb, ordem_linha_importacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            itens,
        )

        conn.executemany(
            """
            INSERT OR REPLACE INTO catalogo_itens
            (cod_item_obra, des_item_obra, tip_item_obra, unidade_medida_inferida, grupo_item, subgrupo_item, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            list(catalogo.values()),
        )

        conn.execute(
            "UPDATE importacoes_base SET status = ?, mensagem_validacao = ? WHERE id_importacao = ?",
            ("CONCLUIDA", "Importação concluída", id_importacao),
        )

    return {
        "id_importacao": id_importacao,
        "versao_importacao": versao,
        "linhas": int(len(df)),
        "obras": int(df["num_obra"].nunique()),
        "itens_catalogo": int(len(catalogo)),
        "arquivo_copiado": str(destino_raw),
    }
