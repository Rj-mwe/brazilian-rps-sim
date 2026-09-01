#!/usr/bin/env python3
"""
Gerador de Malha 3D Fotorrealista PBR para Satélites da Categoria Small GEO / NavSat em formato glTF 2.0 (.glb).
Inclui:
- Barramento central com manta térmica dourada (Gold MLI / Kapton Foil)
- Radiadores térmicos prateados
- 2 Asas de painéis solares GaAs azuis-escuros com armação estrutural
- Antena Phased-Array de Navegação Nadir
- Antena parabólica de Feeder Link
- Bocal de propulsão elétrica/iônica
"""

import os
import json
import struct
import numpy as np

def create_box_mesh(size_x, size_y, size_z, center=(0, 0, 0)):
    """Gera vértices, normais e índices de um paralelepípedo."""
    hx, hy, hz = size_x / 2.0, size_y / 2.0, size_z / 2.0
    cx, cy, cz = center

    # 6 faces * 4 vértices = 24 vértices
    vertices = []
    normals = []
    indices = []

    # +X, -X, +Y, -Y, +Z, -Z
    face_defs = [
        # (+X)
        ([ (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (hx, -hy, hz) ], (1, 0, 0)),
        # (-X)
        ([ (-hx, hy, -hz), (-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz) ], (-1, 0, 0)),
        # (+Y)
        ([ (hx, hy, -hz), (-hx, hy, -hz), (-hx, hy, hz), (hx, hy, hz) ], (0, 1, 0)),
        # (-Y)
        ([ (-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz) ], (0, -1, 0)),
        # (+Z)
        ([ (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz) ], (0, 0, 1)),
        # (-Z)
        ([ (-hx, hy, -hz), (hx, hy, -hz), (hx, -hy, -hz), (-hx, -hy, -hz) ], (0, 0, -1)),
    ]

    base_idx = 0
    for face_verts, norm in face_defs:
        for vx, vy, vz in face_verts:
            vertices.append([vx + cx, vy + cy, vz + cz])
            normals.append(norm)
        indices.extend([base_idx, base_idx + 1, base_idx + 2, base_idx, base_idx + 2, base_idx + 3])
        base_idx += 4

    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(indices, dtype=np.uint32)

def create_cylinder_mesh(radius, height, num_segments=16, center=(0, 0, 0), axis='z'):
    """Gera um cilindro aberto ou fechado."""
    cx, cy, cz = center
    vertices = []
    normals = []
    indices = []

    half_h = height / 2.0
    angles = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)

    # Vértices laterais
    for i, a in enumerate(angles):
        cos_a, sin_a = np.cos(a), np.sin(a)
        if axis == 'z':
            v_bot = [cx + radius * cos_a, cy + radius * sin_a, cz - half_h]
            v_top = [cx + radius * cos_a, cy + radius * sin_a, cz + half_h]
            n = [cos_a, sin_a, 0.0]
        elif axis == 'x':
            v_bot = [cx - half_h, cy + radius * cos_a, cz + radius * sin_a]
            v_top = [cx + half_h, cy + radius * cos_a, cz + radius * sin_a]
            n = [0.0, cos_a, sin_a]
        else:
            v_bot = [cx + radius * cos_a, cy - half_h, cz + radius * sin_a]
            v_top = [cx + radius * cos_a, cy + half_h, cz + radius * sin_a]
            n = [cos_a, 0.0, sin_a]

        vertices.extend([v_bot, v_top])
        normals.extend([n, n])

    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        v0 = i * 2
        v1 = i * 2 + 1
        v2 = next_i * 2 + 1
        v3 = next_i * 2
        indices.extend([v0, v1, v2, v0, v2, v3])

    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(indices, dtype=np.uint32)

def create_dish_mesh(radius, depth, num_segments=16, center=(0, 0, 0)):
    """Gera uma antena parabólica côncava."""
    cx, cy, cz = center
    vertices = [[cx, cy, cz - depth]] # Vértice central do fundo
    normals = [[0.0, 0.0, 1.0]]
    indices = []

    angles = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)
    for a in angles:
        cos_a, sin_a = np.cos(a), np.sin(a)
        vertices.append([cx + radius * cos_a, cy + radius * sin_a, cz])
        normals.append([cos_a * 0.3, sin_a * 0.3, 0.9])

    for i in range(num_segments):
        next_i = (i + 1) % num_segments
        indices.extend([0, i + 1, next_i + 1])

    return np.array(vertices, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(indices, dtype=np.uint32)

def merge_mesh_parts(parts):
    """Funde múltiplas partes de malha que compartilham o mesmo material."""
    all_verts = []
    all_norms = []
    all_indices = []
    offset = 0

    for v, n, idx in parts:
        all_verts.append(v)
        all_norms.append(n)
        all_indices.append(idx + offset)
        offset += len(v)

    if not all_verts:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.float32), np.empty((0,), dtype=np.uint32)

    return np.vstack(all_verts), np.vstack(all_norms), np.concatenate(all_indices)

