from __future__ import annotations

import math
from dataclasses import asdict, dataclass

SCORE_BASE = 2.5
LINHA_CORTE = 8.0
MAX_SCORE = 10.0
MIN_SCORE = 0.0
MAX_PONTOS_ATRASO = 5.5


@dataclass(frozen=True)
class ResultadoScore:
    score_base: float
    pontos_atraso: float
    pontos_reincidencia: float
    pontos_garantia: float
    reducao_quitado: float
    score_bruto: float
    score_final: float
    aprovado: bool

    def as_dict(self) -> dict:
        return asdict(self)


def calcular_pontos_atraso(dias_atraso: int) -> float:
    """Art. 7: +0,5 ponto por faixa de 30 dias acima de 30 dias."""
    dias = max(0, int(dias_atraso))

    if dias <= 30:
        return 0.0

    faixas = math.ceil((dias - 30) / 30)
    pontos = faixas * 0.5
    return min(pontos, MAX_PONTOS_ATRASO)


def calcular_pontos_reincidencia(acordos_rompidos: int) -> float:
    """Art. 8: +1,5 ponto por acordo anteriormente rompido."""
    acordos = max(0, int(acordos_rompidos))
    return acordos * 1.5


def normalizar_garantia(possui_garantia: bool | str) -> bool:
    """Converte valores de formulário como 'Sim'/'Não' em bool."""
    if isinstance(possui_garantia, bool):
        return possui_garantia

    valor = str(possui_garantia).strip().lower()
    if valor in {"sim", "s", "yes", "y", "true", "1"}:
        return True
    if valor in {"não", "nao", "n", "no", "false", "0", ""}:
        return False

    raise ValueError("possui_garantia deve ser 'Sim' ou 'Não' (ou um booleano).")


def calcular_reducao_quitado(percentual_quitado: float) -> float:
    """Art. 10: -0,5 ponto para cada faixa completa de 10% quitados."""
    percentual = float(percentual_quitado)
    percentual = max(0.0, min(percentual, 100.0))

    faixas = math.floor(percentual / 10.0)
    return faixas * 0.5


def calcular_pontos_garantia(percentual_garantia: float) -> float:
    """Art. 9: Escalonamento por percentual de cobertura da garantia."""
    perc = float(percentual_garantia)
    if perc == 0: return 2.0
    if perc <= 25.0: return 1.5
    if perc <= 50.0: return 1.0
    if perc <= 75.0: return 0.5
    return 0.0


def calcular_score(
    *,
    dias_atraso: int,
    acordos_rompidos: int,
    percentual_garantia: float,
    percentual_quitado: float,
) -> ResultadoScore:
    """Executa a matriz determinística dos Arts. 5º a 12º."""
    pontos_atraso = calcular_pontos_atraso(dias_atraso)
    pontos_reincidencia = calcular_pontos_reincidencia(acordos_rompidos)
    pontos_garantia = calcular_pontos_garantia(percentual_garantia)
    reducao_quitado = calcular_reducao_quitado(percentual_quitado)

    score_bruto = (
        SCORE_BASE
        + pontos_atraso
        + pontos_reincidencia
        + pontos_garantia
        - reducao_quitado
    )

    score_final = max(MIN_SCORE, min(score_bruto, MAX_SCORE))
    aprovado = score_final < LINHA_CORTE

    return ResultadoScore(
        score_base=SCORE_BASE,
        pontos_atraso=round(pontos_atraso, 2),
        pontos_reincidencia=round(pontos_reincidencia, 2),
        pontos_garantia=round(pontos_garantia, 2),
        reducao_quitado=round(reducao_quitado, 2),
        score_bruto=round(score_bruto, 2),
        score_final=round(score_final, 2),
        aprovado=aprovado,
    )
