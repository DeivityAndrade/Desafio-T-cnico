"""Testes das regras de negócio e da persistência do estoque."""

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from pathlib import Path

from comissoes import calcular_comissoes, comissao_venda, ler_vendas
from estoque import ARQUIVO_PADRAO, Estoque
from juros import calcular_juros, ler_data
from util import dinheiro


class TestComissoes(unittest.TestCase):
    def test_limites_das_faixas(self):
        casos = {"0": "0.00", "99.99": "0.00", "100": "1.00",
                 "499.99": "5.00", "500": "25.00", "1000": "50.00"}
        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertEqual(comissao_venda(valor), Decimal(esperado))

    def test_arredondamento_de_meio_centavo(self):
        self.assertEqual(comissao_venda("100.50"), Decimal("1.01"))

    def test_taxa_aplicada_por_venda_e_nao_ao_total(self):
        dados = {"vendas": [{"vendedor": "A", "valor": 99},
                            {"vendedor": "A", "valor": 400},
                            {"vendedor": "A", "valor": 500}]}
        self.assertEqual(calcular_comissoes(dados), {"A": Decimal("29.00")})

    def test_arredonda_antes_de_somar(self):
        dados = {"vendas": [{"vendedor": "A", "valor": "100.50"}] * 2}
        self.assertEqual(calcular_comissoes(dados)["A"], Decimal("2.02"))

    def test_resultados_do_enunciado(self):
        self.assertEqual(ler_vendas(), {
            "João Silva": Decimal("495.69"), "Maria Souza": Decimal("465.96"),
            "Carlos Oliveira": Decimal("379.38"), "Ana Lima": Decimal("404.99")})

    def test_vendedor_com_venda_sem_comissao_aparece(self):
        self.assertEqual(calcular_comissoes({"vendas": [{"vendedor": "A", "valor": 50}]}),
                         {"A": Decimal("0.00")})

    def test_lista_vazia(self):
        self.assertEqual(calcular_comissoes({"vendas": []}), {})

    def test_rejeita_registros_invalidos(self):
        for dados in ([], {}, {"vendas": {}}, {"vendas": [None]},
                      {"vendas": [{"vendedor": "", "valor": 500}]},
                      {"vendas": [{"vendedor": "A", "valor": -1}]}):
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                calcular_comissoes(dados)


