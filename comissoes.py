"""Exercício 1: calcula e soma a comissão de cada venda por vendedor."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from util import arredondar, dinheiro, reais

ARQUIVO_PADRAO = Path(__file__).resolve().parent / "dados" / "vendas.json"


def comissao_venda(valor):
    valor = dinheiro(valor)
    if valor < Decimal("100"):
        taxa = Decimal("0")
    elif valor < Decimal("500"):
        taxa = Decimal("0.01")
    else:
        taxa = Decimal("0.05")
    return arredondar(valor * taxa)


def calcular_comissoes(dados):
    if not isinstance(dados, dict) or not isinstance(dados.get("vendas"), list):
        raise ValueError('O JSON deve conter uma lista chamada "vendas".')
    totais = {}
    for indice, venda in enumerate(dados["vendas"], start=1):
        if not isinstance(venda, dict):
            raise ValueError(f"Venda {indice}: registro inválido.")
        nome = venda.get("vendedor")
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError(f"Venda {indice}: vendedor não informado.")
        nome = nome.strip()
        try:
            comissao = comissao_venda(venda.get("valor"))
        except ValueError as erro:
            raise ValueError(f"Venda {indice}: {erro}") from erro
        totais[nome] = totais.get(nome, Decimal("0.00")) + comissao
    return totais


def ler_vendas(caminho=ARQUIVO_PADRAO):
    with Path(caminho).open(encoding="utf-8-sig") as arquivo:
        # parse_float preserva os centavos escritos no JSON.
        dados = json.load(arquivo, parse_float=Decimal)
    return calcular_comissoes(dados)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arquivo", nargs="?", default=str(ARQUIVO_PADRAO),
                        help="Arquivo JSON de vendas (opcional).")
    argumentos = parser.parse_args(argv)
    try:
        totais = ler_vendas(argumentos.arquivo)
    except (OSError, ValueError) as erro:
        print(f"Erro: {erro}")
        return 1
    print("\nComissões por vendedor")
    for nome, total in totais.items():
        print(f"{nome:<25} {reais(total):>15}")
    print(f"{'TOTAL':<25} {reais(sum(totais.values(), Decimal('0.00'))):>15}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
