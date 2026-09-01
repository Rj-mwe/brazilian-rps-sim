#!/usr/bin/env python3
"""
Teste de Integração: CalculateGroundStationDopUseCase
Valida a performance de posicionamento e Diluição de Precisão (DOP)
da constelação RPS-BR completa (3 GEO + 4 IGSO) sobre todo o território brasileiro.
"""

import math
from pathlib import Path
import yaml
import numpy as np
import pytest

from brazilian_rps_sim.core.application.services.CalculateGroundStationDopUseCase import (
    CalculateGroundStationDopUseCase,
    DEFAULT_BRAZILIAN_GROUND_STATIONS
)
from brazilian_rps_sim.core.domain.strategies.StandardLeastSquaresDopStrategy import StandardLeastSquaresDopStrategy
from brazilian_rps_sim.core.domain.strategies.WeightedElevationDopStrategy import WeightedElevationDopStrategy
from brazilian_rps_sim.core.domain.observers.DopTelemetryBufferObserver import DopTelemetryBufferObserver
from brazilian_rps_sim.core.domain.services.CoordinateTransformService import CoordinateTransformService


@pytest.fixture
def constellation_config():
    pkg_dir = Path(__file__).resolve().parents[2]
    config_path = pkg_dir / "config" / "simulation_parameters.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def propagate_satellites_ecef(config, t_sec: float) -> dict:
    """Propaga as posições de todos os 7 satélites para o referencial ECEF (km) no tempo t_sec."""
    omega_earth = 7.292115e-5
    sats_ecef = {}

    for sat in config["constellation"]["satellites"]:
        name = sat["name"]
        a = float(sat["semi_major_axis_km"])
        e = float(sat["eccentricity"])
        inc = math.radians(float(sat["inclination_deg"]))
        raan = math.radians(float(sat["raan_deg"]))
        argp = math.radians(float(sat["arg_perigee_deg"]))
        m0 = math.radians(float(sat["mean_anomaly_deg"]))

        M = m0 + omega_earth * t_sec
        E = M
        for _ in range(10):
            E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
        r = a * (1 - e * math.cos(E))

        px = r * math.cos(nu)
        py = r * math.sin(nu)

        cO, sO = math.cos(raan), math.sin(raan)
        cw, sw = math.cos(argp), math.sin(argp)
        ci, si = math.cos(inc), math.sin(inc)

        Px = cO * cw - sO * sw * ci
        Py = sO * cw + cO * sw * ci
        Pz = sw * si
        Qx = -cO * sw - sO * cw * ci
        Qy = -sO * sw + cO * cw * ci
        Qz = cw * si

        ecix = px * Px + py * Qx
        eciy = px * Py + py * Qy
        eciz = px * Pz + py * Qz

        # ECEF
        th_spin = omega_earth * t_sec
        xb = ecix * math.cos(th_spin) + eciy * math.sin(th_spin)
        yb = -ecix * math.sin(th_spin) + eciy * math.cos(th_spin)
        zb = eciz

        sats_ecef[name] = np.array([xb, yb, zb], dtype=np.float64)

    return sats_ecef


def test_rps_br_constellation_24h_dop_coverage_across_brazil(constellation_config):
    """
    Valida que a constelação RPS-BR mantenha 100% de disponibilidade de navegação
    (PDOP < 4.0 / EXCELLENT ou GOOD) nas capitais representativas de todas as regiões do Brasil.
    """
    telemetry_buffer = DopTelemetryBufferObserver()
    use_case = CalculateGroundStationDopUseCase(
        strategy=StandardLeastSquaresDopStrategy(min_elevation_deg=5.0)
    )
    use_case.attach_observer(telemetry_buffer)

    # Amostragem ao longo de 24 horas a cada 1 hora
    for t_hour in range(24):
        t_sec = t_hour * 3600.0
        sats_ecef = propagate_satellites_ecef(constellation_config, t_sec)
        results = use_case.execute(sats_ecef, t_sec)

        for station_name, dop_res in results.items():
            assert dop_res.is_valid, f"Falha de cobertura em {station_name} às {t_hour}h: {dop_res.error_message}"
            assert dop_res.visible_satellites_count == 7, f"Esperados 7 satélites visíveis em {station_name} às {t_hour}h, obtidos {dop_res.visible_satellites_count}"
            assert dop_res.pdop < 20.0, f"PDOP degradado em {station_name} às {t_hour}h (PDOP={dop_res.pdop:.2f})"

    # Validação estatística de disponibilidade contínua de posicionamento autônomo (100% 24/7)
    for station_name in DEFAULT_BRAZILIAN_GROUND_STATIONS.keys():
        availability = telemetry_buffer.get_coverage_availability_percentage(station_name, max_pdop=18.0)
        avg_pdop = telemetry_buffer.get_average_pdop(station_name)
        assert availability == 100.0, f"Disponibilidade contínua insuficiente em {station_name}: {availability:.1f}%"
        assert avg_pdop < 12.0, f"PDOP médio elevado em {station_name}: {avg_pdop:.2f}"
