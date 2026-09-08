"""
Kernel Compartilhado de Domínio (Shared Kernel)
================================================
Grandezas matemáticas, geométricas e operadores universais imutáveis
compartilhados por todos os subdomínios do Core.
"""

from .value_objects import Vector3DVO, QuaternionVO, GeodeticCoordinatesVO

__all__ = ["Vector3DVO", "QuaternionVO", "GeodeticCoordinatesVO"]
