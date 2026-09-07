"""
Módulo Legado: brazilian_rps_sim.astrodynamics
==============================================
DEPRECATED: A física orbital foi migrada para 'brazilian_rps_sim.core.domain.astrodynamics'
e o carregamento de configurações para 'brazilian_rps_sim.infrastructure.config'.

Mantido provisoriamente para retrocompatibilidade com scripts legados.
"""

import warnings
warnings.warn(
    "Importing from 'brazilian_rps_sim.astrodynamics' is deprecated. "
    "Use 'brazilian_rps_sim.core.domain.astrodynamics' for orbital physics or "
    "'brazilian_rps_sim.infrastructure.config' for YAML loaders.",
    DeprecationWarning,
    stacklevel=2
)

from brazilian_rps_sim.infrastructure.config.config_loader import (
    find_config_file,
    load_simulation_config,
)

__all__ = ["find_config_file", "load_simulation_config"]
