#!/usr/bin/env python3
"""
Application Use Case: CalculateGroundStationDopUseCase
Orquestra o cálculo de DOP para múltiplas estações de solo brasileiras
integrando os padrões Strategy (algoritmo de DOP) e Observer (notificação de eventos).
"""

from typing import Dict, Optional
import numpy as np

from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO
from brazilian_rps_sim.core.domain.strategies.IDopCalculationStrategy import IDopCalculationStrategy
from brazilian_rps_sim.core.domain.strategies.StandardLeastSquaresDopStrategy import StandardLeastSquaresDopStrategy
from brazilian_rps_sim.core.domain.observers.DopSubject import DopSubject
from brazilian_rps_sim.core.domain.observers.IDopObserver import IDopObserver


# Estações terrestres de referência no Brasil para monitoramento da constelação RPS-BR
DEFAULT_BRAZILIAN_GROUND_STATIONS = {
    "Brasília (DF - Centro)": GeodeticCoordinatesVO(-15.7975, -47.8633, 1.172),
    "Manaus (AM - Norte)": GeodeticCoordinatesVO(-3.1190, -60.0217, 0.092),
    "Rio de Janeiro (RJ - Sudeste)": GeodeticCoordinatesVO(-22.9068, -43.1729, 0.005),
    "Porto Alegre (RS - Sul)": GeodeticCoordinatesVO(-30.0346, -51.2177, 0.010),
    "Fortaleza (CE - Nordeste)": GeodeticCoordinatesVO(-3.7172, -38.5433, 0.016),
}


class CalculateGroundStationDopUseCase:
    """Caso de uso de aplicação para avaliação contínua da cobertura e precisão geométrica."""

    def __init__(
        self,
        strategy: Optional[IDopCalculationStrategy] = None,
        ground_stations: Optional[Dict[str, GeodeticCoordinatesVO]] = None
    ):
        self.strategy: IDopCalculationStrategy = strategy or StandardLeastSquaresDopStrategy()
        self.ground_stations: Dict[str, GeodeticCoordinatesVO] = ground_stations or DEFAULT_BRAZILIAN_GROUND_STATIONS
        self.subject = DopSubject()

    def set_strategy(self, strategy: IDopCalculationStrategy) -> None:
        """Permite a troca dinâmica da estratégia algorítmica em tempo de execução (Strategy Pattern)."""
        self.strategy = strategy

    def attach_observer(self, observer: IDopObserver) -> None:
        """Registra um observador para receber métricas de DOP (Observer Pattern)."""
        self.subject.attach(observer)

    def detach_observer(self, observer: IDopObserver) -> None:
        """Remove um observador registrado."""
        self.subject.detach(observer)

    def execute(
        self,
        satellite_positions_ecef: Dict[str, np.ndarray],
        timestamp_sec: float
    ) -> Dict[str, DopResultVO]:
        """
        Executa o cálculo de DOP para todas as estações de solo e notifica os observadores.
        
        :param satellite_positions_ecef: Dicionário {sat_name: pos_ecef_3d_km}.
        :param timestamp_sec: Tempo da simulação em segundos.
        :return: Dicionário {station_name: DopResultVO}.
        """
        results: Dict[str, DopResultVO] = {}

        for station_name, coords in self.ground_stations.items():
            dop_res = self.strategy.calculate_dop(coords, satellite_positions_ecef)
            results[station_name] = dop_res
            self.subject.notify_all(station_name, coords, dop_res, timestamp_sec)

        return results
