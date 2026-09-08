"""
Brazilian RPS Sim (Simulador do Sistema de Posicionamento Regional Brasileiro)
==============================================================================
Pacote ROS 2 e biblioteca científica de simulação sob a Arquitetura Hexagonal Modular (Nível 2).
"""

import sys
from .adapters import gazebo
from .adapters import shared
from .adapters import ros2
from .adapters import export
from .infrastructure.config import config_loader

# Mapeamento transparente de retrocompatibilidade para módulos migrados da raiz
sys.modules[__name__ + ".marker_mesh_generator"] = gazebo.marker_mesh_generator
sys.modules[__name__ + ".orbit_mesh_generator"] = gazebo.orbit_mesh_generator
sys.modules[__name__ + ".world_generator"] = gazebo.world_generator
sys.modules[__name__ + ".earth_globe_generator"] = gazebo.earth_globe_generator
sys.modules[__name__ + ".celestial_mesh_generator"] = gazebo.celestial_mesh_generator
sys.modules[__name__ + ".satellite_mesh_generator"] = gazebo.satellite_mesh_generator
sys.modules[__name__ + ".gltf_builder"] = gazebo.gltf_builder
sys.modules[__name__ + ".color_palette"] = shared.color_palette

# Retrocompatibilidade com adapters.outbound e adapters.inbound
sys.modules[__name__ + ".adapters.outbound"] = gazebo
sys.modules[__name__ + ".adapters.inbound"] = ros2
sys.modules[__name__ + ".adapters.outbound.visualization"] = gazebo
sys.modules[__name__ + ".adapters.outbound.visualization.marker_mesh_generator"] = gazebo.marker_mesh_generator
sys.modules[__name__ + ".adapters.outbound.visualization.orbit_mesh_generator"] = gazebo.orbit_mesh_generator
sys.modules[__name__ + ".adapters.outbound.visualization.world_generator"] = gazebo.world_generator
sys.modules[__name__ + ".adapters.outbound.visualization.earth_globe_generator"] = gazebo.earth_globe_generator
sys.modules[__name__ + ".adapters.outbound.visualization.celestial_mesh_generator"] = gazebo.celestial_mesh_generator
sys.modules[__name__ + ".adapters.outbound.visualization.satellite_mesh_generator"] = gazebo.satellite_mesh_generator
sys.modules[__name__ + ".adapters.outbound.visualization.gltf_builder"] = gazebo.gltf_builder
sys.modules[__name__ + ".adapters.outbound.visualization.color_palette"] = shared.color_palette

# Retrocompatibilidade com adapters.inbound e adapters.outbound
if ros2.Ros2ConstellationNode is not None:
    sys.modules[__name__ + ".adapters.inbound.Ros2ConstellationNode"] = ros2.Ros2ConstellationNode
if ros2.Ros2TelemetryOutboundAdapter is not None:
    sys.modules[__name__ + ".adapters.outbound.Ros2TelemetryOutboundAdapter"] = ros2.Ros2TelemetryOutboundAdapter

# Retrocompatibilidade com tools
tools = gazebo
sys.modules[__name__ + ".tools"] = gazebo
sys.modules[__name__ + ".tools.camera_auto_focus"] = gazebo.camera_auto_focus
sys.modules[__name__ + ".tools.ground_track_plotter"] = export.ground_track_plotter
