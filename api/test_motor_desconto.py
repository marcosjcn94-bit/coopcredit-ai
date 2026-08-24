"""
Testes unitários do motor determinístico de desconto.

Regras testadas:

Art. 15 — Lei Complementar Sintética
    Até 12 parcelas:
        teto legal de 33,33%.

Art. 19 — Regulamento Interno
    Até 18 parcelas:
        teto operacional de 25%.

Art. 19-A — Matriz de desconto por score
    >= 8,0  -> 0%
    >= 7,5  -> 5%
    >= 7,0  -> 10%
    >= 6,5  -> 15%
    >= 6,0  -> 20%
    <  6,0  -> 25%

Art. 19-B — Liquidação à vista
    adicional de 5 pontos percentuais,
    limitado ao teto à vista de 30%.
"""

import pytest

from api.motor_desconto import (
    calcular_desconto,
    calcular_desconto_por_score,
    verificar_artigo_15,
    verificar_artigo_19,
)


# ============================================================
# TESTES DA MATRIZ DE SCORE
# ============================================================

class TestMatrizDescontoScore:
    """Testa exclusivamente a matriz de desconto."""

    def test_score_acima_da_linha_de_corte(self):
        assert calcular_desconto_por_score(8.0) == 0.0

    def test_score_superior_a_linha_de_corte(self):
        assert calcular_desconto_por_score(9.0) == 0.0

    def test_score_7_5(self):
        assert calcular_desconto_por_score(7.5) == 5.0

    def test_score_7_0(self):
        assert calcular_desconto_por_score(7.0) == 10.0

    def test_score_6_5(self):
        assert calcular_desconto_por_score(6.5) == 15.0

    def test_score_6_0(self):
        assert calcular_desconto_por_score(6.0) == 20.0

    def test_score_inferior_a_6(self):
        assert calcular_desconto_por_score(5.9) == 25.0

    def test_score_5_5(self):
        assert calcular_desconto_por_score(5.5) == 25.0

    def test_score_muito_baixo(self):
        assert calcular_desconto_por_score(0.0) == 25.0


# ============================================================
# TESTES DOS LIMITES NORMATIVOS
# ============================================================

class TestLimitesNormativos:
    """Testa os limites de parcelamento."""

    def test_artigo_15_ate_12_parcelas(self):
        assert verificar_artigo_15(12) is True

    def test_artigo_15_13_parcelas(self):
        assert verificar_artigo_15(13) is False

    def test_artigo_15_uma_parcela(self):
        assert verificar_artigo_15(1) is True

    def test_artigo_19_ate_18_parcelas(self):
        assert verificar_artigo_19(18) is True

    def test_artigo_19_19_parcelas(self):
        assert verificar_artigo_19(19) is False

    def test_artigo_19_12_parcelas(self):
        assert verificar_artigo_19(12) is True


# ============================================================
# TESTES DO MOTOR COMPLETO — PARCELADO
# ============================================================

