"""
Porta de Entrada (Interface de Use Case) para propagação orbital da constelação.
"""

from abc import ABC, abstractmethod
from brazilian_rps_sim.core.application.dtos.SimulationDTOs import (
    SimulationStepRequestDTO,
    ConstellationStatusResponseDTO
)

class IPropagateConstellationUseCase(ABC):
    @abstractmethod
    def execute(self, request: SimulationStepRequestDTO) -> ConstellationStatusResponseDTO:
        """Executa a propagação da constelação para o instante especificado no DTO."""
        pass
