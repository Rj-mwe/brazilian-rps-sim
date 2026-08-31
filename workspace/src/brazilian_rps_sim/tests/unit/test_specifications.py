from brazilian_rps_sim.core.domain.specifications.ZenithVisibilitySpec import ZenithVisibilitySpec

def test_zenith_visibility_spec():
    spec = ZenithVisibilitySpec(min_elevation_deg=60.0)

    assert spec.is_satisfied_by(65.0) is True
    assert spec.is_satisfied_by(60.0) is True
    assert spec.is_satisfied_by(59.9) is False
    assert spec.is_satisfied_by(15.0) is False
