#!/usr/bin/env python3
"""
Gera malhas orbitais em formato glTF 2.0 (.gltf) padrão da indústria,
com materiais PBR (baseColorFactor e emissiveFactor) incorporados no arquivo.
"""

import os
import json
import struct
import base64
import numpy as np

def generate_orbit_gltf(output_path: str, radius: float, inclination_deg: float, thickness: float,
                        r: float, g: float, b: float, alpha: float = 0.8, num_pts: int = 480):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    theta = np.linspace(0, 2 * np.pi, num_pts, endpoint=False)
    inc = np.radians(inclination_deg)

    pts = []
    for th in theta:
        x = radius * np.cos(th)
        y = radius * np.sin(th) * np.cos(inc)
        z = radius * np.sin(th) * np.sin(inc)
        pts.append(np.array([x, y, z]))

    vertices = []
    for i, p in enumerate(pts):
        p_next = pts[(i + 1) % len(pts)]
        tangent = p_next - p
        tangent = tangent / np.linalg.norm(tangent)
        up = np.array([0, 0, 1]) if abs(tangent[2]) < 0.9 else np.array([1, 0, 0])
        normal = np.cross(tangent, up)
        normal = normal / np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)

        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            offset = thickness * (np.cos(angle) * normal + np.sin(angle) * binormal)
            v = p + offset
            vertices.append(v)

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
            # Dois triângulos por quad
            indices.extend([v1, v2, v3, v1, v3, v4])

    # Empacota dados binários
    vertex_data = b""
    min_pos = [float('inf')] * 3
    max_pos = [float('-inf')] * 3
    for v in vertices:
        vertex_data += struct.pack("<fff", float(v[0]), float(v[1]), float(v[2]))
        for k in range(3):
            min_pos[k] = min(min_pos[k], float(v[k]))
            max_pos[k] = max(max_pos[k], float(v[k]))

    index_data = b""
    for idx in indices:
        index_data += struct.pack("<I", int(idx))

    # Pad para alinhamento de 4 bytes
    v_len = len(vertex_data)
    pad = (4 - (v_len % 4)) % 4
    vertex_data += b"\x00" * pad
    v_len_padded = len(vertex_data)

    buffer_bytes = vertex_data + index_data
    b64_str = base64.b64encode(buffer_bytes).decode('ascii')
    uri = f"data:application/octet-stream;base64,{b64_str}"

    gltf_doc = {
        "asset": {
            "version": "2.0",
            "generator": "RPS-BR Astrodynamics glTF Generator"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "OrbitRingNode"}],
        "meshes": [{
            "name": "OrbitRingMesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0
                },
                "indices": 1,
                "material": 0
            }]
        }],
        "materials": [{
            "name": "OrbitPbrMaterial",
            "pbrMetallicRoughness": {
                "baseColorFactor": [float(r), float(g), float(b), float(alpha)],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.8
            },
            "emissiveFactor": [float(r * 0.9), float(g * 0.9), float(b * 0.9)],
            "alphaMode": "OPAQUE",
            "doubleSided": True
        }],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126, # FLOAT
                "count": len(vertices),
                "type": "VEC3",
                "max": max_pos,
                "min": min_pos
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5125, # UNSIGNED_INT
                "count": len(indices),
                "type": "SCALAR",
                "max": [len(vertices) - 1],
                "min": [0]
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": v_len,
                "target": 34962 # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": v_len_padded,
                "byteLength": len(index_data),
                "target": 34963 # ELEMENT_ARRAY_BUFFER
            }
        ],
        "buffers": [{
            "byteLength": len(buffer_bytes),
            "uri": uri
        }]
    }

    with open(output_path, 'w') as f:
        json.dump(gltf_doc, f, indent=2)

    print(f"✅ Malha glTF 2.0 gerada com sucesso: {output_path} (Cor RGB: {r},{g},{b})")

def main():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mesh_dir = os.path.join(pkg_dir, "meshes")

    # 1. Órbita da Terra: DOURADO VIBRANTE (R=1.0, G=0.75, B=0.1)
    generate_orbit_gltf(
        output_path=os.path.join(mesh_dir, "earth_orbit_ring.gltf"),
        radius=1200.0,
        inclination_deg=0.0,
        thickness=0.10,
        r=1.0, g=0.75, b=0.1, alpha=0.7,
        num_pts=720
    )

    # 2. Órbita da Lua: CIANO CELESTIAL VIBRANTE (R=0.0, G=0.85, B=1.0)
    generate_orbit_gltf(
        output_path=os.path.join(mesh_dir, "moon_orbit_ring.gltf"),
        radius=384.4,
        inclination_deg=5.145,
        thickness=0.03,
        r=0.0, g=0.85, b=1.0, alpha=0.7,
        num_pts=480
    )

if __name__ == '__main__':
    main()
