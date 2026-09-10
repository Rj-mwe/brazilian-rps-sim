"""
Testes Unitários: Solucionador Iterativo WLS PVT (Issue #15)
============================================================
Valida a resolução numérica da posição do receptor e desvio de relógio:
    Δx = (G^T W G)^(-1) G^T W Δρ
"""

import math
import pytest
import numpy as np

from rps_br.infrastructure.config.config_loader import load_simulation_config
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.signal_propagation.services.PseudorangeSimulationService import PseudorangeSimulationService
from rps_br.core.domain.navigation_pvt.strategies.IPvtSolverStrategy import IPvtSolverStrategy
from rps_br.core.domain.navigation_pvt.strategies.IterativeWlsPvtSolver import IterativeWlsPvtSolver
from rps_br.core.domain.navigation_pvt.value_objects.PvtSolutionVO import PvtSolutionVO


def get_brasilia_true_ecef_m() -> tuple[GeodeticCoordinatesVO, Vector3DVO]:
    """Calcula a verdade terrestre geodésica e cartesiana ECEF de Brasília (DF)."""
    geo = GeodeticCoordinatesVO(latitude_deg=-15.7975, longitude_deg=-47.8919, altitude_km=1.172)
    lat_rad = math.radians(geo.latitude_deg)
    lon_rad = math.radians(geo.longitude_deg)
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = 2.0 * f - f**2
    N = a / math.sqrt(1.0 - e2 * math.sin(lat_rad)**2)
    h_m = geo.altitude_km * 1000.0

    x = (N + h_m) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (N + h_m) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (N * (1.0 - e2) + h_m) * math.sin(lat_rad)
    return geo, Vector3DVO(x, y, z)


def get_test_constellation() -> ConstellationAggregate:
    """Constelação RPS-BR com 7 satélites (3 GEO + 4 IGSO) carregada da configuração oficial."""
    cfg = load_simulation_config()
    return ConstellationAggregate.from_config(cfg.get('constellation', {}))


def test_strategy_compliance_and_instantiation():
    """Verifica a conformidade do solucionador com a interface IPvtSolverStrategy."""
    solver = IterativeWlsPvtSolver(use_elevation_weights=True)
    assert isinstance(solver, IPvtSolverStrategy)
    assert solver.use_elevation_weights is True


def test_exact_pvt_recovery_4_satellites_zero_noise():
    """Verifica a recuperação exata de posição e relógio com sistema 4x4 sem ruído."""
    geo_true, true_ecef_m = get_brasilia_true_ecef_m()
    constellation = get_test_constellation()
    t_sim = 3600.0
    constellation.propagate_all(t_sim)

    # Injeta viés de relógio no receptor de 5 microsegundos (+1498.96 m)
    rx_bias_s = 5.0e-6
    measurements_dict = PseudorangeSimulationService.simulate_constellation_pseudoranges(
        constellation=constellation,
        user_coords=geo_true,
        gps_time_sec=t_sim,
        receiver_clock_bias_s=rx_bias_s,
        noise_sigma_m=0.0,
    )

    # Seleciona exatamente 4 satélites
    selected_sats = list(measurements_dict.keys())[:4]
    meas_subset = [measurements_dict[name] for name in selected_sats]
    sat_pos_m = {name: Vector3DVO(s.r_ecef.x * 1000.0, s.r_ecef.y * 1000.0, s.r_ecef.z * 1000.0)
                 for name, s in [(s.name, s) for s in constellation.satellites if s.name in selected_sats]}

    # Ponto de partida a 100 km de distância
    initial_guess = Vector3DVO(true_ecef_m.x + 80_000.0, true_ecef_m.y - 60_000.0, true_ecef_m.z + 10_000.0)

    solver = IterativeWlsPvtSolver(use_elevation_weights=False)
    solution = solver.solve(
        measurements=meas_subset,
        satellites_ecef_m=sat_pos_m,
        initial_guess_ecef_m=initial_guess,
        true_position_ecef_m=true_ecef_m,
        tolerance_m=1e-4,
    )

    assert isinstance(solution, PvtSolutionVO)
    assert solution.is_converged is True
    assert solution.iterations_count <= 8
    # Erro 3D deve ser submilimétrico
    assert solution.position_error_3d_m is not None
    assert solution.position_error_3d_m < 1e-3  # < 1 mm
    # Viés de relógio recuperado com precisão analítica
    expected_clock_m = rx_bias_s * PseudorangeSimulationService.SPEED_OF_LIGHT
    assert solution.receiver_clock_bias_m == pytest.approx(expected_clock_m, abs=1e-3)
    assert solution.receiver_clock_bias_s == pytest.approx(rx_bias_s, rel=1e-6)
    # Coordenadas geodésicas recuperadas com alta precisão
    assert solution.geodetic.latitude_deg == pytest.approx(geo_true.latitude_deg, abs=1e-5)
    assert solution.geodetic.longitude_deg == pytest.approx(geo_true.longitude_deg, abs=1e-5)
    assert solution.geodetic.altitude_km == pytest.approx(geo_true.altitude_km, abs=1e-4)


