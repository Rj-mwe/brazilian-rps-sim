#!/usr/bin/env python3
"""
Gerador procedural das trajetórias e anéis orbitais 3D em glTF 2.0 PBR:
1. Anel Equatorial dos GEOs (orbit_geo.gltf)
2. Trajetória 3D da Figura-8 dos IGSOs (orbit_igso.gltf)

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


def generate_orbit_tube(output_path: str, pts: np.ndarray, thickness: float = 0.10,
                        color_rgb: tuple = (1.0, 0.8, 0.2), emissive_intensity: float = 0.95):
    """Gera um tubo 3D contínuo ao longo de uma trajetória tridimensional usando GltfMeshBuilder."""
    num_pts = len(pts)
    vertices = []
    normals = []
    indices = []

    for i in range(num_pts):
        p = pts[i]
        p_next = pts[(i + 1) % num_pts]
        tangent = p_next - p
        norm = np.linalg.norm(tangent)
        tangent = tangent / norm if norm > 1e-6 else np.array([1, 0, 0])

        up = np.array([0, 0, 1]) if abs(tangent[2]) < 0.9 else np.array([1, 0, 0])
        normal = np.cross(tangent, up)
        normal = normal / np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)

        for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
            offset = thickness * (math.cos(angle) * normal + math.sin(angle) * binormal)
            vertices.append((p + offset).tolist())
            normals.append((offset / thickness).tolist())

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

    r, g, b = color_rgb
    builder = GltfMeshBuilder(name="OrbitTrajectory", generator_tag="RPS-BR Orbital Trajectory Generator")
    builder.set_positions(vertices)\
           .set_normals(normals)\
           .set_indices(indices)\
           .set_pbr_material(
               name="OrbitGlowMaterial",
               base_color_rgba=(r, g, b, 1.0),
               metallic=0.0,
               roughness=0.1,
               emissive_intensity=emissive_intensity,
               alpha_mode="OPAQUE",
               double_sided=True
           )\
           .save_gltf(output_path, embedded_base64=True)

    print(f"✨ [OrbitGenerator] Trilha orbital salva via GltfMeshBuilder: {output_path} (Cor: {color_rgb})")


def generate_all_orbit_rings(config_path: str = None, mesh_dir: str = None):
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not mesh_dir:
        mesh_dir = os.path.join(pkg_dir, 'meshes')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis_cfg = cfg.get('visualization', {})
    trails_cfg = vis_cfg.get('orbit_trails', vis_cfg.get('markers', {}))

    thick_geo = float(trails_cfg.get('tube_thickness_geo', 0.10))
    thick_igso = float(trails_cfg.get('tube_thickness_igso', 0.12))

    color_geo = resolve_color(trails_cfg.get('color_geo_orbit', 'cyan'), default=(0.0, 0.90, 1.0))
    color_igso = resolve_color(trails_cfg.get('color_igso_orbit', 'amber'), default=(1.0, 0.80, 0.10))

    # 1. Anel Equatorial dos GEOs
    num_pts = 360
    theta = np.linspace(0, 2 * np.pi, num_pts, endpoint=False)
    r_geo = 42.16414
    pts_geo = [[r_geo * math.cos(th), r_geo * math.sin(th), 0.0] for th in theta]

    generate_orbit_tube(
        output_path=os.path.join(mesh_dir, 'orbit_geo.gltf'),
        pts=np.array(pts_geo, dtype=np.float32),
        thickness=thick_geo,
        color_rgb=color_geo,
        emissive_intensity=0.95
    )

    # 2. Trajetória 3D da Figura-8 dos IGSOs
    sat_list = cfg.get('constellation', {}).get('satellites', [])
    igso_sats = [s for s in sat_list if s.get('type') == 'IGSO']
    
    if igso_sats:
        igso = igso_sats[0]
        a = float(igso.get('semi_major_axis_km', 42164.14)) / 1000.0
        e = float(igso.get('eccentricity', 0.04))
        inc = math.radians(float(igso.get('inclination_deg', 25.0)))
        raan = math.radians(float(igso.get('raan_deg', 42.0)))
        argp = math.radians(float(igso.get('arg_perigee_deg', 90.0)))
        m0 = math.radians(float(igso.get('mean_anomaly_deg', 180.0)))
        omega_earth = 7.292115e-5

        pts_figure8 = []
        for t in np.linspace(0, 86164.0905, num_pts, endpoint=False):
            M = m0 + omega_earth * t
            E = M
            for _ in range(10):
                E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
            nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
            r = a * (1 - e * math.cos(E))

            p_x = r * math.cos(nu)
            p_y = r * math.sin(nu)

            cos_O, sin_O = math.cos(raan), math.sin(raan)
            cos_w, sin_w = math.cos(argp), math.sin(argp)
            cos_i, sin_i = math.cos(inc), math.sin(inc)

            P_x = cos_O * cos_w - sin_O * sin_w * cos_i
            P_y = sin_O * cos_w + cos_O * sin_w * cos_i
            P_z = sin_w * sin_i

            Q_x = -cos_O * sin_w - sin_O * cos_w * cos_i
            Q_y = -sin_O * sin_w + cos_O * sin_w * cos_i
            Q_z = cos_w * sin_i

            eci_x = p_x * P_x + p_y * Q_x
            eci_y = p_x * P_y + p_y * Q_y
            eci_z = p_x * P_z + p_y * Q_z

            theta_spin = omega_earth * t
            x_body = eci_x * math.cos(theta_spin) + eci_y * math.sin(theta_spin)
            y_body = -eci_x * math.sin(theta_spin) + eci_y * math.cos(theta_spin)
            z_body = eci_z

            pts_figure8.append([x_body, y_body, z_body])

        generate_orbit_tube(
            output_path=os.path.join(mesh_dir, 'orbit_igso.gltf'),
            pts=np.array(pts_figure8, dtype=np.float32),
            thickness=thick_igso,
            color_rgb=color_igso,
            emissive_intensity=0.95
        )

if __name__ == '__main__':
    generate_all_orbit_rings()
