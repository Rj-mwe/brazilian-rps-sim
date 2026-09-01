#!/usr/bin/env python3
"""
Strategy Pattern Interface: IDopCalculationStrategy
Permite trocar dinamicamente o algoritmo de cálculo de Diluição de Precisão (DOP)
(ex: Mínimos Quadrados Clássico, Máscara de Elevação, Ponderação Troposférica/Elevação).
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np

from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class IDopCalculationStrategy(ABC):
    """Interface abstrata para algoritmos de cálculo de métricas DOP."""

    @abstractmethod
    def calculate_dop(
        self,
        station_coord: GeodeticCoordinatesVO,
        satellite_positions_ecef: Dict[str, np.ndarray]
    ) -> DopResultVO:
        """
        Calcula as métricas DOP para uma estação de solo com base nas posições dos satélites.
        
        :param station_coord: Coordenadas geodésicas (Lat, Lon, Alt) da estação de solo.
        :param satellite_positions_ecef: Dicionário {sat_name: r_ecef_3d} das posições dos satélites em km.
        :return: DopResultVO com GDOP, PDOP, HDOP, VDOP, TDOP.
        """
        pass
