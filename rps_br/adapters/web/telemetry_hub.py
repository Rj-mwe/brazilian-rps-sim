#!/usr/bin/env python3
"""
Telemetry Hub: Servidor de Estado e Agregador de Telemetria da Constelação RPS-BR.
Padrão Hexagonal: Conecta o Core puro (Casos de Uso, Astrodinâmica, PVT e Troposfera)
ao ecossistema Web assíncrono (FastAPI, REST e WebSockets).
"""

import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional
import numpy as np

from rps_br.infrastructure.config.config_loader import load_simulation_config, find_config_file
from rps_br.core.domain.astrodynamics.aggregates.ConstellationAggregate import ConstellationAggregate
from rps_br.core.domain.astrodynamics.services.CoordinateTransformService import CoordinateTransformService
from rps_br.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
from rps_br.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
from rps_br.core.domain.navigation_pvt.strategies.ElevationMaskDopStrategy import ElevationMaskDopStrategy
from rps_br.core.application.services.CalculateGroundStationDopUseCase import (
    CalculateGroundStationDopUseCase,
    DEFAULT_BRAZILIAN_GROUND_STATIONS,
)
from rps_br.core.domain.signal_propagation.services.TroposphereSaastamoinenService import TroposphereSaastamoinenService
from rps_br.core.domain.signal_propagation.value_objects.TroposphericWeatherVO import TroposphericWeatherVO


# Estações terrestres expandidas com o ITA (São José dos Campos) e Alcântara
BRAZILIAN_GROUND_STATIONS = {
    "São José dos Campos (ITA / SP)": GeodeticCoordinatesVO(-23.2128, -45.8755, 0.600),
    "Brasília (DF - Centro)": GeodeticCoordinatesVO(-15.7975, -47.8633, 1.172),
    "Alcântara (CLA / MA)": GeodeticCoordinatesVO(-2.3731, -44.3964, 0.045),
    "Manaus (AM - Norte)": GeodeticCoordinatesVO(-3.1190, -60.0217, 0.092),
    "Rio de Janeiro (RJ - Sudeste)": GeodeticCoordinatesVO(-22.9068, -43.1729, 0.005),
    "Porto Alegre (RS - Sul)": GeodeticCoordinatesVO(-30.0346, -51.2177, 0.010),
    "Fortaleza (CE - Nordeste)": GeodeticCoordinatesVO(-3.7172, -38.5433, 0.016),
}


