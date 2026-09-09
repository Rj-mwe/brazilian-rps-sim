#!/usr/bin/env python3
"""
Adaptador de Entrada ROS 2: Ros2WebBridgeNode
==============================================
Ponte de relógio unificada entre o Gazebo Sim (/clock) e a interface Web (FastAPI).
Opera de forma autônoma sem dependências de frameworks web (FastAPI/Uvicorn),
permitindo execução limpa dentro de contêineres ROS 2 mínimos.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Optional

import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock

from rps_br.infrastructure.config.config_loader import load_simulation_config, find_config_file


class Ros2WebBridgeNode(Node):
    """Nó ROS 2 que ingere o /clock do Gazebo e despacha o tempo virtual para o Core/Web."""

    def __init__(self):
        super().__init__('rps_web_bridge_node')

        # 1. Parâmetros de Configuração
        self.declare_parameter('api_url', 'http://127.0.0.1:8000/api/internal/clock')
        self.declare_parameter('config_path', '')
        
        self.api_url = self.get_parameter('api_url').get_parameter_value().string_value
        config_path = self.get_parameter('config_path').get_parameter_value().string_value or find_config_file()

        # Lê o multiplicador temporal declarativo (3600x = 1h orbital por segundo real)
        default_multiplier = 3600.0
        try:
            cfg = load_simulation_config(config_path)
            sim_cfg = cfg.get('simulation', {})
            default_multiplier = float(sim_cfg.get('time_multiplier', 3600.0))
        except Exception:
            pass

        self.declare_parameter('time_multiplier', default_multiplier)
        self.time_multiplier = self.get_parameter('time_multiplier').get_parameter_value().double_value

        self._last_raw_clock: float = -1.0
        self._last_sim_sec: float = 0.0
        self._last_post_wall: float = 0.0
        self._last_paused_state: bool = False

        # 2. Subscrição ao relógio do Gazebo Sim (via ros_gz_bridge parameter_bridge)
        self.create_subscription(Clock, '/clock', self._clock_callback, 10)

        # 3. Timer de 2 Hz para detecção proativa de pausa na física do Gazebo
        self.create_timer(0.5, self._check_pause_state)

        self.get_logger().info(
            f"🛰️ [Ros2WebBridgeNode] Gateway Gazebo /clock -> Web API ativo "
            f"(Multiplicador: {self.time_multiplier:.0f}x | Destino: {self.api_url})"
        )

    def _clock_callback(self, msg: Clock):
        raw_clock_sec = msg.clock.sec + msg.clock.nanosec * 1e-9
        is_paused = (raw_clock_sec == self._last_raw_clock)
        self._last_raw_clock = raw_clock_sec

        # Mapeia o tempo de física do Gazebo para o tempo orbital virtual (ex: 1s Gazebo = 3600s órbita)
        sim_sec = raw_clock_sec * self.time_multiplier
        self._last_sim_sec = sim_sec
        self._last_paused_state = is_paused

        now_wall = time.time()
        # Envia via HTTP POST limitado a no máximo 10 Hz para evitar saturação
        if now_wall - self._last_post_wall >= 0.1:
            self._last_post_wall = now_wall
            self._post_clock_tick(sim_sec, is_paused=False)

    def _check_pause_state(self):
        """Detecta quando o Gazebo teve a simulação pausada (ausência de avanço do /clock)."""
        now_wall = time.time()
        if self._last_raw_clock >= 0.0 and (now_wall - self._last_post_wall >= 0.6):
            if not self._last_paused_state:
                self._last_paused_state = True
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
            # Tolerante a falha caso o servidor web ainda não esteja rodando
            pass


def main(args=None):
    rclpy.init(args=args)
    node = Ros2WebBridgeNode()
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
