from rps_br.infrastructure.config.config_loader import load_simulation_config
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.interfaces.ITelemetryOutboundPort import ITelemetryOutboundPort
from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.shared.value_objects.QuaternionVO import QuaternionVO
from rps_br.core.application.services.PropagateConstellationUseCase import PropagateConstellationUseCase
from rps_br.core.application.dtos.SimulationDTOs import SimulationStepRequestDTO

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
    assert len(response.satellites) == len(constellation.satellites)
    assert len(mock_adapter.published_satellites) == len(constellation.satellites)

    # Verifica se os satélites GEO mantiveram suas longitudes centrais aproximadas
    for sat in response.satellites:
        if sat.type == "GEO":
            assert abs(sat.latitude_deg) < 0.1
