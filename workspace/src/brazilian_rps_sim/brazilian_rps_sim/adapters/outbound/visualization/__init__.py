"""
Adaptadores de Saída: Visualização e Apresentação 3D
====================================================
Geração de modelos procedurais glTF 2.0 / GLB e mundos SDFormat para o Gazebo Sim.
"""

from .gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube
from .color_palette import resolve_color, COLOR_PALETTE
from .marker_mesh_generator import generate_all_marker_assets
from .orbit_mesh_generator import generate_all_orbit_rings
from .world_generator import generate_world_sdf
from .earth_globe_generator import generate_all_earth_assets
from .celestial_mesh_generator import generate_all_celestial_assets
from .satellite_mesh_generator import generate_satellite_glb

__all__ = [
    "GltfMeshBuilder",
    "build_smooth_rmf_tube",
    "resolve_color",
    "COLOR_PALETTE",
    "generate_all_marker_assets",
    "generate_all_orbit_rings",
    "generate_world_sdf",
    "generate_all_earth_assets",
    "generate_all_celestial_assets",
    "generate_satellite_glb",
]
