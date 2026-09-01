#!/usr/bin/env python3
"""
Concrete Strategy: ElevationMaskDopStrategy
Aplica uma máscara de corte estrita de elevação (ex: 10° ou 15° de elevação mínima)
para simular a operação real de receptores em cenários urbanos/canions ou com obstruções de relevo.
"""

from typing import Dict
import numpy as np

from brazilian_rps_sim.core.domain.strategies.StandardLeastSquaresDopStrategy import StandardLeastSquaresDopStrategy
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class ElevationMaskDopStrategy(StandardLeastSquaresDopStrategy):
    """Estratégia DOP com máscara de elevação configurável (padrão: 10.0°)."""

    def __init__(self, mask_angle_deg: float = 10.0):
        super().__init__(min_elevation_deg=mask_angle_deg)
        self.mask_angle_deg = mask_angle_deg
