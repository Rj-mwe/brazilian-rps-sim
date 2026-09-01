#!/usr/bin/env python3
"""
Concrete Observer: DopAlertThresholdObserver
Monitora limiares de segurança de navegação (ex: PDOP crítico > 6.0 ou visibilidade < 4 satélites)
e emite alertas reativos imediatos.
"""

from typing import List, Callable, Optional
from brazilian_rps_sim.core.domain.observers.IDopObserver import IDopObserver
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class DopAlertThresholdObserver(IDopObserver):
    """Observador sentinela que detecta degradações geométricas e dispara alertas."""

    def __init__(
        self,
        max_allowed_pdop: float = 6.0,
        min_required_satellites: int = 4,
        alert_callback: Optional[Callable[[str, DopResultVO], None]] = None
    ):
        self.max_allowed_pdop = max_allowed_pdop
        self.min_required_satellites = min_required_satellites
        self.alert_callback = alert_callback
        self.active_alerts: List[str] = []

    def on_dop_calculated(
        self,
        station_name: str,
        coordinates: GeodeticCoordinatesVO,
        dop_result: DopResultVO,
        timestamp_sec: float
    ) -> None:
        alert_msg = None

        if not dop_result.is_valid or dop_result.visible_satellites_count < self.min_required_satellites:
            alert_msg = (
                f"🚨 [ALERTA-DOP] Estação '{station_name}': Falha de cobertura! "
                f"Satélites visíveis ({dop_result.visible_satellites_count}) < {self.min_required_satellites}."
            )
        elif dop_result.pdop > self.max_allowed_pdop:
            alert_msg = (
                f"⚠️ [ALERTA-DOP] Estação '{station_name}': Geometria degradada! "
                f"PDOP ({dop_result.pdop:.2f}) excedeu o limite máximo ({self.max_allowed_pdop:.2f})."
            )

        if alert_msg:
            self.active_alerts.append(alert_msg)
            if self.alert_callback:
                self.alert_callback(alert_msg, dop_result)
