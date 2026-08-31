#!/usr/bin/env python3
"""
Módulo de Astrodinâmica e Mecânica Orbital para o Sistema de Posicionamento Regional Brasileiro (RPS-BR)
com suporte à leitura declarativa de parâmetros via arquivo YAML.
"""

import os
import math
import yaml
import numpy as np

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:
    get_package_share_directory = None

# Constantes Gravitacionais e Geodésicas Padrão (WGS-84)
MU_EARTH = 398600.4418          # km^3 / s^2
R_EARTH = 6378.137             # km
FLATTENING = 1.0 / 298.257223563
J2 = 1.08263e-3
OMEGA_EARTH = 7.2921150e-5      # rad/s
SIDEREAL_DAY = 2.0 * math.pi / OMEGA_EARTH # ~86164.09 s
A_GEO = (MU_EARTH / (OMEGA_EARTH**2))**(1.0 / 3.0) # ~42164.14 km

class OrbitalElements:
    def __init__(self, name: str, sat_type: str, a: float, e: float, i_deg: float,
                 raan_deg: float, argp_deg: float, m0_deg: float, station_lon_deg: float = 0.0):
        self.name = name
        self.sat_type = sat_type # "GEO" ou "IGSO"
        self.a = float(a)
        self.e = float(e)
        self.i = math.radians(float(i_deg))
        self.raan = math.radians(float(raan_deg) % 360.0)
        self.argp = math.radians(float(argp_deg) % 360.0)
        self.m0 = math.radians(float(m0_deg) % 360.0)
        self.station_lon_deg = float(station_lon_deg)
        self.n = math.sqrt(MU_EARTH / (self.a**3))

    def __repr__(self):
        return f"<OrbitalElements {self.name} [{self.sat_type}] a={self.a:.1f}km e={self.e:.3f} i={math.degrees(self.i):.1f}°>"

def find_config_file(filename: str = 'simulation_parameters.yaml') -> str:
    """Busca o arquivo de configuração YAML no pacote ROS 2 ou no caminho local."""
    paths_to_check = []
    if get_package_share_directory:
        try:
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            paths_to_check.append(os.path.join(pkg_share, 'config', filename))
        except Exception:
            pass

    # Caminhos relativos de desenvolvimento
    current_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_check.append(os.path.join(current_dir, '..', 'config', filename))
    paths_to_check.append(os.path.join('/home/rjgamito/Projetos/Engenharia/Aeroespacial/brazilian-rps-sim/workspace/src/brazilian_rps_sim/config', filename))

    for p in paths_to_check:
        if os.path.exists(p):
            return os.path.abspath(p)
    return ""

