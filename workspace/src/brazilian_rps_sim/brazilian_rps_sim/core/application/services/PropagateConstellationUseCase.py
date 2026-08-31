"""
Caso de Uso / Application Service responsável por orquestrar a propagação dos 7 satélites do RPS-BR.
"""

from brazilian_rps_sim.core.application.interfaces.IPropagateConstellationUseCase import IPropagateConstellationUseCase
from brazilian_rps_sim.core.application.dtos.SimulationDTOs import (
    SimulationStepRequestDTO,
    ConstellationStatusResponseDTO
)
from brazilian_rps_sim.core.application.mappers.TelemetryMapper import TelemetryMapper
from brazilian_rps_sim.core.domain.aggregates.ConstellationAggregate import ConstellationAggregate
from brazilian_rps_sim.core.domain.interfaces.ITelemetryOutboundPort import ITelemetryOutboundPort

class PropagateConstellationUseCase(IPropagateConstellationUseCase):
    def __init__(self, constellation: ConstellationAggregate, telemetry_port: ITelemetryOutboundPort = None):
        self.constellation = constellation
        self.telemetry_port = telemetry_port

    def execute(self, request: SimulationStepRequestDTO) -> ConstellationStatusResponseDTO:
        t_sec = request.sim_time_sec
        self.constellation.propagate_all(t_sec)

        dto_list = []
        for sat in self.constellation.satellites:
            dto = TelemetryMapper.to_dto(sat)
            dto_list.append(dto)

            # Despacha para a porta de saída (se conectada)
            if self.telemetry_port:
                self.telemetry_port.publish_satellite_state(
                    sat_id=sat.sat_id,
                    name=sat.name,
                    sat_type=sat.sat_type,
                    r_ecef=sat.r_ecef,
                    geodetic=sat.geodetic,
                    attitude=sat.attitude_nadir,
                    t_sec=t_sec
                )

        return ConstellationStatusResponseDTO(
            satellites=dto_list,
            sim_time_sec=t_sec
        )
