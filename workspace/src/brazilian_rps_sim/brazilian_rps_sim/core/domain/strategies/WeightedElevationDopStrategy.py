#!/usr/bin/env python3
"""
Concrete Strategy: WeightedElevationDopStrategy
Calcula o DOP ponderado pela elevação do satélite W = diag(sin^2(elev)),
modelando o aumento de ruído de pseudodistância e refração atmosférica em baixas elevações.
"""

import math
from typing import Dict
import numpy as np

from brazilian_rps_sim.core.domain.strategies.IDopCalculationStrategy import IDopCalculationStrategy
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.DopResultVO import DopResultVO
from brazilian_rps_sim.core.domain.services.CoordinateTransformService import CoordinateTransformService


class WeightedElevationDopStrategy(IDopCalculationStrategy):
    """Estratégia ponderada pela elevação com matriz W = diag(sin^2(elevation))."""

    def __init__(self, min_elevation_deg: float = 5.0):
        self.min_elevation_deg = min_elevation_deg

    def calculate_dop(
        self,
        station_coord: GeodeticCoordinatesVO,
        satellite_positions_ecef: Dict[str, np.ndarray]
    ) -> DopResultVO:
        lat_rad = math.radians(station_coord.latitude_deg)
        lon_rad = math.radians(station_coord.longitude_deg)

        R_enu = np.array([
            [-math.sin(lon_rad), math.cos(lon_rad), 0.0],
            [-math.sin(lat_rad) * math.cos(lon_rad), -math.sin(lat_rad) * math.sin(lon_rad), math.cos(lat_rad)],
            [math.cos(lat_rad) * math.cos(lon_rad), math.cos(lat_rad) * math.sin(lon_rad), math.sin(lat_rad)]
        ], dtype=np.float64)

        r_earth = CoordinateTransformService.R_EARTH_DEFAULT
        f = CoordinateTransformService.FLATTENING_DEFAULT
        e2 = 2.0 * f - f**2
        N = r_earth / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
        h = station_coord.altitude_km
        r_gs_ecef = np.array([
            (N + h) * math.cos(lat_rad) * math.cos(lon_rad),
            (N + h) * math.cos(lat_rad) * math.sin(lon_rad),
            (N * (1.0 - e2) + h) * math.sin(lat_rad)
        ], dtype=np.float64)

        g_rows = []
        weights = []

        for sat_name, r_sat_ecef in satellite_positions_ecef.items():
            rho_ecef = r_sat_ecef - r_gs_ecef
            range_val = np.linalg.norm(rho_ecef)
            if range_val < 1e-6:
                continue

            rho_enu = R_enu @ rho_ecef
            e, n, u = rho_enu[0], rho_enu[1], rho_enu[2]

            elev_deg = math.degrees(math.atan2(u, math.sqrt(e**2 + n**2)))
            if elev_deg >= self.min_elevation_deg:
                u_vec = rho_enu / range_val
                g_rows.append([-u_vec[0], -u_vec[1], -u_vec[2], 1.0])
                
                # Peso proporcional a sin^2(elevacao)
                sin_elev = max(0.01, math.sin(math.radians(elev_deg)))
                weights.append(sin_elev**2)

        n_vis = len(g_rows)
        if n_vis < 4:
            return DopResultVO.invalid(
                reason=f"Satélites visíveis com elevação >= {self.min_elevation_deg}° insuficientes ({n_vis} < 4)",
                visible_count=n_vis
            )

        G = np.array(g_rows, dtype=np.float64)
        W = np.diag(weights)
        GtWG = G.T @ W @ G

        try:
            Q = np.linalg.inv(GtWG)
        except np.linalg.LinAlgError:
            return DopResultVO.invalid("Matriz de geometria ponderada singular", visible_count=n_vis)

        q_ee, q_nn, q_uu, q_tt = Q[0, 0], Q[1, 1], Q[2, 2], Q[3, 3]
        if q_ee < 0 or q_nn < 0 or q_uu < 0 or q_tt < 0:
            return DopResultVO.invalid("Variância negativa na matriz Q ponderada", visible_count=n_vis)

        return DopResultVO(
            gdop=float(math.sqrt(q_ee + q_nn + q_uu + q_tt)),
            pdop=float(math.sqrt(q_ee + q_nn + q_uu)),
            hdop=float(math.sqrt(q_ee + q_nn)),
            vdop=float(math.sqrt(q_uu)),
            tdop=float(math.sqrt(q_tt)),
            visible_satellites_count=n_vis,
            is_valid=True
        )
