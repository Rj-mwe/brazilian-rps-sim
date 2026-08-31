import math
from brazilian_rps_sim.astrodynamics import load_simulation_config
from brazilian_rps_sim.core.domain.aggregates.ConstellationAggregate import ConstellationAggregate

def test_constellation_from_yaml_and_24h_orbit_closure():
    cfg = load_simulation_config()
    constellation = ConstellationAggregate.from_config(cfg.get('constellation', {}))

    assert len(constellation.satellites) == 7

    # 1. Propaga em t=0
    constellation.propagate_all(0.0)
    pos_t0 = {sat.sat_id: (sat.geodetic.latitude_deg, sat.geodetic.longitude_deg) for sat in constellation.satellites}

    # 2. Propaga exatamente 1 Dia Sideral (86164.0905 s)
    sidereal_day = 86164.0905
    constellation.propagate_all(sidereal_day)
    pos_t1 = {sat.sat_id: (sat.geodetic.latitude_deg, sat.geodetic.longitude_deg) for sat in constellation.satellites}

    # 3. Verifica fechamento orbital da Figura-8 e fixação GEO (erro < 0.05 graus)
    for sat_id in pos_t0:
        lat0, lon0 = pos_t0[sat_id]
        lat1, lon1 = pos_t1[sat_id]
        assert math.isclose(lat0, lat1, abs_tol=0.05), f"Satélite {sat_id} não fechou ciclo de latitude em 24h!"
        assert math.isclose(lon0, lon1, abs_tol=0.05), f"Satélite {sat_id} não fechou ciclo de longitude em 24h!"
