from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

TIPOS_CONHECIDOS_PROMPT = """
Classifique a descrição de obra em um tipo_servico_previsto.
Quando não houver confiança, retorne NAO_IDENTIFICADO.
Responda somente JSON com as chaves:
- tipo_servico_previsto
- score_classificacao, número entre 0 e 1
- justificativa
"""


def classificar_com_ia(descricao: str) -> dict[str, Any] | None:
    """Fallback opcional. Se não houver chave OpenAI, retorna None sem quebrar o app."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TIPOS_CONHECIDOS_PROMPT},
                {"role": "user", "content": descricao},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        conteudo = resposta.choices[0].message.content or "{}"
        return json.loads(conteudo)
    except Exception:
        return None
