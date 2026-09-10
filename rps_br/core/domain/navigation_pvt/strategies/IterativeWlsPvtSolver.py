"""
Estratégia Concreta: IterativeWlsPvtSolver
=========================================
Implementa o solucionador iterativo de navegação por Mínimos Quadrados Ponderados (WLS)
via algoritmo de Gauss-Newton multivariado.

Resolve iterativamente a equação não-linear de pseudodistâncias:
    Δx = (G^T W G)^(-1) G^T W Δρ

onde:
    G: Matriz de Geometria/Design (M x 4) contendo os cossenos diretores da linha de visada.
    W: Matriz diagonal de pesos estocásticos (M x M) baseados na elevação: W_ii = sin²(el_i).
    Δρ: Vetor de resíduos de pseudodistância pré-ajuste (M x 1).
    Δx: Incremento do vetor de estado [dx, dy, dz, c*dt_rx]^T.
"""

import math
from typing import Dict, List, Optional
import numpy as np

from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.signal_propagation.value_objects.PseudorangeMeasurementVO import PseudorangeMeasurementVO
from rps_br.core.domain.navigation_pvt.value_objects.PvtSolutionVO import PvtSolutionVO
from rps_br.core.domain.navigation_pvt.value_objects.DopResultVO import DopResultVO
from rps_br.core.domain.astrodynamics.services.CoordinateTransformService import CoordinateTransformService
from rps_br.core.domain.navigation_pvt.strategies.IPvtSolverStrategy import IPvtSolverStrategy


