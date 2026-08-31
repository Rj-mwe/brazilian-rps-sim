import math
import numpy as np
from brazilian_rps_sim.core.domain.services.CoordinateTransformService import CoordinateTransformService

def test_eci_to_ecef_full_rotation():
    r_initial = np.array([42164.14, 0.0, 0.0], dtype=np.float64)
    sidereal_day = 2.0 * math.pi / CoordinateTransformService.OMEGA_EARTH_DEFAULT

    # t = 0 -> ECEF == ECI
    r_t0 = CoordinateTransformService.eci_to_ecef(r_initial, 0.0)
    assert np.allclose(r_t0, r_initial, atol=1e-6)

    # t = 1 Dia Sideral Exato -> ECEF retorna à mesma coordenada
    r_t1 = CoordinateTransformService.eci_to_ecef(r_initial, sidereal_day)
    assert np.allclose(r_t1, r_initial, atol=1e-4)

def test_ecef_to_geodetic_equator():
    r_equator = np.array([6378.137, 0.0, 0.0], dtype=np.float64)
    geo = CoordinateTransformService.ecef_to_geodetic(r_equator)
    assert math.isclose(geo.latitude_deg, 0.0, abs_tol=1e-5)
    assert math.isclose(geo.longitude_deg, 0.0, abs_tol=1e-5)
    assert math.isclose(geo.altitude_km, 0.0, abs_tol=1e-3)
