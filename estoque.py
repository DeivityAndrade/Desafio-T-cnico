"""Exercício 2: movimentações de estoque com histórico persistente."""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from util import inteiro_positivo

BASE = Path(__file__).resolve().parent / "dados"
ARQUIVO_PADRAO = BASE / "estoque.json"
BANCO_PADRAO = BASE / "estoque.sqlite3"


def ler_produtos(arquivo):
    with Path(arquivo).open(encoding="utf-8-sig") as origem:
        dados = json.load(origem)
    if not isinstance(dados, dict) or not isinstance(dados.get("estoque"), list):
        raise ValueError('O JSON deve conter uma lista chamada "estoque".')
    produtos, codigos = [], set()
    for registro in dados["estoque"]:
        if not isinstance(registro, dict):
            raise ValueError("Registro de produto inválido.")
        codigo = inteiro_positivo(registro.get("codigoProduto"), "Código")
        descricao = registro.get("descricaoProduto")
        saldo = registro.get("estoque")
        if codigo in codigos:
            raise ValueError(f"Código de produto duplicado: {codigo}.")
        if not isinstance(descricao, str) or not descricao.strip():
            raise ValueError(f"Produto {codigo}: descrição inválida.")
        if type(saldo) is not int or not 0 <= saldo <= 2**63 - 1:
            raise ValueError(f"Produto {codigo}: estoque deve ser um inteiro não negativo.")
        codigos.add(codigo)
        produtos.append((codigo, descricao.strip(), saldo))
    return produtos


