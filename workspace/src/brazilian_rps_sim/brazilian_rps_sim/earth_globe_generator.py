#!/usr/bin/env python3
"""
Gerador de Malha 3D Científica da Terra e Nuvens em formato glTF 2.0 (.glb)
com Mapeamento Paramétrico Estrito e Builder Pattern (GltfMeshBuilder).
"""

import os
import math
import numpy as np

try:
    from brazilian_rps_sim.gltf_builder import GltfMeshBuilder
except ImportError:
    from gltf_builder import GltfMeshBuilder


def generate_sphere_mesh(radius: float, lat_segs: int = 64, lon_segs: int = 128):
    """Gera vértices, normais, coordenadas UV e índices triangulares parametrizados."""
    vertices = []
    normals = []
    uvs = []
    indices = []

    for i in range(lat_segs + 1):
        lat = (math.pi / 2.0) - (math.pi * i / lat_segs)
        v = i / lat_segs

        for j in range(lon_segs + 1):
            u = j / lon_segs
            phi = (2.0 * math.pi * j / lon_segs) - math.pi

            x = radius * math.cos(lat) * math.cos(phi)
            y = radius * math.cos(lat) * math.sin(phi)
            z = radius * math.sin(lat)

            vertices.append([x, y, z])
            norm = math.sqrt(x * x + y * y + z * z)
            normals.append([x / norm, y / norm, z / norm])
            uvs.append([u, v])

    # Triângulos voltados para FORA (CCW)
    for i in range(lat_segs):
        for j in range(lon_segs):
            p00 = i * (lon_segs + 1) + j
            p01 = p00 + 1
            p10 = (i + 1) * (lon_segs + 1) + j
            p11 = p10 + 1

            indices.extend([p00, p10, p01, p01, p10, p11])

    return (np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32),
            np.array(uvs, dtype=np.float32),
            np.array(indices, dtype=np.uint32))


def write_globe_glb(output_path: str, radius: float, mat_name: str, has_clouds: bool = False):
    """Gera a malha esférica da Terra ou Nuvens usando GltfMeshBuilder."""
    v, n, uv, idx = generate_sphere_mesh(radius, lat_segs=64, lon_segs=128)

    builder = GltfMeshBuilder(name=mat_name, generator_tag="RPS-BR Earth Globe Mesh Generator")
    builder.set_positions(v)\
           .set_normals(n)\
           .set_uvs(uv)\
           .set_indices(idx)

    if has_clouds:
        builder.set_pbr_material(
            name=mat_name,
            base_color_rgba=(1.0, 1.0, 1.0, 0.95),
            metallic=0.0,
            roughness=0.9,
            alpha_mode="BLEND",
            double_sided=True
        )
    else:
        builder.set_pbr_material(
            name=mat_name,
            base_color_rgba=(1.0, 1.0, 1.0, 1.0),
            metallic=0.0,
            roughness=0.5,
            alpha_mode="OPAQUE",
            double_sided=False
        )

    builder.save_glb(output_path)
    print(f"🌍 Malha esférica gerada via GltfMeshBuilder: {output_path} (R={radius}, Vértices={len(v)})")


def generate_all_earth_assets(mesh_dir: str = None):
    if not mesh_dir:
        try:
            from ament_index_python.packages import get_package_share_directory
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            candidate = os.path.join(pkg_share, 'meshes')
            if os.path.exists(candidate):
                mesh_dir = candidate
        except Exception:
            pass

    if not mesh_dir:
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mesh_dir = os.path.join(pkg_dir, 'meshes')

    # 1. Globo Terrestre Sólido (R = 6.378 km)
    write_globe_glb(
        output_path=os.path.join(mesh_dir, 'earth_globe.glb'),
        radius=6.378,
        mat_name="EarthSurfaceMaterial",
        has_clouds=False
    )

    # 2. Camada Atmosférica de Nuvens Dinâmicas (R = 6.405 km)
    write_globe_glb(
        output_path=os.path.join(mesh_dir, 'earth_clouds.glb'),
        radius=6.405,
        mat_name="EarthCloudsMaterial",
        has_clouds=True
    )


if __name__ == '__main__':
    generate_all_earth_assets()
