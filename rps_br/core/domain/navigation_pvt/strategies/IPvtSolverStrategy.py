"""
Interface: IPvtSolverStrategy
=============================
Define o contrato do padrão Strategy para a família de algoritmos de resolução
de navegação PVT (Mínimos Quadrados Ordinários, Mínimos Quadrados Ponderados - WLS,
Filtro de Kalman Estendido - EKF).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.signal_propagation.value_objects.PseudorangeMeasurementVO import PseudorangeMeasurementVO
from rps_br.core.domain.navigation_pvt.value_objects.PvtSolutionVO import PvtSolutionVO


class IPvtSolverStrategy(ABC):
    """
    Interface formal para algoritmos de cálculo da solução de navegação PVT.
    """

    @abstractmethod
    def solve(
        self,
        measurements: List[PseudorangeMeasurementVO],
        satellites_ecef_m: Dict[str, Vector3DVO],
        initial_guess_ecef_m: Optional[Vector3DVO] = None,
        true_position_ecef_m: Optional[Vector3DVO] = None,
        tolerance_m: float = 1e-4,
        max_iterations: int = 15,
    ) -> PvtSolutionVO:
        """
        Calcula a posição 3D do usuário e o desvio do relógio local.

        Parâmetros:
            measurements: Lista de observáveis de pseudodistância dos satélites visíveis.
            satellites_ecef_m: Dicionário mapeando satellite_id -> vetor de posição ECEF em metros.
            initial_guess_ecef_m: Posição inicial estimada (se None, adota centro da Terra ou ponto médio).
            true_position_ecef_m: Posição verdadeira conhecida (opcional, para computar erro nos testes).
            tolerance_m: Tolerância de convergência do incremento de posição em metros (padrão 0.1 mm).
            max_iterations: Limite máximo de iterações do método de Newton-Raphson / Gauss-Newton.

        Retorna:
            PvtSolutionVO com a estimativa convergida, resíduos e métricas de qualidade.
        """
        pass
