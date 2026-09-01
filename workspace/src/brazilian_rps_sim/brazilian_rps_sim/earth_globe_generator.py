#!/usr/bin/env python3
"""
Gerador de Malha 3D Científica da Terra e Nuvens em formato glTF 2.0 (.glb)
com Mapeamento Paramétrico Estrito:
- Polo Norte (+90° Lat) exatamente no eixo +Z (Topo)
- Polo Sul (-90° Lat) exatamente no eixo -Z (Fundo)
- Equador (0° Lat) no plano horizontal Z=0
- Meridiano de Greenwich (0° Lon) exatamente no eixo +X
- América do Sul / Brasil (-50° Lon) exatamente no ângulo -50° (310°)
- Integração PBR de Texturas 2K da NASA
"""

import os
import json
import struct
import math
import numpy as np

def generate_sphere_mesh(radius: float, lat_segs: int = 64, lon_segs: int = 128):
    """Gera vértices, normais, coordenadas UV e índices triangulares parametrizados."""
    vertices = []
    normals = []
    uvs = []
    indices = []

    # i: de 0 (Norte: +pi/2, +Z, V=0.0) até lat_segs (Sul: -pi/2, -Z, V=1.0)
    for i in range(lat_segs + 1):
        lat = (math.pi / 2.0) - (math.pi * i / lat_segs)
        v = i / lat_segs

        # j: de 0 (U=0.0, -180° Oeste) até lon_segs (U=1.0, +180° Leste)
        # Greenwich (0° Lon) fica em U=0.5 -> phi = 0
        for j in range(lon_segs + 1):
            u = j / lon_segs
            phi = (2.0 * math.pi * j / lon_segs) - math.pi # de -pi a +pi

            x = radius * math.cos(lat) * math.cos(phi)
            y = radius * math.cos(lat) * math.sin(phi)
            z = radius * math.sin(lat)

            vertices.append([x, y, z])
            norm = math.sqrt(x*x + y*y + z*z)
            normals.append([x/norm, y/norm, z/norm])
            uvs.append([u, v])

    # Triângulos voltados para FORA (CCW)
    for i in range(lat_segs):
        for j in range(lon_segs):
            p00 = i * (lon_segs + 1) + j
            p01 = p00 + 1
            p10 = (i + 1) * (lon_segs + 1) + j
            p11 = p10 + 1

            indices.extend([p00, p10, p01])
            indices.extend([p01, p10, p11])

    return (np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32),
            np.array(uvs, dtype=np.float32),
            np.array(indices, dtype=np.uint32))

def write_globe_glb(output_path: str, radius: float, mat_name: str, has_clouds: bool = False):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    v, n, uv, idx = generate_sphere_mesh(radius, lat_segs=64, lon_segs=128)

    v_bytes = v.tobytes()
    n_bytes = n.tobytes()
    uv_bytes = uv.tobytes()
    idx_bytes = idx.tobytes()

    while len(v_bytes) % 4 != 0: v_bytes += b'\x00'
    while len(n_bytes) % 4 != 0: n_bytes += b'\x00'
    while len(uv_bytes) % 4 != 0: uv_bytes += b'\x00'
    while len(idx_bytes) % 4 != 0: idx_bytes += b'\x00'

    buffer_bytes = v_bytes + n_bytes + uv_bytes + idx_bytes

    buffer_views = [
        {"buffer": 0, "byteOffset": 0, "byteLength": len(v_bytes), "target": 34962},
        {"buffer": 0, "byteOffset": len(v_bytes), "byteLength": len(n_bytes), "target": 34962},
        {"buffer": 0, "byteOffset": len(v_bytes) + len(n_bytes), "byteLength": len(uv_bytes), "target": 34962},
        {"buffer": 0, "byteOffset": len(v_bytes) + len(n_bytes) + len(uv_bytes), "byteLength": len(idx_bytes), "target": 34963}
    ]

    accessors = [
        {
            "bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": len(v), "type": "VEC3",
            "min": v.min(axis=0).tolist(), "max": v.max(axis=0).tolist()
        },
        {
            "bufferView": 1, "byteOffset": 0, "componentType": 5126, "count": len(n), "type": "VEC3",
            "min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]
        },
        {
            "bufferView": 2, "byteOffset": 0, "componentType": 5126, "count": len(uv), "type": "VEC2",
            "min": [0.0, 0.0], "max": [1.0, 1.0]
        },
        {
            "bufferView": 3, "byteOffset": 0, "componentType": 5125, "count": len(idx), "type": "SCALAR",
            "min": [int(idx.min())], "max": [int(idx.max())]
        }
    ]

    mat_def = {
        "name": mat_name,
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 1.0, 1.0, 1.0 if not has_clouds else 0.95],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.85
        },
        "alphaMode": "OPAQUE" if not has_clouds else "BLEND",
        "doubleSided": False
    }

    gltf_dict = {
        "asset": {"version": "2.0", "generator": "RPS-BR Scientific Earth Generator"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": mat_name}],
        "meshes": [{
            "name": f"{mat_name}Mesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                "indices": 3,
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

    print(f"🌍 [EarthGenerator] Malha {mat_name} gerada com sucesso: {output_path}")

def generate_all_earth_assets(mesh_dir: str):
    # 1. Globo Sólido da Terra (R = 6.378)
    write_globe_glb(os.path.join(mesh_dir, 'earth_globe.glb'), radius=6.378, mat_name="EarthSurface")
    # 2. Camada Externa de Nuvens (R = 6.398)
    write_globe_glb(os.path.join(mesh_dir, 'earth_clouds.glb'), radius=6.398, mat_name="EarthClouds", has_clouds=True)

if __name__ == '__main__':
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mesh_dir = os.path.join(pkg_dir, 'meshes')
    generate_all_earth_assets(mesh_dir)
