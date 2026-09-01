#!/usr/bin/env python3
"""
Gerador procedural das trajetórias e anéis orbitais 3D em glTF 2.0 PBR:
1. Anel Equatorial dos GEOs (orbit_geo.gltf)
2. Trajetória 3D da Figura-8 dos IGSOs (orbit_igso.gltf)

Implementa:
- Rotation Minimizing Frames (RMF / Parallel Transport Frames) para eliminar
  completamente descontinuidades de Gimbal, torções e distorções na malha 3D.
- GltfMeshBuilder Pattern para empacotamento PBR limpo.
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


def build_smooth_rmf_tube(pts: np.ndarray, radius: float = 0.12, radial_segs: int = 8):
    """
    Gera malha 3D tubular perfeitamente lisa e contínua usando
    Rotation Minimizing Frames (RMF / Bishop Frames).
    Elimina 100% de torções de Frenet e singularidades de Gimbal.
    """
    n = len(pts)
    
    # 1. Vetores tangentes unitários contínuos
    tangents = []
    for i in range(n):
        p_prev = pts[(i - 1) % n]
        p_next = pts[(i + 1) % n]
        t = p_next - p_prev
        norm = np.linalg.norm(t)
        tangents.append(t / norm if norm > 1e-9 else np.array([1.0, 0.0, 0.0]))
    tangents = np.array(tangents)

    # 2. Frame inicial perpendicular a tangents[0]
    t0 = tangents[0]
    ref = np.array([0.0, 0.0, 1.0]) if abs(t0[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    n0 = np.cross(t0, ref)
    n0 = n0 / np.linalg.norm(n0)
    b0 = np.cross(t0, n0)

    normals = [n0]
    binormals = [b0]

    # 3. Propagação por RMF (Rodrigues Rotation)
    for i in range(n - 1):
        t_curr = tangents[i]
        t_next = tangents[i + 1]
        v = np.cross(t_curr, t_next)
        v_norm = np.linalg.norm(v)
        
        if v_norm < 1e-8:
            n_next = normals[-1]
        else:
            axis = v / v_norm
            c = np.clip(np.dot(t_curr, t_next), -1.0, 1.0)
            angle = math.acos(c)
            n_prev = normals[-1]
            n_next = (n_prev * math.cos(angle) +
                      np.cross(axis, n_prev) * math.sin(angle) +
                      axis * np.dot(axis, n_prev) * (1.0 - math.cos(angle)))
            n_next = n_next / np.linalg.norm(n_next)
            
        b_next = np.cross(t_next, n_next)
        b_next = b_next / np.linalg.norm(b_next)
        normals.append(n_next)
        binormals.append(b_next)

    # 4. Correção de Holonomia/Torção de fechamento ao longo do anel periódico
    t_end = tangents[-1]
    t_start = tangents[0]
    v_close = np.cross(t_end, t_start)
    v_close_norm = np.linalg.norm(v_close)
    if v_close_norm < 1e-8:
        n_close = normals[-1]
    else:
        axis = v_close / v_close_norm
        angle = math.acos(np.clip(np.dot(t_end, t_start), -1.0, 1.0))
        n_close = (normals[-1] * math.cos(angle) +
                   np.cross(axis, normals[-1]) * math.sin(angle) +
                   axis * np.dot(axis, normals[-1]) * (1.0 - math.cos(angle)))
        n_close = n_close / np.linalg.norm(n_close)
        
    dot_close = np.clip(np.dot(n_close, normals[0]), -1.0, 1.0)
    cross_close = np.dot(tangents[0], np.cross(n_close, normals[0]))
    twist_angle = math.atan2(cross_close, dot_close)

    # Distribui a rotação suavemente para fechar sem descontinuidade
    corrected_normals = []
    corrected_binormals = []
    for i in range(n):
        frac = i / n
        theta_twist = frac * twist_angle
        t_i = tangents[i]
        n_i = normals[i]
        n_corr = (n_i * math.cos(theta_twist) +
                  np.cross(t_i, n_i) * math.sin(theta_twist) +
                  t_i * np.dot(t_i, n_i) * (1.0 - math.cos(theta_twist)))
        n_corr = n_corr / np.linalg.norm(n_corr)
        b_corr = np.cross(t_i, n_corr)
        b_corr = b_corr / np.linalg.norm(b_corr)
        corrected_normals.append(n_corr)
        corrected_binormals.append(b_corr)

    # 5. Geração dos vértices e normais da seção transversal circular
    vertices = []
    v_normals = []
    angles = np.linspace(0, 2 * math.pi, radial_segs, endpoint=False)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    for i in range(n):
        center = pts[i]
        n_i = corrected_normals[i]
        b_i = corrected_binormals[i]
        for j in range(radial_segs):
            offset_dir = cos_a[j] * n_i + sin_a[j] * b_i
            pos = center + radius * offset_dir
            vertices.append(pos.tolist())
            v_normals.append(offset_dir.tolist())

    indices = []
    for i in range(n):
        i_next = (i + 1) % n
        base_curr = i * radial_segs
        base_next = i_next * radial_segs
        for j in range(radial_segs):
            j_next = (j + 1) % radial_segs
            p00 = base_curr + j
            p01 = base_curr + j_next
            p10 = base_next + j
            p11 = base_next + j_next
            indices.extend([p00, p10, p01, p01, p10, p11])

    return np.array(vertices, dtype=np.float32), np.array(v_normals, dtype=np.float32), np.array(indices, dtype=np.uint32)


def generate_orbit_tube(output_path: str, pts: np.ndarray, thickness: float = 0.12,
                        color_rgb: tuple = (1.0, 0.8, 0.2), emissive_intensity: float = 0.95):
    """Exporta um tubo 3D contínuo e suave usando RMF e GltfMeshBuilder."""
    vertices, normals, indices = build_smooth_rmf_tube(pts, radius=thickness, radial_segs=8)

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

    print(f"✨ [OrbitGenerator] Trilha orbital RMF salva via GltfMeshBuilder: {output_path} (Cor: {color_rgb})")


def generate_all_orbit_rings(config_path: str = None, mesh_dir: str = None):
    if not config_path or not os.path.exists(config_path):
        try:
            from ament_index_python.packages import get_package_share_directory
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            candidate = os.path.join(pkg_share, 'config', 'simulation_parameters.yaml')
            if os.path.exists(candidate):
                config_path = candidate
        except Exception:
            pass

    if not config_path or not os.path.exists(config_path):
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
        if os.path.exists(candidate):
            config_path = candidate
        else:
            config_path = '/home/rjgamito/ros2_ws/src/brazilian_rps_sim/config/simulation_parameters.yaml'

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
        if config_path and os.path.exists(config_path):
            mesh_dir = os.path.join(os.path.dirname(os.path.dirname(config_path)), 'meshes')
        else:
            mesh_dir = '/home/rjgamito/ros2_ws/src/brazilian_rps_sim/meshes'

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis_cfg = cfg.get('visualization', {})
    trails_cfg = vis_cfg.get('orbit_trails', vis_cfg.get('markers', {}))

    thick_geo = float(trails_cfg.get('tube_thickness_geo', 0.10))
    thick_igso = float(trails_cfg.get('tube_thickness_igso', 0.12))

    color_geo = resolve_color(trails_cfg.get('color_geo_orbit', 'cyan'), default=(0.0, 0.90, 1.0))
    color_igso = resolve_color(trails_cfg.get('color_igso_orbit', 'amber'), default=(1.0, 0.80, 0.10))

    # 1. Anel Equatorial dos GEOs (720 pontos)
    num_pts_geo = 720
    theta = np.linspace(0, 2 * np.pi, num_pts_geo, endpoint=False)
    r_geo = 42.16414
    pts_geo = [[r_geo * math.cos(th), r_geo * math.sin(th), 0.0] for th in theta]

    generate_orbit_tube(
        output_path=os.path.join(mesh_dir, 'orbit_geo.gltf'),
        pts=np.array(pts_geo, dtype=np.float32),
        thickness=thick_geo,
        color_rgb=color_geo,
        emissive_intensity=0.95
    )

    # 2. Trajetória 3D da Figura-8 dos IGSOs (720 pontos = amostragem a cada 2 min)
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

        num_pts_igso = 720
        pts_figure8 = []
        for t in np.linspace(0, 86164.0905, num_pts_igso, endpoint=False):
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
            Q_y = -sin_O * sin_w + cos_O * cos_w * cos_i
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
