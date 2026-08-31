import pytest
import math
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.KeplerianElementsVO import KeplerianElementsVO

def test_vector3d_vo_operations():
    v1 = Vector3DVO(3.0, 4.0, 0.0)
    assert math.isclose(v1.magnitude(), 5.0)
    
    v_norm = v1.normalized()
    assert math.isclose(v_norm.magnitude(), 1.0)
    assert math.isclose(v_norm.x, 0.6)
    assert math.isclose(v_norm.y, 0.8)

    v2 = Vector3DVO(0.0, 1.0, 0.0)
    assert math.isclose(v1.dot(v2), 4.0)

    v_cross = v1.cross(v2)
    assert math.isclose(v_cross.z, 3.0)

def test_geodetic_coordinates_vo_validation():
    geo = GeodeticCoordinatesVO(-15.7801, -47.9292, 1.1) # Brasília
    assert math.isclose(geo.latitude_deg, -15.7801)
    assert math.isclose(geo.longitude_deg, -47.9292)

    with pytest.raises(ValueError):
        GeodeticCoordinatesVO(100.0, 0.0, 0.0) # Latitude > 90

def test_keplerian_elements_vo():
    elem = KeplerianElementsVO.from_degrees(
        a_km=42164.14,
        e=0.06,
        inc_deg=29.0,
        raan_deg=310.0,
        argp_deg=270.0,
        m0_deg=0.0
    )
    assert math.isclose(elem.semi_major_axis_km, 42164.14)
    assert math.isclose(elem.period_sec(), 86164.09, rel_tol=1e-3)

    with pytest.raises(ValueError):
        KeplerianElementsVO(-1000.0, 0.0, 0.0, 0.0, 0.0, 0.0)
