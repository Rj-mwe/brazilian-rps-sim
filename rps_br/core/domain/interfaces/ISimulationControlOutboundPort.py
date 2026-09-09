"""
Porta de Saída Abstrata (Hexagonal): ISimulationControlOutboundPort
===================================================================
Define o contrato para qualquer adaptador de motor de física, visualizador
ou hardware (ex: Gazebo Sim, Cesium, Unreal) receber ordens de controle
de simulação emitidas pelo Core do domínio.
"""

from abc import ABC, abstractmethod


class ISimulationControlOutboundPort(ABC):
    """Contrato que adaptadores externos devem implementar para atuar na simulação."""

    @abstractmethod
    def pause_simulation(self) -> bool:
        """Pausa o motor de simulação físico/gráfico."""
        pass

    @abstractmethod
    def resume_simulation(self) -> bool:
        """Retoma a execução do motor de simulação."""
        pass

    @abstractmethod
    def step_simulation(self, steps: int = 1) -> bool:
        """Avança o motor de simulação em N passos discretos."""
        pass

    @abstractmethod
    def set_simulation_rate(self, multiplier: float) -> bool:
        """Ajusta a taxa de aceleração temporal do motor de simulação."""
        pass
