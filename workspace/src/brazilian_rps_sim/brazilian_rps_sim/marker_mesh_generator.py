#!/usr/bin/env python3
"""
Gerador de Malhas 3D Procedurais PBR (glTF 2.0 / .glb) para Marcadores Espaciais:
1. Retículo/Anel Holográfico de Mira (Torus Neon Emissivo)
2. Feixes Nadir com parâmetros independentes de cor, opacidade, brilho e raio.

Refatorado com o Design Pattern BUILDER (GltfMeshBuilder).
"""

import os
import math
import numpy as np
import yaml

try:
    from brazilian_rps_sim.color_palette import resolve_color
    from brazilian_rps_sim.gltf_builder import GltfMeshBuilder
except ImportError:
    from color_palette import resolve_color
    from gltf_builder import GltfMeshBuilder


def generate_nadir_beam_glb(output_path: str, r_top: float, r_bottom: float, height: float,
                            color_rgba: tuple, emissive_intensity: float = 0.5, segs: int = 48):
    """Gera o feixe cônico Nadir procedural usando o GltfMeshBuilder."""
    theta = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    dr = r_bottom - r_top
    length = math.sqrt(dr * dr + height * height)
    nr = height / length
    nz = -dr / length

    vertices = []
    normals = []
    indices = []

    # 1. Anel do Topo (Z = 0)
    for i in range(segs):
        vertices.append([r_top * cos_t[i], r_top * sin_t[i], 0.0])
        normals.append([nr * cos_t[i], nr * sin_t[i], nz])

    # 2. Anel da Base (Z = height)
    for i in range(segs):
        vertices.append([r_bottom * cos_t[i], r_bottom * sin_t[i], height])
        normals.append([nr * cos_t[i], nr * sin_t[i], nz])

    # 3. Triângulos do Cone Truncado (CCW)
    for i in range(segs):
        i_next = (i + 1) % segs
        p0, p1, p2, p3 = i, i_next, segs + i, segs + i_next
        indices.extend([p0, p1, p3, p0, p3, p2])

    builder = GltfMeshBuilder(name="NadirBeam", generator_tag="RPS-BR Nadir Beam Mesh Generator")
    builder.set_positions(vertices)\
           .set_normals(normals)\
           .set_indices(indices)\
           .set_pbr_material(
               name="NadirBeamMaterial",
               base_color_rgba=color_rgba,
               metallic=0.0,
               roughness=1.0,
               emissive_intensity=emissive_intensity,
               alpha_mode="BLEND",
               double_sided=True
           )\
           .save_glb(output_path)


def generate_locator_ring_glb(output_path: str, r_major: float, r_minor: float,
                             color_rgb: tuple, emissive_intensity: float = 1.0,
                             segs_major: int = 36, segs_minor: int = 12):
    """Gera o anel holográfico (Torus) usando o GltfMeshBuilder."""
    vertices = []
    normals = []
    indices = []

    for i in range(segs_major):
        phi = 2 * math.pi * i / segs_major
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)
        center = np.array([r_major * cos_phi, r_major * sin_phi, 0.0])

        for j in range(segs_minor):
            theta = 2 * math.pi * j / segs_minor
            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)

            offset = np.array([r_minor * cos_theta * cos_phi,
                               r_minor * cos_theta * sin_phi,
                               r_minor * sin_theta])
            pos = center + offset
            normal = offset / r_minor

            vertices.append(pos.tolist())
            normals.append(normal.tolist())

    for i in range(segs_major):
        i_next = (i + 1) % segs_major
        for j in range(segs_minor):
            j_next = (j + 1) % segs_minor
            p00 = i * segs_minor + j
            p01 = i * segs_minor + j_next
            p10 = i_next * segs_minor + j
            p11 = i_next * segs_minor + j_next

            indices.extend([p00, p10, p01, p01, p10, p11])

    r, g, b = color_rgb
    builder = GltfMeshBuilder(name="LocatorRing", generator_tag="RPS-BR Locator Ring Mesh Generator")
    builder.set_positions(vertices)\
           .set_normals(normals)\
           .set_indices(indices)\
           .set_pbr_material(
               name="LocatorRingNeonMaterial",
               base_color_rgba=(r, g, b, 1.0),
               metallic=0.0,
               roughness=0.2,
               emissive_intensity=emissive_intensity,
               alpha_mode="OPAQUE",
               double_sided=True
           )\
           .save_glb(output_path)


def generate_all_marker_assets(config_path: str = None, mesh_dir: str = None):
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not mesh_dir:
        mesh_dir = os.path.join(pkg_dir, 'meshes')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis = cfg.get('visualization', {})
    markers_cfg = vis.get('satellite_markers', vis.get('markers', {}))

    r_beacon = float(markers_cfg.get('beacon_radius', 0.35))
    t_beacon = float(markers_cfg.get('beacon_tube_thickness', 0.015))
    e_beacon_geo = float(markers_cfg.get('beacon_emissive_geo', 0.80))
    e_beacon_igso = float(markers_cfg.get('beacon_emissive_igso', 0.85))

    color_beacon_geo = resolve_color(markers_cfg.get('color_beacon_geo', 'cyan'), default=(0.0, 0.90, 1.0))
    color_beacon_igso = resolve_color(markers_cfg.get('color_beacon_igso', 'amber'), default=(1.0, 0.80, 0.10))

    color_cone_geo = resolve_color(markers_cfg.get('color_nadir_cone_geo', 'cyan'), default=(0.0, 0.90, 1.0))
    color_cone_igso = resolve_color(markers_cfg.get('color_nadir_cone_igso', 'amber'), default=(1.0, 0.80, 0.10))

    r_top = float(markers_cfg.get('nadir_cone_top_radius', 0.08))
    r_bottom_geo = float(markers_cfg.get('nadir_cone_bottom_radius_geo', 4.80))
    r_bottom_igso = float(markers_cfg.get('nadir_cone_bottom_radius_igso', 1.15))
    
    op_geo = float(markers_cfg.get('nadir_cone_opacity_geo', 0.05))
    op_igso = float(markers_cfg.get('nadir_cone_opacity_igso', 0.35))
    e_cone_geo = float(markers_cfg.get('nadir_cone_emissive_geo', 0.08))
    e_cone_igso = float(markers_cfg.get('nadir_cone_emissive_igso', 0.90))
    
    height = 45.0

    # 1. Halos/Retículos de Mira Neon
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_geo.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=color_beacon_geo,
        emissive_intensity=e_beacon_geo
    )
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_igso.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=color_beacon_igso,
        emissive_intensity=e_beacon_igso
    )

    # 2. Cones Nadir
    generate_nadir_beam_glb(
        output_path=os.path.join(mesh_dir, 'nadir_beam_geo.glb'),
        r_top=r_top, r_bottom=r_bottom_geo, height=height,
        color_rgba=(color_cone_geo[0], color_cone_geo[1], color_cone_geo[2], op_geo),
        emissive_intensity=e_cone_geo
    )
    generate_nadir_beam_glb(
        output_path=os.path.join(mesh_dir, 'nadir_beam_igso.glb'),
        r_top=r_top, r_bottom=r_bottom_igso, height=height,
        color_rgba=(color_cone_igso[0], color_cone_igso[1], color_cone_igso[2], op_igso),
        emissive_intensity=e_cone_igso
    )

    print(f"✨ [MarkerGenerator] Marcadores gerados com GltfMeshBuilder com sucesso!")

if __name__ == '__main__':
    generate_all_marker_assets()
