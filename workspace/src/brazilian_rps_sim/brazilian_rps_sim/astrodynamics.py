#!/usr/bin/env python3
"""
Módulo de Astrodinâmica e Mecânica Orbital para o Sistema de Posicionamento Regional Brasileiro (RPS-BR)
"""

import math
import numpy as np

MU_EARTH = 398600.4418          # km^3 / s^2
R_EARTH = 6378.137             # km
FLATTENING = 1.0 / 298.257223563
J2 = 1.08263e-3
OMEGA_EARTH = 7.2921150e-5      # rad/s
SIDEREAL_DAY = 2.0 * math.pi / OMEGA_EARTH # ~86164.09 s
A_GEO = (MU_EARTH / (OMEGA_EARTH**2))**(1.0 / 3.0) # ~42164.14 km

class OrbitalElements:
    def __init__(self, name: str, sat_type: str, a: float, e: float, i_deg: float,
                 raan_deg: float, argp_deg: float, m0_deg: float):
        self.name = name
        self.sat_type = sat_type # "GEO" ou "IGSO"
        self.a = a
        self.e = e
        self.i = math.radians(i_deg)
        self.raan = math.radians(raan_deg % 360.0)
        self.argp = math.radians(argp_deg % 360.0)
        self.m0 = math.radians(m0_deg % 360.0)
        self.n = math.sqrt(MU_EARTH / (self.a**3))

def get_brazilian_rps_constellation() -> list[OrbitalElements]:
    """
    Retorna os satélites de referência:
    - Sat 1: GEO Central (Geoestacionário fixo sobre Brasília, 50°W)
    - Sat 2: IGSO-1 (Geossíncrono Inclinado a 29°, descreve a Figura-8 em 24h)
    """
    return [
        # Satélite 1: GEO Âncora
        OrbitalElements("RPS-GEO (Centro/BSB)", "GEO", A_GEO, 0.0, 0.0, 0.0, 0.0, 310.0), # 50.0° W

        # Satélite 2: IGSO Figura-8
        OrbitalElements("RPS-IGSO (Figura-8)", "IGSO", A_GEO, 0.06, 29.0, 310.0, 270.0, 0.0), # 50.0° W
    ]

def solve_kepler(M: float, e: float, tol: float = 1e-10) -> float:
    M = M % (2.0 * math.pi)
    E = M if e < 0.8 else math.pi
    for _ in range(30):
        f = E - e * math.sin(E) - M
        f_prime = 1.0 - e * math.cos(E)
        dE = -f / f_prime
        E += dE
        if abs(dE) < tol:
            break
    return E

def true_anomaly_from_eccentric(E: float, e: float) -> float:
    sin_nu = (math.sqrt(1.0 - e**2) * math.sin(E)) / (1.0 - e * math.cos(E))
    cos_nu = (math.cos(E) - e) / (1.0 - e * math.cos(E))
    return math.atan2(sin_nu, cos_nu)

def propagate_orbit_eci(coe: OrbitalElements, t_sec: float) -> np.ndarray:
    p = coe.a * (1.0 - coe.e**2)
    j2_factor = 1.5 * J2 * (R_EARTH / p)**2 * coe.n
    draan_dt = -j2_factor * math.cos(coe.i)
    dargp_dt = j2_factor * (2.0 - 2.5 * (math.sin(coe.i)**2))

    raan_t = coe.raan + draan_dt * t_sec
    argp_t = coe.argp + dargp_dt * t_sec
    M_t = coe.m0 + coe.n * t_sec

    E_t = solve_kepler(M_t, coe.e)
    nu_t = true_anomaly_from_eccentric(E_t, coe.e)
    r_mag = coe.a * (1.0 - coe.e * math.cos(E_t))

    r_pqw = np.array([
        r_mag * math.cos(nu_t),
        r_mag * math.sin(nu_t),
        0.0
    ])

    c_O, s_O = math.cos(raan_t), math.sin(raan_t)
    c_i, s_i = math.cos(coe.i), math.sin(coe.i)
    c_w, s_w = math.cos(argp_t), math.sin(argp_t)

    R_pqw2eci = np.array([
        [c_O * c_w - s_O * s_w * c_i, -c_O * s_w - s_O * c_w * c_i,  s_O * s_i],
        [s_O * c_w + c_O * s_w * c_i, -s_O * s_w + c_O * c_w * c_i, -c_O * s_i],
        [s_w * s_i,                    c_w * s_i,                    c_i       ]
    ])

    return R_pqw2eci @ r_pqw

def eci_to_ecef(r_eci: np.ndarray, t_sec: float, theta0: float = 0.0) -> np.ndarray:
    theta = theta0 + OMEGA_EARTH * t_sec
    c_th, s_th = math.cos(theta), math.sin(theta)
    R_eci2ecef = np.array([
        [ c_th,  s_th, 0.0],
        [-s_th,  c_th, 0.0],
        [  0.0,   0.0, 1.0]
    ])
    return R_eci2ecef @ r_eci

def ecef_to_lat_lon_alt(r_ecef: np.ndarray) -> tuple[float, float, float]:
    x, y, z = r_ecef
    lon_rad = math.atan2(y, x)
    p = math.hypot(x, y)
    lat_rad = math.atan2(z, p * (1.0 - (2.0 * FLATTENING - FLATTENING**2)))
    for _ in range(5):
        N = R_EARTH / math.sqrt(1.0 - (2.0 * FLATTENING - FLATTENING**2) * math.sin(lat_rad)**2)
        alt = p / math.cos(lat_rad) - N
        lat_rad = math.atan2(z, p * (1.0 - (2.0 * FLATTENING - FLATTENING**2) * (N / (N + alt))))

    lat_deg = math.degrees(lat_rad)
    lon_deg = math.degrees(lon_rad)
    lon_deg = ((lon_deg + 180.0) % 360.0) - 180.0
    return lat_deg, lon_deg, alt

def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    e2 = 2.0 * FLATTENING - FLATTENING**2
    N = R_EARTH / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
    x = (N + alt_km) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (N + alt_km) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (N * (1.0 - e2) + alt_km) * math.sin(lat_rad)
    return np.array([x, y, z])

def compute_elevation_azimuth(user_lat_deg: float, user_lon_deg: float, sat_r_ecef: np.ndarray) -> tuple[float, float, float]:
    user_ecef = geodetic_to_ecef(user_lat_deg, user_lon_deg, 0.0)
    rho_ecef = sat_r_ecef - user_ecef
    dist = np.linalg.norm(rho_ecef)

    lat_rad = math.radians(user_lat_deg)
    lon_rad = math.radians(user_lon_deg)

    s_lat, c_lat = math.sin(lat_rad), math.cos(lat_rad)
    s_lon, c_lon = math.sin(lon_rad), math.cos(lon_rad)

    R_ecef2enu = np.array([
        [-s_lon,          c_lon,         0.0  ],
        [-s_lat * c_lon, -s_lat * s_lon, c_lat],
        [ c_lat * c_lon,  c_lat * s_lon, s_lat]
    ])

    rho_enu = R_ecef2enu @ rho_ecef
    e, n, u = rho_enu

    elevation_rad = math.asin(u / dist)
    azimuth_rad = math.atan2(e, n)
    azimuth_deg = (math.degrees(azimuth_rad) + 360.0) % 360.0

    return math.degrees(elevation_rad), azimuth_deg, dist
