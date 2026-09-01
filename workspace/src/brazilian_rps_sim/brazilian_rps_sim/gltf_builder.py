#!/usr/bin/env python3
"""
Design Pattern: Builder para Malhas 3D Procedurais glTF 2.0 (.gltf) e Binary glTF (.glb).

Responsabilidade Única:
- Encapsular a complexidade de alinhamento binário de 4 bytes, packing em little-endian,
  estruturação de Accessors, BufferViews, Primitives, Nodes e Materials PBR.
- Fornecer uma API fluente (Method Chaining) e limpa para todos os geradores procedurais.
"""

import os
import json
import struct
import base64
from typing import List, Tuple, Optional, Union
import numpy as np


class GltfMeshBuilder:
    """Builder fluente para construção e exportação de malhas glTF 2.0 e GLB."""

    def __init__(self, name: str = "ProceduralMesh", generator_tag: str = "RPS-BR glTF Builder"):
        self.name = name
        self.generator_tag = generator_tag
        
        self.positions: Optional[np.ndarray] = None
        self.normals: Optional[np.ndarray] = None
        self.uvs: Optional[np.ndarray] = None
        self.indices: Optional[np.ndarray] = None
        
        self.material_def: Optional[dict] = None

    def set_positions(self, positions: Union[np.ndarray, List[List[float]]]) -> 'GltfMeshBuilder':
        """Define os vértices 3D (VEC3 - Float32)."""
        self.positions = np.array(positions, dtype=np.float32)
        return self

    def set_normals(self, normals: Union[np.ndarray, List[List[float]]]) -> 'GltfMeshBuilder':
        """Define os vetores normais 3D (VEC3 - Float32)."""
        self.normals = np.array(normals, dtype=np.float32)
        return self

    def set_uvs(self, uvs: Union[np.ndarray, List[List[float]]]) -> 'GltfMeshBuilder':
        """Define as coordenadas de mapeamento de textura 2D (VEC2 - Float32)."""
        self.uvs = np.array(uvs, dtype=np.float32)
        return self

    def set_indices(self, indices: Union[np.ndarray, List[int]]) -> 'GltfMeshBuilder':
        """Define os índices triangulares (SCALAR - UInt32)."""
        self.indices = np.array(indices, dtype=np.uint32)
        return self

    def set_pbr_material(
        self,
        name: str = "PbrMaterial",
        base_color_rgba: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        metallic: float = 0.0,
        roughness: float = 0.5,
        emissive_rgb: Optional[Tuple[float, float, float]] = None,
        emissive_intensity: float = 0.0,
        alpha_mode: str = "OPAQUE",
        double_sided: bool = True
    ) -> 'GltfMeshBuilder':
        """Define o material PBR (Physically Based Rendering) da malha."""
        r, g, b, a = base_color_rgba
        
        if emissive_rgb is not None:
            er, eg, eb = emissive_rgb
        elif emissive_intensity > 0.0:
            er, eg, eb = r * emissive_intensity, g * emissive_intensity, b * emissive_intensity
        else:
            er, eg, eb = 0.0, 0.0, 0.0

        self.material_def = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [float(r), float(g), float(b), float(a)],
                "metallicFactor": float(metallic),
                "roughnessFactor": float(roughness)
            },
            "emissiveFactor": [float(er), float(eg), float(eb)],
            "alphaMode": alpha_mode,
            "doubleSided": double_sided
        }
        return self

    def _pack_binary_buffers(self) -> Tuple[List[dict], List[dict], bytes, dict]:
        """Empacota os atributos geométricos nos buffers binários alinhados a 4 bytes."""
        if self.positions is None:
            raise ValueError("GltfMeshBuilder: 'positions' (vértices) são obrigatórios.")

        buffer_views = []
        accessors = []
        raw_chunks = []
        primitive_attributes = {}
        byte_offset = 0

        def append_chunk(data_bytes: bytes, target: int, count: int, comp_type: int,
                         type_str: str, min_val, max_val) -> int:
            nonlocal byte_offset
            # Alinhamento obrigatório do glTF a 4 bytes
            pad = (4 - (len(data_bytes) % 4)) % 4
            aligned_data = data_bytes + (b'\x00' * pad)
            chunk_len = len(aligned_data)
            
            raw_chunks.append(aligned_data)
            
            bv_idx = len(buffer_views)
            buffer_views.append({
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(data_bytes),
                "target": target
            })
            
            acc_idx = len(accessors)
            accessors.append({
                "bufferView": bv_idx,
                "byteOffset": 0,
                "componentType": comp_type,
                "count": count,
                "type": type_str,
                "min": min_val,
                "max": max_val
            })
            
            byte_offset += chunk_len
            return acc_idx

        # 1. Posições (VEC3 Float32)
        pos_bytes = self.positions.tobytes()
        acc_pos = append_chunk(
            pos_bytes,
            target=34962, # ARRAY_BUFFER
            count=len(self.positions),
            comp_type=5126, # FLOAT
            type_str="VEC3",
            min_val=self.positions.min(axis=0).tolist(),
            max_val=self.positions.max(axis=0).tolist()
        )
        primitive_attributes["POSITION"] = acc_pos

        # 2. Normais (VEC3 Float32 - Opcional)
        if self.normals is not None and len(self.normals) > 0:
            norm_bytes = self.normals.tobytes()
            acc_norm = append_chunk(
                norm_bytes,
                target=34962,
                count=len(self.normals),
                comp_type=5126,
                type_str="VEC3",
                min_val=[-1.0, -1.0, -1.0],
                max_val=[1.0, 1.0, 1.0]
            )
            primitive_attributes["NORMAL"] = acc_norm

        # 3. Coordenadas UV (VEC2 Float32 - Opcional)
        if self.uvs is not None and len(self.uvs) > 0:
            uv_bytes = self.uvs.tobytes()
            acc_uv = append_chunk(
                uv_bytes,
                target=34962,
                count=len(self.uvs),
                comp_type=5126,
                type_str="VEC2",
                min_val=[0.0, 0.0],
                max_val=[1.0, 1.0]
            )
            primitive_attributes["TEXCOORD_0"] = acc_uv

        # 4. Índices Triangulares (SCALAR UInt32 - Opcional)
        indices_acc_idx = None
        if self.indices is not None and len(self.indices) > 0:
            idx_bytes = self.indices.tobytes()
            indices_acc_idx = append_chunk(
                idx_bytes,
                target=34963, # ELEMENT_ARRAY_BUFFER
                count=len(self.indices),
                comp_type=5125, # UNSIGNED_INT
                type_str="SCALAR",
                min_val=[int(self.indices.min())],
                max_val=[int(self.indices.max())]
            )

        full_bin_buffer = b"".join(raw_chunks)
        return buffer_views, accessors, full_bin_buffer, primitive_attributes

    def build_gltf_dict(self, embedded_base64: bool = False) -> Tuple[dict, bytes]:
        """Constrói a árvore de nós do glTF 2.0 e retorna o JSON estruturado e o buffer binário."""
        buffer_views, accessors, bin_buffer, primitive_attrs = self._pack_binary_buffers()

        primitive = {
            "attributes": primitive_attrs
        }
        if self.indices is not None and len(self.indices) > 0:
            primitive["indices"] = len(accessors) - 1 # Último acessor empacotado

        if self.material_def is not None:
            primitive["material"] = 0

        buffer_entry = {"byteLength": len(bin_buffer)}
        if embedded_base64:
            b64_str = base64.b64encode(bin_buffer).decode('ascii')
            buffer_entry["uri"] = f"data:application/octet-stream;base64,{b64_str}"

        gltf_doc = {
            "asset": {
                "version": "2.0",
                "generator": self.generator_tag
            },
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": f"{self.name}Node"}],
            "meshes": [{
                "name": f"{self.name}Mesh",
                "primitives": [primitive]
            }],
            "buffers": [buffer_entry],
            "bufferViews": buffer_views,
            "accessors": accessors
        }

        if self.material_def is not None:
            gltf_doc["materials"] = [self.material_def]

        return gltf_doc, bin_buffer

    def save_glb(self, file_path: str) -> None:
        """Exporta o modelo no formato binário autossuficiente GLB (Container glTF 2.0)."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        gltf_doc, bin_buffer = self.build_gltf_dict(embedded_base64=False)

        json_bytes = json.dumps(gltf_doc, separators=(',', ':')).encode('utf-8')
        json_pad = (4 - (len(json_bytes) % 4)) % 4
        json_bytes_padded = json_bytes + (b' ' * json_pad)

        total_length = 12 + 8 + len(json_bytes_padded) + 8 + len(bin_buffer)

        # Cabeçalho GLB de 12 bytes
        header = struct.pack('<4sII', b'glTF', 2, total_length)
        # Chunk 0: JSON
        chunk0_header = struct.pack('<II', len(json_bytes_padded), 0x4E4F534A)
        # Chunk 1: BIN
        chunk1_header = struct.pack('<II', len(bin_buffer), 0x004E4942)

        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(chunk0_header)
            f.write(json_bytes_padded)
            f.write(chunk1_header)
            f.write(bin_buffer)

    def save_gltf(self, file_path: str, embedded_base64: bool = True) -> None:
        """Exporta o modelo no formato JSON glTF 2.0 (com payload binário Base64 embutido)."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        gltf_doc, _ = self.build_gltf_dict(embedded_base64=embedded_base64)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(gltf_doc, f, indent=2)
