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


if __name__ == "__main__":
    unittest.main()
