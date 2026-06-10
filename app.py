from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.classificador_servico import classificar_tipo_servico
from src.database import (
    carregar_historico_previsoes,
    carregar_obras_historicas,
    init_db,
    resumo_base,
    salvar_previsao,
)
from src.exportador_excel import gerar_excel_orcamento
from src.extracao_variaveis import extrair_variaveis_tecnicas
from src.importacao_excel import importar_planilha
from src.recomendador import gerar_recomendacao
from src.utils import timestamp_nome

st.set_page_config(page_title="Orçamento de Obras", page_icon="assets/logo.png", layout="wide")
init_db()


COLUNAS_VISIVEIS = [
    "cod_item_obra",
    "des_item_obra",
    "tip_item_obra",
    "unidade_medida_inferida",
    "qtd_sugerida_sistema",
    "val_unitario_sugerido",
    "val_total_sugerido",
    "qtd_final_engenheiro",
    "val_unitario_final",
    "val_total_final",
    "frequencia_historica",
]


def calcular_totais(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    for col in ["qtd_final_engenheiro", "val_unitario_final"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)
    df["val_total_final"] = (df["qtd_final_engenheiro"] * df["val_unitario_final"]).round(2)
    return df


def filtrar_tipo(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUNAS_VISIVEIS)
    return df[df["tip_item_obra"].astype(str).str.upper() == tipo].copy()


def tela_importacao() -> None:
    st.header("1. Importar base histórica")
    st.write("Importe a planilha Excel com materiais, mão de obra e taxas.")

    stats = resumo_base()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Importações", stats["importacoes"])
    c2.metric("Obras", stats["obras"])
    c3.metric("Linhas de itens", stats["linhas"])
    c4.metric("Itens no catálogo", stats["itens"])

    arquivo = st.file_uploader("Selecione a planilha Excel", type=["xlsx"])
    modo_label = st.radio(
        "Como importar?",
        ["Criar nova versão e manter histórico", "Substituir base histórica atual"],
        horizontal=True,
    )
    modo = "versionar" if modo_label.startswith("Criar") else "substituir"

    if st.button("Importar planilha", type="primary", disabled=arquivo is None):
        temp_dir = Path("data") / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        caminho_temp = temp_dir / arquivo.name
        caminho_temp.write_bytes(arquivo.getbuffer())
        try:
            resultado = importar_planilha(caminho_temp, modo=modo)
            st.success("Importação concluída.")
            st.json(resultado)
        except Exception as exc:
            st.error(f"Erro na importação: {exc}")


def tela_nova_previsao() -> None:
    st.header("2. Nova previsão")
    st.caption("Primeiro o sistema interpreta a descrição. Depois você valida as variáveis antes de gerar a previsão.")

    descricao = st.text_area(
        "Descrição curta da obra",
        value="CONSTRUÇÃO DE 1000M DE RDR MT 19,9KV COM INSTALAÇÃO DE 01 TRAFO 15KVA",
        height=100,
    )
    usar_ia = st.checkbox("Usar IA externa como fallback quando o modelo local tiver baixa confiança", value=True)

    if st.button("Analisar descrição", type="primary"):
        if not descricao.strip():
            st.warning("Informe a descrição da obra.")
        else:
            obras_df = carregar_obras_historicas()
            extracao = extrair_variaveis_tecnicas(descricao)
            classificacao = classificar_tipo_servico(descricao, obras_df, usar_ia_fallback=usar_ia)
            st.session_state["descricao_input"] = descricao
            st.session_state["extracao"] = extracao
            st.session_state["classificacao"] = classificacao
            st.session_state.pop("resultado_recomendacao", None)
            st.session_state.pop("itens_automaticos", None)
            st.session_state.pop("itens_opcionais", None)

    if "extracao" not in st.session_state:
        return

    extracao = st.session_state["extracao"]
    classificacao = st.session_state["classificacao"]

    st.subheader("Validação das variáveis extraídas")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tipo previsto", classificacao.tipo_servico_previsto)
    c2.metric("Confiança", f"{classificacao.score_classificacao:.0%}")
    c3.metric("Origem", classificacao.origem)

    with st.form("form_variaveis"):
        col1, col2, col3 = st.columns(3)
        tipo_servico_previsto = col1.text_input("Tipo de serviço previsto", value=classificacao.tipo_servico_previsto)
        extensao_mt_m = col2.number_input("Extensão MT (m)", value=float(extracao.get("extensao_mt_m") or 0), min_value=0.0, step=1.0)
        tensao_mt_kv = col3.number_input("Tensão MT (kV)", value=float(extracao.get("tensao_mt_kv") or 0), min_value=0.0, step=0.01)

        col4, col5, col6 = st.columns(3)
        qtd_trafo = col4.number_input("Quantidade de trafos", value=int(extracao.get("qtd_trafo") or 1), min_value=0, step=1)
        potencia_trafo_kva = col5.number_input("Potência do trafo (kVA)", value=float(extracao.get("potencia_trafo_kva") or 0), min_value=0.0, step=1.0)
        fase = col6.selectbox("Fase", ["nao_informado", "monofasico", "trifasico"], index=["nao_informado", "monofasico", "trifasico"].index(extracao.get("fase", "nao_informado")))

        gerar = st.form_submit_button("Confirmar variáveis e gerar previsão", type="primary")

    if gerar:
        variaveis = dict(extracao)
        variaveis.update(
            {
                "extensao_mt_m": extensao_mt_m if extensao_mt_m > 0 else None,
                "tensao_mt_kv": tensao_mt_kv if tensao_mt_kv > 0 else None,
                "qtd_trafo": qtd_trafo if qtd_trafo > 0 else None,
                "potencia_trafo_kva": potencia_trafo_kva if potencia_trafo_kva > 0 else None,
                "fase": fase,
            }
        )
        resultado = gerar_recomendacao(variaveis, tipo_servico_previsto, classificacao.score_classificacao)
        st.session_state["extracao"] = variaveis
        st.session_state["resultado_recomendacao"] = resultado
        st.session_state["itens_automaticos"] = resultado.itens_automaticos
        st.session_state["itens_opcionais"] = resultado.itens_opcionais

    if "resultado_recomendacao" not in st.session_state:
        return

    resultado = st.session_state["resultado_recomendacao"]
    if resultado.status_previsao != "gerada_automaticamente":
        st.warning(f"{resultado.status_previsao}: {resultado.mensagem}")
        if resultado.criterios_usados:
            st.json(resultado.criterios_usados)
        return

    st.success(resultado.mensagem)
    with st.expander("Critérios usados pela recomendação", expanded=False):
        st.json(resultado.criterios_usados)

    itens = st.session_state.get("itens_automaticos", pd.DataFrame()).copy()
    opcionais = st.session_state.get("itens_opcionais", pd.DataFrame()).copy()

    st.subheader("Previsão editável")
    st.caption("Edite quantidade final e valor unitário final. A coluna de total final será recalculada na exportação.")

    abas = st.tabs(["Materiais", "Mão de obra", "Taxas", "Sugestões opcionais", "Resumo e exportação"])

    with abas[0]:
        mat = filtrar_tipo(itens, "MATERIAL")
        mat = st.data_editor(mat[COLUNAS_VISIVEIS] if not mat.empty else mat, num_rows="dynamic", use_container_width=True, key="edit_materiais")
        st.session_state["edit_materiais_df"] = calcular_totais(mat)

    with abas[1]:
        mo = filtrar_tipo(itens, "MAO-DE-OBRA")
        mo = st.data_editor(mo[COLUNAS_VISIVEIS] if not mo.empty else mo, num_rows="dynamic", use_container_width=True, key="edit_mo")
        st.session_state["edit_mo_df"] = calcular_totais(mo)

    with abas[2]:
        tx = filtrar_tipo(itens, "TAXAS")
        tx = st.data_editor(tx[COLUNAS_VISIVEIS] if not tx.empty else tx, num_rows="dynamic", use_container_width=True, key="edit_taxas")
        st.session_state["edit_taxas_df"] = calcular_totais(tx)

    with abas[3]:
        st.write("Itens opcionais aparecem aqui. Nesta primeira versão, copie/adapte os itens para as abas principais quando quiser usá-los.")
        if opcionais.empty:
            st.info("Nenhum item opcional encontrado.")
        else:
            st.dataframe(opcionais[COLUNAS_VISIVEIS], use_container_width=True)

    with abas[4]:
        mat_final = st.session_state.get("edit_materiais_df", pd.DataFrame())
        mo_final = st.session_state.get("edit_mo_df", pd.DataFrame())
        tx_final = st.session_state.get("edit_taxas_df", pd.DataFrame())
        total_material = float(mat_final.get("val_total_final", pd.Series(dtype=float)).sum()) if not mat_final.empty else 0
        total_mo = float(mo_final.get("val_total_final", pd.Series(dtype=float)).sum()) if not mo_final.empty else 0
        total_taxas = float(tx_final.get("val_total_final", pd.Series(dtype=float)).sum()) if not tx_final.empty else 0
        total_geral = total_material + total_mo + total_taxas

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Materiais", f"R$ {total_material:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Mão de obra", f"R$ {total_mo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c3.metric("Taxas", f"R$ {total_taxas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c4.metric("Total", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        auditoria = pd.concat([mat_final, mo_final, tx_final], ignore_index=True)
        resumo = {
            "descricao_original": st.session_state.get("descricao_input", ""),
            "tipo_servico_previsto": tipo_servico_previsto,
            "score_classificacao": classificacao.score_classificacao,
            "status_previsao": resultado.status_previsao,
            "extensao_mt_m": st.session_state["extracao"].get("extensao_mt_m"),
            "tensao_mt_kv": st.session_state["extracao"].get("tensao_mt_kv"),
            "qtd_trafo": st.session_state["extracao"].get("qtd_trafo"),
            "potencia_trafo_kva": st.session_state["extracao"].get("potencia_trafo_kva"),
            "fase": st.session_state["extracao"].get("fase"),
            "total_material": total_material,
            "total_mao_de_obra": total_mo,
            "total_taxas": total_taxas,
            "total_geral": total_geral,
            "data_exportacao": datetime.now().isoformat(timespec="seconds"),
        }
        excel_bytes = gerar_excel_orcamento(resumo, mat_final, mo_final, tx_final, auditoria)
        nome_arquivo = f"orcamento_{timestamp_nome()}.xlsx"
        st.download_button("Exportar Excel", data=excel_bytes, file_name=nome_arquivo, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

        if st.button("Salvar previsão no banco local"):
            id_prev = salvar_previsao(
                st.session_state.get("descricao_input", ""),
                tipo_servico_previsto,
                classificacao.score_classificacao,
                resultado.status_previsao,
                st.session_state["extracao"],
                auditoria,
            )
            st.success(f"Previsão salva com ID {id_prev}.")


def tela_historico() -> None:
    st.header("3. Histórico de previsões")
    df = carregar_historico_previsoes()
    if df.empty:
        st.info("Nenhuma previsão salva ainda.")
    else:
        st.dataframe(df, use_container_width=True)


st.sidebar.title("Orçamento de Obras")
pagina = st.sidebar.radio("Menu", ["Importar base", "Nova previsão", "Histórico"])

if pagina == "Importar base":
    tela_importacao()
elif pagina == "Nova previsão":
    tela_nova_previsao()
else:
    tela_historico()
