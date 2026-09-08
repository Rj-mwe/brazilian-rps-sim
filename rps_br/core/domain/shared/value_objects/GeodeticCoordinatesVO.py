"""
Value Object imutável para coordenadas geodésicas na Terra (WGS-84).
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class GeodeticCoordinatesVO:
    latitude_deg: float
    longitude_deg: float
    altitude_km: float

    def __post_init__(self):
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise ValueError(f"Latitude inválida: {self.latitude_deg}°. Deve estar entre -90° e +90°.")
        # Normaliza longitude no intervalo [-180, +180]
        lon = (self.longitude_deg + 180.0) % 360.0 - 180.0
        object.__setattr__(self, 'longitude_deg', lon)
