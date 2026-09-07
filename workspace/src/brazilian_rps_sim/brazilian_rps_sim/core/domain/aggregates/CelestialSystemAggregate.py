import warnings
warnings.warn(
    "Importing CelestialSystemAggregate from 'brazilian_rps_sim.core.domain.aggregates' is deprecated. "
    "Use the Level 2 canonical subdomains instead. This facade will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

"""Backward-compatibility facade."""
from brazilian_rps_sim.core.domain.astrodynamics.aggregates.CelestialSystemAggregate import CelestialSystemAggregate

__all__ = ["CelestialSystemAggregate"]
