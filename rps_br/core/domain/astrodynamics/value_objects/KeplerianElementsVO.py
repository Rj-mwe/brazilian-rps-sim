"""
Value Object imutável para os 6 Elementos Orbitais Keplerianos Clássicos (COE).
"""

from dataclasses import dataclass
import math

@dataclass(frozen=True)
class KeplerianElementsVO:
    semi_major_axis_km: float
    eccentricity: float
    inclination_rad: float
    raan_rad: float
    arg_perigee_rad: float
    mean_anomaly_rad: float

    def __post_init__(self):
        if self.semi_major_axis_km <= 0.0:
            raise ValueError(f"Semieixo maior deve ser positivo: {self.semi_major_axis_km}")
        if not (0.0 <= self.eccentricity < 1.0):
            raise ValueError(f"Excentricidade para órbita elíptica deve estar em [0, 1): {self.eccentricity}")

    @classmethod
    def from_degrees(cls, a_km: float, e: float, inc_deg: float, raan_deg: float,
                     argp_deg: float, m0_deg: float) -> 'KeplerianElementsVO':
        return cls(
            semi_major_axis_km=float(a_km),
            eccentricity=float(e),
            inclination_rad=math.radians(float(inc_deg)),
            raan_rad=math.radians(float(raan_deg) % 360.0),
            arg_perigee_rad=math.radians(float(argp_deg) % 360.0),
            mean_anomaly_rad=math.radians(float(m0_deg) % 360.0)
        )

    def period_sec(self, mu: float = 398600.4418) -> float:
        """Calcula o período orbital Kepleriano T = 2π √(a³ / μ)."""
        return 2.0 * math.pi * math.sqrt((self.semi_major_axis_km**3) / mu)

    def mean_motion_rad_s(self, mu: float = 398600.4418) -> float:
        """Calcula o movimento médio n = √(μ / a³)."""
        return math.sqrt(mu / (self.semi_major_axis_km**3))
