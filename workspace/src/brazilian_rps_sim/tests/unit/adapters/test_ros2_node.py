#!/usr/bin/env python3
"""
Testes Unitários para o Adaptador ROS 2 (Ros2ConstellationNode).
Valida a orquestração do timer, conversão de DTOs e disparo de Casos de Uso com mock de rclpy.
"""

import sys
from unittest.mock import MagicMock
import pytest

class DummyNode:
    def __init__(self, name="dummy_node"):
        self.name = name
    def declare_parameter(self, *args, **kwargs):
        pass
    def get_parameter(self, *args, **kwargs):
        mock_param = MagicMock()
        mock_param.get_parameter_value().string_value = ""
        return mock_param
    def get_clock(self):
        mock_clock = MagicMock()
        mock_clock.now().nanoseconds = 0
        return mock_clock
    def create_timer(self, *args, **kwargs):
        return MagicMock()
    def get_logger(self):
        return MagicMock()
    def create_publisher(self, *args, **kwargs):
        return MagicMock()

@pytest.fixture(autouse=True)
def mock_ros2_environment():
    """Garante que dependências de rclpy estejam mockadas durante o teste."""
    modules_to_mock = [
        'rclpy', 'rclpy.node', 'rclpy.executors',
        'geometry_msgs', 'geometry_msgs.msg',
        'std_msgs', 'std_msgs.msg'
    ]
    orig_modules = {}
    for mod in modules_to_mock:
        if mod in sys.modules:
            orig_modules[mod] = sys.modules[mod]

    sys.modules['rclpy'] = MagicMock()
    sys.modules['rclpy.node'] = MagicMock()
    sys.modules['rclpy.node'].Node = DummyNode
    sys.modules['rclpy.executors'] = MagicMock()
    sys.modules['geometry_msgs'] = MagicMock()
    sys.modules['geometry_msgs.msg'] = MagicMock()
    sys.modules['std_msgs'] = MagicMock()
    sys.modules['std_msgs.msg'] = MagicMock()

    yield

    for mod in modules_to_mock:
        if mod in orig_modules:
            sys.modules[mod] = orig_modules[mod]
        else:
            sys.modules.pop(mod, None)

def test_ros2_constellation_node_step_execution():
    """Testa a inicialização do nó e a execução de um ciclo de clock sem erros de DTO ou tipos."""
    from brazilian_rps_sim.adapters.ros2.Ros2ConstellationNode import Ros2ConstellationNode

    node = Ros2ConstellationNode()
    assert node is not None

    # Simula timestamp do relógio (/clock)
    mock_now = MagicMock()
    mock_now.nanoseconds = 5_000_000_000  # 5.0 s
    node.get_clock = MagicMock(return_value=MagicMock(now=MagicMock(return_value=mock_now)))

    # Executa o ciclo de step (deve executar SimulationStepRequestDTO sem NameError)
    node._on_step()

    # Verifica se os 7 satélites foram propagados
    assert len(node.constellation.satellites) == 7
    for sat in node.constellation.satellites:
        assert sat.last_sim_time_sec >= 0.0
        assert sat.r_ecef is not None

def test_ros2_telemetry_outbound_adapter_publishing():
    """Testa se o adaptador de saída ROS 2 publica poses e coordenadas sem exceções."""
    from brazilian_rps_sim.adapters.ros2.Ros2TelemetryOutboundAdapter import Ros2TelemetryOutboundAdapter
    from brazilian_rps_sim.core.domain.shared.value_objects.Vector3DVO import Vector3DVO
    from brazilian_rps_sim.core.domain.shared.value_objects.GeodeticCoordinatesVO import GeodeticCoordinatesVO
    from brazilian_rps_sim.core.domain.shared.value_objects.QuaternionVO import QuaternionVO

    mock_node = MagicMock()
    adapter = Ros2TelemetryOutboundAdapter(node=mock_node, total_satellites=7)

    r_ecef = Vector3DVO(42164.0, 0.0, 0.0)
    geodetic = GeodeticCoordinatesVO(0.0, -70.0, 35786.0)
    attitude = QuaternionVO.identity()

    # Publica estado de um satélite
    adapter.publish_satellite_state(
        sat_id=1,
        name="RPS-GEO1",
        sat_type="GEO",
        r_ecef=r_ecef,
        geodetic=geodetic,
        attitude=attitude,
        t_sec=100.0
    )

    # Verifica se o publisher do satélite 1 foi acionado
    assert adapter.pose_pubs[1].publish.called
    assert adapter.geo_pubs[1].publish.called
