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
import math
from typing import List, Tuple, Optional, Union
import numpy as np


class GltfPrimitiveDef:
    """Representa uma primitiva geométrica do glTF com material próprio."""
    def __init__(
        self,
        positions: Optional[Union[np.ndarray, List[List[float]]]] = None,
        normals: Optional[Union[np.ndarray, List[List[float]]]] = None,
        uvs: Optional[Union[np.ndarray, List[List[float]]]] = None,
        indices: Optional[Union[np.ndarray, List[int]]] = None,
        material_def: Optional[dict] = None
    ):
        self.positions = np.array(positions, dtype=np.float32) if positions is not None else None
        self.normals = np.array(normals, dtype=np.float32) if normals is not None and len(normals) > 0 else None
        self.uvs = np.array(uvs, dtype=np.float32) if uvs is not None and len(uvs) > 0 else None
        self.indices = np.array(indices, dtype=np.uint32) if indices is not None and len(indices) > 0 else None
        self.material_def = material_def


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

        self.primitives: List[GltfPrimitiveDef] = []

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

    def add_primitive(
        self,
        positions: Union[np.ndarray, List[List[float]]],
        normals: Optional[Union[np.ndarray, List[List[float]]]] = None,
        uvs: Optional[Union[np.ndarray, List[List[float]]]] = None,
        indices: Optional[Union[np.ndarray, List[int]]] = None,
        material_name: str = "PbrMaterial",
        base_color_rgba: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        metallic: float = 0.0,
        roughness: float = 0.5,
        emissive_rgb: Optional[Tuple[float, float, float]] = None,
        emissive_intensity: float = 0.0,
        alpha_mode: str = "OPAQUE",
        double_sided: bool = True
    ) -> 'GltfMeshBuilder':
        """Adiciona uma primitiva com material PBR independente (Multi-material)."""
        r, g, b, a = base_color_rgba
        if emissive_rgb is not None:
            er, eg, eb = emissive_rgb
        elif emissive_intensity > 0.0:
            er, eg, eb = r * emissive_intensity, g * emissive_intensity, b * emissive_intensity
        else:
            er, eg, eb = 0.0, 0.0, 0.0

        mat_def = {
            "name": material_name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [float(r), float(g), float(b), float(a)],
                "metallicFactor": float(metallic),
                "roughnessFactor": float(roughness)
            },
            "emissiveFactor": [float(er), float(eg), float(eb)],
            "alphaMode": alpha_mode,
            "doubleSided": double_sided
        }
        self.primitives.append(GltfPrimitiveDef(positions, normals, uvs, indices, mat_def))
        return self

    def _pack_binary_buffers(self) -> Tuple[List[dict], List[dict], bytes, List[dict], List[dict]]:
        """Empacota os atributos geométricos nos buffers binários alinhados a 4 bytes."""
        prim_list = self.primitives if self.primitives else [
            GltfPrimitiveDef(self.positions, self.normals, self.uvs, self.indices, self.material_def)
        ]

        if not prim_list or prim_list[0].positions is None:
            raise ValueError("GltfMeshBuilder: 'positions' (vértices) são obrigatórios.")

        buffer_views = []
        accessors = []
        raw_chunks = []
        materials = []
        gltf_primitives = []
        byte_offset = 0

        def append_chunk(data_bytes: bytes, target: int, count: int, comp_type: int,
                          type_str: str, min_val, max_val) -> int:
            nonlocal byte_offset
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

        for prim in prim_list:
            prim_attrs = {}

            # POSITION
            pos_bytes = prim.positions.tobytes()
            acc_pos = append_chunk(
                pos_bytes,
                target=34962,
                count=len(prim.positions),
                comp_type=5126,
                type_str="VEC3",
                min_val=prim.positions.min(axis=0).tolist(),
                max_val=prim.positions.max(axis=0).tolist()
            )
            prim_attrs["POSITION"] = acc_pos

            # NORMAL
            if prim.normals is not None and len(prim.normals) > 0:
                norm_bytes = prim.normals.tobytes()
                acc_norm = append_chunk(
                    norm_bytes,
                    target=34962,
                    count=len(prim.normals),
                    comp_type=5126,
                    type_str="VEC3",
                    min_val=[-1.0, -1.0, -1.0],
                    max_val=[1.0, 1.0, 1.0]
                )
                prim_attrs["NORMAL"] = acc_norm

            # TEXCOORD_0
            if prim.uvs is not None and len(prim.uvs) > 0:
                uv_bytes = prim.uvs.tobytes()
                acc_uv = append_chunk(
                    uv_bytes,
                    target=34962,
                    count=len(prim.uvs),
                    comp_type=5126,
                    type_str="VEC2",
                    min_val=[0.0, 0.0],
                    max_val=[1.0, 1.0]
                )
                prim_attrs["TEXCOORD_0"] = acc_uv

            prim_dict = {"attributes": prim_attrs}

            # INDICES
            if prim.indices is not None and len(prim.indices) > 0:
                idx_bytes = prim.indices.tobytes()
                acc_idx = append_chunk(
                    idx_bytes,
                    target=34963,
                    count=len(prim.indices),
                    comp_type=5125,
                    type_str="SCALAR",
                    min_val=[int(prim.indices.min())],
                    max_val=[int(prim.indices.max())]
                )
                prim_dict["indices"] = acc_idx

            # MATERIAL
            if prim.material_def is not None:
                mat_idx = len(materials)
                materials.append(prim.material_def)
                prim_dict["material"] = mat_idx

            gltf_primitives.append(prim_dict)

        full_bin_buffer = b"".join(raw_chunks)
        return buffer_views, accessors, full_bin_buffer, gltf_primitives, materials

    def build_gltf_dict(self, embedded_base64: bool = False) -> Tuple[dict, bytes]:
        """Constrói a árvore de nós do glTF 2.0 e retorna o JSON estruturado e o buffer binário."""
        buffer_views, accessors, bin_buffer, primitives, materials = self._pack_binary_buffers()

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
                "primitives": primitives
            }],
            "buffers": [buffer_entry],
            "bufferViews": buffer_views,
            "accessors": accessors
        }

        if materials:
            gltf_doc["materials"] = materials

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


def build_smooth_rmf_tube(pts: np.ndarray, radius: float = 0.12, radial_segs: int = 8) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Gera malha 3D tubular contínua usando Rotation Minimizing Frames (RMF / Bishop Frames).
    Elimina 100% de singularidades de Gimbal, flips de vetor normal e torções de fita.
    """
    n = len(pts)
    tangents = []
    for i in range(n):
        p_prev = pts[(i - 1) % n]
        p_next = pts[(i + 1) % n]
        t = p_next - p_prev
        norm = np.linalg.norm(t)
        tangents.append(t / norm if norm > 1e-9 else np.array([1.0, 0.0, 0.0]))
    tangents = np.array(tangents)

    # Frame inicial
    t0 = tangents[0]
    ref = np.array([0.0, 0.0, 1.0]) if abs(t0[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    n0 = np.cross(t0, ref)
    n0 = n0 / np.linalg.norm(n0)
    b0 = np.cross(t0, n0)

    normals = [n0]
    binormals = [b0]

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

    # Correção de holonomia no fechamento da curva periódica
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
