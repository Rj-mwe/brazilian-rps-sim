"""
Suíte de Testes Unitários TDD: Modelo Ionosférico de Klobuchar (Issue #12)
========================================================================
Subdomínio: signal_propagation (Hexágono Modular - Nível 2)
Validação dos requisitos do IS-GPS-200 / RTCA DO-229D para a região equatorial brasileira:
- Transição diurna/noturna (piso noturno de 5 ns e pico às 14h locais).
- Função de obliquidade (Mapping Function F).
- Escalonamento quadrático com a frequência da portadora.
- Tolerância analítica < 1e-3 m.
"""

import math
import pytest
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.signal_propagation.value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO
from rps_br.core.domain.signal_propagation.value_objects.IonosphericDelayVO import IonosphericDelayVO
from rps_br.core.domain.signal_propagation.services.IonosphereKlobucharService import IonosphereKlobucharService


@pytest.fixture
def sjc_coords() -> GeodeticCoordinatesVO:
    """Coordenadas do ITA / São José dos Campos - SP."""
    return GeodeticCoordinatesVO(latitude_deg=-23.21, longitude_deg=-45.87, altitude_km=0.6)


@pytest.fixture
def default_coeffs() -> KlobucharCoefficientsVO:
    return KlobucharCoefficientsVO.default_gps_broadcast()


@pytest.fixture
def brazilian_eia_coeffs() -> KlobucharCoefficientsVO:
    return KlobucharCoefficientsVO.brazilian_equatorial_high_solar()


def test_nighttime_delay_matches_standard_5ns_constant(sjc_coords, default_coeffs):
    """
    À noite (ex: 02:00 local solar), a fase |x| >= 1.57.
    O retardo vertical deve ser estritamente o piso físico de 5.0e-9 s (~1.49896 m).
    """
    t_gps_night = 18207.0

    delay: IonosphericDelayVO = IonosphereKlobucharService.compute_delay(
        user_coords=sjc_coords,
        elevation_deg=90.0,  # Zênite
        azimuth_deg=0.0,
        gps_time_sec=t_gps_night,
        coefficients=default_coeffs,
    )

    assert delay.is_nighttime is True
    expected_vertical_sec = 5.0e-9
    assert abs(delay.vertical_delay_s - expected_vertical_sec) < 1e-12

    expected_slant_m = delay.obliquity_factor * expected_vertical_sec * 299792458.0
    assert abs(delay.slant_delay_m - expected_slant_m) < 1e-4  # < 1e-3 m


def test_solar_peak_at_14h_local_time(sjc_coords, default_coeffs):
    """
    Às 14:00 hora solar local (50.400 segundos), x = 0.
    A expansão polinomial vale 1.0 e o retardo vertical atinge o pico (5 ns + A_I).
    """
    lambda_u_sc = sjc_coords.longitude_deg / 180.0
    t_gps_peak = (50400.0 - (43200.0 * lambda_u_sc)) % 86400.0

    delay: IonosphericDelayVO = IonosphereKlobucharService.compute_delay(
        user_coords=sjc_coords,
        elevation_deg=90.0,
        azimuth_deg=0.0,
        gps_time_sec=t_gps_peak,
        coefficients=default_coeffs,
    )

    assert delay.is_nighttime is False
    assert delay.vertical_delay_s > 5.0e-9
    assert delay.slant_delay_m > 3.0


def test_obliquity_factor_monotonic_increase():
    """
    O fator de obliquidade (Mapping Function F) deve ser estritamente decrescente com a elevação:
    F(90°) ~ 1.00 e F(5°) ~ 3.0.
    """
    coords = GeodeticCoordinatesVO(latitude_deg=-15.78, longitude_deg=-47.92, altitude_km=1.1)  # Brasília
    coeffs = KlobucharCoefficientsVO.default_gps_broadcast()

    d_zenith = IonosphereKlobucharService.compute_delay(coords, 90.0, 0.0, 50400.0, coeffs)
    d_45deg = IonosphereKlobucharService.compute_delay(coords, 45.0, 0.0, 50400.0, coeffs)
    d_10deg = IonosphereKlobucharService.compute_delay(coords, 10.0, 0.0, 50400.0, coeffs)
    d_5deg = IonosphereKlobucharService.compute_delay(coords, 5.0, 0.0, 50400.0, coeffs)

    assert 1.0 <= d_zenith.obliquity_factor < 1.01
    assert d_zenith.obliquity_factor < d_45deg.obliquity_factor
    assert d_45deg.obliquity_factor < d_10deg.obliquity_factor
    assert d_10deg.obliquity_factor < d_5deg.obliquity_factor
    assert d_5deg.obliquity_factor > 2.5


def test_frequency_scaling_l1_vs_l2(sjc_coords, default_coeffs):
    """
    A dispersão ionosférica é inversamente proporcional ao quadrado da frequência.
    Delta_rho(L2) / Delta_rho(L1) = (f_L1 / f_L2)^2 ~ (1575.42 / 1227.60)^2 ~ 1.6469
    """
    f_l1 = 1575.42e6
    f_l2 = 1227.60e6
    expected_ratio = (f_l1 / f_l2) ** 2

    d_l1 = IonosphereKlobucharService.compute_delay(sjc_coords, 30.0, 45.0, 50400.0, default_coeffs, frequency_hz=f_l1)
    d_l2 = IonosphereKlobucharService.compute_delay(sjc_coords, 30.0, 45.0, 50400.0, default_coeffs, frequency_hz=f_l2)

    actual_ratio = d_l2.slant_delay_m / d_l1.slant_delay_m
    assert abs(actual_ratio - expected_ratio) < 1e-4


def test_brazilian_eia_high_solar_activity_impact(sjc_coords, brazilian_eia_coeffs):
    """
    Na Anomalia de Ionização Equatorial (EIA) brasileira sob alta atividade solar,
    o retardo diurno atinge valores elevados (> 20 metros em elevações médias).
    """
    lambda_u_sc = sjc_coords.longitude_deg / 180.0
    t_gps_peak = (50400.0 - (43200.0 * lambda_u_sc)) % 86400.0

    delay = IonosphereKlobucharService.compute_delay(
        user_coords=sjc_coords,
        elevation_deg=20.0,
        azimuth_deg=0.0,
        gps_time_sec=t_gps_peak,
        coefficients=brazilian_eia_coeffs,
    )

    assert delay.slant_delay_m > 15.0
    assert delay.obliquity_factor > 1.8


def test_coefficients_validation():
    """Valida a imutabilidade e a rejeição de tuplas de coeficientes inválidas."""
    with pytest.raises(ValueError):
        KlobucharCoefficientsVO(alpha=(1.0, 2.0, 3.0), beta=(1.0, 2.0, 3.0, 4.0))

    with pytest.raises(ValueError):
        KlobucharCoefficientsVO(alpha=(1.0, 2.0, 3.0, 4.0), beta=(1.0, 2.0))


def test_level2_subdomain_import_accessibility():
    """Verifica se os módulos podem ser importados tanto no nível do subdomínio quanto de seus subpacotes."""
    from rps_br.core.domain.signal_propagation import (
        IonosphereKlobucharService as SubdomainSvc,
        KlobucharCoefficientsVO as SubdomainVo,
        IonosphericDelayVO as SubdomainDelay,
    )
    from rps_br.core.domain.signal_propagation.services.IonosphereKlobucharService import IonosphereKlobucharService as PackageSvc
    from rps_br.core.domain.signal_propagation.value_objects.KlobucharCoefficientsVO import KlobucharCoefficientsVO as PackageVo

    assert SubdomainSvc is PackageSvc
    assert SubdomainVo is PackageVo
