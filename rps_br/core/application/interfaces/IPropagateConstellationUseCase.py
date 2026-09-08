"""
Porta de Entrada (Interface de Use Case) para propagação orbital da constelação.
"""

from abc import ABC, abstractmethod
from rps_br.core.application.dtos.SimulationDTOs import (
    SimulationStepRequestDTO,
    ConstellationStatusResponseDTO
)

class IPropagateConstellationUseCase(ABC):
    @abstractmethod
    def execute(self, request: SimulationStepRequestDTO) -> ConstellationStatusResponseDTO:
        """Executa a propagação da constelação para o instante especificado no DTO."""
        pass
