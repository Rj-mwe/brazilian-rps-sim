#!/usr/bin/env python3
"""
Gerador de Malhas 3D de Alta Fidelidade para Marcadores Visuais (glTF 2.0 / .glb).
Lê todos os parâmetros diretamente de config/simulation_parameters.yaml:
1. Cone Truncado de Feixe Nadir (Diâmetro do topo, diâmetro da base, opacidade configurável)
2. Retículos/Anéis Holográficos Radiantes (Raio do anel, espessura e intensidade de brilho)
"""

import os
import json
import struct
import yaml
import numpy as np

def create_frustum_cone_mesh(top_radius, bottom_radius, height, num_segments=32):
    """Gera um cone truncado suave com ponta no topo (Z=0) e base na Terra (+Z=height)."""
    vertices = []
    normals = []
    indices = []

    angles = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)

    dr = bottom_radius - top_radius
    slope_angle = np.arctan2(dr, height)
    cos_s, sin_s = np.cos(slope_angle), np.sin(slope_angle)

    for a in angles:
        cos_a, sin_a = np.cos(a), np.sin(a)
        v_top = [top_radius * cos_a, top_radius * sin_a, 0.0]
        v_bot = [bottom_radius * cos_a, bottom_radius * sin_a, height]
        norm = [cos_a * cos_s, sin_a * cos_s, -sin_s]

        vertices.extend([v_top, v_bot])
        normals.extend([norm, norm])

    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        v0 = i * 2
        v1 = i * 2 + 1
        v2 = next_i * 2 + 1
        v3 = next_i * 2
        indices.extend([v0, v1, v2, v0, v2, v3])
        indices.extend([v0, v2, v1, v0, v3, v2])

    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(indices, dtype=np.uint32)

def create_ring_mesh(radius, tube_radius, num_segments=48, num_tube=8):
    """Gera um anel/toro fino emissivo como retículo de mira holográfico."""
    vertices = []
    normals = []
    indices = []

    theta = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)
    phi = np.linspace(0, 2 * np.pi, num_tube, endpoint=False)

    for i, t in enumerate(theta):
        cos_t, sin_t = np.cos(t), np.sin(t)
        for j, p in enumerate(phi):
            cos_p, sin_p = np.cos(p), np.sin(p)
            r = radius + tube_radius * cos_p
            x = r * cos_t
            y = r * sin_t
            z = tube_radius * sin_p
            n = [cos_p * cos_t, cos_p * sin_t, sin_p]
            vertices.append([x, y, z])
            normals.append(n)

    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        for j in range(num_tube):
            next_j = (j + 1) % num_tube
            v0 = i * num_tube + j
            v1 = i * num_tube + next_j
            v2 = next_i * num_tube + next_j
            v3 = next_i * num_tube + j
            indices.extend([v0, v1, v2, v0, v2, v3])

    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(indices, dtype=np.uint32)