class TelemetryHub:
    """Hub centralizador de telemetria em tempo real para clientes REST e WebSockets."""

    _instance: Optional['TelemetryHub'] = None
    _lock = threading.Lock()

    def __init__(self, config_path: Optional[str] = None):
        self.lock = threading.RLock()
        
        # Carregamento de configurações
        cfg_file = config_path or find_config_file()
        self.config = load_simulation_config(cfg_file)
        
        # Agregado do Domínio
        self.constellation = ConstellationAggregate.from_config(self.config)
        
        # Parâmetros de Simulação
        sim_cfg = self.config.get("simulation", {})
        self.time_multiplier = float(sim_cfg.get("time_multiplier", 1.0))
        self.sim_time_sec = 0.0
        self.is_paused = False
        self.elevation_mask_deg = 5.0
        self.selected_station_name = "São José dos Campos (ITA / SP)"
        
        # Serviços de Domínio
        self.coord_service = CoordinateTransformService()
        self.weather = TroposphericWeatherVO(
            pressure_hpa=1013.25,
            temperature_k=293.15,
            relative_humidity_pct=60.0
        )
        self.tropo_service = TroposphereSaastamoinenService()
        self.dop_use_case = CalculateGroundStationDopUseCase(
            strategy=ElevationMaskDopStrategy(mask_angle_deg=self.elevation_mask_deg),
            ground_stations=BRAZILIAN_GROUND_STATIONS
        )
        
        # Histórico temporal para gráficos (máximo 120 pontos)
        self.dop_history: deque = deque(maxlen=120)
        
        # Inicializa primeiro snapshot
        self._recompute_state()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> 'TelemetryHub':
        """Singleton thread-safe para compartilhamento entre rotas FastAPI e nós ROS 2."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config_path)
            return cls._instance

    def set_time_multiplier(self, multiplier: float) -> None:
        with self.lock:
            self.time_multiplier = max(0.1, min(multiplier, 86400.0))

    def set_paused(self, paused: bool) -> None:
        with self.lock:
            self.is_paused = paused

    def set_elevation_mask(self, mask_deg: float) -> None:
        with self.lock:
            self.elevation_mask_deg = max(0.0, min(mask_deg, 45.0))
            self.dop_use_case.set_strategy(ElevationMaskDopStrategy(mask_angle_deg=self.elevation_mask_deg))
            self._recompute_state()

    def set_station(self, station_name: str) -> bool:
        with self.lock:
            if station_name in BRAZILIAN_GROUND_STATIONS:
                self.selected_station_name = station_name
                self._recompute_state()
                return True
            return False

    def step(self, dt_wall_sec: float) -> None:
        """Avança o relógio de simulação e recalcula a astrodinâmica."""
        with self.lock:
            if not self.is_paused:
                self.sim_time_sec += dt_wall_sec * self.time_multiplier
                self._recompute_state()

    def update_sim_time(self, sim_time_sec: float) -> None:
        """Atualiza o relógio a partir de uma fonte externa (ex: /clock do ROS 2 ou Gazebo)."""
        with self.lock:
            self.sim_time_sec = sim_time_sec
            self._recompute_state()

    def _recompute_state(self) -> None:
        """Propaga a constelação e atualiza todas as métricas analíticas em $O(N)$."""
        # 1. Posições dos Satélites
        ecef_dict: Dict[str, np.ndarray] = {}
        sats_info: List[Dict[str, Any]] = []
        
        station_vo = BRAZILIAN_GROUND_STATIONS.get(
            self.selected_station_name,
            BRAZILIAN_GROUND_STATIONS["São José dos Campos (ITA / SP)"]
        )
        
        atmospheric_delays: Dict[str, Dict[str, float]] = {}

        self.constellation.propagate_all(self.sim_time_sec)
        for sat in self.constellation.satellites:
            r_ecef = sat.r_ecef
            geodetic = sat.geodetic
            ecef_np = r_ecef.to_numpy()
            ecef_dict[sat.name] = ecef_np

            # Cálculo de Azimute, Elevação e Distância Topocêntrica ENU
            el_deg, az_deg, dist_km = self.coord_service.compute_topocentric_look_angles(
                ecef_np,
                station_vo.latitude_deg,
                station_vo.longitude_deg
            )
            in_view = el_deg >= self.elevation_mask_deg

            # Retardo Troposférico Saastamoinen
            if el_deg > 1.0:
                tropo_res = self.tropo_service.compute_delay(
                    user_coords=station_vo,
                    elevation_deg=el_deg,
                    weather=self.weather
                )
                tropo_m = round(tropo_res.slant_total_delay_m, 3)
                tropo_ns = round(tropo_res.slant_total_delay_sec * 1e9, 2)
            else:
                tropo_m = 0.0
                tropo_ns = 0.0

            # Retardo Ionosférico aproximado (Klobuchar L1 baseline)
            iono_m = round(4.5 / max(0.1, np.sin(np.radians(max(5.0, el_deg)))), 3) if in_view else 0.0

            atmospheric_delays[sat.name] = {
                "tropo_delay_m": tropo_m,
                "tropo_delay_ns": tropo_ns,
                "iono_delay_m": iono_m,
            }

            sats_info.append({
                "id": sat.sat_id,
                "name": sat.name,
                "type": sat.sat_type,
                "lat": round(geodetic.latitude_deg, 4),
                "lon": round(geodetic.longitude_deg, 4),
                "alt_km": round(geodetic.altitude_km, 2),
                "distance_km": round(dist_km, 1),
                "azimuth_deg": round(az_deg, 1),
                "elevation_deg": round(el_deg, 1),
                "in_view": bool(in_view),
                "tropo_m": tropo_m,
                "tropo_ns": tropo_ns,
            })

        # 2. Avaliação de DOP para todas as estações de solo
        dop_results = self.dop_use_case.execute(ecef_dict, self.sim_time_sec)
        active_dop = dop_results.get(self.selected_station_name)

        if active_dop:
            dop_snapshot = {
                "gdop": round(active_dop.gdop, 2) if np.isfinite(active_dop.gdop) else 99.9,
                "pdop": round(active_dop.pdop, 2) if np.isfinite(active_dop.pdop) else 99.9,
                "hdop": round(active_dop.hdop, 2) if np.isfinite(active_dop.hdop) else 99.9,
                "vdop": round(active_dop.vdop, 2) if np.isfinite(active_dop.vdop) else 99.9,
                "tdop": round(active_dop.tdop, 2) if np.isfinite(active_dop.tdop) else 99.9,
                "visible_count": int(active_dop.visible_satellites_count),
                "status": self._classify_pdop(active_dop.pdop),
            }
        else:
            dop_snapshot = {
                "gdop": 99.9, "pdop": 99.9, "hdop": 99.9, "vdop": 99.9, "tdop": 99.9,
                "visible_count": 0, "status": "Sem Cobertura"
            }

        # Armazena histórico DOP
        hours = self.sim_time_sec / 3600.0
        time_label = f"{int(hours):02d}:{int((self.sim_time_sec % 3600) / 60):02d}:{int(self.sim_time_sec % 60):02d}"
        self.dop_history.append({
            "time_sec": round(self.sim_time_sec, 1),
            "time_str": time_label,
            "pdop": dop_snapshot["pdop"],
            "hdop": dop_snapshot["hdop"],
            "vdop": dop_snapshot["vdop"],
            "sats": dop_snapshot["visible_count"]
        })

        self.last_snapshot = {
            "simulation": {
                "time_sec": round(self.sim_time_sec, 1),
                "time_str": time_label,
                "multiplier": self.time_multiplier,
                "is_paused": self.is_paused,
                "elevation_mask_deg": self.elevation_mask_deg,
                "station_name": self.selected_station_name,
                "station_lat": station_vo.latitude_deg,
                "station_lon": station_vo.longitude_deg,
                "station_alt_km": station_vo.altitude_km,
            },
            "dop": dop_snapshot,
            "satellites": sats_info,
            "atmospheric": atmospheric_delays,
            "stations": list(BRAZILIAN_GROUND_STATIONS.keys()),
            "history": list(self.dop_history)
        }

    @staticmethod
    def _classify_pdop(pdop: float) -> str:
        if not np.isfinite(pdop) or pdop > 10.0:
            return "Pobre / Insuficiente"
        if pdop <= 2.5:
            return "Excelente (Grau Aeronáutico)"
        if pdop <= 5.0:
            return "Bom (Operação Padrão)"
        return "Moderado"

    def get_snapshot(self) -> Dict[str, Any]:
        """Retorna o estado serializável completo da constelação e da missão."""
        with self.lock:
            return self.last_snapshot
