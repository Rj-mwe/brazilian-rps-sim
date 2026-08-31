"""
Política de Propagação Orbital Analítica Kepleriana de 2 Corpos.
"""

import math
import numpy as np
from brazilian_rps_sim.core.domain.value_objects.KeplerianElementsVO import KeplerianElementsVO
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.services.KeplerSolverService import KeplerSolverService

class KeplerianPropagationPolicy:
    @classmethod
    def propagate(cls, elem: KeplerianElementsVO, t_sec: float, mu: float = 398600.4418) -> tuple[Vector3DVO, Vector3DVO]:
        """Propaga o estado orbital para o instante t_sec no referencial inercial ECI J2000."""
        n = elem.mean_motion_rad_s(mu)
        M = (elem.mean_anomaly_rad + n * t_sec) % (2.0 * math.pi)

        E = KeplerSolverService.solve_kepler(M, elem.eccentricity)
        nu = KeplerSolverService.true_anomaly_from_eccentric(E, elem.eccentricity)

        r_mag = elem.semi_major_axis_km * (1.0 - elem.eccentricity * math.cos(E))
        p_x = r_mag * math.cos(nu)
        p_y = r_mag * math.sin(nu)
        r_pqw = np.array([p_x, p_y, 0.0], dtype=np.float64)

        p = elem.semi_major_axis_km * (1.0 - elem.eccentricity**2)
        v_factor = math.sqrt(mu / p)
        v_x = -v_factor * math.sin(nu)
        v_y = v_factor * (elem.eccentricity + math.cos(nu))
        v_pqw = np.array([v_x, v_y, 0.0], dtype=np.float64)

        O, w, i = elem.raan_rad, elem.arg_perigee_rad, elem.inclination_rad
        R_z_O = np.array([
            [math.cos(O), -math.sin(O), 0.0],
            [math.sin(O),  math.cos(O), 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        R_x_i = np.array([
            [1.0, 0.0, 0.0],
            [0.0, math.cos(i), -math.sin(i)],
            [0.0, math.sin(i),  math.cos(i)]
        ], dtype=np.float64)
        R_z_w = np.array([
            [math.cos(w), -math.sin(w), 0.0],
            [math.sin(w),  math.cos(w), 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)

        R_matrix = R_z_O @ R_x_i @ R_z_w
        r_eci = R_matrix @ r_pqw
        v_eci = R_matrix @ v_pqw

        return Vector3DVO.from_numpy(r_eci), Vector3DVO.from_numpy(v_eci)
