"""
Plataforma ROS 2 (Sub-Hexágono de Middleware)
==============================================
Encapsula o nó principal da constelação, subscrição de relógio e publicador
de telemetria no barramento DDS.
"""

try:
    from .Ros2ConstellationNode import Ros2ConstellationNode, main
    from .Ros2TelemetryOutboundAdapter import Ros2TelemetryOutboundAdapter
    __all__ = [
        "Ros2ConstellationNode",
        "Ros2TelemetryOutboundAdapter",
        "main",
    ]
except ImportError:
    Ros2ConstellationNode = None
    Ros2TelemetryOutboundAdapter = None
    main = None
    __all__ = []
