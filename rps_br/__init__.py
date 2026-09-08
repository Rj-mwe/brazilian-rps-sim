"""
Brazilian RPS Sim (Simulador do Sistema de Posicionamento Regional Brasileiro)
==============================================================================
Pacote ROS 2 e biblioteca científica de simulação sob a Arquitetura Hexagonal Modular (Nível 2).
"""

__version__ = "1.0.0"

from . import core
from . import adapters
from . import infrastructure

__all__ = [
    "core",
    "adapters",
    "infrastructure",
]
