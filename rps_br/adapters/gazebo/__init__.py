"""
Plataforma Gazebo Sim (Sub-Hexágono de Visualização e Simulação 3D)
===================================================================
Geração procedural de modelos glTF 2.0 / GLB, mundos SDFormat, tubos RMF de
Frenet-Serret e ferramentas de controle de câmera virtual para o Gazebo Harmonic.
"""

from .gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube
from .marker_mesh_generator import generate_all_marker_assets
from .orbit_mesh_generator import generate_all_orbit_rings
from .world_generator import generate_world_sdf
from .earth_globe_generator import generate_all_earth_assets
from .celestial_mesh_generator import generate_all_celestial_assets
from .satellite_mesh_generator import generate_satellite_glb
from .camera_auto_focus import focus_camera
from .GazeboWorldControlAdapter import GazeboWorldControlAdapter

import sys
# Alias de retrocompatibilidade para o antigo submódulo visualization
visualization = sys.modules[__name__]

__all__ = [
    "GltfMeshBuilder",
    "build_smooth_rmf_tube",
    "generate_all_marker_assets",
    "generate_all_orbit_rings",
    "generate_world_sdf",
    "generate_all_earth_assets",
    "generate_all_celestial_assets",
    "generate_satellite_glb",
    "focus_camera",
    "GazeboWorldControlAdapter",
    "visualization",
]
