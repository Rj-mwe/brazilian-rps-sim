#!/usr/bin/env python3
"""
Gera malhas 3D em formato glTF 2.0 PBR para as órbitas da constelação brasileira (GEO e IGSO).
"""

import sys
import os
import json
import struct
import base64
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from brazilian_rps_sim.astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        SIDEREAL_DAY
    )
except ImportError:
    from astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        SIDEREAL_DAY
    )

def generate_orbit_gltf_from_points(output_path: str, pts: list, thickness: float, r: float, g: float, b: float, alpha: float = 1.0):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    num_pts = len(pts)

    vertices = []
    for i, p in enumerate(pts):
        p_next = pts[(i + 1) % len(pts)]
        tangent = p_next - p
        norm = np.linalg.norm(tangent)
        tangent = tangent / norm if norm > 1e-6 else np.array([1, 0, 0])
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
            indices.extend([v1, v2, v3, v1, v3, v4])

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

    v_len = len(vertex_data)
    pad = (4 - (v_len % 4)) % 4
    vertex_data += b"\x00" * pad
    v_len_padded = len(vertex_data)

    buffer_bytes = vertex_data + index_data
    b64_str = base64.b64encode(buffer_bytes).decode('ascii')
    uri = f"data:application/octet-stream;base64,{b64_str}"

    gltf_doc = {
        "asset": {"version": "2.0", "generator": "RPS-BR Constellation Mesh Generator"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "ConstellationOrbitNode"}],
        "meshes": [{
            "name": "ConstellationOrbitMesh",
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "material": 0
            }]
        }],
        "materials": [{
            "name": "ConstellationPbrMaterial",
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
                "componentType": 5126,
                "count": len(vertices),
                "type": "VEC3",
                "max": max_pos,
                "min": min_pos
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5125,
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
                "target": 34962
            },
            {
                "buffer": 0,
                "byteOffset": v_len_padded,
                "byteLength": len(index_data),
                "target": 34963
            }
        ],
        "buffers": [{
            "byteLength": len(buffer_bytes),
            "uri": uri
        }]
    }

    with open(output_path, 'w') as f:
        json.dump(gltf_doc, f, indent=2)

    print(f"✅ Malha glTF 2.0 salva: {output_path} (Cor RGB: {r},{g},{b})")

def generate_constellation_meshes(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    constellation = get_brazilian_rps_constellation()
    num_pts = 360
    t_seconds = np.linspace(0, SIDEREAL_DAY, num_pts, endpoint=False)
    scale = 1.0 / 1000.0 # 1 unidade = 1000 km

    for sat in constellation:
        if sat.sat_type == "GEO":
            pts = [eci_to_ecef(propagate_orbit_eci(sat, t), t) * scale for t in t_seconds]
            generate_orbit_gltf_from_points(
                output_path=os.path.join(output_dir, "orbit_geo.gltf"),
                pts=pts,
                thickness=0.15,
                r=1.0, g=0.75, b=0.1, alpha=1.0
            )
        elif sat.sat_type == "IGSO":
            pts = [eci_to_ecef(propagate_orbit_eci(sat, t), t) * scale for t in t_seconds]
            generate_orbit_gltf_from_points(
                output_path=os.path.join(output_dir, "orbit_igso.gltf"),
                pts=pts,
                thickness=0.15,
                r=0.0, g=0.85, b=1.0, alpha=1.0
            )

if __name__ == '__main__':
    meshes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "meshes")
    generate_constellation_meshes(meshes_dir)
