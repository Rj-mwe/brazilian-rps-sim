"""
Adaptadores de Saída: Visualização e Apresentação 3D
====================================================
Geração de modelos procedurais glTF 2.0 / GLB e mundos SDFormat para o Gazebo Sim.
"""

from .gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube
from .color_palette import resolve_color, COLOR_PALETTE

__all__ = [
    "GltfMeshBuilder",
    "build_smooth_rmf_tube",
    "resolve_color",
    "COLOR_PALETTE",
]
