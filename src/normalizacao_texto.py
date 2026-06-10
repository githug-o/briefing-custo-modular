from __future__ import annotations

import re
import unicodedata


ABREVIACOES = {
    r"\bCONST\.?\b": "CONSTRUCAO",
    r"\bCONSTR\.?\b": "CONSTRUCAO",
    r"\bINST\.?\b": "INSTALACAO",
    r"\bSUBST\.?\b": "SUBSTITUICAO",
    r"\bRET\.?\b": "RETIRADA",
    r"\bTRAFO\b": "TRANSFORMADOR",
    r"\bTRAFOS\b": "TRANSFORMADORES",
    r"\bTRANSF\.?\b": "TRANSFORMADOR",
    r"\bMONOFASICA\b": "MONOFASICO",
    r"\bMONOF\.?\b": "MONOFASICO",
    r"\bTRIFASICA\b": "TRIFASICO",
    r"\bTRIF\.?\b": "TRIFASICO",
    r"\bRDMT\b": "REDE MT",
    r"\bRDBT\b": "REDE BT",
}

NUMEROS_POR_EXTENSO = {
    "UM": "1",
    "UMA": "1",
    "DOIS": "2",
    "DUAS": "2",
    "TRES": "3",
}


def remover_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def _normalizar_numeros_brasileiros(texto: str) -> str:
    """Converte padrões comuns: 1.361M -> 1361 M, 19,9KV -> 19.9 KV."""
    texto = re.sub(r"(\d)\.(\d{3})(?=\s*(M|METROS?\b))", r"\1\2", texto)
    texto = re.sub(r"(\d),(\d)", r"\1.\2", texto)
    texto = re.sub(r"(\d),(\d{2})", r"\1.\2", texto)
    return texto


def _espacar_unidades(texto: str) -> str:
    texto = re.sub(r"(\d)\s*(KV|KVA|V|KM|M)\b", r"\1 \2", texto)
    texto = re.sub(r"\bMETRO\b", "M", texto)
    texto = re.sub(r"\bMETROS\b", "M", texto)
    return texto


def normalizar_descricao(descricao: str | None) -> str:
    if descricao is None:
        return ""
    texto = str(descricao).strip().upper()
    texto = remover_acentos(texto)
    texto = _normalizar_numeros_brasileiros(texto)

    for palavra, numero in NUMEROS_POR_EXTENSO.items():
        texto = re.sub(rf"\b{palavra}\b", numero, texto)

    for padrao, destino in ABREVIACOES.items():
        texto = re.sub(padrao, destino, texto)

    texto = _espacar_unidades(texto)
    texto = re.sub(r"[^A-Z0-9./\-\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def parse_float(valor) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if texto == "" or texto.lower() == "nan":
        return None
    texto = texto.replace("R$", "").replace(" ", "")
    # Formato brasileiro: 1.234,56
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None