def test_overdetermined_wls_recovery_all_visible_satellites():
    """Verifica a resolução sobredeterminada com todos os 7 satélites visíveis."""
    geo_true, true_ecef_m = get_brasilia_true_ecef_m()
    constellation = get_test_constellation()
    t_sim = 7200.0
    constellation.propagate_all(t_sim)

    rx_bias_s = -2.5e-6  # Viés negativo (-749.48 m)
    measurements_dict = PseudorangeSimulationService.simulate_constellation_pseudoranges(
        constellation=constellation,
        user_coords=geo_true,
        gps_time_sec=t_sim,
        receiver_clock_bias_s=rx_bias_s,
        noise_sigma_m=0.0,
    )

    meas_list = list(measurements_dict.values())
    assert len(meas_list) >= 5

    sat_pos_m = {s.name: Vector3DVO(s.r_ecef.x * 1000.0, s.r_ecef.y * 1000.0, s.r_ecef.z * 1000.0)
                 for s in constellation.satellites}

    # Chute inicial distante a 500 km
    distant_guess = Vector3DVO(true_ecef_m.x + 300_000.0, true_ecef_m.y - 400_000.0, true_ecef_m.z)

    solver = IterativeWlsPvtSolver(use_elevation_weights=True)
    solution = solver.solve(
        measurements=meas_list,
        satellites_ecef_m=sat_pos_m,
        initial_guess_ecef_m=distant_guess,
        true_position_ecef_m=true_ecef_m,
    )

    assert solution.is_converged is True
    assert solution.position_error_3d_m < 1e-3
    assert solution.dop is not None
    assert solution.dop.pdop < 15.0
    assert solution.dop.visible_satellites_count == len(meas_list)


def test_noisy_measurements_accuracy_and_residuals():
    """Verifica a robustez estatística frente a ruído térmico gaussiano de 1 metro."""
    geo_true, true_ecef_m = get_brasilia_true_ecef_m()
    constellation = get_test_constellation()
    t_sim = 10800.0
    constellation.propagate_all(t_sim)

    # Injeção de ruído térmico sigma = 1.0 metro
    measurements_dict = PseudorangeSimulationService.simulate_constellation_pseudoranges(
        constellation=constellation,
        user_coords=geo_true,
        gps_time_sec=t_sim,
        receiver_clock_bias_s=1.0e-6,
        noise_sigma_m=1.0,
        random_seed=42,
    )

    meas_list = list(measurements_dict.values())
    sat_pos_m = {s.name: Vector3DVO(s.r_ecef.x * 1000.0, s.r_ecef.y * 1000.0, s.r_ecef.z * 1000.0)
                 for s in constellation.satellites}

    solver = IterativeWlsPvtSolver(use_elevation_weights=True)
    solution = solver.solve(
        measurements=meas_list,
        satellites_ecef_m=sat_pos_m,
        true_position_ecef_m=true_ecef_m,
    )

    assert solution.is_converged is True
    # O erro 3D deve ser da ordem da precisão teórica: erro < 3 * PDOP * sigma
    assert solution.dop is not None
    max_expected_error = 3.0 * solution.dop.pdop * 1.0
    assert solution.position_error_3d_m < max_expected_error
    # Resíduos pós-ajuste devem ter média próxima de zero e magnitude compatível com o ruído
    assert len(solution.residuals_m) == len(meas_list)
    for res in solution.residuals_m.values():
        assert abs(res) < 5.0  # < 5 metros


def test_insufficient_satellites_raises_exception():
    """Verifica que menos de 4 satélites levanta ValueError por sistema subdeterminado."""
    geo_true, _ = get_brasilia_true_ecef_m()
    constellation = get_test_constellation()
    constellation.propagate_all(0.0)

    measurements_dict = PseudorangeSimulationService.simulate_constellation_pseudoranges(
        constellation=constellation,
        user_coords=geo_true,
        noise_sigma_m=0.0,
    )

    # Pega apenas 3 satélites
    only_3_meas = list(measurements_dict.values())[:3]
    sat_pos_m = {m.satellite_id: Vector3DVO(0.0, 0.0, 42164000.0) for m in only_3_meas}

    solver = IterativeWlsPvtSolver()
    with pytest.raises(ValueError, match="mínimo de 4 satélites"):
        solver.solve(measurements=only_3_meas, satellites_ecef_m=sat_pos_m)


def test_pvt_solution_vo_immutability():
    """Verifica a imutabilidade e integridade defensiva do PvtSolutionVO."""
    geo = GeodeticCoordinatesVO(latitude_deg=-15.0, longitude_deg=-47.0, altitude_km=1.0)
    pos = Vector3DVO(4000000.0, -4000000.0, -1500000.0)
    solution = PvtSolutionVO(
        position_ecef_m=pos,
        geodetic=geo,
        receiver_clock_bias_m=150.0,
        receiver_clock_bias_s=150.0 / PseudorangeSimulationService.SPEED_OF_LIGHT,
        residuals_m={"SAT-1": 0.1},
        iterations_count=3,
        is_converged=True,
    )
    with pytest.raises(Exception):
        solution.receiver_clock_bias_m = 200.0  # Imutável (frozen=True)

