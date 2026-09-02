# ADR 0002: Padrão Builder para Geração Procedural de Malhas glTF 2.0 / GLB

* **Status**: Aprovado e Implementado
* **Data**: 2026-08-28

---

## 1. Contexto & Problema
Modelos tridimensionais (trajetórias em tubo, anéis de órbita, esferas planetárias e cones holográficos) eram exportados em formatos legados (.obj, .dae) ou dependiam de ferramentas gráficas externas (Blender), dificultando parametrizações procedurais em tempo de launch. Além disso, o motor OGRE 2 do Gazebo Sim apresentava inconsistências de renderização e sombreamento quando os buffers binários não seguiam o alinhamento de 4 bytes exigido pelo padrão Khronos glTF 2.0.

---

## 2. Decisão
Implementar um gerador de malhas em Python puro utilizando o **Builder Pattern** (`GltfMeshBuilder` em `gltf_builder.py`):
1. **Multi-primitivas e Multi-materiais**: Capacidade de empacotar geometrias independentes (ex: gaiola externa vs feixe laser central) com materiais PBR dedicados em um único arquivo binário `.glb`.
2. **Alinhamento e Little-Endian**: Empacotamento direto de vértices, normais, coordenadas UV e índices triangulares alinhados a 4 bytes.
3. **PBR Integrado**: Configuração nativa de fatores `emissiveFactor`, `baseColorFactor` e `roughnessFactor`.

---

## 3. Consequências
* Geração 100% procedural e instantânea durante o boot do launch.
* Fidelidade visual no motor OGRE 2 com iluminação emissiva estável no vácuo espacial.
