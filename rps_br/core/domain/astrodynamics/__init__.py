"""
Subdomínio: Astrodinâmica e Mecânica Celeste
============================================
Propagação orbital kepleriana, perturbações orbitais e transformações de coordenadas.
"""

from .services.KeplerSolverService import KeplerSolverService
from .services.CoordinateTransformService import CoordinateTransformService
from .aggregates.SatelliteAggregate import SatelliteAggregate
from .aggregates.ConstellationAggregate import ConstellationAggregate
from .aggregates.CelestialSystemAggregate import CelestialSystemAggregate
from .value_objects.KeplerianElementsVO import KeplerianElementsVO
from .specifications.ZenithVisibilitySpec import ZenithVisibilitySpec
from .policies.KeplerianPropagationPolicy import KeplerianPropagationPolicy
from .exceptions.OrbitalExceptions import (
    DomainException,
    OrbitalSingularityException,
    InvalidSatelliteParametersException,
)

__all__ = [
    "KeplerSolverService",
    "CoordinateTransformService",
    "SatelliteAggregate",
    "ConstellationAggregate",
    "CelestialSystemAggregate",
    "KeplerianElementsVO",
    "ZenithVisibilitySpec",
    "KeplerianPropagationPolicy",
    "DomainException",
    "OrbitalSingularityException",
    "InvalidSatelliteParametersException",
]
