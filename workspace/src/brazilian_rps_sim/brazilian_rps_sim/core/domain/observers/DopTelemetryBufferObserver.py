#!/usr/bin/env python3
"""
Concrete Observer: DopTelemetryBufferObserver
Armazena a série temporal histórica de métricas DOP para análises estatísticas,
gráficos de cobertura contínua de 24h e relatórios de missão.
"""

from typing import Dict, List, Tuple
from brazilian_rps_sim.core.domain.observers.IDopObserver import IDopObserver
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO


class DopTelemetryBufferObserver(IDopObserver):
    """Observador acumulador de telemetria histórica por estação."""

    def __init__(self):
        # Dicionário: {station_name: [(timestamp, DopResultVO)]}
        self.history: Dict[str, List[Tuple[float, DopResultVO]]] = {}

    def on_dop_calculated(
        self,
        station_name: str,
        coordinates: GeodeticCoordinatesVO,
        dop_result: DopResultVO,
        timestamp_sec: float
    ) -> None:
        if station_name not in self.history:
            self.history[station_name] = []
        self.history[station_name].append((timestamp_sec, dop_result))

    def get_average_pdop(self, station_name: str) -> float:
        """Calcula a média de PDOP para uma dada estação."""
        records = self.history.get(station_name, [])
        valid_pdops = [res.pdop for _, res in records if res.is_valid and res.pdop < 100.0]
        return sum(valid_pdops) / len(valid_pdops) if valid_pdops else float('inf')

    def get_coverage_availability_percentage(self, station_name: str, max_pdop: float = 6.0) -> float:
        """Calcula a disponibilidade percentual de cobertura útil (PDOP <= max_pdop)."""
        records = self.history.get(station_name, [])
        if not records:
            return 0.0
        available_count = sum(1 for _, res in records if res.is_valid and res.pdop <= max_pdop)
        return (available_count / len(records)) * 100.0
