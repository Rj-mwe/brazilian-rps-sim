#!/usr/bin/env python3
"""
Concrete Observer: DopLoggingObserver
Gera registros de log estruturados e formatados sobre as métricas de cobertura DOP.
"""

from brazilian_rps_sim.core.domain.observers.IDopObserver import IDopObserver
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class DopLoggingObserver(IDopObserver):
    """Observador que formata e registra as métricas DOP calculadas."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.last_log = ""

    def on_dop_calculated(
        self,
        station_name: str,
        coordinates: GeodeticCoordinatesVO,
        dop_result: DopResultVO,
        timestamp_sec: float
    ) -> None:
        if not dop_result.is_valid:
            self.last_log = (
                f"📡 [DOP-Log] Estação '{station_name}': COBERTURA INVÁLIDA "
                f"({dop_result.error_message}, Visíveis: {dop_result.visible_satellites_count})"
            )
        else:
            self.last_log = (
                f"📡 [DOP-Log] Estação '{station_name}' (t={timestamp_sec/3600:.1f}h) | "
                f"Satélites: {dop_result.visible_satellites_count} | "
                f"PDOP: {dop_result.pdop:.2f} ({dop_result.quality_rating}) | "
                f"HDOP: {dop_result.hdop:.2f} | VDOP: {dop_result.vdop:.2f} | GDOP: {dop_result.gdop:.2f}"
            )

        if self.verbose:
            print(self.last_log)
