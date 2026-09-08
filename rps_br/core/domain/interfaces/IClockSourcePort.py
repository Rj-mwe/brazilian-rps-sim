"""
Porta de Entrada/Saída para sincronização e leitura do relógio de simulação.
"""

from abc import ABC, abstractmethod

class IClockSourcePort(ABC):
    @abstractmethod
    def get_current_sim_time_sec(self) -> float:
        """Retorna o tempo de simulação atual em segundos."""
        pass
