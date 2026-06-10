from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.classificador_servico import classificar_tipo_servico
from src.extracao_variaveis import extrair_variaveis_tecnicas
from src.normalizacao_texto import normalizar_descricao


def montar_base_treino(df: pd.DataFrame) -> pd.DataFrame:
    base = df.copy()
    base["descricao_normalizada"] = base["descricao"].apply(normalizar_descricao)
    base["tipo_servico_real"] = base["tipo_servico_descricao"].astype(str)
    return base


def analisar(caminho: Path) -> None:
    df = pd.read_excel(caminho)
    colunas_esperadas = {"num_obra", "descricao", "tip_servico", "tipo_servico_descricao"}
    faltantes = sorted(colunas_esperadas - set(df.columns))
    if faltantes:
        raise ValueError(f"Colunas ausentes: {', '.join(faltantes)}")

    base_treino = montar_base_treino(df)
    linhas = []
    for _, row in df.iterrows():
        descricao = str(row["descricao"])
        ext = extrair_variaveis_tecnicas(descricao)
        classificacao = classificar_tipo_servico(descricao, base_treino, usar_ia_fallback=False)
        linhas.append(
            {
                "num_obra": row["num_obra"],
                "tipo_real": row["tipo_servico_descricao"],
                "tipo_previsto": classificacao.tipo_servico_previsto,
                "score": classificacao.score_classificacao,
                "origem": classificacao.origem,
                "extensao_mt_m": ext.get("extensao_mt_m"),
                "extensao_bt_m": ext.get("extensao_bt_m"),
                "tensao_mt_kv": ext.get("tensao_mt_kv"),
                "tensao_bt_v": ext.get("tensao_bt_v"),
                "possui_rede_mt": ext.get("possui_rede_mt"),
                "possui_rede_bt": ext.get("possui_rede_bt"),
                "possui_rdu": ext.get("possui_rdu"),
                "possui_trafo": ext.get("possui_trafo"),
                "qtd_trafo": ext.get("qtd_trafo"),
                "potencia_trafo_kva": ext.get("potencia_trafo_kva"),
                "fase": ext.get("fase"),
                "possui_recondutoramento": ext.get("possui_recondutoramento"),
                "possui_retirada": ext.get("possui_retirada"),
                "possui_deslocamento": ext.get("possui_deslocamento"),
                "possui_trifaseamento": ext.get("possui_trifaseamento"),
                "campos_ausentes": ",".join(ext.get("campos_ausentes", [])),
                "descricao": descricao,
            }
        )

    resultado = pd.DataFrame(linhas)
    acertos = (resultado["tipo_real"] == resultado["tipo_previsto"]).sum()
    total = len(resultado)

    print(f"Arquivo: {caminho}")
    print(f"Linhas: {total}")
    print(f"Obras unicas: {df['num_obra'].nunique()}")
    print(f"Descricoes unicas: {df['descricao'].nunique()}")
    print(f"Tipos de servico: {df['tipo_servico_descricao'].nunique()}")
    print(f"Acuracia aparente da classificacao: {acertos}/{total} ({acertos / total:.1%})")
    print()

    print("Distribuicao por tipo real:")
    print(df["tipo_servico_descricao"].value_counts().to_string())
    print()

    print("Fase inferida:")
    print(resultado["fase"].value_counts(dropna=False).to_string())
    print()

    print("Tensoes MT encontradas:")
    print(resultado["tensao_mt_kv"].value_counts(dropna=False).sort_index().to_string())
    print()

    print("Campos ausentes:")
    ausentes = resultado[resultado["campos_ausentes"].astype(str).str.len() > 0]
    if ausentes.empty:
        print("Nenhum")
    else:
        print(ausentes["campos_ausentes"].value_counts().to_string())
    print()

    print("Divergencias de classificacao:")
    divergencias = resultado[resultado["tipo_real"] != resultado["tipo_previsto"]]
    if divergencias.empty:
        print("Nenhuma")
    else:
        print(
            divergencias[
                ["num_obra", "tipo_real", "tipo_previsto", "score", "origem", "descricao"]
            ]
            .head(30)
            .to_string(index=False)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa descricoes historicas do Custo Modular.")
    parser.add_argument("arquivo", type=Path, help="Caminho para descricoes.xlsx")
    args = parser.parse_args()
    analisar(args.arquivo)


if __name__ == "__main__":
    main()
