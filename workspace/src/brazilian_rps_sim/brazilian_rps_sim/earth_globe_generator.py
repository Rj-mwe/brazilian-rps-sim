#!/usr/bin/env python3
"""
Gera o modelo 3D hiper-realista da Terra em glTF 2.0 PBR utilizando as texturas
oficiais de domínio público da NASA (Blue Marble + Night Lights).

Calibração Cartográfica:
- Raio: 6.378137 unidades (6.378 km)
- Longitude 0° (Greenwich): Rigorosamente alinhado ao eixo +X (U = 0.5)
- Longitude 50°W (Brasília): Posição angular exata para ancoragem do satélite GEO
"""

import os
import json
import struct
import base64
import urllib.request
import math
import numpy as np
from PIL import Image

def download_nasa_textures(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    day_path = os.path.join(target_dir, "earth_day_albedo_2k.jpg")
    night_path = os.path.join(target_dir, "earth_night_lights_2k.jpg")

    url_day = "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_2048.jpg"
    url_night = "https://eoimages.gsfc.nasa.gov/images/imagerecords/55000/55167/earth_lights_lrg.jpg"

    if not os.path.exists(day_path):
        print(f"📥 [NASA] Baixando textura diurna Blue Marble (2048x1024)...")
        urllib.request.urlretrieve(url_day, day_path)
        print(f"✅ Textura diurna salva em: {day_path}")

    if not os.path.exists(night_path):
        print(f"📥 [NASA] Baixando textura noturna Earth at Night (City Lights)...")
        urllib.request.urlretrieve(url_night, night_path)
        # Redimensiona para exatamente 2048x1024 para casar com a textura diurna
        img_night = Image.open(night_path)
        img_night_resized = img_night.resize((2048, 1024), Image.Resampling.LANCZOS)
        img_night_resized.save(night_path, "JPEG", quality=90)
        print(f"✅ Textura noturna calibrada em: {night_path}")

    return day_path, night_path

def generate_earth_sphere_gltf(output_gltf_path: str, day_img_path: str, night_img_path: str,
                               radius: float = 6.378137, lat_segs: int = 64, lon_segs: int = 128):
    os.makedirs(os.path.dirname(output_gltf_path), exist_ok=True)

    vertices = []
    normals = []
    uvs = []
    indices = []

    # Gera a esfera com mapeamento Equiretangular (WGS84 / Plate Carrée)
    # Latitude: -90° (Polo Sul) até +90° (Polo Norte)
    # Longitude: -180° até +180°
    for i in range(lat_segs + 1):
        lat = -math.pi / 2.0 + (math.pi * i / lat_segs) # [-pi/2, +pi/2]
        v = (lat + math.pi / 2.0) / math.pi             # [0, 1] de Sul para Norte

        for j in range(lon_segs + 1):
            lon = -math.pi + (2.0 * math.pi * j / lon_segs) # [-pi, +pi]
            # Longitude 0° (Greenwich) ocorre em j = lon_segs / 2 -> u = 0.5 -> vetor (+X, 0, 0)
            u = 1.0 - (j / lon_segs) # Inverte horizontal para orientação natural no Gazebo

            x = radius * math.cos(lat) * math.cos(lon)
            y = radius * math.cos(lat) * math.sin(lon)
            z = radius * math.sin(lat)

            vertices.append([x, y, z])
            norm = math.sqrt(x*x + y*y + z*z)
            normals.append([x/norm, y/norm, z/norm])
            uvs.append([u, v])

    # Gera triângulos
    for i in range(lat_segs):
        for j in range(lon_segs):
            first = i * (lon_segs + 1) + j
            second = first + lon_segs + 1

            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])

    # Empacota buffers binários
    vertex_bytes = b"".join(struct.pack("<fff", *v) for v in vertices)
    normal_bytes = b"".join(struct.pack("<fff", *n) for n in normals)
    uv_bytes = b"".join(struct.pack("<ff", *uv) for uv in uvs)
    index_bytes = b"".join(struct.pack("<I", idx) for idx in indices)

    def pad4(b):
        return b + b"\x00" * ((4 - (len(b) % 4)) % 4)

    v_padded = pad4(vertex_bytes)
    n_padded = pad4(normal_bytes)
    uv_padded = pad4(uv_bytes)
    idx_padded = pad4(index_bytes)

    total_bin = v_padded + n_padded + uv_padded + idx_padded
    b64_str = base64.b64encode(total_bin).decode('ascii')
    uri_bin = f"data:application/octet-stream;base64,{b64_str}"

    with open(day_img_path, "rb") as f_day:
        b64_day = base64.b64encode(f_day.read()).decode('ascii')
    uri_day = f"data:image/jpeg;base64,{b64_day}"

    with open(night_img_path, "rb") as f_night:
        b64_night = base64.b64encode(f_night.read()).decode('ascii')
    uri_night = f"data:image/jpeg;base64,{b64_night}"

    min_v = [min(v[k] for v in vertices) for k in range(3)]
    max_v = [max(v[k] for v in vertices) for k in range(3)]

    offset_v = 0
    len_v = len(vertex_bytes)

    offset_n = len(v_padded)
    len_n = len(normal_bytes)

    offset_uv = offset_n + len(n_padded)
    len_uv = len(uv_bytes)

    offset_idx = offset_uv + len(uv_padded)
    len_idx = len(index_bytes)

    gltf_doc = {
        "asset": {
            "version": "2.0",
            "generator": "RPS-BR NASA Blue Marble Earth Generator"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "EarthGlobeNode"}],
        "meshes": [{
            "name": "EarthGlobeMesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 3,
                "material": 0
            }]
        }],
        "materials": [{
            "name": "EarthNasaPbrMaterial",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.05,
                "roughnessFactor": 0.85
            },
            "emissiveTexture": {"index": 1},
            "emissiveFactor": [0.35, 0.35, 0.35],
            "doubleSided": False
        }],
        "textures": [
            {"sampler": 0, "source": 0},
            {"sampler": 0, "source": 1}
        ],
        "images": [
            {"uri": uri_day, "name": "NasaBlueMarbleAlbedo"},
            {"uri": uri_night, "name": "NasaEarthAtNightLights"}
        ],
        "samplers": [{
            "magFilter": 9729,
            "minFilter": 9987,
            "wrapS": 10497,
            "wrapT": 33071
        }],
        "accessors": [
            {
                "bufferView": 0, "byteOffset": 0,
                "componentType": 5126, "count": len(vertices),
                "type": "VEC3", "max": max_v, "min": min_v
            },
            {
                "bufferView": 1, "byteOffset": 0,
                "componentType": 5126, "count": len(normals),
                "type": "VEC3", "max": [1.0, 1.0, 1.0], "min": [-1.0, -1.0, -1.0]
            },
            {
                "bufferView": 2, "byteOffset": 0,
                "componentType": 5126, "count": len(uvs),
                "type": "VEC2", "max": [1.0, 1.0], "min": [0.0, 0.0]
            },
            {
                "bufferView": 3, "byteOffset": 0,
                "componentType": 5125, "count": len(indices),
                "type": "SCALAR", "max": [len(vertices) - 1], "min": [0]
            }
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": offset_v, "byteLength": len_v, "target": 34962},
            {"buffer": 0, "byteOffset": offset_n, "byteLength": len_n, "target": 34962},
            {"buffer": 0, "byteOffset": offset_uv, "byteLength": len_uv, "target": 34962},
            {"buffer": 0, "byteOffset": offset_idx, "byteLength": len_idx, "target": 34963}
        ],
        "buffers": [{
            "byteLength": len(total_bin),
            "uri": uri_bin
        }]
    }

    with open(output_gltf_path, "w") as f:
        json.dump(gltf_doc, f, indent=2)

    print(f"🌍 [NASA Blue Marble] Modelo glTF 2.0 da Terra gerado com sucesso: {output_gltf_path}")

def main():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_tex_dir = os.path.join(pkg_dir, "materials", "textures")
    output_gltf = os.path.join(pkg_dir, "meshes", "earth_globe.gltf")

    day_path, night_path = download_nasa_textures(target_tex_dir)
    generate_earth_sphere_gltf(output_gltf, day_path, night_path)

if __name__ == '__main__':
    main()
