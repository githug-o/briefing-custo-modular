from __future__ import annotations

import unittest

from src.extracao_variaveis import extrair_variaveis_tecnicas


class ExtracaoVariaveisTest(unittest.TestCase):
    def assert_fase(self, descricao: str, fase_esperada: str) -> None:
        resultado = extrair_variaveis_tecnicas(descricao)
        self.assertEqual(resultado["fase"], fase_esperada)

    def test_infere_rdr_199_como_monofasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE RDR MT 19,9KV COM INSTALACAO DE 01 TRAFO 15KVA",
            "monofasico",
        )

    def test_infere_rdr_345_como_trifasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE RDR MT 34,5KV COM INSTALACAO DE 01 TRAFO 45KVA",
            "trifasico",
        )

    def test_infere_rdu_79_como_monofasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE RDU 7,9KV COM INSTALACAO DE 01 TRAFO 15KVA",
            "monofasico",
        )

    def test_infere_rdu_138_como_trifasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE RDU 13,8KV COM INSTALACAO DE 01 TRAFO 45KVA",
            "trifasico",
        )

    def test_infere_rede_generica_199_sem_bt_rdu_como_monofasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE REDE 19,9KV COM INSTALACAO DE 01 TRAFO 15KVA",
            "monofasico",
        )

    def test_infere_rede_generica_345_sem_bt_rdu_como_trifasico(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE REDE 34,5KV COM INSTALACAO DE 01 TRAFO 45KVA",
            "trifasico",
        )

    def test_nao_infere_fase_generica_quando_tem_bt(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE REDE 13,8KV E REDE BT 380/220V",
            "nao_informado",
        )

    def test_nao_infere_rdr_797(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE RDR MT 7,97KV COM INSTALACAO DE 01 TRAFO 15KVA",
            "nao_informado",
        )

    def test_fase_explicita_prevalece_sobre_tensao(self) -> None:
        self.assert_fase(
            "CONSTRUCAO DE 1000M DE REDE MONOFASICA 34,5KV COM INSTALACAO DE 01 TRAFO 45KVA",
            "monofasico",
        )

    def test_extrai_rede_rural_sem_sigla_rdr(self) -> None:
        resultado = extrair_variaveis_tecnicas(
            "CONSTRUCAO DE 600M de rede rural 19,9kv e instalacao de 2 transformadores DE 20KVA"
        )

        self.assertEqual(resultado["extensao_mt_m"], 600)
        self.assertEqual(resultado["tensao_mt_kv"], 19.9)
        self.assertEqual(resultado["qtd_trafo"], 2)
        self.assertEqual(resultado["potencia_trafo_kva"], 20)
        self.assertEqual(resultado["fase"], "monofasico")

    def test_converte_km_para_metros_na_extensao_mt(self) -> None:
        resultado = extrair_variaveis_tecnicas(
            "CONSTRUCAO DE 2KM DE RDR MT 19,9KV COM INSTALACAO DE 01 TRAFO DE 15KVA"
        )

        self.assertEqual(resultado["extensao_mt_m"], 2000)

    def test_nao_marca_extensao_mt_ausente_em_rede_bt_pura(self) -> None:
        resultado = extrair_variaveis_tecnicas("CONSTRUCAO DE 122 METROS DE REDE BT 440/220V")

        self.assertNotIn("extensao_mt_m", resultado["campos_ausentes"])


if __name__ == "__main__":
    unittest.main()
