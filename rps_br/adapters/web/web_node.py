#!/usr/bin/env python3
"""
Nó ROS 2 do Adaptador Web: Sincroniza o relógio e estado de execução do Gazebo
diretamente com o Core e com o endpoint de sincronização do Web Dashboard.
"""

import json
import time
import urllib.request
import urllib.error
from rclpy.node import Node
from rosgraph_msgs.msg import Clock

from rps_br.adapters.web.telemetry_hub import TelemetryHub


class WebAdapterRos2Node(Node):
    """Nó ROS 2 que atua como Gateway de Entrada (Inbound Clock Bridge) para o Web Adapter."""

    def __init__(self, api_url: str = "http://127.0.0.1:8000/api/internal/clock"):
        super().__init__('rps_web_adapter_node')
        self.api_url = api_url
        self.hub = TelemetryHub.get_instance()

        self._last_sim_sec: float = -1.0
        self._last_post_wall: float = 0.0
        self._last_paused_state: bool = False
        self._pause_detector_timer = None

        # Subscreve ao relógio de simulação unificado do Gazebo Sim
        self.create_subscription(Clock, '/clock', self._clock_callback, 10)
        
        # Timer de 2 Hz para detectar se o relógio parou (física pausada no Gazebo)
        self.create_timer(0.5, self._check_pause_state)
        
        self.get_logger().info("🛰️ [WebAdapterNode] Gateway de Sincronia ROS 2 / Web ativo.")

    def _clock_callback(self, msg: Clock):
        sim_sec = msg.clock.sec + msg.clock.nanosec * 1e-9
        is_paused = (sim_sec == self._last_sim_sec)
        self._last_sim_sec = sim_sec
        self._last_paused_state = is_paused

        # Atualiza o Hub no mesmo processo se estiver compartilhado
        self.hub.update_sim_time(sim_sec, is_paused=is_paused)

        # Envia via HTTP POST para o FastAPI no host (limitado a no máximo 10 Hz)
        now_wall = time.time()
        if now_wall - self._last_post_wall >= 0.1:
            self._last_post_wall = now_wall
            self._post_clock_tick(sim_sec, is_paused=False)

    def _check_pause_state(self):
        """Disparado periodicamente para detectar congelamento do /clock (Gazebo pausado)."""
        now_wall = time.time()
        # Se passou mais de 0.6s sem novos ticks e tínhamos um relógio válido, Gazebo está pausado
        if self._last_sim_sec >= 0.0 and (now_wall - self._last_post_wall >= 0.6):
            if not self._last_paused_state:
                self._last_paused_state = True
                self.hub.update_sim_time(self._last_sim_sec, is_paused=True)
                self._post_clock_tick(self._last_sim_sec, is_paused=True)

    def _post_clock_tick(self, sim_sec: float, is_paused: bool):
        try:
            payload = json.dumps({
                "sim_time": round(sim_sec, 4),
                "is_paused": bool(is_paused)
            }).encode('utf-8')
            req = urllib.request.Request(
                self.api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=0.2):
                pass
        except Exception:
            # Falha silenciosa se o servidor web FastAPI ainda não foi inicializado
            pass


def main(args=None):
    import rclpy
    rclpy.init(args=args)
    node = WebAdapterRos2Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