class TestJuros(unittest.TestCase):
    def test_juros_simples_em_tres_dias(self):
        resultado = calcular_juros("1000", date(2026, 10, 2), date(2026, 10, 5))
        self.assertEqual(resultado["dias_atraso"], 3)
        self.assertEqual(resultado["juros"], Decimal("75.00"))
        self.assertEqual(resultado["valor_total"], Decimal("1075.00"))

    def test_vencimento_hoje(self):
        resultado = calcular_juros(100, date(2026, 10, 5), date(2026, 10, 5))
        self.assertEqual(resultado["juros"], Decimal("0.00"))

    def test_vencimento_futuro(self):
        resultado = calcular_juros(100, date(2026, 10, 6), date(2026, 10, 5))
        self.assertEqual(resultado["dias_atraso"], 0)
        self.assertEqual(resultado["valor_total"], Decimal("100.00"))

    def test_valor_zero(self):
        self.assertEqual(calcular_juros(0, date(2026, 1, 1), date(2026, 10, 5))["juros"], 0)

    def test_arredondamento(self):
        self.assertEqual(calcular_juros("0.20", date(2026, 10, 4), date(2026, 10, 5))["juros"],
                         Decimal("0.01"))

    def test_ano_bissexto(self):
        resultado = calcular_juros(100, date(2024, 2, 28), date(2024, 3, 1))
        self.assertEqual(resultado["dias_atraso"], 2)
        self.assertEqual(resultado["juros"], Decimal("5.00"))

    def test_data_atual_e_obtida_automaticamente(self):
        self.assertEqual(calcular_juros(100, date.today())["data_calculo"], date.today())

    def test_formatos_de_data(self):
        self.assertEqual(ler_data("05/10/2026"), date(2026, 10, 5))
        self.assertEqual(ler_data("2026-10-05"), date(2026, 10, 5))

    def test_rejeita_data_invalida(self):
        for texto in ("31/02/2026", "texto", "29/02/2025"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                ler_data(texto)


class TestDinheiro(unittest.TestCase):
    def test_aceita_virgula_decimal(self):
        self.assertEqual(dinheiro("1200,50"), Decimal("1200.50"))

    def test_rejeita_valores_invalidos(self):
        for valor in (True, None, "NaN", "Infinity", "-1", "1.001", "abc", "1.200,00"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                dinheiro(valor)


class TestEstoque(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.banco = Path(self.temporario.name) / "teste.sqlite3"
        self.sistema = Estoque(self.banco)
        self.addCleanup(self.sistema.conexao.close)

    def saldo(self, codigo=101):
        return next(p["saldo"] for p in self.sistema.listar() if p["codigo"] == codigo)

    def test_carrega_produtos_originais(self):
        self.assertEqual([p["saldo"] for p in self.sistema.listar()], [150, 75, 200, 320, 90])

    def test_entrada_saida_e_identificadores_unicos(self):
        entrada = self.sistema.movimentar(101, "entrada", 20, "Compra de mercadoria")
        saida = self.sistema.movimentar(101, "saída", 10, "Venda")
        self.assertEqual(entrada["saldo_anterior"], 150)
        self.assertEqual(entrada["saldo_final"], 170)
        self.assertEqual(saida["saldo_final"], 160)
        self.assertNotEqual(entrada["id"], saida["id"])
        self.assertEqual(saida["descricao"], "Venda")
        self.assertEqual(self.saldo(), 160)

    def test_saida_exata_permite_saldo_zero(self):
        self.assertEqual(self.sistema.movimentar(101, "saida", 150, "Venda")["saldo_final"], 0)

    def test_saida_insuficiente_nao_altera_saldo_nem_historico(self):
        with self.assertRaisesRegex(ValueError, "insuficiente"):
            self.sistema.movimentar(101, "saida", 151, "Venda")
        self.assertEqual(self.saldo(), 150)
        self.assertEqual(self.sistema.historico(), [])

    def test_rejeita_movimentacoes_invalidas(self):
        for codigo, tipo, quantidade, descricao in (
            (999, "entrada", 1, "Compra"), (101, "ajuste", 1, "Compra"),
            (101, "entrada", 0, "Compra"), (101, "entrada", -1, "Compra"),
            (101, "entrada", 1.5, "Compra"), (101, "entrada", True, "Compra"),
            (101, "entrada", "1.5", "Compra"), (101, "entrada", 1, "   "),
        ):
            with self.subTest(quantidade=quantidade), self.assertRaises(ValueError):
                self.sistema.movimentar(codigo, tipo, quantidade, descricao)
        self.assertEqual(self.saldo(), 150)
        self.assertEqual(self.sistema.historico(), [])

    def test_saldos_historico_e_ids_persistem(self):
        primeira = self.sistema.movimentar(101, "entrada", 10, "Compra")
        with Estoque(self.banco) as outra:
            self.assertEqual(outra.listar()[0]["saldo"], 160)
            self.assertEqual(len(outra.historico()), 1)
            segunda = outra.movimentar(102, "saida", 5, "Venda")
            self.assertGreater(segunda["id"], primeira["id"])
        self.assertEqual(self.sistema.listar()[1]["saldo"], 70)

    def test_movimentacao_nao_altera_outros_produtos(self):
        antes = self.sistema.listar()[1:]
        self.sistema.movimentar(101, "entrada", 10, "Compra")
        self.assertEqual(self.sistema.listar()[1:], antes)

    def test_duas_saidas_simultaneas_nao_geram_estoque_negativo(self):
        def retirar(_):
            with Estoque(self.banco) as sistema:
                try:
                    sistema.movimentar(101, "saida", 120, "Venda")
                    return True
                except ValueError:
                    return False
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(retirar, range(2)))
        self.assertEqual(sorted(resultados), [False, True])
        self.assertEqual(self.saldo(), 30)
        self.assertEqual(len(self.sistema.historico()), 1)

    def test_rejeita_codigos_duplicados_no_json(self):
        arquivo = Path(self.temporario.name) / "duplicados.json"
        produtos = json.loads(ARQUIVO_PADRAO.read_text(encoding="utf-8"))
        produtos["estoque"].append(produtos["estoque"][0])
        arquivo.write_text(json.dumps(produtos), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            Estoque(Path(self.temporario.name) / "outro.sqlite3", arquivo)


if __name__ == "__main__":
    unittest.main()
