#!/usr/bin/env python3
"""
Nó ROS 2 do Adaptador Web: Sincroniza o relógio e tópicos de telemetria do Gazebo
diretamente com o TelemetryHub do servidor FastAPI.
"""

from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String

from rps_br.adapters.web.telemetry_hub import TelemetryHub


class WebAdapterRos2Node(Node):
    """Nó ROS 2 de escuta passiva para alimentar a interface Web com dados do Gazebo."""

    def __init__(self):
        super().__init__('rps_web_adapter_node')
        self.hub = TelemetryHub.get_instance()

        # Subscreve ao relógio de simulação unificado do Gazebo Sim
        self.create_subscription(Clock, '/clock', self._clock_callback, 10)
        self.get_logger().info("🛰️ [WebAdapterNode] Conectado ao barramento ROS 2 e ao TelemetryHub.")

    def _clock_callback(self, msg: Clock):
        sim_sec = msg.clock.sec + msg.clock.nanosec * 1e-9
        self.hub.update_sim_time(sim_sec)


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
