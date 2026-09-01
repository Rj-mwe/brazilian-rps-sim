#!/usr/bin/env python3
"""
Gerador de Malhas 3D Procedurais PBR (glTF 2.0 / .glb) para Marcadores Espaciais:
1. Retículo/Anel Holográfico de Mira (Torus Neon Emissivo)
2. Gaiolas Holográficas Radar Nadir (STK / NASA WorldWind Standard):
   - Anel de Pegada 2D na Superfície (Footprint Ring)
   - Feixes Laser Geratrizes (Generatrix Rays / Ribs)
   - Eixo Central de Apontamento Boresight (Nadir Line)
   - Anel de Alcance de Meia-Altitude (Mid Range Ring)
   - Mira de Centro Sub-satélite (Target Crosshairs)

Refatorado com o Design Pattern BUILDER (GltfMeshBuilder) e RMF Tubes.
"""

import os
import math
from typing import List, Tuple
import numpy as np
import yaml

try:
    from brazilian_rps_sim.color_palette import resolve_color
    from brazilian_rps_sim.gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube
except ImportError:
    from color_palette import resolve_color
    from gltf_builder import GltfMeshBuilder, build_smooth_rmf_tube


def _create_cylinder_segment(
    p1: List[float],
    p2: List[float],
    radius: float,
    radial_segs: int = 8
) -> Tuple[List[List[float]], List[List[float]], List[int]]:
    """Gera a geometria tubular 3D (vértices, normais, índices) conectando p1 a p2."""
    p1_arr = np.array(p1, dtype=np.float64)
    p2_arr = np.array(p2, dtype=np.float64)
    v = p2_arr - p1_arr
    length = np.linalg.norm(v)
    if length < 1e-6:
        return [], [], []

    tangent = v / length
    if abs(tangent[2]) < 0.9:
        normal = np.array([-tangent[1], tangent[0], 0.0])
    else:
        normal = np.array([0.0, -tangent[2], tangent[1]])
    normal = normal / np.linalg.norm(normal)
    binormal = np.cross(tangent, normal)
    binormal = binormal / np.linalg.norm(binormal)

    verts = []
    norms = []
    indices = []

    theta = np.linspace(0, 2 * math.pi, radial_segs, endpoint=False)
    for t in theta:
        radial_dir = math.cos(t) * normal + math.sin(t) * binormal
        verts.append((p1_arr + radius * radial_dir).tolist())
        norms.append(radial_dir.tolist())
    for t in theta:
        radial_dir = math.cos(t) * normal + math.sin(t) * binormal
        verts.append((p2_arr + radius * radial_dir).tolist())
        norms.append(radial_dir.tolist())

    for i in range(radial_segs):
        i_next = (i + 1) % radial_segs
        p00 = i
        p01 = i_next
        p10 = radial_segs + i
        p11 = radial_segs + i_next
        indices.extend([p00, p01, p11, p00, p11, p10])

    return verts, norms, indices


