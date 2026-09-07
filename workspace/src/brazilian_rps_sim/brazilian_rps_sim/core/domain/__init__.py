"""
Camada de Domínio Puro (Hexágono Modular - Nível 2)
===================================================
Contém as regras de negócio, a física aeroespacial e a mecânica matemática
particionada em Subdomínios Coesos com um Kernel Compartilhado (shared).
"""

from . import shared
from . import astrodynamics
from . import signal_propagation
from . import navigation_pvt

__all__ = ["shared", "astrodynamics", "signal_propagation", "navigation_pvt"]
