"""
Testes Unitários: PseudorangeSimulationService & PseudorangeMeasurementVO
========================================================================
Valida a equação de observáveis de pseudodistância bruta (IS-GPS-200 / RTCA DO-229D):
    ρ = R + c*(δt_rx - δt_sat) + I + T + Δ_rel + ε
"""

import math
import random
import pytest
import numpy as np

from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.astrodynamics.value_objects.KeplerianElementsVO import KeplerianElementsVO
from rps_br.core.domain.astrodynamics.aggregates.SatelliteAggregate import SatelliteAggregate
from rps_br.core.domain.signal_propagation.value_objects.PseudorangeMeasurementVO import PseudorangeMeasurementVO
from rps_br.core.domain.signal_propagation.services.PseudorangeSimulationService import PseudorangeSimulationService


@pytest.fixture
def brasilia_coords() -> GeodeticCoordinatesVO:
    """Coordenadas geodésicas de Brasília (DF)."""
    return GeodeticCoordinatesVO(latitude_deg=-15.7975, longitude_deg=-47.8919, altitude_km=1.172)


@pytest.fixture
def sample_geo_sat() -> SatelliteAggregate:
    """Satélite GEO-2 estacionário posicionado sobre o meridiano 48°W."""
    elem = KeplerianElementsVO.from_degrees(
        a_km=42164.14, e=0.0, inc_deg=0.0, raan_deg=0.0, argp_deg=0.0, m0_deg=0.0
    )
    sat = SatelliteAggregate(sat_id=2, name="RPS-GEO-2", sat_type="GEO", elements=elem, station_lon_deg=-48.0)
    sat.propagate_to(0.0)
    return sat


@pytest.fixture
def sample_igso_sat() -> SatelliteAggregate:
    """Satélite IGSO-1 inclinado a 25° com excentricidade e=0.040."""
    elem = KeplerianElementsVO.from_degrees(
        a_km=42164.14, e=0.040, inc_deg=25.0, raan_deg=0.0, argp_deg=90.0, m0_deg=45.0
    )
    sat = SatelliteAggregate(sat_id=4, name="RPS-IGSO-1", sat_type="IGSO", elements=elem)
    sat.propagate_to(1800.0)
    return sat


def test_pure_geometric_range_without_perturbations(sample_geo_sat, brasilia_coords):
    """Verifica que na ausência de ruído, erros de relógio e atmosfera, a pseudodistância é idêntica ao range geométrico."""
    meas = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        receiver_clock_bias_s=0.0,
        satellite_clock_bias_s=0.0,
        include_ionosphere=False,
        include_troposphere=False,
        include_relativity=False,
        noise_sigma_m=0.0,
    )

    assert isinstance(meas, PseudorangeMeasurementVO)
    assert meas.pseudorange_m == pytest.approx(meas.geometric_range_m, abs=1e-6)
    assert meas.receiver_clock_bias_m == 0.0
    assert meas.satellite_clock_bias_m == 0.0
    assert meas.ionospheric_delay_m == 0.0
    assert meas.tropospheric_delay_m == 0.0
    assert meas.relativistic_delay_m == 0.0
    assert meas.noise_m == 0.0
    assert meas.geometric_range_m > 35_000_000.0  # GEO a > 35.000 km
    assert meas.transit_time_sec == pytest.approx(meas.geometric_range_m / 299792458.0, rel=1e-7)


def test_receiver_and_satellite_clock_biases(sample_geo_sat, brasilia_coords):
    """Verifica a injeção exata de viés do oscilador local do receptor e do relógio do satélite."""
    # 10 microsegundos no receptor (+2997.92 m) e 50 nanossegundos no satélite (-14.99 m)
    rx_bias_s = 10.0e-6
    sat_bias_s = 50.0e-9
    c = PseudorangeSimulationService.SPEED_OF_LIGHT

    meas = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        receiver_clock_bias_s=rx_bias_s,
        satellite_clock_bias_s=sat_bias_s,
        include_ionosphere=False,
        include_troposphere=False,
        include_relativity=False,
        noise_sigma_m=0.0,
    )

    expected_rx_m = rx_bias_s * c
    expected_sat_m = sat_bias_s * c
    assert meas.receiver_clock_bias_m == pytest.approx(expected_rx_m, abs=1e-4)
    assert meas.satellite_clock_bias_m == pytest.approx(expected_sat_m, abs=1e-4)
    assert (meas.pseudorange_m - meas.geometric_range_m) == pytest.approx(expected_rx_m - expected_sat_m, abs=1e-4)


