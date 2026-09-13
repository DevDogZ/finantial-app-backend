from datetime import date
from decimal import Decimal

def calcular_mes_ano_fatura(data_compra: date, dia_fechamento: int, numero_parcela: int) -> tuple[int, int]:
    mes = data_compra.month
    ano = data_compra.year


    if data_compra.day > dia_fechamento:
        mes += 1

    mes += numero_parcela - 1

    while mes > 12:
        mes -= 12
        ano += 1

    return mes, ano


def dividir_em_parcelas(valor_total: Decimal, numero_parcelas: int) -> list[Decimal]:
    valor_base = (valor_total / numero_parcelas).quantize(Decimal("0.01"))
    parcelas = [valor_base] * (numero_parcelas - 1)
    ultima_parcela = valor_total - sum(parcelas)
    parcelas.append(ultima_parcela)
    return parcelas