#!/usr/bin/env python3
"""
Testes Unitários para as Estratégias de Cálculo de DOP (Strategy Pattern).
"""

import math
import numpy as np
import pytest

from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.strategies.StandardLeastSquaresDopStrategy import StandardLeastSquaresDopStrategy
from brazilian_rps_sim.core.domain.strategies.ElevationMaskDopStrategy import ElevationMaskDopStrategy
from brazilian_rps_sim.core.domain.strategies.WeightedElevationDopStrategy import WeightedElevationDopStrategy


def test_standard_dop_insufficient_satellites_returns_invalid():
    """Garante que menos de 4 satélites resulte em DopResultVO inválido."""
    strategy = StandardLeastSquaresDopStrategy()
    station = GeodeticCoordinatesVO(-15.7975, -47.8633, 1.0)
    
    # Apenas 3 satélites fornecidos
    sats_ecef = {
        "SAT_1": np.array([42164.0, 0.0, 0.0]),
        "SAT_2": np.array([0.0, 42164.0, 0.0]),
        "SAT_3": np.array([0.0, 0.0, 42164.0]),
    }
    
    res = strategy.calculate_dop(station, sats_ecef)
    assert not res.is_valid
    assert res.pdop == float('inf')
    assert res.quality_rating == "POOR_COVERAGE"


def test_elevation_mask_dop_filters_low_satellites():
    """Garante que satélites abaixo da máscara de elevação sejam descartados."""
    station = GeodeticCoordinatesVO(0.0, 0.0, 0.0) # Equador / Greenwich
    
    # 4 satélites: 3 bem altos e 1 abaixo do horizonte
    sats_ecef = {
        "SAT_ZENITH": np.array([42164.0, 0.0, 0.0]), # Direto no zênite (elevação 90°)
        "SAT_EAST": np.array([30000.0, 30000.0, 0.0]),
        "SAT_NORTH": np.array([30000.0, 0.0, 30000.0]),
        "SAT_UNDERGROUND": np.array([-42164.0, 0.0, 0.0]), # Do outro lado da Terra (elevação negativa)
    }

    # Estratégia com máscara de 5°
    strategy_mask = ElevationMaskDopStrategy(mask_angle_deg=5.0)
    res = strategy_mask.calculate_dop(station, sats_ecef)

    # Apenas 3 satélites visíveis acima do horizonte -> deve ser inválido
    assert not res.is_valid
    assert res.visible_satellites_count == 3


def test_weighted_elevation_dop_computes_finite_values():
    """Testa a estratégia ponderada pela elevação com 4 satélites bem distribuídos."""
    strategy = WeightedElevationDopStrategy(min_elevation_deg=5.0)
    station = GeodeticCoordinatesVO(-15.7975, -47.8633, 1.0) # Brasília

    # 4 satélites com boa cobertura sobre Brasília
    sats_ecef = {
        "GEO_1": np.array([36000.0, -20000.0, 0.0]),
        "GEO_2": np.array([28000.0, -31000.0, 0.0]),
        "IGSO_ZENITH": np.array([25000.0, -28000.0, -18000.0]),
        "IGSO_EAST": np.array([38000.0, -15000.0, -5000.0]),
    }

    res = strategy.calculate_dop(station, sats_ecef)
    assert res.is_valid
    assert res.pdop > 0.0
    assert res.hdop > 0.0
    assert res.vdop > 0.0
    assert res.gdop >= res.pdop
