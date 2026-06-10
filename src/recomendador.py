from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .database import get_connection
from .utils import arredondar_quantidade, classificar_comportamento_item, inferir_unidade_medida

TIPO_RAMAL_RURAL = "CONSTR. DE RAMAL RURAL"
MIN_OBRAS_SEMELHANTES = 5
MAX_OBRAS_REFERENCIA = 20
FREQ_AUTOMATICO = 0.40
FREQ_OPCIONAL = 0.15
LIMIAR_CONFIANCA = 0.35


@dataclass
class ResultadoRecomendacao:
    status_previsao: str
    mensagem: str
    obras_referencia: list[int]
    criterios_usados: dict[str, Any]
    itens_automaticos: pd.DataFrame
    itens_opcionais: pd.DataFrame


def _faixas_adaptativas(extensao_m: float) -> list[float]:
    if extensao_m <= 500:
        return [0.30, 0.40, 0.50]
    if extensao_m <= 1500:
        return [0.25, 0.35, 0.50]
    return [0.20, 0.30, 0.50]


def _buscar_obras_referencia(variaveis: dict, tipo_servico: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    extensao = float(variaveis["extensao_mt_m"])
    tensao = float(variaveis["tensao_mt_kv"])
    potencia = float(variaveis["potencia_trafo_kva"])

    criterios = {
        "tipo_servico": tipo_servico,
        "tensao_mt_kv": tensao,
        "potencia_trafo_kva": potencia,
        "max_obras": MAX_OBRAS_REFERENCIA,
        "faixa_extensao": None,
    }

    with get_connection() as conn:
        base = pd.read_sql_query(
            """
            SELECT *
            FROM obras_historicas
            WHERE tipo_servico_real = ?
              AND tensao_mt_kv IS NOT NULL
              AND potencia_trafo_kva IS NOT NULL
              AND ABS(tensao_mt_kv - ?) < 0.011
              AND ABS(potencia_trafo_kva - ?) < 0.011
            ORDER BY id_importacao DESC, ordem_obra_importacao DESC, id_obra DESC
            """,
            conn,
            params=[tipo_servico, tensao, potencia],
        )

    if base.empty:
        return base, criterios

    for tolerancia in _faixas_adaptativas(extensao):
        minimo = extensao * (1 - tolerancia)
        maximo = extensao * (1 + tolerancia)
        filtrada = base[(base["extensao_mt_m"] >= minimo) & (base["extensao_mt_m"] <= maximo)].head(MAX_OBRAS_REFERENCIA)
        if len(filtrada) >= MIN_OBRAS_SEMELHANTES:
            criterios["faixa_extensao"] = f"{minimo:.0f}m a {maximo:.0f}m"
            criterios["tolerancia_extensao"] = f"±{int(tolerancia * 100)}%"
            return filtrada, criterios

    # Retorno final com a maior faixa, mesmo se insuficiente, para diagnóstico.
    tolerancia = _faixas_adaptativas(extensao)[-1]
    minimo = extensao * (1 - tolerancia)
    maximo = extensao * (1 + tolerancia)
    criterios["faixa_extensao"] = f"{minimo:.0f}m a {maximo:.0f}m"
    criterios["tolerancia_extensao"] = f"±{int(tolerancia * 100)}%"
    return base[(base["extensao_mt_m"] >= minimo) & (base["extensao_mt_m"] <= maximo)].head(MAX_OBRAS_REFERENCIA), criterios


def _calcular_itens(itens: pd.DataFrame, obras: pd.DataFrame, variaveis: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    if itens.empty:
        return pd.DataFrame(), pd.DataFrame()

    total_obras = obras["id_obra"].nunique()
    extensao_nova = float(variaveis["extensao_mt_m"])
    qtd_trafo = int(variaveis.get("qtd_trafo") or 1)

    extensoes = obras.set_index("id_obra")["extensao_mt_m"].to_dict()
    qtd_trafos = obras.set_index("id_obra")["qtd_trafo"].fillna(1).to_dict()

    registros: list[dict[str, Any]] = []
    for cod, grupo in itens.groupby("cod_item_obra", dropna=False):
        cod = str(cod)
        desc = str(grupo["des_item_obra"].dropna().iloc[0]) if not grupo["des_item_obra"].dropna().empty else ""
        tipo = str(grupo["tip_item_obra"].dropna().iloc[0]) if not grupo["tip_item_obra"].dropna().empty else ""
        unidade = inferir_unidade_medida(desc, tipo)
        comportamento = classificar_comportamento_item(desc, tipo)
        freq = grupo["id_obra"].nunique() / total_obras
        val_unitario = float(grupo["val_unitario"].max()) if grupo["val_unitario"].notna().any() else 0.0

        if comportamento == "por_metro":
            taxas = []
            for _, row in grupo.iterrows():
                ext = extensoes.get(row["id_obra"])
                if ext and ext > 0 and pd.notna(row["qtd_item_obra"]):
                    taxas.append(float(row["qtd_item_obra"]) / float(ext))
            qtd = (pd.Series(taxas).median() * extensao_nova) if taxas else grupo["qtd_item_obra"].median()
        elif comportamento == "por_trafo":
            taxas = []
            for _, row in grupo.iterrows():
                qt = qtd_trafos.get(row["id_obra"]) or 1
                if qt and qt > 0 and pd.notna(row["qtd_item_obra"]):
                    taxas.append(float(row["qtd_item_obra"]) / float(qt))
            qtd = (pd.Series(taxas).median() * qtd_trafo) if taxas else grupo["qtd_item_obra"].median()
        else:
            qtd = grupo["qtd_item_obra"].median()

        qtd = arredondar_quantidade(qtd, unidade)
        registros.append(
            {
                "cod_item_obra": cod,
                "des_item_obra": desc,
                "tip_item_obra": tipo,
                "unidade_medida_inferida": unidade,
                "qtd_sugerida_sistema": qtd,
                "val_unitario_sugerido": round(val_unitario, 2),
                "val_total_sugerido": round(qtd * val_unitario, 2),
                "qtd_final_engenheiro": qtd,
                "val_unitario_final": round(val_unitario, 2),
                "val_total_final": round(qtd * val_unitario, 2),
                "frequencia_historica": round(freq, 3),
                "comportamento_calculo": comportamento,
                "origem_item": "automatico" if freq >= FREQ_AUTOMATICO else "opcional",
                "acao_usuario": "mantido" if freq >= FREQ_AUTOMATICO else "opcional",
            }
        )

    df = pd.DataFrame(registros).sort_values(["tip_item_obra", "des_item_obra"])
    automaticos = df[df["frequencia_historica"] >= FREQ_AUTOMATICO].copy()
    opcionais = df[(df["frequencia_historica"] >= FREQ_OPCIONAL) & (df["frequencia_historica"] < FREQ_AUTOMATICO)].copy()
    return automaticos, opcionais


def gerar_recomendacao(variaveis: dict, tipo_servico_previsto: str, score_classificacao: float) -> ResultadoRecomendacao:
    if score_classificacao < LIMIAR_CONFIANCA:
        return ResultadoRecomendacao("bloqueada_baixa_confianca", "Classificação com baixa confiança.", [], {}, pd.DataFrame(), pd.DataFrame())

    if tipo_servico_previsto != TIPO_RAMAL_RURAL:
        return ResultadoRecomendacao(
            "bloqueada_tipo_nao_habilitado",
            "No MVP, a previsão automática completa está habilitada apenas para CONSTR. DE RAMAL RURAL puro.",
            [],
            {"tipo_servico": tipo_servico_previsto},
            pd.DataFrame(),
            pd.DataFrame(),
        )

    if variaveis.get("possui_rede_bt") or variaveis.get("possui_rdu"):
        return ResultadoRecomendacao("bloqueada_excecao", "Descrição contém rede BT/RDU; tratar como exceção no MVP.", [], {}, pd.DataFrame(), pd.DataFrame())

    for campo in ["extensao_mt_m", "tensao_mt_kv", "potencia_trafo_kva"]:
        if variaveis.get(campo) is None:
            return ResultadoRecomendacao("bloqueada_campo_obrigatorio", f"Campo obrigatório ausente: {campo}.", [], {}, pd.DataFrame(), pd.DataFrame())

    obras, criterios = _buscar_obras_referencia(variaveis, tipo_servico_previsto)
    if len(obras) < MIN_OBRAS_SEMELHANTES:
        return ResultadoRecomendacao(
            "bloqueada_base_insuficiente",
            f"Base insuficiente: {len(obras)} obra(s) semelhante(s). Mínimo recomendado: {MIN_OBRAS_SEMELHANTES}.",
            obras["id_obra"].tolist() if not obras.empty else [],
            criterios,
            pd.DataFrame(),
            pd.DataFrame(),
        )

    ids = obras["id_obra"].tolist()
    placeholders = ",".join(["?"] * len(ids))
    with get_connection() as conn:
        itens = pd.read_sql_query(
            f"SELECT * FROM itens_obra_historica WHERE id_obra IN ({placeholders})",
            conn,
            params=ids,
        )

    automaticos, opcionais = _calcular_itens(itens, obras, variaveis)
    return ResultadoRecomendacao(
        "gerada_automaticamente",
        "Previsão gerada com base nas obras semelhantes.",
        ids,
        criterios,
        automaticos,
        opcionais,
    )
