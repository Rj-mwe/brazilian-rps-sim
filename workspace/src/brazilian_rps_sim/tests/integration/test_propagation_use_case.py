from brazilian_rps_sim.astrodynamics import load_simulation_config
from brazilian_rps_sim.core.domain.aggregates.ConstellationAggregate import ConstellationAggregate
from brazilian_rps_sim.core.domain.interfaces.ITelemetryOutboundPort import ITelemetryOutboundPort
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO
from brazilian_rps_sim.core.application.services.PropagateConstellationUseCase import PropagateConstellationUseCase
from brazilian_rps_sim.core.application.dtos.SimulationDTOs import SimulationStepRequestDTO

class MockTelemetryOutboundAdapter(ITelemetryOutboundPort):
    def __init__(self):
        self.published_satellites = []
        self.published_celestial = []

    def publish_satellite_state(self, sat_id: int, name: str, sat_type: str,
                                r_ecef: Vector3DVO, geodetic: GeodeticCoordinatesVO,
                                attitude: QuaternionVO, t_sec: float) -> None:
        self.published_satellites.append({
            'sat_id': sat_id,
            'name': name,
            'sat_type': sat_type,
            'lat': geodetic.latitude_deg,
            'lon': geodetic.longitude_deg,
            't': t_sec
        })

    def publish_celestial_state(self, celestial_state: dict) -> None:
        self.published_celestial.append(celestial_state)

def test_propagate_constellation_use_case():
    cfg = load_simulation_config()
    constellation = ConstellationAggregate.from_config(cfg.get('constellation', {}))
    mock_adapter = MockTelemetryOutboundAdapter()

    use_case = PropagateConstellationUseCase(
        constellation=constellation,
        telemetry_port=mock_adapter
    )

    req = SimulationStepRequestDTO(sim_time_sec=3600.0)
    response = use_case.execute(req)

    assert response.sim_time_sec == 3600.0
    assert len(response.satellites) == 7
    assert len(mock_adapter.published_satellites) == 7

    # Verifica se os 3 GEO mantiveram suas longitudes centrais aproximadas
    geo_1 = [s for s in response.satellites if s.id == 1][0]
    geo_2 = [s for s in response.satellites if s.id == 2][0]
    geo_3 = [s for s in response.satellites if s.id == 3][0]

    assert abs(geo_1.longitude_deg - (-70.0)) < 1.0
    assert abs(geo_2.longitude_deg - (-50.0)) < 1.0
    assert abs(geo_3.longitude_deg - (-35.0)) < 1.0
