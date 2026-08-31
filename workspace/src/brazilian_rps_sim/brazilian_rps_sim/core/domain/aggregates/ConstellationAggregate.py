"""
Agregado Raiz da Constelação RPS-BR mantendo a coleção dos 7 satélites (3 GEO + 4 IGSO).
"""

from dataclasses import dataclass, field
from brazilian_rps_sim.core.domain.aggregates.SatelliteAggregate import SatelliteAggregate
from brazilian_rps_sim.core.domain.value_objects.KeplerianElementsVO import KeplerianElementsVO

@dataclass
class ConstellationAggregate:
    satellites: list[SatelliteAggregate] = field(default_factory=list)

    @classmethod
    def from_config(cls, constellation_cfg: dict) -> 'ConstellationAggregate':
        """Instancia a constelação a partir do dicionário de configuração declarativo."""
        sats_list = constellation_cfg.get('satellites', [])
        satellites = []
        for s in sats_list:
            elem = KeplerianElementsVO.from_degrees(
                a_km=s.get('semi_major_axis_km', 42164.14),
                e=s.get('eccentricity', 0.0),
                inc_deg=s.get('inclination_deg', 0.0),
                raan_deg=s.get('raan_deg', 0.0),
                argp_deg=s.get('arg_perigee_deg', 0.0),
                m0_deg=s.get('mean_anomaly_deg', 0.0)
            )
            sat = SatelliteAggregate(
                sat_id=s.get('id', 1),
                name=s.get('name', f"SAT-{s.get('id', 1)}"),
                sat_type=s.get('type', 'GEO'),
                elements=elem,
                station_lon_deg=s.get('station_longitude_deg', 0.0)
            )
            satellites.append(sat)
        return cls(satellites=satellites)

    def propagate_all(self, t_sec: float) -> None:
        """Propaga todos os satélites da constelação para o instante t_sec."""
        for sat in self.satellites:
            sat.propagate_to(t_sec)

    def get_satellite_by_id(self, sat_id: int) -> SatelliteAggregate | None:
        for s in self.satellites:
            if s.sat_id == sat_id:
                return s
        return None