def test_orbital_relativity_effect(sample_geo_sat, sample_igso_sat, brasilia_coords):
    """Verifica o termo relativístico orbital: nulo em órbita circular (GEO) e não-nulo em IGSO excêntrico."""
    # Para GEO circular: r e v são ortogonais (r . v = 0)
    meas_geo = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        include_ionosphere=False,
        include_troposphere=False,
        include_relativity=True,
        noise_sigma_m=0.0,
    )
    assert meas_geo.relativistic_delay_m == pytest.approx(0.0, abs=1e-6)

    # Para IGSO (e = 0.040): r . v != 0 dependendo da anomalia verdadeira
    meas_igso = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_igso_sat.name,
        r_sat_eci=sample_igso_sat.r_eci,
        v_sat_eci=sample_igso_sat.v_eci,
        r_sat_ecef=sample_igso_sat.r_ecef,
        user_coords=brasilia_coords,
        include_ionosphere=False,
        include_troposphere=False,
        include_relativity=True,
        noise_sigma_m=0.0,
    )
    dot_r_v = sample_igso_sat.r_eci.dot(sample_igso_sat.v_eci) * 1.0e6
    expected_rel_m = -2.0 * dot_r_v / PseudorangeSimulationService.SPEED_OF_LIGHT
    assert meas_igso.relativistic_delay_m == pytest.approx(expected_rel_m, abs=1e-5)
    # A correção relativística em IGSO é não-nula e tem magnitude física plausível (< 50 m)
    assert abs(meas_igso.relativistic_delay_m) > 0.1
    assert abs(meas_igso.relativistic_delay_m) < 50.0


def test_atmospheric_delays_integrated(sample_geo_sat, brasilia_coords):
    """Verifica a correta integração de retardos ionosféricos (Klobuchar) e troposféricos (Saastamoinen)."""
    meas = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        gps_time_sec=14.0 * 3600.0,  # 14h locais (pico de ionização solar)
        include_ionosphere=True,
        include_troposphere=True,
        include_relativity=True,
        noise_sigma_m=0.0,
    )

    # Troposfera típica ao nível do solo no zênite/alta elevação: 2.0 a 3.5 metros
    assert 2.0 <= meas.tropospheric_delay_m <= 15.0
    # Ionosfera equatorial no Brasil durante o dia: tipicamente > 5 metros
    assert meas.ionospheric_delay_m > 3.0

    # Confirmação do balanço da equação completa
    expected_pseudorange = (
        meas.geometric_range_m
        + meas.receiver_clock_bias_m
        - meas.satellite_clock_bias_m
        + meas.ionospheric_delay_m
        + meas.tropospheric_delay_m
        + meas.relativistic_delay_m
        + meas.noise_m
    )
    assert meas.pseudorange_m == pytest.approx(expected_pseudorange, abs=1e-5)


def test_stochastic_noise_reproducibility(sample_geo_sat, brasilia_coords):
    """Verifica o determinismo estocástico do ruído quando uma semente de gerador é fixada."""
    rng1 = random.Random(12345)
    meas1 = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        noise_sigma_m=1.5,
        rng=rng1,
    )

    rng2 = random.Random(12345)
    meas2 = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        noise_sigma_m=1.5,
        rng=rng2,
    )

    assert meas1.noise_m == pytest.approx(meas2.noise_m, abs=1e-12)
    assert meas1.pseudorange_m == pytest.approx(meas2.pseudorange_m, abs=1e-12)
    assert meas1.noise_m != 0.0

    # Com semente diferente, o ruído diverge
    rng3 = random.Random(99999)
    meas3 = PseudorangeSimulationService.compute_pseudorange(
        sat_name=sample_geo_sat.name,
        r_sat_eci=sample_geo_sat.r_eci,
        v_sat_eci=sample_geo_sat.v_eci,
        r_sat_ecef=sample_geo_sat.r_ecef,
        user_coords=brasilia_coords,
        noise_sigma_m=1.5,
        rng=rng3,
    )
    assert meas1.noise_m != meas3.noise_m


