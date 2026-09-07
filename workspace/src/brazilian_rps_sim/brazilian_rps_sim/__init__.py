"""
Brazilian RPS Sim (Simulador do Sistema de Posicionamento Regional Brasileiro)
==============================================================================
Pacote ROS 2 e biblioteca científica de simulação sob a Arquitetura Hexagonal Modular (Nível 2).
"""

import sys
from .adapters.outbound import visualization
from .infrastructure.config import config_loader

# Mapeamento transparente de retrocompatibilidade para módulos migrados da raiz
sys.modules[__name__ + ".marker_mesh_generator"] = visualization.marker_mesh_generator
sys.modules[__name__ + ".orbit_mesh_generator"] = visualization.orbit_mesh_generator
sys.modules[__name__ + ".world_generator"] = visualization.world_generator
sys.modules[__name__ + ".earth_globe_generator"] = visualization.earth_globe_generator
sys.modules[__name__ + ".celestial_mesh_generator"] = visualization.celestial_mesh_generator
sys.modules[__name__ + ".satellite_mesh_generator"] = visualization.satellite_mesh_generator
sys.modules[__name__ + ".gltf_builder"] = visualization.gltf_builder
sys.modules[__name__ + ".color_palette"] = visualization.color_palette
