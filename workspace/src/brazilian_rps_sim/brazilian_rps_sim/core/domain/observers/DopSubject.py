#!/usr/bin/env python3
"""
Observer Pattern Subject: DopSubject
Gerencia o registro, cancelamento e despacho de notificações para observadores de DOP.
"""

from typing import List
from brazilian_rps_sim.core.domain.observers.IDopObserver import IDopObserver
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class DopSubject:
    """Sujeito observável que notifica observadores registrados sobre eventos de DOP."""

    def __init__(self):
        self._observers: List[IDopObserver] = []

    def attach(self, observer: IDopObserver) -> None:
        """Registra um novo observador."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: IDopObserver) -> None:
        """Remove um observador registrado."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_all(
        self,
        station_name: str,
        coordinates: GeodeticCoordinatesVO,
        dop_result: DopResultVO,
        timestamp_sec: float
    ) -> None:
        """Dispara a notificação para todos os observadores cadastrados."""
        for observer in self._observers:
            observer.on_dop_calculated(station_name, coordinates, dop_result, timestamp_sec)

    @property
    def observer_count(self) -> int:
        return len(self._observers)
