#!/usr/bin/env python3
"""
Gera malhas orbitais em formato glTF 2.0 (.gltf) padrão da indústria para Sol, Terra e Lua.
Refatorado com o Design Pattern BUILDER (GltfMeshBuilder).
"""

import os
import math
import numpy as np

try:
    from brazilian_rps_sim.gltf_builder import GltfMeshBuilder
except ImportError:
    from gltf_builder import GltfMeshBuilder


def generate_orbit_gltf(output_path: str, radius: float, inclination_deg: float, thickness: float,
                        r: float, g: float, b: float, alpha: float = 1.0, num_pts: int = 480):
    """Gera um anel orbital usando o GltfMeshBuilder."""
    theta = np.linspace(0, 2 * np.pi, num_pts, endpoint=False)
    inc = np.radians(inclination_deg)

    pts = []
    for th in theta:
        x = radius * np.cos(th)
        y = radius * np.sin(th) * np.cos(inc)
        z = radius * np.sin(th) * np.sin(inc)
        pts.append(np.array([x, y, z]))

    vertices = []
    normals = []
    for i, p in enumerate(pts):
        p_next = pts[(i + 1) % len(pts)]
        tangent = p_next - p
        tangent = tangent / np.linalg.norm(tangent)
        up = np.array([0, 0, 1]) if abs(tangent[2]) < 0.9 else np.array([1, 0, 0])
        normal = np.cross(tangent, up)
        normal = normal / np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)

        for angle in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
            offset = thickness * (np.cos(angle) * normal + np.sin(angle) * binormal)
            vertices.append((p + offset).tolist())
            normals.append((offset / thickness).tolist())

    indices = []
    for i in range(num_pts):
        i_next = (i + 1) % num_pts
        base_curr = i * 4
        base_next = i_next * 4
        for j in range(4):
            j_next = (j + 1) % 4
            v1 = base_curr + j
            v2 = base_curr + j_next
            v3 = base_next + j_next
            v4 = base_next + j
            indices.extend([v1, v2, v3, v1, v3, v4])

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


def main():
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
        num_pts=480
    )


if __name__ == '__main__':
    main()
