from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def inferir_unidade_medida(descricao_item: str | None, tip_item_obra: str | None = None) -> str:
    desc = (descricao_item or "").upper()
    tipo = (tip_item_obra or "").upper()

    if "TAXA" in tipo:
        return "taxa"
    if any(p in desc for p in ["CABO", "CONDUTOR", "CORDOALHA"]):
        return "kg"
    if any(p in desc for p in ["TRANSF", "TRANSFORMADOR", "POSTE", "HASTE", "PARA-RAIO", "PARA RAIOS", "CHAVE", "ISOLADOR", "CONECTOR", "ARRUELA", "PARAFUSO", "ALCA", "ARMACAO"]):
        return "un"
    if any(p in desc for p in ["LOCACAO", "ABRIR CAVA", "INST ", "RETIRADA", "DISTR "]):
        return "servico"
    if "MAO" in tipo:
        return "servico"
    return "un"


def classificar_comportamento_item(descricao_item: str | None, tip_item_obra: str | None = None) -> str:
    desc = (descricao_item or "").upper()
    tipo = (tip_item_obra or "").upper()

    if "TAXA" in tipo:
        return "fixo"
    if any(p in desc for p in ["CABO", "CONDUTOR", "POSTE", "CAVA", "LOCACAO", "DISTR PST", "INST POSTE", "ISOLADOR", "CONECTOR", "ESTRIBO", "ALCA"]):
        return "por_metro"
    if any(p in desc for p in ["TRANSF", "TRANSFORMADOR", "PARA-RAIO", "PARA RAIOS", "CHAVE FUSIVEL", "ATERR", "HASTE", "MEDICAO ATERR"]):
        return "por_trafo"
    return "fixo"


def arredondar_quantidade(valor: float | None, unidade: str) -> float:
    if valor is None:
        return 0.0
    if unidade in {"un", "taxa"}:
        return float(round(valor))
    return round(float(valor), 3)


def dinheiro(valor: float | None) -> str:
    if valor is None:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def timestamp_nome() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