def load_simulation_config(config_path: str = None) -> dict:
    """Carrega o dicionário de configurações do arquivo YAML."""
    if not config_path:
        config_path = find_config_file()
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Suporta formato ROS 2 com /** / ros__parameters
            if isinstance(data, dict):
                if '/**' in data and 'ros__parameters' in data['/**']:
                    return data['/**']['ros__parameters']
                return data
            return {}
    return {}

def get_brazilian_rps_constellation(config_path: str = None) -> list[OrbitalElements]:
    """
    Retorna a lista completa de satélites da constelação do RPS-BR carregada do YAML:
    - 3 GEO (Oeste 70°W, Centro 50°W, Leste 35°W)
    - 4 IGSO (Figura-8 inclinados em 4 planos de RAAN)
    """
    cfg = load_simulation_config(config_path)
    sats_cfg = cfg.get('constellation', {}).get('satellites', [])

    if sats_cfg:
        constellation = []
        for s in sats_cfg:
            elem = OrbitalElements(
                name=s.get('name', f"SAT-{s.get('id', 1)}"),
                sat_type=s.get('type', 'GEO'),
                a=s.get('semi_major_axis_km', A_GEO),
                e=s.get('eccentricity', 0.0),
                i_deg=s.get('inclination_deg', 0.0),
                raan_deg=s.get('raan_deg', 0.0),
                argp_deg=s.get('arg_perigee_deg', 0.0),
                m0_deg=s.get('mean_anomaly_deg', 0.0),
                station_lon_deg=s.get('station_longitude_deg', 0.0)
            )
            constellation.append(elem)
        return constellation

    # Fallback padrão caso o YAML não seja localizado
    return [
        OrbitalElements("RPS-GEO-1 (Oeste/Amazônia)", "GEO", A_GEO, 0.0, 0.0, 0.0, 0.0, 290.0, -70.0),
        OrbitalElements("RPS-GEO-2 (Centro/BSB)", "GEO", A_GEO, 0.0, 0.0, 0.0, 0.0, 310.0, -50.0),
        OrbitalElements("RPS-GEO-3 (Leste/Atlântico)", "GEO", A_GEO, 0.0, 0.0, 0.0, 0.0, 325.0, -35.0),
        OrbitalElements("RPS-IGSO-1", "IGSO", A_GEO, 0.06, 29.0, 310.0, 270.0, 0.0),
        OrbitalElements("RPS-IGSO-2", "IGSO", A_GEO, 0.06, 29.0, 40.0, 270.0, 90.0),
        OrbitalElements("RPS-IGSO-3", "IGSO", A_GEO, 0.06, 29.0, 130.0, 270.0, 180.0),
        OrbitalElements("RPS-IGSO-4", "IGSO", A_GEO, 0.06, 29.0, 220.0, 270.0, 270.0),
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

def propagate_orbit_eci(elem: OrbitalElements, t_sec: float) -> tuple[np.ndarray, np.ndarray]:
    """Propaga a órbita no referencial inercial ECI J2000."""
    M = (elem.m0 + elem.n * t_sec) % (2.0 * math.pi)
    E = solve_kepler(M, elem.e)
    nu = true_anomaly_from_eccentric(E, elem.e)

    r_mag = elem.a * (1.0 - elem.e * math.cos(E))
    p_x = r_mag * math.cos(nu)
    p_y = r_mag * math.sin(nu)
    r_pqw = np.array([p_x, p_y, 0.0])

    p = elem.a * (1.0 - elem.e**2)
    v_mag_factor = math.sqrt(MU_EARTH / p)
    v_x = -v_mag_factor * math.sin(nu)
    v_y = v_mag_factor * (elem.e + math.cos(nu))
    v_pqw = np.array([v_x, v_y, 0.0])

    O, w, i = elem.raan, elem.argp, elem.i
    R_z_O = np.array([
        [math.cos(O), -math.sin(O), 0],
        [math.sin(O),  math.cos(O), 0],
        [0, 0, 1]
    ])
    R_x_i = np.array([
        [1, 0, 0],
        [0, math.cos(i), -math.sin(i)],
        [0, math.sin(i),  math.cos(i)]
    ])
    R_z_w = np.array([
        [math.cos(w), -math.sin(w), 0],
        [math.sin(w),  math.cos(w), 0],
        [0, 0, 1]
    ])

    R_pqw_to_eci = R_z_O @ R_x_i @ R_z_w
    r_eci = R_pqw_to_eci @ r_pqw
    v_eci = R_pqw_to_eci @ v_pqw

    return r_eci, v_eci

def eci_to_ecef(r_eci: np.ndarray, t_sec: float) -> np.ndarray:
    """Converte vetor ECI para o referencial fixo na Terra (ECEF)."""
    theta = (OMEGA_EARTH * t_sec) % (2.0 * math.pi)
    R_z = np.array([
        [math.cos(theta),  math.sin(theta), 0],
        [-math.sin(theta), math.cos(theta), 0],
        [0, 0, 1]
    ])
    return R_z @ r_eci

def ecef_to_lat_lon_alt(r_ecef: np.ndarray) -> tuple[float, float, float]:
    """Converte vetor ECEF em Latitude Geodésica, Longitude e Altitude elipsoidal WGS-84."""
    x, y, z = r_ecef[0], r_ecef[1], r_ecef[2]
    lon_rad = math.atan2(y, x)
    lon_deg = math.degrees(lon_rad)

    p = math.sqrt(x**2 + y**2)
    e2 = 2.0 * FLATTENING - FLATTENING**2
    lat_rad = math.atan2(z, p * (1.0 - e2))

    for _ in range(10):
        N = R_EARTH / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
        lat_rad = math.atan2(z + e2 * N * math.sin(lat_rad), p)

    N = R_EARTH / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
    alt_km = p / math.cos(lat_rad) - N
    lat_deg = math.degrees(lat_rad)

    return lat_deg, lon_deg, alt_km

def compute_elevation_azimuth(r_sat_ecef: np.ndarray, lat_gs_deg: float, lon_gs_deg: float) -> tuple[float, float, float]:
    """Calcula Elevação, Azimute e Alcance (Range) de um satélite a partir de uma estação de solo."""
    lat_rad = math.radians(lat_gs_deg)
    lon_rad = math.radians(lon_gs_deg)

    e2 = 2.0 * FLATTENING - FLATTENING**2
    N = R_EARTH / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
    r_gs = np.array([
        N * math.cos(lat_rad) * math.cos(lon_rad),
        N * math.cos(lat_rad) * math.sin(lon_rad),
        N * (1.0 - e2) * math.sin(lat_rad)
    ])

    rho_ecef = r_sat_ecef - r_gs
    range_km = float(np.linalg.norm(rho_ecef))

    R_enu = np.array([
        [-math.sin(lon_rad), math.cos(lon_rad), 0],
        [-math.sin(lat_rad) * math.cos(lon_rad), -math.sin(lat_rad) * math.sin(lon_rad), math.cos(lat_rad)],
        [math.cos(lat_rad) * math.cos(lon_rad), math.cos(lat_rad) * math.sin(lon_rad), math.sin(lat_rad)]
    ])

    rho_enu = R_enu @ rho_ecef
    e, n, u = rho_enu[0], rho_enu[1], rho_enu[2]

    elevation_deg = math.degrees(math.atan2(u, math.sqrt(e**2 + n**2)))
    azimuth_deg = math.degrees(math.atan2(e, n)) % 360.0

    return elevation_deg, azimuth_deg, range_km
