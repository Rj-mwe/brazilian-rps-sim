"""
Mapper responsável pela conversão bidirecional entre Agregados de Domínio e DTOs de Aplicação.
"""

from brazilian_rps_sim.core.domain.aggregates.SatelliteAggregate import SatelliteAggregate
from brazilian_rps_sim.core.application.dtos.SimulationDTOs import SatelliteTelemetryResponseDTO

class TelemetryMapper:
    @staticmethod
    def to_dto(sat: SatelliteAggregate) -> SatelliteTelemetryResponseDTO:
        """Mapeia o estado do Agregado do Satélite em um DTO de resposta serializável."""
        return SatelliteTelemetryResponseDTO(
            id=sat.sat_id,
            name=sat.name,
            type=sat.sat_type,
            latitude_deg=round(sat.geodetic.latitude_deg, 4),
            longitude_deg=round(sat.geodetic.longitude_deg, 4),
            altitude_km=round(sat.geodetic.altitude_km, 2),
            x_ecef_km=round(sat.r_ecef.x, 3),
            y_ecef_km=round(sat.r_ecef.y, 3),
            z_ecef_km=round(sat.r_ecef.z, 3),
            qx=round(sat.attitude_nadir.x, 6),
            qy=round(sat.attitude_nadir.y, 6),
            qz=round(sat.attitude_nadir.z, 6),
            qw=round(sat.attitude_nadir.w, 6),
            sim_time_sec=round(sat.last_sim_time_sec, 3)
        )
