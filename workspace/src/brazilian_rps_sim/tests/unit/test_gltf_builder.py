#!/usr/bin/env python3
"""
Testes Unitários para o GltfMeshBuilder (Builder Pattern para glTF/GLB)
Valida a geração de buffers binários, alinhamento de 4 bytes, accessors e PBR materials.
"""

import os
import struct
import numpy as np
import pytest
from brazilian_rps_sim.gltf_builder import GltfMeshBuilder

def test_gltf_builder_triangle_glb(tmp_path):
    """Testa a geração de um triângulo básico em GLB binário."""
    positions = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    normals = [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]
    indices = [0, 1, 2]

    output_glb = str(tmp_path / "triangle.glb")
    
    builder = GltfMeshBuilder(name="TriangleTest")
    builder.set_positions(positions)\
           .set_normals(normals)\
           .set_indices(indices)\
           .set_pbr_material(
               name="TestMat",
               base_color_rgba=(1.0, 0.5, 0.2, 1.0),
               emissive_intensity=0.8,
               alpha_mode="OPAQUE"
           )\
           .save_glb(output_glb)

    assert os.path.exists(output_glb)
    file_size = os.path.getsize(output_glb)
    assert file_size > 0
    assert file_size % 4 == 0, "O arquivo GLB deve ser múltiplo exato de 4 bytes"

    # Validação do cabeçalho GLB de 12 bytes
    with open(output_glb, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF"
        assert version == 2
        assert length == file_size

def test_gltf_builder_gltf_json_structure(tmp_path):
    """Testa a árvore JSON e o payload Base64 para exportação .gltf."""
    positions = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0]], dtype=np.float32)
    indices = np.array([0, 1, 2], dtype=np.uint32)

    output_gltf = str(tmp_path / "test.gltf")
    builder = GltfMeshBuilder(name="JsonTest")
    builder.set_positions(positions)\
           .set_indices(indices)\
           .save_gltf(output_gltf, embedded_base64=True)

    assert os.path.exists(output_gltf)
    with open(output_gltf, "r", encoding="utf-8") as f:
        import json
        doc = json.load(f)
        assert doc["asset"]["version"] == "2.0"
        assert len(doc["meshes"]) == 1
        assert doc["accessors"][0]["min"] == [0.0, 0.0, 0.0]
        assert doc["accessors"][0]["max"] == [10.0, 10.0, 0.0]
        assert doc["buffers"][0]["uri"].startswith("data:application/octet-stream;base64,")

def test_gltf_builder_missing_positions_raises():
    """Garante que a falta de posições lance exceção informativa."""
    builder = GltfMeshBuilder()
    with pytest.raises(ValueError, match="positions"):
        builder.build_gltf_dict()
