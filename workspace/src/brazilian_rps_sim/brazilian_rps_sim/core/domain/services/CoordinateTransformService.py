"""
Serviço de Domínio para conversões geométricas e transformações de referenciais espaciais (ECI, ECEF, WGS-84, ENU).
"""

import math
import numpy as np
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO

class CoordinateTransformService:
    OMEGA_EARTH_DEFAULT = 7.2921150e-5 # rad/s
    R_EARTH_DEFAULT = 6378.137         # km
    FLATTENING_DEFAULT = 1.0 / 298.257223563

    @classmethod
    def eci_to_ecef(cls, r_eci: np.ndarray, t_sec: float, omega_earth: float = OMEGA_EARTH_DEFAULT) -> np.ndarray:
        """Converte vetor de posição ECI J2000 para ECEF (Referencial Terrestre Fixo)."""
        theta = (omega_earth * t_sec) % (2.0 * math.pi)
        c, s = math.cos(theta), math.sin(theta)
        R_z = np.array([
            [c,  s, 0.0],
            [-s, c, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        return R_z @ r_eci

    @classmethod
    def ecef_to_geodetic(cls, r_ecef: np.ndarray, r_earth: float = R_EARTH_DEFAULT,
                          flattening: float = FLATTENING_DEFAULT) -> GeodeticCoordinatesVO:
        """Converte coordenadas cartesianas ECEF em Latitude Geodésica, Longitude e Altitude WGS-84."""
        x, y, z = float(r_ecef[0]), float(r_ecef[1]), float(r_ecef[2])
        lon_deg = math.degrees(math.atan2(y, x))

        p = math.sqrt(x**2 + y**2)
        e2 = 2.0 * flattening - flattening**2
        lat_rad = math.atan2(z, p * (1.0 - e2))

        for _ in range(10):
            N = r_earth / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
            lat_rad = math.atan2(z + e2 * N * math.sin(lat_rad), p)

        N = r_earth / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
        alt_km = p / math.cos(lat_rad) - N
        lat_deg = math.degrees(lat_rad)

        return GeodeticCoordinatesVO(lat_deg, lon_deg, alt_km)

    @classmethod
    def compute_topocentric_look_angles(cls, r_sat_ecef: np.ndarray, lat_gs_deg: float, lon_gs_deg: float,
                                        r_earth: float = R_EARTH_DEFAULT, flattening: float = FLATTENING_DEFAULT) -> tuple[float, float, float]:
        """Calcula Ângulo de Elevação (°), Azimute (°) e Distância Slant-Range (km) a partir de uma estação de solo."""
        lat_rad = math.radians(lat_gs_deg)
        lon_rad = math.radians(lon_gs_deg)

        e2 = 2.0 * flattening - flattening**2
        N = r_earth / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
        r_gs = np.array([
            N * math.cos(lat_rad) * math.cos(lon_rad),
            N * math.cos(lat_rad) * math.sin(lon_rad),
            N * (1.0 - e2) * math.sin(lat_rad)
        ], dtype=np.float64)

        rho_ecef = r_sat_ecef - r_gs
        range_km = float(np.linalg.norm(rho_ecef))

        R_enu = np.array([
            [-math.sin(lon_rad), math.cos(lon_rad), 0.0],
            [-math.sin(lat_rad) * math.cos(lon_rad), -math.sin(lat_rad) * math.sin(lon_rad), math.cos(lat_rad)],
            [math.cos(lat_rad) * math.cos(lon_rad), math.cos(lat_rad) * math.sin(lon_rad), math.sin(lat_rad)]
        ], dtype=np.float64)

        rho_enu = R_enu @ rho_ecef
        e, n, u = rho_enu[0], rho_enu[1], rho_enu[2]

        elevation_deg = math.degrees(math.atan2(u, math.sqrt(e**2 + n**2)))
        azimuth_deg = math.degrees(math.atan2(e, n)) % 360.0

        return elevation_deg, azimuth_deg, range_km