class TestDescontoParcelado:
    """Testa o cálculo completo sem pagamento à vista."""

    def test_score_7_5_com_12_parcelas(self):
        resultado = calcular_desconto(
            score=7.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_por_score == 5.0
        assert resultado.adicional_avista == 0.0
        assert resultado.desconto_final == 5.0
        assert resultado.desconto_aplicavel is True

    def test_score_7_com_12_parcelas(self):
        resultado = calcular_desconto(
            score=7.0,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 10.0

    def test_score_6_5_com_12_parcelas(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 15.0

    def test_score_6_com_12_parcelas(self):
        resultado = calcular_desconto(
            score=6.0,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 20.0

    def test_score_5_5_com_12_parcelas(self):
        resultado = calcular_desconto(
            score=5.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 25.0

    def test_score_5_com_18_parcelas(self):
        resultado = calcular_desconto(
            score=5.0,
            quantidade_parcelas=18,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 25.0


# ============================================================
# TESTES DE LINHA DE CORTE
# ============================================================

class TestLinhaDeCorte:
    """Garante que score >= 8 não receba benefício."""

    def test_score_8_nao_recebe_desconto(self):
        resultado = calcular_desconto(
            score=8.0,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 0.0
        assert resultado.desconto_aplicavel is False

    def test_score_8_1_nao_recebe_desconto(self):
        resultado = calcular_desconto(
            score=8.1,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 0.0
        assert resultado.desconto_aplicavel is False

    def test_score_10_nao_recebe_desconto(self):
        resultado = calcular_desconto(
            score=10.0,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.desconto_final == 0.0
        assert resultado.desconto_aplicavel is False


# ============================================================
# TESTES DE PAGAMENTO À VISTA
# ============================================================

class TestPagamentoAvista:
    """Testa o adicional de 5 pontos percentuais."""

    def test_score_7_5_avista(self):
        resultado = calcular_desconto(
            score=7.5,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_por_score == 5.0
        assert resultado.adicional_avista == 5.0
        assert resultado.desconto_final == 10.0

    def test_score_7_avista(self):
        resultado = calcular_desconto(
            score=7.0,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_por_score == 10.0
        assert resultado.adicional_avista == 5.0
        assert resultado.desconto_final == 15.0

    def test_score_6_5_avista(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_por_score == 15.0
        assert resultado.adicional_avista == 5.0
        assert resultado.desconto_final == 20.0

    def test_score_6_avista(self):
        resultado = calcular_desconto(
            score=6.0,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_por_score == 20.0
        assert resultado.adicional_avista == 5.0
        assert resultado.desconto_final == 25.0

    def test_score_5_5_avista(self):
        resultado = calcular_desconto(
            score=5.5,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_por_score == 25.0
        assert resultado.adicional_avista == 5.0
        assert resultado.desconto_final == 30.0


# ============================================================
# TESTES DOS LIMITES DE DESCONTO
# ============================================================

class TestLimitesDesconto:
    """Garante que os tetos nunca sejam ultrapassados."""

    def test_parcelado_nao_ultrapassa_25_porcento(self):
        resultado = calcular_desconto(
            score=0.0,
            quantidade_parcelas=18,
            pagamento_avista=False,
        )

        assert resultado.desconto_final <= 25.0

    def test_avista_nao_ultrapassa_30_porcento(self):
        resultado = calcular_desconto(
            score=0.0,
            quantidade_parcelas=1,
            pagamento_avista=True,
        )

        assert resultado.desconto_final <= 30.0

    def test_teto_operacional_registrado(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.teto_operacional == 25.0

    def test_teto_legal_ate_12_parcelas(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.teto_legal == 33.33


# ============================================================
# TESTES DO ART. 19 — ACIMA DE 18 PARCELAS
# ============================================================

class TestExcessoParcelamento:
    """Operações acima de 18 parcelas não recebem benefício."""

    def test_19_parcelas_sem_desconto(self):
        resultado = calcular_desconto(
            score=5.0,
            quantidade_parcelas=19,
            pagamento_avista=False,
        )

        assert resultado.desconto_aplicavel is False
        assert resultado.desconto_final == 0.0

    def test_24_parcelas_sem_desconto(self):
        resultado = calcular_desconto(
            score=5.0,
            quantidade_parcelas=24,
            pagamento_avista=False,
        )

        assert resultado.desconto_aplicavel is False
        assert resultado.desconto_final == 0.0


# ============================================================
# TESTES DE VALIDAÇÃO
# ============================================================

class TestValidacao:
    """Testa entradas inválidas."""

    def test_zero_parcelas(self):
        with pytest.raises(ValueError):
            calcular_desconto(
                score=6.5,
                quantidade_parcelas=0,
                pagamento_avista=False,
            )

    def test_parcelas_negativas(self):
        with pytest.raises(ValueError):
            calcular_desconto(
                score=6.5,
                quantidade_parcelas=-1,
                pagamento_avista=False,
            )


# ============================================================
# TESTES DE RASTREABILIDADE
# ============================================================

class TestRastreabilidade:
    """
    Garante que o motor devolva informações suficientes
    para auditoria e observabilidade.
    """

    def test_resultado_possui_fundamento(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.fundamento
        assert isinstance(resultado.fundamento, str)

    def test_resultado_possui_motivo(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.motivo
        assert isinstance(resultado.motivo, str)

    def test_resultado_registra_score(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.score == 6.5

    def test_resultado_registra_parcelas(self):
        resultado = calcular_desconto(
            score=6.5,
            quantidade_parcelas=12,
            pagamento_avista=False,
        )

        assert resultado.quantidade_parcelas == 12