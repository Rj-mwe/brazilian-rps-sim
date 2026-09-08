"""
Módulo Legado: rps_br.astrodynamics
==============================================
DEPRECATED: A física orbital foi migrada para 'rps_br.core.domain.astrodynamics'
e o carregamento de configurações para 'rps_br.infrastructure.config'.

Mantido provisoriamente para retrocompatibilidade com scripts legados.
"""

import warnings
warnings.warn(
    "Importing from 'rps_br.astrodynamics' is deprecated. "
    "Use 'rps_br.core.domain.astrodynamics' for orbital physics or "
    "'rps_br.infrastructure.config' for YAML loaders.",
    DeprecationWarning,
    stacklevel=2
)

from rps_br.infrastructure.config.config_loader import (
    find_config_file,
    load_simulation_config,
)

__all__ = ["find_config_file", "load_simulation_config"]
