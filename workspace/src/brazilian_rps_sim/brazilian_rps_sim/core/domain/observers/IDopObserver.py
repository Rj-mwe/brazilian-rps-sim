#!/usr/bin/env python3
"""
Observer Pattern Interface: IDopObserver
Permite que múltiplos observadores independentes e desacoplados sejam notificados
sempre que métricas de Diluição de Precisão (DOP) forem recalculadas.
"""

from abc import ABC, abstractmethod
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class IDopObserver(ABC):
    """Interface abstrata de Observador de métricas DOP."""

    @abstractmethod
    def on_dop_calculated(
        self,
        station_name: str,
        coordinates: GeodeticCoordinatesVO,
        dop_result: DopResultVO,
        timestamp_sec: float
    ) -> None:
        """
        Método de callback disparado pelo DopSubject quando um novo cálculo de DOP é concluído.
        """
        pass
