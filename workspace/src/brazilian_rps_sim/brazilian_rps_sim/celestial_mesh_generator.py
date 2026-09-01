#!/usr/bin/env python3
"""
Gera malhas orbitais em formato glTF 2.0 (.gltf) padrão da indústria para Sol, Terra e Lua.
Refatorado com RMF e GltfMeshBuilder.
"""

import os
import math
import numpy as np

try:
    from brazilian_rps_sim.gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube
except ImportError:
    from gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube


def generate_orbit_gltf(output_path: str, radius: float, inclination_deg: float, thickness: float,
                        r: float, g: float, b: float, alpha: float = 1.0, num_pts: int = 720):
    """Gera um anel orbital usando RMF e GltfMeshBuilder."""
    theta = np.linspace(0, 2 * math.pi, num_pts, endpoint=False)
    inc = math.radians(inclination_deg)

    pts = []
    for th in theta:
        x = radius * math.cos(th)
        y = radius * math.sin(th) * math.cos(inc)
        z = radius * math.sin(th) * math.sin(inc)
        pts.append([x, y, z])

    vertices, normals, indices = build_smooth_rmf_tube(np.array(pts, dtype=np.float32), radius=thickness, radial_segs=8)

    builder = GltfMeshBuilder(name="CelestialOrbitRing", generator_tag="RPS-BR Astrodynamics glTF Generator")
    builder.set_positions(vertices)\
           .set_normals(normals)\
           .set_indices(indices)\
           .set_pbr_material(
               name="OrbitPbrMaterial",
               base_color_rgba=(r, g, b, alpha),
               metallic=0.0,
               roughness=0.8,
               emissive_intensity=0.90,
               alpha_mode="OPAQUE",
               double_sided=True
           )\
           .save_gltf(output_path, embedded_base64=True)

    print(f"✅ Malha glTF 2.0 gerada via GltfMeshBuilder: {output_path} (Cor RGB: {r},{g},{b})")


def generate_all_celestial_assets(mesh_dir: str = None):
    if not mesh_dir:
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mesh_dir = os.path.join(pkg_dir, "meshes")

    # 1. Órbita da Terra: DOURADO VIBRANTE (R=1.0, G=0.75, B=0.1)
    generate_orbit_gltf(
        output_path=os.path.join(mesh_dir, "earth_orbit_ring.gltf"),
        radius=1200.0,
        inclination_deg=0.0,
        thickness=0.10,
        r=1.0, g=0.75, b=0.1, alpha=1.0,
        num_pts=720
    )

    # 2. Órbita da Lua: CIANO CELESTIAL VIBRANTE (R=0.0, G=0.85, B=1.0)
    generate_orbit_gltf(
        output_path=os.path.join(mesh_dir, "moon_orbit_ring.gltf"),
        radius=384.4,
        inclination_deg=5.145,
        thickness=0.03,
        r=0.0, g=0.85, b=1.0, alpha=1.0,
        num_pts=720
    )


def main():
    generate_all_celestial_assets()


if __name__ == '__main__':
    main()