class Estoque:
    def __init__(self, banco=BANCO_PADRAO, arquivo=ARQUIVO_PADRAO):
        banco = Path(banco)
        banco.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(banco, timeout=10)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        try:
            self.conexao.executescript("""
                CREATE TABLE IF NOT EXISTS produtos (
                    codigo INTEGER PRIMARY KEY,
                    descricao TEXT NOT NULL,
                    saldo INTEGER NOT NULL CHECK(typeof(saldo) = 'integer' AND saldo >= 0)
                );
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_produto INTEGER NOT NULL REFERENCES produtos(codigo),
                    tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida')),
                    descricao TEXT NOT NULL,
                    quantidade INTEGER NOT NULL CHECK(quantidade > 0),
                    saldo_anterior INTEGER NOT NULL,
                    saldo_final INTEGER NOT NULL,
                    data TEXT NOT NULL
                );
            """)
            # Inicialização e movimentações usam uma transação exclusiva de escrita.
            with self.conexao:
                self.conexao.execute("BEGIN IMMEDIATE")
                if self.conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                    self.conexao.executemany(
                        "INSERT INTO produtos(codigo, descricao, saldo) VALUES (?, ?, ?)",
                        ler_produtos(arquivo),
                    )
        except Exception:
            self.conexao.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.conexao.close()

    def listar(self):
        return [dict(linha) for linha in self.conexao.execute(
            "SELECT codigo, descricao, saldo FROM produtos ORDER BY codigo"
        )]

    def historico(self):
        return [dict(linha) for linha in self.conexao.execute(
            "SELECT * FROM movimentacoes ORDER BY id"
        )]

    def movimentar(self, codigo, tipo, quantidade, descricao):
        codigo = inteiro_positivo(codigo, "Código")
        quantidade = inteiro_positivo(quantidade)
        if not isinstance(tipo, str):
            raise ValueError("Tipo deve ser entrada ou saida.")
        tipo = tipo.strip().lower().replace("í", "i")
        if tipo not in ("entrada", "saida"):
            raise ValueError("Tipo deve ser entrada ou saida.")
        if not isinstance(descricao, str) or not descricao.strip():
            raise ValueError("Informe a descrição da movimentação.")
        with self.conexao:
            self.conexao.execute("BEGIN IMMEDIATE")
            produto = self.conexao.execute(
                "SELECT * FROM produtos WHERE codigo = ?", (codigo,)
            ).fetchone()
            if produto is None:
                raise ValueError(f"Produto {codigo} não encontrado.")
            anterior = produto["saldo"]
            final = anterior + quantidade if tipo == "entrada" else anterior - quantidade
            if final < 0:
                raise ValueError(f"Estoque insuficiente: saldo disponível é {anterior}.")
            if final > 2**63 - 1:
                raise ValueError("O estoque resultante excede o limite permitido.")
            self.conexao.execute("UPDATE produtos SET saldo = ? WHERE codigo = ?", (final, codigo))
            cursor = self.conexao.execute("""
                INSERT INTO movimentacoes
                (codigo_produto, tipo, descricao, quantidade, saldo_anterior, saldo_final, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (codigo, tipo, descricao.strip(), quantidade, anterior, final,
                  datetime.now().astimezone().isoformat(timespec="seconds")))
            resultado = dict(self.conexao.execute(
                "SELECT * FROM movimentacoes WHERE id = ?", (cursor.lastrowid,)
            ).fetchone())
        return resultado


def mostrar_produtos(sistema):
    print(f"\n{'Código':<8} {'Produto':<35} {'Estoque':>8}")
    for produto in sistema.listar():
        print(f"{produto['codigo']:<8} {produto['descricao']:<35} {produto['saldo']:>8}")


def mostrar_movimentacao(movimento):
    print(f"\nMovimentação #{movimento['id']} — {movimento['tipo']}")
    print(f"Produto: {movimento['codigo_produto']} | Quantidade: {movimento['quantidade']}")
    print(f"Descrição: {movimento['descricao']}")
    print(f"Estoque anterior: {movimento['saldo_anterior']}")
    print(f"Estoque final: {movimento['saldo_final']}")


def mostrar_historico(sistema):
    historico = sistema.historico()
    if not historico:
        print("Nenhuma movimentação registrada.")
    for movimento in historico:
        mostrar_movimentacao(movimento)
        print(f"Data: {movimento['data']}")


def menu(sistema):
    while True:
        print("\nEstoque: 1 Consultar | 2 Entrada | 3 Saída | 4 Histórico | 0 Voltar")
        try:
            opcao = input("Opção: ").strip()
            if opcao == "0":
                return
            if opcao == "1":
                mostrar_produtos(sistema)
            elif opcao == "4":
                mostrar_historico(sistema)
            elif opcao in ("2", "3"):
                codigo = input("Código do produto: ")
                quantidade = input("Quantidade: ")
                descricao = input("Descrição da movimentação: ")
                movimento = sistema.movimentar(codigo, "entrada" if opcao == "2" else "saida",
                                               quantidade, descricao)
                mostrar_movimentacao(movimento)
            else:
                print("Opção inválida.")
        except ValueError as erro:
            print(f"Erro: {erro}")
        except EOFError:
            return


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banco", default=str(BANCO_PADRAO), help="Caminho do banco SQLite.")
    parser.add_argument("--arquivo", default=str(ARQUIVO_PADRAO), help="JSON de estoque inicial.")
    comandos = parser.add_subparsers(dest="comando")
    comandos.add_parser("listar", help="Consultar produtos e saldos.")
    comandos.add_parser("historico", help="Consultar movimentações.")
    movimento = comandos.add_parser("movimentar", help="Registrar entrada ou saída.")
    movimento.add_argument("codigo")
    movimento.add_argument("tipo", choices=("entrada", "saida", "saída"))
    movimento.add_argument("quantidade")
    movimento.add_argument("descricao")
    argumentos = parser.parse_args(argv)
    try:
        with Estoque(argumentos.banco, argumentos.arquivo) as sistema:
            if argumentos.comando == "listar":
                mostrar_produtos(sistema)
            elif argumentos.comando == "historico":
                mostrar_historico(sistema)
            elif argumentos.comando == "movimentar":
                mostrar_movimentacao(sistema.movimentar(
                    argumentos.codigo, argumentos.tipo, argumentos.quantidade, argumentos.descricao
                ))
            else:
                menu(sistema)
    except (OSError, ValueError, sqlite3.Error) as erro:
        print(f"Erro: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
