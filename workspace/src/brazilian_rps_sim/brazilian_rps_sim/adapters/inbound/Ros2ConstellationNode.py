"""
Adaptador de Entrada ROS 2 (Driver Silencioso).
Conecta o relógio /clock ao UseCase de propagação do Domínio seguindo o princípio da Regra do Silêncio
(Unix Rule of Silence) — executa de forma limpa sem poluição periódica no stdout.
"""

import rclpy
from rclpy.node import Node

from brazilian_rps_sim.astrodynamics import load_simulation_config, find_config_file
from brazilian_rps_sim.core.domain.aggregates.ConstellationAggregate import ConstellationAggregate
from brazilian_rps_sim.core.domain.aggregates.CelestialSystemAggregate import CelestialSystemAggregate
from brazilian_rps_sim.core.application.services.PropagateConstellationUseCase import PropagateConstellationUseCase
from brazilian_rps_sim.core.application.dtos.SimulationDTOs import SimulationStepRequestDTO
from brazilian_rps_sim.adapters.outbound.Ros2TelemetryOutboundAdapter import Ros2TelemetryOutboundAdapter

from brazilian_rps_sim.core.application.services.CalculateGroundStationDopUseCase import CalculateGroundStationDopUseCase
from brazilian_rps_sim.core.domain.strategies.StandardLeastSquaresDopStrategy import StandardLeastSquaresDopStrategy
from brazilian_rps_sim.core.domain.observers.DopTelemetryBufferObserver import DopTelemetryBufferObserver

class Ros2ConstellationNode(Node):
    def __init__(self):
        super().__init__('rps_constellation_node')

        # 1. Carrega parâmetros declarativos do YAML (Fonte Única da Verdade)
        default_config_path = find_config_file()
        self.declare_parameter('config_path', default_config_path)
        config_path = self.get_parameter('config_path').get_parameter_value().string_value

        cfg = load_simulation_config(config_path)
        sim_cfg = cfg.get('simulation', {})

        self.time_multiplier = float(sim_cfg.get('time_multiplier', 1.0))
        render_scale = float(sim_cfg.get('render_scale', 0.001))
        rate_hz = float(sim_cfg.get('telemetry_rate_hz', 1.0))

        # 2. Instancia Agregados de Domínio Puro
        self.constellation = ConstellationAggregate.from_config(cfg.get('constellation', {}))
        self.celestial_system = CelestialSystemAggregate()

        # 3. Instancia Adaptador de Saída e Casos de Uso (Hexagonal)
        self.outbound_adapter = Ros2TelemetryOutboundAdapter(
            node=self,
            total_satellites=len(self.constellation.satellites),
            render_scale=render_scale
        )
        self.propagate_use_case = PropagateConstellationUseCase(
            constellation=self.constellation,
            telemetry_port=self.outbound_adapter
        )

        # 4. Caso de Uso de Avaliação de DOP (Strategy + Observer Pattern)
        self.dop_use_case = CalculateGroundStationDopUseCase(
            strategy=StandardLeastSquaresDopStrategy(min_elevation_deg=5.0)
        )
        self.dop_buffer_observer = DopTelemetryBufferObserver()
        self.dop_use_case.attach_observer(self.dop_buffer_observer)

        # 5. Timer de atualização (1.0 Hz)
        timer_period = 1.0 / max(rate_hz, 0.1)
        self.timer = self.create_timer(timer_period, self._on_step)

        speed_desc = "1:1 (Tempo Real)" if self.time_multiplier == 1.0 else f"{self.time_multiplier:.0f}x (1s = {self.time_multiplier/86400.0:.2f} dia)"
        self.get_logger().info(
            f"🛰️ [Hexágono Dourado] Constelação RPS-BR (7 satélites) + Motor DOP (Strategy/Observer) ativo | Velocidade: {speed_desc} | Taxa: {rate_hz:.1f} Hz"
        )

    def _on_step(self):
        # Lê o tempo de simulação vindo da ponte /clock
        now_time = self.get_clock().now()
        sim_time_sec = now_time.nanoseconds * 1e-9 * self.time_multiplier

        # Executa o Caso de Uso de Propagação
        req = SimulationStepRequestDTO(sim_time_sec=sim_time_sec)
        self.propagate_use_case.execute(req)

        # Atualiza e despacha estado celeste
        celestial_state = self.celestial_system.compute_state(sim_time_sec)
        self.outbound_adapter.publish_celestial_state(celestial_state)

        # Coleta posições ECEF dos satélites e calcula métricas DOP
        sats_ecef = {sat.name: sat.r_ecef.to_numpy() for sat in self.constellation.satellites}
        self.dop_use_case.execute(sats_ecef, sim_time_sec)
        # Execução estritamente silenciosa (sem spam de terminal)

def main(args=None):
    rclpy.init(args=args)
    node = Ros2ConstellationNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
