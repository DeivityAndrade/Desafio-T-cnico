"""Exercício 3: calcula juros simples de 2,5% por dia de atraso."""

import argparse
from datetime import date, datetime
from decimal import Decimal

from util import arredondar, dinheiro, reais

TAXA_DIARIA = Decimal("0.025")


def ler_data(texto):
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto.strip(), formato).date()
        except ValueError:
            pass
    raise ValueError("Data inválida. Use DD/MM/AAAA ou AAAA-MM-DD.")


def calcular_juros(valor, vencimento, hoje=None):
    valor = dinheiro(valor)
    if isinstance(vencimento, str):
        vencimento = ler_data(vencimento)
    hoje = date.today() if hoje is None else hoje
    if type(vencimento) is not date or type(hoje) is not date:
        raise ValueError("Vencimento e data de cálculo devem ser datas válidas.")
    dias = max(0, (hoje - vencimento).days)
    juros = arredondar(valor * TAXA_DIARIA * dias)
    return {
        "valor_original": valor,
        "vencimento": vencimento,
        "data_calculo": hoje,
        "dias_atraso": dias,
        "juros": juros,
        "valor_total": valor + juros,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("valor", nargs="?", help="Valor sem separador de milhar.")
    parser.add_argument("vencimento", nargs="?", help="DD/MM/AAAA ou AAAA-MM-DD.")
    argumentos = parser.parse_args(argv)
    try:
        valor = argumentos.valor if argumentos.valor is not None else input("Valor original: ")
        vencimento = argumentos.vencimento or input("Vencimento (DD/MM/AAAA): ")
        resultado = calcular_juros(valor, vencimento)
    except (ValueError, EOFError) as erro:
        print(f"Erro: {erro}")
        return 1
    print(f"\nData do cálculo: {resultado['data_calculo']:%d/%m/%Y}")
    print(f"Vencimento: {resultado['vencimento']:%d/%m/%Y}")
    print(f"Dias de atraso: {resultado['dias_atraso']}")
    print(f"Valor original: {reais(resultado['valor_original'])}")
    print(f"Juros (2,5% ao dia): {reais(resultado['juros'])}")
    print(f"Valor total: {reais(resultado['valor_total'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