class IterativeWlsPvtSolver(IPvtSolverStrategy):
    """
    Solucionador PVT iterativo baseado em Mínimos Quadrados Ponderados (WLS).
    """

    SPEED_OF_LIGHT: float = 299792458.0  # m/s

    def __init__(self, use_elevation_weights: bool = True):
        self.use_elevation_weights = use_elevation_weights

    def solve(
        self,
        measurements: List[PseudorangeMeasurementVO],
        satellites_ecef_m: Dict[str, Vector3DVO],
        initial_guess_ecef_m: Optional[Vector3DVO] = None,
        true_position_ecef_m: Optional[Vector3DVO] = None,
        tolerance_m: float = 1e-4,
        max_iterations: int = 15,
    ) -> PvtSolutionVO:
        # 1. Filtra observáveis que possuem posição correspondente de satélite
        valid_meas = [m for m in measurements if m.satellite_id in satellites_ecef_m]
        m_count = len(valid_meas)

        if m_count < 4:
            raise ValueError(
                f"Satélites insuficientes para solução PVT 3D: mínimo de 4 satélites exigidos, "
                f"recebido {m_count}."
            )

        # 2. Inicialização do vetor de estado: x_k = [x, y, z, c*dt_rx]^T (metros)
        if initial_guess_ecef_m is not None:
            x_est = float(initial_guess_ecef_m.x)
            y_est = float(initial_guess_ecef_m.y)
            z_est = float(initial_guess_ecef_m.z)
        else:
            # Ponto de partida padrão: centro da Terra (0, 0, 0)
            x_est, y_est, z_est = 0.0, 0.0, 0.0

        b_est = 0.0  # Viés de relógio inicial (metros)
        is_converged = False
        final_residuals: Dict[str, float] = {}
        iterations_executed = 0
        H_cov = np.eye(4)

        # 3. Laço Iterativo de Gauss-Newton
        for k in range(max_iterations):
            iterations_executed = k + 1
            G_rows = []
            delta_rho_list = []
            weights_list = []

            for meas in valid_meas:
                sat_pos = satellites_ecef_m[meas.satellite_id]
                sx, sy, sz = float(sat_pos.x), float(sat_pos.y), float(sat_pos.z)

                # Distância geométrica da posição estimada atual até o satélite
                dx = x_est - sx
                dy = y_est - sy
                dz = z_est - sz
                r_hat = math.sqrt(dx**2 + dy**2 + dz**2)
                if r_hat == 0.0:
                    r_hat = 1.0

                # Pseudodistância teórica esperada na estimativa atual
                # rho_hat = r_hat + b_est - sat_clock + iono + tropo + rel
                rho_hat = (
                    r_hat
                    + b_est
                    - meas.satellite_clock_bias_m
                    + meas.ionospheric_delay_m
                    + meas.tropospheric_delay_m
                    + meas.relativistic_delay_m
                )

                # Resíduo de pseudodistância
                d_rho = meas.pseudorange_m - rho_hat
                delta_rho_list.append(d_rho)
                final_residuals[meas.satellite_id] = d_rho

                # Linha da Matriz de Geometria: gradiente em relação a [x, y, z, b]
                G_rows.append([dx / r_hat, dy / r_hat, dz / r_hat, 1.0])

                # Peso por elevação
                if self.use_elevation_weights:
                    sin_el = math.sin(math.radians(max(5.0, meas.elevation_deg)))
                    weights_list.append(sin_el**2)
                else:
                    weights_list.append(1.0)

            G = np.array(G_rows, dtype=np.float64)
            delta_rho = np.array(delta_rho_list, dtype=np.float64)
            W = np.diag(weights_list)

            # Matriz Normal: A = G^T * W * G
            A = G.T @ W @ G
            det_A = np.linalg.det(A)

            if abs(det_A) < 1e-14 or not np.isfinite(det_A):
                raise ValueError("Geometria singular ou degenerada: matriz normal não inversível.")

            # Solução de Mínimos Quadrados: delta_x = A^(-1) * G^T * W * delta_rho
            delta_x = np.linalg.solve(A, G.T @ W @ delta_rho)

            # Atualização do estado
            x_est += float(delta_x[0])
            y_est += float(delta_x[1])
            z_est += float(delta_x[2])
            b_est += float(delta_x[3])

            # Matriz de covariância normal sem pesos para cálculo de DOP
            try:
                H_cov = np.linalg.inv(G.T @ G)
            except np.linalg.LinAlgError:
                H_cov = np.eye(4)

            # Critério de convergência euclidiano na posição 3D
            pos_increment_m = math.sqrt(delta_x[0]**2 + delta_x[1]**2 + delta_x[2]**2)
            if pos_increment_m < tolerance_m:
                is_converged = True
                break

        # 4. Construção da solução final
        final_pos_ecef = Vector3DVO(x_est, y_est, z_est)
        # Conversão ECEF (m) -> ECEF (km) para chamada do serviço de coordenadas WGS-84
        pos_ecef_km = np.array([x_est, y_est, z_est], dtype=np.float64) / 1000.0
        geodetic_coords = CoordinateTransformService.ecef_to_geodetic(pos_ecef_km)

        # Cálculo de DOP
        gdop = math.sqrt(max(0.0, float(np.trace(H_cov))))
        pdop = math.sqrt(max(0.0, float(H_cov[0, 0] + H_cov[1, 1] + H_cov[2, 2])))
        hdop = math.sqrt(max(0.0, float(H_cov[0, 0] + H_cov[1, 1])))
        vdop = math.sqrt(max(0.0, float(H_cov[2, 2])))
        tdop = math.sqrt(max(0.0, float(H_cov[3, 3])))
        dop_vo = DopResultVO(
            gdop=gdop,
            pdop=pdop,
            hdop=hdop,
            vdop=vdop,
            tdop=tdop,
            visible_satellites_count=m_count,
            is_valid=True,
        )

        # Erro 3D frente à verdade terrestre (se fornecida)
        pos_error_3d: Optional[float] = None
        if true_position_ecef_m is not None:
            err_vec = final_pos_ecef.to_numpy() - true_position_ecef_m.to_numpy()
            pos_error_3d = float(np.linalg.norm(err_vec))

        return PvtSolutionVO(
            position_ecef_m=final_pos_ecef,
            geodetic=geodetic_coords,
            receiver_clock_bias_m=b_est,
            receiver_clock_bias_s=b_est / self.SPEED_OF_LIGHT,
            residuals_m=final_residuals,
            iterations_count=iterations_executed,
            is_converged=is_converged,
            dop=dop_vo,
            position_error_3d_m=pos_error_3d,
        )
