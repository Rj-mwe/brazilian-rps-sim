import warnings
warnings.warn(
    "Importing ZenithVisibilitySpec from 'brazilian_rps_sim.core.domain.specifications' is deprecated. "
    "Use the Level 2 canonical subdomains instead. This facade will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

"""Backward-compatibility facade."""
from brazilian_rps_sim.core.domain.astrodynamics.specifications.ZenithVisibilitySpec import ZenithVisibilitySpec

__all__ = ["ZenithVisibilitySpec"]