def write_glb(output_path, vertices, normals, indices, material_def):
    """Escreve um arquivo glTF 2.0 binário (.glb)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    v_bytes = vertices.tobytes()
    n_bytes = normals.tobytes()
    idx_bytes = indices.tobytes()

    while len(v_bytes) % 4 != 0: v_bytes += b'\x00'
    while len(n_bytes) % 4 != 0: n_bytes += b'\x00'
    while len(idx_bytes) % 4 != 0: idx_bytes += b'\x00'

    buffer_bytes = v_bytes + n_bytes + idx_bytes

    buffer_views = [
        {"buffer": 0, "byteOffset": 0, "byteLength": len(v_bytes), "target": 34962},
        {"buffer": 0, "byteOffset": len(v_bytes), "byteLength": len(n_bytes), "target": 34962},
        {"buffer": 0, "byteOffset": len(v_bytes) + len(n_bytes), "byteLength": len(idx_bytes), "target": 34963}
    ]

    accessors = [
        {
            "bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(vertices), "type": "VEC3",
            "min": vertices.min(axis=0).tolist(), "max": vertices.max(axis=0).tolist()
        },
        {
            "bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(normals), "type": "VEC3",
            "min": normals.min(axis=0).tolist(), "max": normals.max(axis=0).tolist()
        },
        {
            "bufferView": 2, "byteOffset": 0, "componentType": 5125, "count": len(indices), "type": "SCALAR",
            "min": [int(indices.min())], "max": [int(indices.max())]
        }
    ]

    gltf_dict = {
        "asset": {"version": "2.0", "generator": "RPS-BR Visual Marker Generator"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "name": "MarkerMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2,
                "material": 0
            }]
        }],
        "materials": [material_def],
        "buffers": [{"byteLength": len(buffer_bytes)}],
        "bufferViews": buffer_views,
        "accessors": accessors
    }

    json_bytes = json.dumps(gltf_dict, separators=(',', ':')).encode('utf-8')
    while len(json_bytes) % 4 != 0: json_bytes += b' '

    glb_header = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(json_bytes) + 8 + len(buffer_bytes))
    chunk0_header = struct.pack('<II', len(json_bytes), 0x4E4F534A)
    chunk1_header = struct.pack('<II', len(buffer_bytes), 0x004E4942)

    with open(output_path, 'wb') as f:
        f.write(glb_header)
        f.write(chunk0_header)
        f.write(json_bytes)
        f.write(chunk1_header)
        f.write(buffer_bytes)

def generate_all_marker_assets(config_path: str = None, mesh_dir: str = None):
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not mesh_dir:
        mesh_dir = os.path.join(pkg_dir, 'meshes')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis_cfg = cfg.get('visualization', {}).get('markers', {})
    cone_opacity = float(vis_cfg.get('nadir_cone_opacity', 0.28))
    top_r = float(vis_cfg.get('nadir_cone_top_radius', 0.08))
    bot_r = float(vis_cfg.get('nadir_cone_bottom_radius', 2.8))
    cone_emiss = float(vis_cfg.get('nadir_cone_emissive_intensity', 0.65))

    beacon_r = float(vis_cfg.get('beacon_radius', 0.32))
    tube_r = float(vis_cfg.get('beacon_tube_thickness', 0.015))
    beacon_emiss = float(vis_cfg.get('beacon_emissive_intensity', 1.0))

    # 1. Cone de Feixe Nadir GEO (Ciano)
    v_c, n_c, idx_c = create_frustum_cone_mesh(top_radius=top_r, bottom_radius=bot_r, height=35.786, num_segments=36)
    mat_cone_geo = {
        "name": "NadirBeam_GEO",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.0, 0.85, 1.0, cone_opacity],
            "metallicFactor": 0.1,
            "roughnessFactor": 0.9
        },
        "emissiveFactor": [0.0, 0.85 * cone_emiss, 1.0 * cone_emiss],
        "alphaMode": "BLEND",
        "doubleSided": True
    }
    write_glb(os.path.join(mesh_dir, 'nadir_beam_geo.glb'), v_c, n_c, idx_c, mat_cone_geo)

    # 2. Cone de Feixe Nadir IGSO (Âmbar/Dourado)
    mat_cone_igso = {
        "name": "NadirBeam_IGSO",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 0.65, 0.0, cone_opacity],
            "metallicFactor": 0.1,
            "roughnessFactor": 0.9
        },
        "emissiveFactor": [1.0 * cone_emiss, 0.65 * cone_emiss, 0.0],
        "alphaMode": "BLEND",
        "doubleSided": True
    }
    write_glb(os.path.join(mesh_dir, 'nadir_beam_igso.glb'), v_c, n_c, idx_c, mat_cone_igso)

    # 3. Anel Holográfico Radiante GEO (Ciano Neon)
    v_r, n_r, idx_r = create_ring_mesh(radius=beacon_r, tube_radius=tube_r, num_segments=48, num_tube=8)
    mat_ring_geo = {
        "name": "LocatorRing_GEO",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.0, 0.95, 1.0, 1.0],
            "metallicFactor": 0.1,
            "roughnessFactor": 0.2
        },
        "emissiveFactor": [0.0, 0.95 * beacon_emiss, 1.0 * beacon_emiss],
        "doubleSided": True
    }
    write_glb(os.path.join(mesh_dir, 'locator_ring_geo.glb'), v_r, n_r, idx_r, mat_ring_geo)

    # 4. Anel Holográfico Radiante IGSO (Âmbar/Laranja Neon)
    mat_ring_igso = {
        "name": "LocatorRing_IGSO",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 0.70, 0.0, 1.0],
            "metallicFactor": 0.1,
            "roughnessFactor": 0.2
        },
        "emissiveFactor": [1.0 * beacon_emiss, 0.70 * beacon_emiss, 0.0],
        "doubleSided": True
    }
    write_glb(os.path.join(mesh_dir, 'locator_ring_igso.glb'), v_r, n_r, idx_r, mat_ring_igso)

    print(f"✨ [MarkerGenerator] Marcadores gerados com opacidade {cone_opacity*100:.0f}%, raio base {bot_r} e raio topo {top_r}!")

if __name__ == '__main__':
    generate_all_marker_assets()
