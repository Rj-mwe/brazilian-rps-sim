#!/usr/bin/env python3
"""
Value Object: DopResultVO
Representa os índices de Diluição de Precisão Geométrica (DOP - Dilution of Precision)
para um receptor GNSS/RPS-BR na superfície terrestre.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DopResultVO:
    """Métricas de Diluição de Precisão Geométrica (DOP)."""
    gdop: float  # Geometric DOP (3D Pos + Clock Bias)
    pdop: float  # Position DOP (3D Pos)
    hdop: float  # Horizontal DOP (2D East-North)
    vdop: float  # Vertical DOP (1D Up)
    tdop: float  # Time DOP (Clock Bias)
    visible_satellites_count: int
    is_valid: bool = True
    error_message: Optional[str] = None

    @property
    def quality_rating(self) -> str:
        """Classificação internacional de qualidade da geometria GNSS."""
        if not self.is_valid or self.visible_satellites_count < 4:
            return "POOR_COVERAGE"
        if self.pdop < 2.0:
            return "EXCELLENT"
        if self.pdop < 4.0:
            return "GOOD"
        if self.pdop < 6.0:
            return "MODERATE"
        return "FAIR"

    @classmethod
    def invalid(cls, reason: str, visible_count: int = 0) -> 'DopResultVO':
        """Fábrica para resultados inválidos (ex: satélites insuficientes < 4 ou matriz singular)."""
        return cls(
            gdop=float('inf'),
            pdop=float('inf'),
            hdop=float('inf'),
            vdop=float('inf'),
            tdop=float('inf'),
            visible_satellites_count=visible_count,
            is_valid=False,
            error_message=reason
        )
