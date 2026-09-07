import warnings
warnings.warn(
    "Importing IDopObserver from 'brazilian_rps_sim.core.domain.observers' is deprecated. "
    "Use the Level 2 canonical subdomains instead. This facade will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

"""Backward-compatibility facade."""
from brazilian_rps_sim.core.domain.navigation_pvt.observers.IDopObserver import IDopObserver

__all__ = ["IDopObserver"]
