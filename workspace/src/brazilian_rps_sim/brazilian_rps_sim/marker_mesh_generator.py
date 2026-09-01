#!/usr/bin/env python3
"""
Gerador de Malhas 3D Procedurais PBR (glTF 2.0 / .glb) para Marcadores Espaciais:
1. Retículo/Anel Holográfico de Mira (Torus Neon Emissivo)
2. Feixes Nadir com parâmetros independentes de opacidade, brilho e raio para GEO e IGSO.
"""

import os
import json
import struct
import math
import numpy as np
import yaml

def generate_nadir_beam_glb(output_path: str, r_top: float, r_bottom: float, height: float,
                            color_rgba: tuple, emissive_intensity: float = 0.5, segs: int = 48):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    vertices = []
    normals = []
    indices = []

    theta = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # Ângulo do cone
    dr = r_bottom - r_top
    length = math.sqrt(dr*dr + height*height)
    nr = height / length
    nz = -dr / length

    # 1. Anel do Topo (Z = 0)
    for i in range(segs):
        x = r_top * cos_t[i]
        y = r_top * sin_t[i]
        z = 0.0
        vertices.append([x, y, z])
        normals.append([nr * cos_t[i], nr * sin_t[i], nz])

    # 2. Anel da Base (Z = height)
    for i in range(segs):
        x = r_bottom * cos_t[i]
        y = r_bottom * sin_t[i]
        z = height
        vertices.append([x, y, z])
        normals.append([nr * cos_t[i], nr * sin_t[i], nz])

    # 3. Triângulos do Cone Truncado (Dupla Face)
    for i in range(segs):
        i_next = (i + 1) % segs
        p0 = i
        p1 = i_next
        p2 = segs + i
        p3 = segs + i_next

        # Face Externa
        indices.extend([p0, p1, p3])
        indices.extend([p0, p3, p2])
        # Face Interna (Inverted CCW)
        indices.extend([p0, p3, p1])
        indices.extend([p0, p2, p3])

    v_arr = np.array(vertices, dtype=np.float32)
    n_arr = np.array(normals, dtype=np.float32)
    idx_arr = np.array(indices, dtype=np.uint32)

    v_bytes = v_arr.tobytes()
    n_bytes = n_arr.tobytes()
    idx_bytes = idx_arr.tobytes()

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
            "bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(v_arr), "type": "VEC3",
            "min": v_arr.min(axis=0).tolist(), "max": v_arr.max(axis=0).tolist()
        },
        {
            "bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(n_arr), "type": "VEC3",
            "min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]
        },
        {
            "bufferView": 2, "byteOffset": 0, "componentType": 5125, "count": len(idx_arr), "type": "SCALAR",
            "min": [int(idx_arr.min())], "max": [int(idx_arr.max())]
        }
    ]

    r, g, b, a = color_rgba
    mat_def = {
        "name": "NadirBeamMaterial",
        "pbrMetallicRoughness": {
            "baseColorFactor": [float(r), float(g), float(b), float(a)],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.1
        },
        "emissiveFactor": [float(r * emissive_intensity), float(g * emissive_intensity), float(b * emissive_intensity)],
        "alphaMode": "BLEND",
        "doubleSided": True
    }

    gltf_dict = {
        "asset": {"version": "2.0", "generator": "RPS-BR Nadir Beam Mesh Generator"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "NadirBeamNode"}],
        "meshes": [{
            "name": "NadirBeamMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2,
                "material": 0
            }]
        }],
        "materials": [mat_def],
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

