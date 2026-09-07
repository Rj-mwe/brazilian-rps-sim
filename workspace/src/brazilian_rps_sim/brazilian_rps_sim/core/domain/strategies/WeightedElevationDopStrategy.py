import warnings
warnings.warn(
    "Importing WeightedElevationDopStrategy from 'brazilian_rps_sim.core.domain.strategies' is deprecated. "
    "Use the Level 2 canonical subdomains instead. This facade will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

"""Backward-compatibility facade."""
from brazilian_rps_sim.core.domain.navigation_pvt.strategies.WeightedElevationDopStrategy import WeightedElevationDopStrategy

__all__ = ["WeightedElevationDopStrategy"]
