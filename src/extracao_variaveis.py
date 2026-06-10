from __future__ import annotations

import re
from typing import Any

from .normalizacao_texto import normalizar_descricao


def _first_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def _first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return int(float(match.group(1)))
    except (TypeError, ValueError):
        return None


def _extrair_extensao_mt(text: str) -> float | None:
    padroes = [
        r"(\d+(?:\.\d+)?)\s*M\s+DE\s+RDR\s+MT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+DE\s+REDE\s+MT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+DE\s+MT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+.*?\bREDE\s+MT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+.*?\bRDR\s+MT\b",
    ]
    for padrao in padroes:
        valor = _first_float(padrao, text)
        if valor is not None:
            return valor

    # Se existir uma única extensão e o texto indicar MT/RDR, usar como extensão MT.
    todas = re.findall(r"(\d+(?:\.\d+)?)\s*M\b", text)
    if len(todas) == 1 and re.search(r"\b(RDR|REDE MT|MT)\b", text):
        return float(todas[0])
    return None


def _extrair_extensao_bt(text: str) -> float | None:
    padroes = [
        r"(\d+(?:\.\d+)?)\s*M\s+DE\s+REDE\s+BT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+DE\s+BT\b",
        r"(\d+(?:\.\d+)?)\s*M\s+.*?\bREDE\s+BT\b",
    ]
    for padrao in padroes:
        valor = _first_float(padrao, text)
        if valor is not None:
            return valor
    return None


def extrair_variaveis_tecnicas(descricao: str | None) -> dict[str, Any]:
    text = normalizar_descricao(descricao)

    acao_principal = "nao_identificado"
    if "CONSTRUCAO" in text:
        acao_principal = "construcao"
    elif "INSTALACAO" in text:
        acao_principal = "instalacao"
    elif "RECONDUTORAMENTO" in text:
        acao_principal = "recondutoramento"
    elif "DESLOCAMENTO" in text:
        acao_principal = "deslocamento"
    elif "RETIRADA" in text:
        acao_principal = "retirada"

    tensoes_kv = [float(v) for v in re.findall(r"(\d+(?:\.\d+)?)\s*KV\b", text)]
    tensao_mt_kv = tensoes_kv[0] if tensoes_kv else None

    tensao_bt_match = re.search(r"(\d{3}\s*/\s*\d{3})\s*V\b", text)
    tensao_bt_v = tensao_bt_match.group(1).replace(" ", "") if tensao_bt_match else None

    possui_trafo = bool(re.search(r"\bTRANSFORMADOR(ES)?\b", text))
    qtd_trafo = None
    if possui_trafo:
        qtd_trafo = _first_int(r"(?:DE|INSTALACAO DE|SUBSTITUICAO DE)?\s*(\d+)\s+TRANSFORMADOR", text)
        if qtd_trafo is None:
            qtd_trafo = _first_int(r"(\d+)\s+TRANSFORMADORES", text)

    potencia_trafo_kva = _first_float(r"(\d+(?:\.\d+)?)\s*KVA\b", text)

    fase = "nao_informado"
    if "MONOFASICO" in text:
        fase = "monofasico"
    elif "TRIFASICO" in text:
        fase = "trifasico"

    possui_rede_bt = bool(re.search(r"\b(REDE BT|BT)\b", text)) or tensao_bt_v is not None
    possui_rdu = bool(re.search(r"\bRDU\b", text))
    possui_rede_mt = bool(re.search(r"\b(REDE MT|MT|RDR)\b", text))
    rede_rural_indicador = bool(re.search(r"\b(RDR|RAMAL RURAL|REDE RURAL)\b", text))

    possui_recondutoramento = "RECONDUTORAMENTO" in text
    possui_retirada = "RETIRADA" in text
    possui_deslocamento = "DESLOCAMENTO" in text
    possui_trifaseamento = "TRIFASEAMENTO" in text

    extensao_mt_m = _extrair_extensao_mt(text)
    extensao_bt_m = _extrair_extensao_bt(text)

    campos_ausentes: list[str] = []
    if extensao_mt_m is None:
        campos_ausentes.append("extensao_mt_m")
    if possui_trafo and potencia_trafo_kva is None:
        campos_ausentes.append("potencia_trafo_kva")

    return {
        "descricao_normalizada": text,
        "acao_principal": acao_principal,
        "extensao_mt_m": extensao_mt_m,
        "extensao_bt_m": extensao_bt_m,
        "tensao_mt_kv": tensao_mt_kv,
        "tensao_bt_v": tensao_bt_v,
        "possui_rede_mt": possui_rede_mt,
        "possui_rede_bt": possui_rede_bt,
        "possui_rdu": possui_rdu,
        "rede_rural_indicador": rede_rural_indicador,
        "possui_trafo": possui_trafo,
        "qtd_trafo": qtd_trafo,
        "potencia_trafo_kva": potencia_trafo_kva,
        "fase": fase,
        "possui_recondutoramento": possui_recondutoramento,
        "possui_retirada": possui_retirada,
        "possui_deslocamento": possui_deslocamento,
        "possui_trifaseamento": possui_trifaseamento,
        "campos_ausentes": campos_ausentes,
    }
