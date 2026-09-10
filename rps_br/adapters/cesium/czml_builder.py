#!/usr/bin/env python3
"""
Adaptador Geoespacial 3D: CzmlConstellationBuilder
===================================================
Gera documentos no formato oficial CZML (Cesium Language - NASA / Cesium),
descrevendo a constelação brasileira de 7 satélites (3 GEO + 4 IGSO),
suas órbitas contínuas em 3D, cones de cobertura e as estações terrestres de referência.
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np

from rps_br.infrastructure.config.config_loader import load_simulation_config, find_config_file
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.application.services.CalculateGroundStationDopUseCase import DEFAULT_BRAZILIAN_GROUND_STATIONS


from rps_br.core.application.services.SimulationSessionService import SimulationSessionService


class CzmlConstellationBuilder:
    """Tradutor de modelo astrodinâmico para pacotes CZML (Cesium Language)."""

    def __init__(self, config_path: Optional[str] = None):
        cfg_file = config_path or find_config_file()
        self.config = load_simulation_config(cfg_file)
        self.constellation = ConstellationAggregate.from_config(self.config)

    def generate_czml(
        self,
        epoch_iso: str = "2026-09-09T00:00:00Z",
        duration_hours: float = 24.0,
        sample_step_sec: float = 600.0
    ) -> List[Dict[str, Any]]:
        """
        Produz a lista completa de pacotes CZML para a constelação de satélites e estações de solo.
        """
        czml_packets: List[Dict[str, Any]] = []

        total_sec = int(duration_hours * 3600.0)
        end_iso = "2026-09-10T00:00:00Z"
        interval = f"{epoch_iso}/{end_iso}"

        # Obtém estado soberano da sessão de simulação para inicializar relógio alinhado
        session = SimulationSessionService.get_instance()
        state = session.get_state()
        multiplier = float(state.time_multiplier)
        current_time_iso = epoch_iso
        if state.sim_time_sec > 0:
            from datetime import datetime, timedelta
            base_dt = datetime.fromisoformat(epoch_iso.replace("Z", "+00:00"))
            curr_dt = base_dt + timedelta(seconds=float(state.sim_time_sec))
            current_time_iso = curr_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Pacote de Documento Mestre
        czml_packets.append({
            "id": "document",
            "name": "Brazilian Regional Positioning System (RPS-BR) 3D Constellation",
            "version": "1.0",
            "clock": {
                "interval": interval,
                "currentTime": current_time_iso,
                "multiplier": multiplier,
                "range": "LOOP_STOP",
                "step": "SYSTEM_CLOCK_MULTIPLIER"
            }
        })

        # 2. Amostragem temporal de trajetórias para cada satélite
        time_samples = np.arange(0, total_sec + 1, sample_step_sec)
        sat_trajectories: Dict[str, List[float]] = {s.sat_id: [] for s in self.constellation.satellites}

        for t in time_samples:
            self.constellation.propagate_all(float(t))
            for s in self.constellation.satellites:
                # Posição ECEF em metros (WGS84)
                r_m = s.r_ecef.to_numpy() * 1000.0
                sat_trajectories[s.sat_id].extend([float(t), round(float(r_m[0]), 1), round(float(r_m[1]), 1), round(float(r_m[2]), 1)])

        # 3. Pacotes de Satélites (GEO em Ciano, IGSO em Âmbar Dourado)
        for s in self.constellation.satellites:
            is_geo = (s.sat_type == "GEO")
            color_rgba = [0, 230, 255, 255] if is_geo else [245, 158, 11, 255]
            trail_rgba = [0, 230, 255, 180] if is_geo else [245, 158, 11, 180]

            sat_packet = {
                "id": f"SAT-{s.sat_id}",
                "name": s.name,
                "description": f"<b>{s.name}</b><br>Tipo: {s.sat_type}<br>Semieixo: {s.elements.semi_major_axis_km:.1f} km<br>Inclinação: {math.degrees(s.elements.inclination_rad):.1f}°",
                "availability": interval,
                "point": {
                    "pixelSize": 12 if is_geo else 10,
                    "color": {"rgba": color_rgba},
                    "outlineColor": {"rgba": [15, 23, 42, 255]},
                    "outlineWidth": 2
                },
                "label": {
                    "text": s.name,
                    "font": "11pt Inter, sans-serif",
                    "fillColor": {"rgba": [255, 255, 255, 255]},
                    "outlineColor": {"rgba": [15, 23, 42, 255]},
                    "outlineWidth": 2,
                    "style": "FILL_AND_OUTLINE",
                    "verticalOrigin": "BOTTOM",
                    "pixelOffset": {"cartesian2": [0, -12]}
                },
                "path": {
                    "material": {
                        "solidColor": {
                            "color": {"rgba": trail_rgba}
                        }
                    },
                    "width": 2.0 if is_geo else 2.5,
                    "leadTime": total_sec,
                    "trailTime": total_sec,
                    "resolution": 600
                },
                "position": {
                    "epoch": epoch_iso,
                    "cartesian": sat_trajectories[s.sat_id]
                }
            }
            czml_packets.append(sat_packet)

        # 4. Pacotes das Estações Terrestres Brasileiras (ITA, BSB, Alcântara, etc.)
        r_earth = 6378.137
        flattening = 1.0 / 298.257223563
        e2 = 2.0 * flattening - flattening**2

        for name, coords in DEFAULT_BRAZILIAN_GROUND_STATIONS.items():
            lat_r = math.radians(coords.latitude_deg)
            lon_r = math.radians(coords.longitude_deg)
            n_val = r_earth / math.sqrt(1.0 - e2 * math.sin(lat_r)**2)
            alt_k = coords.altitude_km
            x_m = (n_val + alt_k) * math.cos(lat_r) * math.cos(lon_r) * 1000.0
            y_m = (n_val + alt_k) * math.cos(lat_r) * math.sin(lon_r) * 1000.0
            z_m = (n_val * (1.0 - e2) + alt_k) * math.sin(lat_r) * 1000.0

            sta_packet = {
                "id": f"STA-{name.replace(' ', '_')}",
                "name": name,
                "description": f"<b>Estação Terrestre de Monitoramento</b><br>Local: {name}<br>Lat: {coords.latitude_deg:.4f}°<br>Lon: {coords.longitude_deg:.4f}°<br>Alt: {coords.altitude_km*1000:.1f} m",
                "availability": interval,
                "position": {
                    "cartesian": [round(float(x_m), 1), round(float(y_m), 1), round(float(z_m), 1)]
                },
                "point": {
                    "pixelSize": 8,
                    "color": {"rgba": [16, 185, 129, 255]},  # Verde Esmeralda
                    "outlineColor": {"rgba": [255, 255, 255, 255]},
                    "outlineWidth": 1.5
                },
                "label": {
                    "text": name.split("(")[0].strip(),
                    "font": "10pt Inter, sans-serif",
                    "fillColor": {"rgba": [16, 185, 129, 255]},
                    "outlineColor": {"rgba": [15, 23, 42, 255]},
                    "outlineWidth": 2,
                    "style": "FILL_AND_OUTLINE",
                    "verticalOrigin": "TOP",
                    "pixelOffset": {"cartesian2": [0, 8]}
                }
            }
            czml_packets.append(sta_packet)

        return czml_packets
