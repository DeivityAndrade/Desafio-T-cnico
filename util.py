"""Validação e formatação de valores monetários, sem ponto flutuante."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTAVO = Decimal("0.01")


def dinheiro(valor):
    """Aceita um número ou texto sem separador de milhar e com até 2 casas."""
    if isinstance(valor, bool):
        raise ValueError("O valor deve ser um número monetário.")
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor válido, como 1200.50 ou 1200,50.") from None
    if not numero.is_finite() or numero < 0:
        raise ValueError("O valor deve ser finito e não negativo.")
    try:
        arredondado = numero.quantize(CENTAVO)
    except InvalidOperation:
        raise ValueError("O valor monetário informado é muito grande.") from None
    if numero != arredondado:
        raise ValueError("O valor deve ter no máximo duas casas decimais.")
    return arredondado


def arredondar(valor):
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def reais(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def inteiro_positivo(valor, nome="Quantidade"):
    if isinstance(valor, bool):
        raise ValueError(f"{nome} deve ser um inteiro positivo.")
    if isinstance(valor, str):
        if not valor.strip().isascii() or not valor.strip().isdigit():
            raise ValueError(f"{nome} deve ser um inteiro positivo.")
        valor = int(valor.strip())
    if not isinstance(valor, int) or valor <= 0 or valor > 2**63 - 1:
        raise ValueError(f"{nome} deve ser um inteiro positivo válido.")
    return valor
