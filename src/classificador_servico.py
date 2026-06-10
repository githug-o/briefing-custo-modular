from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .extracao_variaveis import extrair_variaveis_tecnicas
from .normalizacao_texto import normalizar_descricao
from .ia_fallback import classificar_com_ia


@dataclass
class ResultadoClassificacao:
    tipo_servico_previsto: str
    score_classificacao: float
    origem: str
    mensagem: str = ""


def _treinar_modelo_local(obras_df: pd.DataFrame) -> Pipeline | None:
    if obras_df.empty:
        return None
    treino = obras_df.dropna(subset=["descricao_normalizada", "tipo_servico_real"]).copy()
    treino = treino[treino["tipo_servico_real"].astype(str).str.len() > 0]
    if treino["tipo_servico_real"].nunique() < 2 or len(treino) < 10:
        return None

    modelo = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    modelo.fit(treino["descricao_normalizada"], treino["tipo_servico_real"])
    return modelo


def classificar_tipo_servico(
    descricao: str,
    obras_df: pd.DataFrame,
    usar_ia_fallback: bool = False,
) -> ResultadoClassificacao:
    texto = normalizar_descricao(descricao)
    modelo = _treinar_modelo_local(obras_df)
    resultado_modelo_baixa_confianca: ResultadoClassificacao | None = None

    if modelo is not None:
        proba = modelo.predict_proba([texto])[0]
        idx = int(proba.argmax())
        tipo = str(modelo.named_steps["clf"].classes_[idx])
        score = float(proba[idx])
        if score >= 0.35:
            return ResultadoClassificacao(tipo, score, "modelo_local")
        resultado_modelo_baixa_confianca = ResultadoClassificacao(
            tipo,
            score,
            "modelo_local_baixa_confianca",
            "Classificacao abaixo do limiar de confianca.",
        )

    # Regra simples para quando ainda não há base/modelo suficiente.
    ext = extrair_variaveis_tecnicas(descricao)
    if (
        ext.get("acao_principal") == "construcao"
        and ext.get("possui_rede_mt")
        and ext.get("possui_trafo")
        and not ext.get("possui_rede_bt")
        and not ext.get("possui_rdu")
    ):
        return ResultadoClassificacao("CONSTR. DE RAMAL RURAL", 0.70, "regra_local")

    if usar_ia_fallback:
        retorno_ia = classificar_com_ia(descricao)
        if retorno_ia:
            return ResultadoClassificacao(
                retorno_ia.get("tipo_servico_previsto", "NAO_IDENTIFICADO"),
                float(retorno_ia.get("score_classificacao", 0.40)),
                "ia_fallback",
                retorno_ia.get("justificativa", ""),
            )

    if resultado_modelo_baixa_confianca is not None:
        return resultado_modelo_baixa_confianca

    return ResultadoClassificacao("NAO_IDENTIFICADO", 0.0, "sem_classificacao")
