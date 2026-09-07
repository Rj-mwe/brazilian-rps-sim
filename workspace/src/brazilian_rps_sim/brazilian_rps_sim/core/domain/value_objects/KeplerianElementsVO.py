import warnings
warnings.warn(
    "Importing KeplerianElementsVO from 'brazilian_rps_sim.core.domain.value_objects' is deprecated. "
    "Use the Level 2 canonical subdomains instead. This facade will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

"""Backward-compatibility facade."""
from brazilian_rps_sim.core.domain.astrodynamics.value_objects.KeplerianElementsVO import KeplerianElementsVO

__all__ = ["KeplerianElementsVO"]