def generate_locator_ring_glb(output_path: str, r_major: float, r_minor: float,
                             color_rgb: tuple, emissive_intensity: float = 1.0,
                             segs_major: int = 36, segs_minor: int = 12):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
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

            indices.extend([p00, p10, p01])
            indices.extend([p01, p10, p11])

    v_arr = np.array(vertices, dtype=np.float32)
    n_arr = np.array(normals, dtype=np.float32)
    idx_arr = np.array(indices, dtype=np.uint32)

    v_bytes = v_arr.tobytes()
    n_bytes = n_arr.tobytes()
    idx_bytes = idx_arr.tobytes()

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
            "bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(v_arr), "type": "VEC3",
            "min": v_arr.min(axis=0).tolist(), "max": v_arr.max(axis=0).tolist()
        },
        {
            "bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(n_arr), "type": "VEC3",
            "min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]
        },
        {
            "bufferView": 2, "byteOffset": 0, "componentType": 5125, "count": len(idx_arr), "type": "SCALAR",
            "min": [int(idx_arr.min())], "max": [int(idx_arr.max())]
        }
    ]

    r, g, b = color_rgb
    mat_def = {
        "name": "LocatorRingNeonMaterial",
        "pbrMetallicRoughness": {
            "baseColorFactor": [float(r), float(g), float(b), 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.2
        },
        "emissiveFactor": [float(r * emissive_intensity), float(g * emissive_intensity), float(b * emissive_intensity)],
        "alphaMode": "OPAQUE",
        "doubleSided": True
    }

    gltf_dict = {
        "asset": {"version": "2.0", "generator": "RPS-BR Locator Ring Mesh Generator"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "LocatorRingNode"}],
        "meshes": [{
            "name": "LocatorRingMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2,
                "material": 0
            }]
        }],
        "materials": [mat_def],
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

    vis = cfg.get('visualization', {})
    markers_cfg = vis.get('satellite_markers', vis.get('markers', {}))

    r_beacon = float(markers_cfg.get('beacon_radius', 0.35))
    t_beacon = float(markers_cfg.get('beacon_tube_thickness', 0.015))
    e_beacon_geo = float(markers_cfg.get('beacon_emissive_geo', markers_cfg.get('beacon_emissive_intensity_geo', 0.80)))
    e_beacon_igso = float(markers_cfg.get('beacon_emissive_igso', markers_cfg.get('beacon_emissive_intensity_igso', 0.85)))

    r_top = float(markers_cfg.get('nadir_cone_top_radius', 0.08))
    
    # Parâmetros independentes de raio, opacidade e emissão
    r_bottom_geo = float(markers_cfg.get('nadir_cone_bottom_radius_geo', 2.60))
    r_bottom_igso = float(markers_cfg.get('nadir_cone_bottom_radius_igso', 1.15))
    
    op_geo = float(markers_cfg.get('nadir_cone_opacity_geo', 0.15))
    op_igso = float(markers_cfg.get('nadir_cone_opacity_igso', 0.22))
    
    e_cone_geo = float(markers_cfg.get('nadir_cone_emissive_geo', markers_cfg.get('nadir_cone_emissive_intensity_geo', 0.20)))
    e_cone_igso = float(markers_cfg.get('nadir_cone_emissive_igso', markers_cfg.get('nadir_cone_emissive_intensity_igso', 0.35)))
    
    height = 45.0 # Comprimento seguro para contato contínuo no apogeu

    # 1. Halos/Retículos de Mira Neon
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_geo.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=(0.0, 0.9, 1.0), # Ciano Neon
        emissive_intensity=e_beacon_geo
    )
    generate_locator_ring_glb(
        output_path=os.path.join(mesh_dir, 'locator_ring_igso.glb'),
        r_major=r_beacon, r_minor=t_beacon,
        color_rgb=(1.0, 0.8, 0.1), # Dourado/Âmbar Neon
        emissive_intensity=e_beacon_igso
    )

    # 2. Cones Nadir (GEO: Cobertura Ampla Continental | IGSO: Spot Beam Zenital Focado)
    generate_nadir_beam_glb(
        output_path=os.path.join(mesh_dir, 'nadir_beam_geo.glb'),
        r_top=r_top, r_bottom=r_bottom_geo, height=height,
        color_rgba=(0.0, 0.85, 1.0, op_geo),
        emissive_intensity=e_cone_geo
    )
    generate_nadir_beam_glb(
        output_path=os.path.join(mesh_dir, 'nadir_beam_igso.glb'),
        r_top=r_top, r_bottom=r_bottom_igso, height=height,
        color_rgba=(1.0, 0.75, 0.1, op_igso),
        emissive_intensity=e_cone_igso
    )

    print(f"✨ [MarkerGenerator] Marcadores gerados: GEO (Op: {op_geo*100:.0f}%, Raio: {r_bottom_geo}) | IGSO (Op: {op_igso*100:.0f}%, Raio: {r_bottom_igso})!")

if __name__ == '__main__':
    generate_all_marker_assets()
