from api.motor_score import (
    calcular_pontos_atraso,
    calcular_reducao_quitado,
    calcular_score,
)


def test_atraso_30_dias():
    assert calcular_pontos_atraso(30) == 0.0


def test_atraso_31_dias():
    assert calcular_pontos_atraso(31) == 0.5


def test_atraso_150_dias():
    assert calcular_pontos_atraso(150) == 2.0


def test_quitado_45_porcento():
    assert calcular_reducao_quitado(45) == 2.0


def test_cenario_da_imagem_com_nova_matriz():
    resultado = calcular_score(
        dias_atraso=150,
        acordos_rompidos=2,
        percentual_garantia=0,
        percentual_quitado=45,
    )

    assert resultado.score_base == 2.5
    assert resultado.pontos_atraso == 2.0
    assert resultado.pontos_reincidencia == 3.0
    assert resultado.pontos_garantia == 2.0
    assert resultado.reducao_quitado == 2.0
    assert resultado.score_bruto == 7.5
    assert resultado.score_final == 7.5
    assert resultado.aprovado is True


def test_score_reprovado():
    resultado = calcular_score(
        dias_atraso=330,
        acordos_rompidos=2,
        percentual_garantia=0,
        percentual_quitado=0,
    )

    assert resultado.score_final == 10.0
    assert resultado.aprovado is False