def generate_satellite_glb(output_path: str):
    """Constrói o arquivo glTF 2.0 binário (.glb) do satélite de posicionamento Small GEO."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # --------------------------------------------------------------------------
    # Material 0: Manta Térmica Dourada (Gold MLI Kapton) - Barramento Principal
    # --------------------------------------------------------------------------
    gold_parts = [
        # Barramento Central (1.2m x 1.2m x 1.6m)
        create_box_mesh(1.2, 1.2, 1.6, center=(0, 0, 0)),
        # Braço de suporte da antena
        create_box_mesh(0.1, 0.1, 0.3, center=(0, 0, 0.95))
    ]
    v_gold, n_gold, idx_gold = merge_mesh_parts(gold_parts)

    # --------------------------------------------------------------------------
    # Material 1: Painéis Solares GaAs (Azul Marinho Metálico)
    # --------------------------------------------------------------------------
    solar_parts = [
        # Asa Solar +Y (3 painéis articulados: comprimento total 2.6m, largura 0.9m)
        create_box_mesh(0.9, 2.6, 0.03, center=(0, 2.2, 0)),
        # Asa Solar -Y (3 painéis articulados: comprimento total 2.6m, largura 0.9m)
        create_box_mesh(0.9, 2.6, 0.03, center=(0, -2.2, 0)),
    ]
    v_solar, n_solar, idx_solar = merge_mesh_parts(solar_parts)

    # --------------------------------------------------------------------------
    # Material 2: Radiadores e Estrutura Prateada (Silver Metal)
    # --------------------------------------------------------------------------
    silver_parts = [
        # Hastes de suporte dos painéis solares
        create_cylinder_mesh(0.04, 0.9, num_segments=8, center=(0, 0.8, 0), axis='y'),
        create_cylinder_mesh(0.04, 0.9, num_segments=8, center=(0, -0.8, 0), axis='y'),
        # Radiadores térmicos nas faces +X e -X
        create_box_mesh(0.02, 1.0, 1.4, center=(0.61, 0, 0)),
        create_box_mesh(0.02, 1.0, 1.4, center=(-0.61, 0, 0)),
        # Antena Parabólica de Feeder Link (Banda C/Ku articulada)
        create_dish_mesh(0.4, 0.15, num_segments=16, center=(0.4, 0.4, 0.95)),
        create_cylinder_mesh(0.03, 0.25, num_segments=8, center=(0.4, 0.4, 0.88), axis='z')
    ]
    v_silver, n_silver, idx_silver = merge_mesh_parts(silver_parts)

    # --------------------------------------------------------------------------
    # Material 3: Antena Phased Array de Navegação Nadir (Branca/Metálica)
    # --------------------------------------------------------------------------
    antenna_parts = [
        # Domo/Dísculo da antena de posicionamento apontada para a Terra (+Z)
        create_cylinder_mesh(0.45, 0.08, num_segments=24, center=(0, 0, 0.84), axis='z'),
        create_dish_mesh(0.42, 0.05, num_segments=24, center=(0, 0, 0.88)),
        # Corneta central de alimentação
        create_cylinder_mesh(0.06, 0.15, num_segments=12, center=(0, 0, 0.95), axis='z')
    ]
    v_antenna, n_antenna, idx_antenna = merge_mesh_parts(antenna_parts)

    # --------------------------------------------------------------------------
    # Material 4: Bocal de Propulsão Iônica / Química (Titânio Escuro)
    # --------------------------------------------------------------------------
    thruster_parts = [
        create_cylinder_mesh(0.18, 0.25, num_segments=16, center=(0, 0, -0.92), axis='z')
    ]
    v_thruster, n_thruster, idx_thruster = merge_mesh_parts(thruster_parts)

    # Agrupa todos os grupos de primitivas
    groups = [
        (v_gold, n_gold, idx_gold, 0),       # Gold MLI
        (v_solar, n_solar, idx_solar, 1),    # Solar Panels
        (v_silver, n_silver, idx_silver, 2), # Silver Structure
        (v_antenna, n_antenna, idx_antenna, 3), # Nav Antenna
        (v_thruster, n_thruster, idx_thruster, 4) # Thruster
    ]

    # Construção dos Buffers Binários glTF
    buffer_bytes = bytearray()
    buffer_views = []
    accessors = []
    primitives = []

    for v, n, idx, mat_id in groups:
        if len(v) == 0:
            continue

        # 1. Posições dos Vértices
        v_bytes = v.tobytes()
        v_offset = len(buffer_bytes)
        buffer_bytes.extend(v_bytes)
        # Padding 4 bytes
        while len(buffer_bytes) % 4 != 0:
            buffer_bytes.append(0)

        v_view_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": v_offset,
            "byteLength": len(v_bytes),
            "target": 34962 # ARRAY_BUFFER
        })

        v_acc_idx = len(accessors)
        accessors.append({
            "bufferView": v_view_idx,
            "byteOffset": 0,
            "componentType": 5126, # FLOAT
            "count": len(v),
            "type": "VEC3",
            "min": v.min(axis=0).tolist(),
            "max": v.max(axis=0).tolist()
        })

        # 2. Vetores Normais
        n_bytes = n.tobytes()
        n_offset = len(buffer_bytes)
        buffer_bytes.extend(n_bytes)
        while len(buffer_bytes) % 4 != 0:
            buffer_bytes.append(0)

        n_view_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": n_offset,
            "byteLength": len(n_bytes),
            "target": 34962
        })

        n_acc_idx = len(accessors)
        accessors.append({
            "bufferView": n_view_idx,
            "byteOffset": 0,
            "componentType": 5126,
            "count": len(n),
            "type": "VEC3",
            "min": n.min(axis=0).tolist(),
            "max": n.max(axis=0).tolist()
        })

        # 3. Índices de Triângulos
        idx_bytes = idx.tobytes()
        idx_offset = len(buffer_bytes)
        buffer_bytes.extend(idx_bytes)
        while len(buffer_bytes) % 4 != 0:
            buffer_bytes.append(0)

        idx_view_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": idx_offset,
            "byteLength": len(idx_bytes),
            "target": 34963 # ELEMENT_ARRAY_BUFFER
        })

        idx_acc_idx = len(accessors)
        accessors.append({
            "bufferView": idx_view_idx,
            "byteOffset": 0,
            "componentType": 5125, # UNSIGNED_INT
            "count": len(idx),
            "type": "SCALAR",
            "min": [int(idx.min())],
            "max": [int(idx.max())]
        })

        primitives.append({
            "attributes": {
                "POSITION": v_acc_idx,
                "NORMAL": n_acc_idx
            },
            "indices": idx_acc_idx,
            "material": mat_id
        })

    # Materiais PBR Metálicos
    materials = [
        {
            "name": "Gold_Kapton_MLI",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.95, 0.75, 0.15, 1.0],
                "metallicFactor": 0.95,
                "roughnessFactor": 0.20
            }
        },
        {
            "name": "Solar_Panels_GaAs",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.05, 0.12, 0.38, 1.0],
                "metallicFactor": 0.85,
                "roughnessFactor": 0.25
            }
        },
        {
            "name": "Silver_Radiators_Structure",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.85, 0.88, 0.92, 1.0],
                "metallicFactor": 0.90,
                "roughnessFactor": 0.15
            }
        },
        {
            "name": "Nav_Antenna_Nadir",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.92, 0.92, 0.92, 1.0],
                "metallicFactor": 0.80,
                "roughnessFactor": 0.30
            }
        },
        {
            "name": "Thruster_Titanium",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.22, 0.22, 0.25, 1.0],
                "metallicFactor": 0.85,
                "roughnessFactor": 0.40
            }
        }
    ]

    gltf_dict = {
        "asset": {"version": "2.0", "generator": "RPS-BR Procedural Small GEO Generator"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "RPS_Small_GEO_Satellite"}],
        "meshes": [{"name": "Satellite_Mesh", "primitives": primitives}],
        "materials": materials,
        "buffers": [{"byteLength": len(buffer_bytes)}],
        "bufferViews": buffer_views,
        "accessors": accessors
    }

    json_str = json.dumps(gltf_dict, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    # Pad JSON para múltiplo de 4
    while len(json_bytes) % 4 != 0:
        json_bytes += b' '

    # Estrutura GLB: Header (12 bytes) + Chunk 0 JSON + Chunk 1 BIN
    glb_header = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(json_bytes) + 8 + len(buffer_bytes))
    chunk0_header = struct.pack('<II', len(json_bytes), 0x4E4F534A) # 'JSON'
    chunk1_header = struct.pack('<II', len(buffer_bytes), 0x004E4942) # 'BIN\0'

    with open(output_path, 'wb') as f:
        f.write(glb_header)
        f.write(chunk0_header)
        f.write(json_bytes)
        f.write(chunk1_header)
        f.write(buffer_bytes)

    print(f"🛰️ [MeshGenerator] Malha 3D PBR do satélite gerada com sucesso: {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")

if __name__ == '__main__':
    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'meshes', 'satellite_navsat.glb')
    generate_satellite_glb(default_out)