def _create_circular_ring(
    radius: float,
    height: float,
    tube_radius: float = 0.015,
    num_pts: int = 64,
    radial_segs: int = 8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gera um anel circular fechado 3D em torno do eixo Z na altura especificada."""
    theta = np.linspace(0, 2 * math.pi, num_pts, endpoint=False)
    pts = np.column_stack([
        radius * np.cos(theta),
        radius * np.sin(theta),
        np.full(num_pts, height)
    ])
    return build_smooth_rmf_tube(pts, radius=tube_radius, radial_segs=radial_segs)


def generate_holographic_nadir_cage_glb(
    output_path: str,
    r_top: float,
    r_bottom: float,
    height: float,
    color_cage_rgb: Tuple[float, float, float],
    color_boresight_rgb: Optional[Tuple[float, float, float]] = None,
    emissive_intensity: float = 0.90,
    show_generatrix_rays: bool = True,
    num_rays: int = 4,
    tube_radius: float = 0.018,
    show_top_ring: bool = True,
    show_footprint_ring: bool = True,
    show_mid_ring: bool = False,
    show_boresight: bool = True,
    show_crosshair: bool = True
) -> None:
    """
    Gera a Gaiola Holográfica Radar Nadir (Padrão Aeroespacial STK/NASA).
    Utiliza duas primitivas PBR independentes:
    1. Gaiola / Anel de Pegada / Raios Geratrizes (color_cage_rgb)
    2. Raio Central Laser Boresight / Mira de Alvo (color_boresight_rgb)
    """
    if color_boresight_rgb is None:
        color_boresight_rgb = color_cage_rgb

    builder = GltfMeshBuilder(name="HolographicNadirCage", generator_tag="RPS-BR Holographic Nadir Cage Generator")

    # 1. Primitiva da Gaiola Externa (Anel de Pegada, Anel do Topo, Anel Intermediário, Raios Geratrizes)
    cage_verts: List[List[float]] = []
    cage_norms: List[List[float]] = []
    cage_indices: List[int] = []

    def append_cage(v, n, idx):
        base_idx = len(cage_verts)
        cage_verts.extend(v if isinstance(v, list) else v.tolist())
        cage_norms.extend(n if isinstance(n, list) else n.tolist())
        cage_indices.extend([int(i) + base_idx for i in idx])

    if show_footprint_ring and r_bottom > 0.01:
        v, n, idx = _create_circular_ring(r_bottom, height, tube_radius=tube_radius * 1.3, num_pts=64)
        append_cage(v, n, idx)

    if show_top_ring and r_top > 0.01:
        v, n, idx = _create_circular_ring(r_top, 0.0, tube_radius=tube_radius * 1.0, num_pts=32)
        append_cage(v, n, idx)

    if show_mid_ring:
        r_mid = (r_top + r_bottom) * 0.5
        h_mid = height * 0.5
        v, n, idx = _create_circular_ring(r_mid, h_mid, tube_radius=tube_radius * 0.85, num_pts=48)
        append_cage(v, n, idx)

    if show_generatrix_rays and num_rays > 0:
        clamped_rays = max(1, min(16, num_rays))
        ray_angles = np.linspace(0, 2 * math.pi, clamped_rays, endpoint=False)
        for phi in ray_angles:
            p_top = [r_top * math.cos(phi), r_top * math.sin(phi), 0.0]
            p_bottom = [r_bottom * math.cos(phi), r_bottom * math.sin(phi), height]
            v, n, idx = _create_cylinder_segment(p_top, p_bottom, radius=tube_radius, radial_segs=8)
            append_cage(v, n, idx)

    if cage_verts:
        rc, gc, bc = color_cage_rgb
        builder.add_primitive(
            positions=cage_verts,
            normals=cage_norms,
            indices=cage_indices,
            material_name="CageWireframeMaterial",
            base_color_rgba=(rc, gc, bc, 1.0),
            metallic=0.0,
            roughness=0.2,
            emissive_rgb=(rc, gc, bc),
            emissive_intensity=emissive_intensity,
            alpha_mode="OPAQUE",
            double_sided=True
        )

    # 2. Primitiva do Raio Central Boresight & Mira Crosshair
    bore_verts: List[List[float]] = []
    bore_norms: List[List[float]] = []
    bore_indices: List[int] = []

    def append_bore(v, n, idx):
        base_idx = len(bore_verts)
        bore_verts.extend(v if isinstance(v, list) else v.tolist())
        bore_norms.extend(n if isinstance(n, list) else n.tolist())
        bore_indices.extend([int(i) + base_idx for i in idx])

    if show_boresight:
        v, n, idx = _create_cylinder_segment([0.0, 0.0, 0.0], [0.0, 0.0, height], radius=tube_radius * 1.15, radial_segs=8)
        append_bore(v, n, idx)

    if show_crosshair and r_bottom > 0.01:
        ch_len = r_bottom * 0.25
        v, n, idx = _create_cylinder_segment([-ch_len, 0.0, height], [ch_len, 0.0, height], radius=tube_radius * 0.9, radial_segs=6)
        append_bore(v, n, idx)
        v, n, idx = _create_cylinder_segment([0.0, -ch_len, height], [0.0, ch_len, height], radius=tube_radius * 0.9, radial_segs=6)
        append_bore(v, n, idx)

    if bore_verts:
        rb, gb, bb = color_boresight_rgb
        builder.add_primitive(
            positions=bore_verts,
            normals=bore_norms,
            indices=bore_indices,
            material_name="BoresightLaserMaterial",
            base_color_rgba=(rb, gb, bb, 1.0),
            metallic=0.0,
            roughness=0.1,
            emissive_rgb=(rb, gb, bb),
            emissive_intensity=min(1.0, emissive_intensity * 1.05),
            alpha_mode="OPAQUE",
            double_sided=True
        )

    # Se nenhum elemento estiver ativo, gera ao menos um ponto central neutro
    if not cage_verts and not bore_verts:
        v, n, idx = _create_cylinder_segment([0.0, 0.0, 0.0], [0.0, 0.0, 0.01], radius=tube_radius, radial_segs=4)
        builder.add_primitive(v, n, indices=idx)

    builder.save_glb(output_path)


def generate_nadir_beam_glb(
    output_path: str,
    r_top: float,
    r_bottom: float,
    height: float,
    color_rgba: Tuple[float, float, float, float],
    emissive_intensity: float = 0.5,
    segs: int = 48
) -> None:
    """Gera o cone translúcido sólido clássico via GltfMeshBuilder (Modo Legado)."""
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


def generate_locator_ring_glb(
    output_path: str,
    r_major: float,
    r_minor: float,
    color_rgb: Tuple[float, float, float],
    emissive_intensity: float = 1.0,
    segs_major: int = 36,
    segs_minor: int = 12
) -> None:
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

            offset = np.array([
                r_minor * cos_theta * cos_phi,
                r_minor * cos_theta * sin_phi,
                r_minor * sin_theta
            ])
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
               emissive_rgb=(r, g, b),
               emissive_intensity=emissive_intensity,
               alpha_mode="OPAQUE",
               double_sided=True
           )\
           .save_glb(output_path)


def generate_all_marker_assets(config_path: str = None, mesh_dir: str = None):
    """Gera todos os marcadores espaciais a partir do YAML com controle granular GEO vs IGSO."""
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not mesh_dir:
        mesh_dir = os.path.join(pkg_dir, 'meshes')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis = cfg.get('visualization', {})
    markers_cfg = vis.get('satellite_markers', vis.get('markers', {}))

    geo_cfg = markers_cfg.get('geo_markers', {})
    igso_cfg = markers_cfg.get('igso_markers', {})

    r_beacon = float(markers_cfg.get('beacon_radius', 0.35))
    t_beacon = float(markers_cfg.get('beacon_tube_thickness', 0.015))
    r_top = float(markers_cfg.get('nadir_cone_top_radius', 0.08))
    style = markers_cfg.get('nadir_beam_style', 'holographic_cage')
    height = 45.0

    # Extrai configurações do GEO
    color_cage_geo = resolve_color(geo_cfg.get('color', markers_cfg.get('color_nadir_cone_geo', 'cyan')), default=(0.0, 0.90, 1.0))
    color_bore_geo = resolve_color(geo_cfg.get('color_boresight', 'white'), default=(0.95, 0.95, 1.0))
    e_beacon_geo = float(geo_cfg.get('beacon_emissive', markers_cfg.get('beacon_emissive_geo', 0.80)))
    e_cone_geo = float(geo_cfg.get('emissive_intensity', markers_cfg.get('nadir_cone_emissive_geo', 0.85)))
    r_bottom_geo = float(geo_cfg.get('footprint_radius_km', 4800.0)) / 1000.0
    ray_thickness_geo = float(geo_cfg.get('ray_thickness', markers_cfg.get('nadir_ray_thickness', 0.016)))
    num_rays_geo = int(geo_cfg.get('num_generatrix_rays', markers_cfg.get('num_generatrix_rays_geo', 4)))
    show_gen_geo = bool(geo_cfg.get('show_generatrix_rays', True))
    show_boresight_geo = bool(geo_cfg.get('show_boresight_ray', markers_cfg.get('show_boresight_axis', True)))
    show_footprint_geo = bool(geo_cfg.get('show_footprint_ring', True))
    show_mid_geo = bool(geo_cfg.get('show_mid_altitude_ring', markers_cfg.get('show_mid_altitude_ring', False)))
    show_crosshair_geo = bool(geo_cfg.get('show_footprint_crosshair', markers_cfg.get('show_footprint_crosshair', True)))

    # Extrai configurações do IGSO
    color_cage_igso = resolve_color(igso_cfg.get('color', markers_cfg.get('color_nadir_cone_igso', 'amber')), default=(1.0, 0.80, 0.10))
    color_bore_igso = resolve_color(igso_cfg.get('color_boresight', 'orange'), default=(1.0, 0.45, 0.05))
    e_beacon_igso = float(igso_cfg.get('beacon_emissive', markers_cfg.get('beacon_emissive_igso', 0.85)))
    e_cone_igso = float(igso_cfg.get('emissive_intensity', markers_cfg.get('nadir_cone_emissive_igso', 0.95)))
    r_bottom_igso = float(igso_cfg.get('footprint_radius_km', 1150.0)) / 1000.0
    ray_thickness_igso = float(igso_cfg.get('ray_thickness', markers_cfg.get('nadir_ray_thickness', 0.018)))
    num_rays_igso = int(igso_cfg.get('num_generatrix_rays', markers_cfg.get('num_generatrix_rays_igso', 4)))
    show_gen_igso = bool(igso_cfg.get('show_generatrix_rays', True))
    show_boresight_igso = bool(igso_cfg.get('show_boresight_ray', markers_cfg.get('show_boresight_axis', True)))
    show_footprint_igso = bool(igso_cfg.get('show_footprint_ring', True))
    show_mid_igso = bool(igso_cfg.get('show_mid_altitude_ring', markers_cfg.get('show_mid_altitude_ring', False)))
    show_crosshair_igso = bool(igso_cfg.get('show_footprint_crosshair', markers_cfg.get('show_footprint_crosshair', True)))

    # 1. Halos/Retículos de Mira Neon
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_geo.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=color_cage_geo,
        emissive_intensity=e_beacon_geo
    )
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_igso.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=color_cage_igso,
        emissive_intensity=e_beacon_igso
    )

    # 2. Feixes / Gaiolas Nadir (Holográfico vs Sólido)
    if style == 'holographic_cage':
        generate_holographic_nadir_cage_glb(
            output_path=os.path.join(mesh_dir, 'nadir_beam_geo.glb'),
            r_top=r_top, r_bottom=r_bottom_geo, height=height,
            color_cage_rgb=color_cage_geo,
            color_boresight_rgb=color_bore_geo,
            emissive_intensity=e_cone_geo,
            show_generatrix_rays=show_gen_geo,
            num_rays=num_rays_geo,
            tube_radius=ray_thickness_geo,
            show_footprint_ring=show_footprint_geo,
            show_mid_ring=show_mid_geo,
            show_boresight=show_boresight_geo,
            show_crosshair=show_crosshair_geo
        )
        generate_holographic_nadir_cage_glb(
            output_path=os.path.join(mesh_dir, 'nadir_beam_igso.glb'),
            r_top=r_top, r_bottom=r_bottom_igso, height=height,
            color_cage_rgb=color_cage_igso,
            color_boresight_rgb=color_bore_igso,
            emissive_intensity=e_cone_igso,
            show_generatrix_rays=show_gen_igso,
            num_rays=num_rays_igso,
            tube_radius=ray_thickness_igso,
            show_footprint_ring=show_footprint_igso,
            show_mid_ring=show_mid_igso,
            show_boresight=show_boresight_igso,
            show_crosshair=show_crosshair_igso
        )
    else:
        op_geo = float(markers_cfg.get('nadir_cone_opacity_geo', 0.05))
        op_igso = float(markers_cfg.get('nadir_cone_opacity_igso', 0.35))
        generate_nadir_beam_glb(
            output_path=os.path.join(mesh_dir, 'nadir_beam_geo.glb'),
            r_top=r_top, r_bottom=r_bottom_geo, height=height,
            color_rgba=(color_cage_geo[0], color_cage_geo[1], color_cage_geo[2], op_geo),
            emissive_intensity=e_cone_geo
        )
        generate_nadir_beam_glb(
            output_path=os.path.join(mesh_dir, 'nadir_beam_igso.glb'),
            r_top=r_top, r_bottom=r_bottom_igso, height=height,
            color_rgba=(color_cage_igso[0], color_cage_igso[1], color_cage_igso[2], op_igso),
            emissive_intensity=e_cone_igso
        )

    print(f"✨ [MarkerGenerator] Marcadores holográficos gerados ({style}) com configurações granulares GEO/IGSO!")


if __name__ == '__main__':
    generate_all_marker_assets()
