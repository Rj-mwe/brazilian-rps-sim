"""
Serviço de Aplicação: SimulationSessionService
==============================================
Detém o Estado Soberano da Sessão de Simulação no Core da aplicação (DDD/Hexagonal).
Todos os adaptadores (Web, Gazebo, ROS 2, CLI) atuam como meros clientes ou
observadores deste serviço, preservando o princípio da Fonte Única da Verdade.
"""

import threading
from typing import List, Optional

from rps_br.core.application.dtos.SimulationDTOs import (
    SimulationClockTickDTO,
    PauseSimulationRequestDTO,
    SetTimeMultiplierRequestDTO,
    SimulationSessionStateDTO,
)
from rps_br.core.domain.interfaces.ISimulationControlOutboundPort import (
    ISimulationControlOutboundPort,
)


class SimulationSessionService:
    """
    Controlador centralizado do estado de execução e tempo virtual da simulação.
    Thread-safe com suporte a múltiplos adaptadores de saída.
    """

    _instance: Optional['SimulationSessionService'] = None
    _singleton_lock = threading.Lock()

    def __init__(self, initial_multiplier: float = 1.0):
        self._lock = threading.RLock()
        self._sim_time_sec: float = 0.0
        self._is_paused: bool = False
        self._time_multiplier: float = max(0.1, float(initial_multiplier))
        self._mode: str = "STANDALONE_AUTONOMOUS"  # Muda para MASTER_GAZEBO ao receber ticks
        self._elevation_mask_deg: float = 5.0
        self._selected_station_name: str = "São José dos Campos (ITA / SP)"
        self._last_tick_time_wall: float = 0.0

        # Portas de Saída registradas (ex: GazeboWorldControlAdapter)
        self._control_outbound_ports: List[ISimulationControlOutboundPort] = []

    @classmethod
    def get_instance(cls, initial_multiplier: float = 1.0) -> 'SimulationSessionService':
        """Obtém a instância canônica compartilhada do serviço no processo."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls(initial_multiplier=initial_multiplier)
            return cls._instance

    def register_control_outbound_port(self, port: ISimulationControlOutboundPort) -> None:
        """Registra uma porta de saída para receber comandos de controle (ex: Gazebo)."""
        with self._lock:
            if port not in self._control_outbound_ports:
                self._control_outbound_ports.append(port)

    def unregister_control_outbound_port(self, port: ISimulationControlOutboundPort) -> None:
        with self._lock:
            if port in self._control_outbound_ports:
                self._control_outbound_ports.remove(port)

    # --------------------------------------------------------------------------
    # Casos de Uso de Ingestão de Relógio (Inbound)
    # --------------------------------------------------------------------------
    def ingest_clock_tick(self, tick: SimulationClockTickDTO) -> None:
        """
        Recebe um pulso de relógio emitido pelo Master Clock (ex: Gazebo /clock).
        Promove o modo para MASTER_GAZEBO e atualiza o estado canônico.
        """
        with self._lock:
            self._mode = "MASTER_GAZEBO"
            self._sim_time_sec = float(tick.sim_time_sec)
            self._is_paused = bool(tick.is_paused)

    def advance_standalone_clock(self, dt_wall_sec: float) -> bool:
        """
        Avança o tempo se e somente se o Core estiver operando em modo autônomo (sem Master Clock externo).
        Retorna True se o tempo avançou.
        """
        with self._lock:
            if self._mode == "STANDALONE_AUTONOMOUS" and not self._is_paused:
                self._sim_time_sec += dt_wall_sec * self._time_multiplier
                return True
            return False

    # --------------------------------------------------------------------------
    # Casos de Uso de Controle de Execução (Inbound -> Notifica Outbound Ports)
    # --------------------------------------------------------------------------
    def pause(self, req: PauseSimulationRequestDTO) -> bool:
        """Pausa ou retoma a simulação e comanda os adaptadores de motor físico conectados."""
        with self._lock:
            self._is_paused = bool(req.paused)
            success = True
            for port in self._control_outbound_ports:
                try:
                    if self._is_paused:
                        ok = port.pause_simulation()
                    else:
                        ok = port.resume_simulation()
                    if not ok:
                        success = False
                except Exception:
                    success = False
            return success

    def step(self, steps: int = 1) -> bool:
        """Comanda N passos de simulação nos motores físicos conectados."""
        with self._lock:
            success = True
            for port in self._control_outbound_ports:
                try:
                    ok = port.step_simulation(steps)
                    if not ok:
                        success = False
                except Exception:
                    success = False
            return success

    def set_time_multiplier(self, req: SetTimeMultiplierRequestDTO) -> None:
        """Ajusta o fator de aceleração temporal."""
        with self._lock:
            self._time_multiplier = max(0.1, min(req.multiplier, 86400.0))
            for port in self._control_outbound_ports:
                try:
                    port.set_simulation_rate(self._time_multiplier)
                except Exception:
                    pass

    def set_elevation_mask(self, mask_deg: float) -> None:
        with self._lock:
            self._elevation_mask_deg = max(0.0, min(mask_deg, 45.0))

    def set_station_name(self, station_name: str) -> None:
        with self._lock:
            self._selected_station_name = station_name

    # --------------------------------------------------------------------------
    # Consulta de Estado Canônico
    # --------------------------------------------------------------------------
    def get_state(self) -> SimulationSessionStateDTO:
        with self._lock:
            return SimulationSessionStateDTO(
                sim_time_sec=self._sim_time_sec,
                is_paused=self._is_paused,
                time_multiplier=self._time_multiplier,
                mode=self._mode,
                elevation_mask_deg=self._elevation_mask_deg,
                selected_station_name=self._selected_station_name,
            )

    def reset(self) -> None:
        """Reinicia o estado da sessão para os valores padrão."""
        with self._lock:
            self._sim_time_sec = 0.0
            self._is_paused = False
            self._time_multiplier = 1.0
            self._mode = "STANDALONE_AUTONOMOUS"
            self._elevation_mask_deg = 5.0
            self._selected_station_name = "São José dos Campos (ITA / SP)"
            self._control_outbound_ports.clear()