def test_simulate_constellation_pseudoranges_batch(brasilia_coords):
    """Verifica a geração em lote de pseudodistâncias para a constelação inteira."""
    # Constelação com 7 satélites
    constellation = ConstellationAggregate.from_config({
        "satellites": [
            {"id": 1, "name": "RPS-GEO-1", "type": "GEO", "semi_major_axis_km": 42164.14, "eccentricity": 0.0, "inclination_deg": 0.0, "raan_deg": 0.0, "arg_perigee_deg": 0.0, "mean_anomaly_deg": 0.0, "station_longitude_deg": -60.0},
            {"id": 2, "name": "RPS-GEO-2", "type": "GEO", "semi_major_axis_km": 42164.14, "eccentricity": 0.0, "inclination_deg": 0.0, "raan_deg": 0.0, "arg_perigee_deg": 0.0, "mean_anomaly_deg": 0.0, "station_longitude_deg": -48.0},
            {"id": 3, "name": "RPS-GEO-3", "type": "GEO", "semi_major_axis_km": 42164.14, "eccentricity": 0.0, "inclination_deg": 0.0, "raan_deg": 0.0, "arg_perigee_deg": 0.0, "mean_anomaly_deg": 0.0, "station_longitude_deg": -36.0},
            {"id": 4, "name": "RPS-IGSO-1", "type": "IGSO", "semi_major_axis_km": 42164.14, "eccentricity": 0.040, "inclination_deg": 25.0, "raan_deg": 0.0, "arg_perigee_deg": 90.0, "mean_anomaly_deg": 0.0},
            {"id": 5, "name": "RPS-IGSO-2", "type": "IGSO", "semi_major_axis_km": 42164.14, "eccentricity": 0.040, "inclination_deg": 25.0, "raan_deg": 0.0, "arg_perigee_deg": 90.0, "mean_anomaly_deg": 90.0},
            {"id": 6, "name": "RPS-IGSO-3", "type": "IGSO", "semi_major_axis_km": 42164.14, "eccentricity": 0.040, "inclination_deg": 25.0, "raan_deg": 0.0, "arg_perigee_deg": 90.0, "mean_anomaly_deg": 180.0},
            {"id": 7, "name": "RPS-IGSO-4", "type": "IGSO", "semi_major_axis_km": 42164.14, "eccentricity": 0.040, "inclination_deg": 25.0, "raan_deg": 0.0, "arg_perigee_deg": 90.0, "mean_anomaly_deg": 270.0},
        ]
    })
    constellation.propagate_all(3600.0)

    # Máscara de elevação de 5 graus
    measurements = PseudorangeSimulationService.simulate_constellation_pseudoranges(
        constellation=constellation,
        user_coords=brasilia_coords,
        gps_time_sec=3600.0,
        elevation_mask_deg=5.0,
        receiver_clock_bias_s=1.0e-6,
        noise_sigma_m=0.5,
        random_seed=42,
    )

    # Deve conter múltiplos satélites visíveis a partir de Brasília
    assert len(measurements) >= 4  # Mínimo para PVT
    for name, meas in measurements.items():
        assert meas.elevation_deg >= 5.0
        assert meas.pseudorange_m > 30_000_000.0
        assert meas.satellite_id == name
        assert meas.receiver_clock_bias_m == pytest.approx(1.0e-6 * 299792458.0, abs=1e-4)


def test_pseudorange_vo_defensive_invariants():
    """Valida a programação defensiva do Value Object PseudorangeMeasurementVO."""
    # satellite_id vazio deve lançar erro
    with pytest.raises(ValueError, match="satellite_id"):
        PseudorangeMeasurementVO(
            satellite_id="",
            pseudorange_m=38000000.0,
            geometric_range_m=38000000.0,
            ionospheric_delay_m=0.0,
            tropospheric_delay_m=0.0,
            receiver_clock_bias_m=0.0,
            satellite_clock_bias_m=0.0,
            relativistic_delay_m=0.0,
            noise_m=0.0,
            elevation_deg=45.0,
            azimuth_deg=180.0,
            transit_time_sec=0.12,
        )

    # geometric_range_m não-positivo deve lançar erro
    with pytest.raises(ValueError, match="geometric_range_m"):
        PseudorangeMeasurementVO(
            satellite_id="SAT-1",
            pseudorange_m=38000000.0,
            geometric_range_m=-100.0,
            ionospheric_delay_m=0.0,
            tropospheric_delay_m=0.0,
            receiver_clock_bias_m=0.0,
            satellite_clock_bias_m=0.0,
            relativistic_delay_m=0.0,
            noise_m=0.0,
            elevation_deg=45.0,
            azimuth_deg=180.0,
            transit_time_sec=0.12,
        )

    # pseudorange_m não-positivo deve lançar erro
    with pytest.raises(ValueError, match="pseudorange_m"):
        PseudorangeMeasurementVO(
            satellite_id="SAT-1",
            pseudorange_m=0.0,
            geometric_range_m=38000000.0,
            ionospheric_delay_m=0.0,
            tropospheric_delay_m=0.0,
            receiver_clock_bias_m=0.0,
            satellite_clock_bias_m=0.0,
            relativistic_delay_m=0.0,
            noise_m=0.0,
            elevation_deg=45.0,
            azimuth_deg=180.0,
            transit_time_sec=0.12,
        )
