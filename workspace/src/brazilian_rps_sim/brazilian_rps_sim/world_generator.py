#!/usr/bin/env python3
"""
Gerador Dinâmico e Desacoplado do Mundo SDFormat (solar_system_brazilian_rps.sdf)
para o Sistema Solar e a Constelação de N Satélites do RPS-BR.
Lê dinamicamente o arquivo central config/simulation_parameters.yaml e constrói
os modelos 3D com malhas PBR fotorrealistas e os 3 estilos de marcadores visuais configuráveis.
"""

import os
import yaml

def generate_world_sdf(config_path: str = None, output_path: str = None):
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not output_path:
        output_path = os.path.join(pkg_dir, 'worlds', 'solar_system_brazilian_rps.sdf')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    # 1. Parâmetros Globais de Visualização e Marcadores
    vis_cfg = cfg.get('visualization', {}).get('markers', {})
    show_beacon = vis_cfg.get('show_beacon_halo', True)
    show_cone = vis_cfg.get('show_nadir_cone', True)
    show_rings = vis_cfg.get('show_orbital_ring', True)
    sat_scale = float(vis_cfg.get('satellite_visual_scale', 0.08))

    # 2. Parâmetros da Constelação
    satellites = cfg.get('constellation', {}).get('satellites', [])

    # 3. Construção do Cabeçalho e Corpos Celestes
    sdf_content = f"""<?xml version="1.0" ?>
<!--
  ==============================================================================
  Projeto: Brazilian RPS Sim (Sistema de Posicionamento e Aumento Brasileiro)
  Arquivo: solar_system_brazilian_rps.sdf
  Descrição: Mundo SDFormat gerado dinamicamente a partir de config/simulation_parameters.yaml
             Contém Sol, Terra NASA PBR 5 camadas (Malha GLB Paramétrica), Lua LRO,
             Cúpula 360° da Via Láctea e {len(satellites)} Satélites Small GEO com marcadores configuráveis.
  ==============================================================================
-->
<sdf version="1.8">
  <world name="solar_system_rps_world">
    <!-- Configurações de Física Analítica -->
    <physics name="physics_60hz" type="ignored">
      <max_step_size>0.016666667</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <gravity>0 0 0</gravity>

    <!-- 🌌 Vácuo Espacial -->
    <scene>
      <ambient>0.0 0.0 0.0 1.0</ambient>
      <background>0.0005 0.0005 0.002 1.0</background>
      <grid>false</grid>
      <shadows>false</shadows>
    </scene>

    <!-- Plugins Fundamentais do Gazebo Sim -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics" />
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands" />
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster">
      <state_hertz>60</state_hertz>
    </plugin>

    <!-- ======================================================================= -->
    <!-- 🌌 CAMPO ESTRELADO DO ESPAÇO PROFUNDO E VIA LÁCTEA (NASA/ESA Gaia GLB)  -->
    <!-- ======================================================================= -->
    <model name="celestial_starfield">
      <static>true</static>
      <pose>0 0 0 0 0 0</pose>
      <link name="starfield_link">
        <visual name="v_stars">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/celestial_skydome.glb</uri>
            </mesh>
          </geometry>
        </visual>
      </link>
    </model>

    <!-- ======================================================================= -->
    <!-- ☀️ ILUMINAÇÃO SOLAR HELIOCÊNTRICA (Luz Pontual Omnidirecional na Origem) -->
    <!-- ======================================================================= -->
    <light name="sun_radial_light" type="point">
      <pose>0 0 0 0 0 0</pose>
      <cast_shadows>false</cast_shadows>
      <diffuse>1.0 0.98 0.94 1.0</diffuse>
      <specular>0.8 0.78 0.75 1.0</specular>
      <attenuation>
        <range>500000.0</range>
        <constant>1.0</constant>
        <linear>0.0</linear>
        <quadratic>0.0</quadratic>
      </attenuation>
    </light>

    <!-- O Sol: Esfera com Fotosfera SDO PBR 2K -->
    <model name="sun">
      <static>true</static>
      <pose>0 0 0 0 0 0</pose>
      <link name="sun_link">
        <visual name="sun_photosphere">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <sphere><radius>45.0</radius></sphere>
          </geometry>
          <material>
            <diffuse>1.0 0.95 0.8 1.0</diffuse>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/sun_photosphere_2k.jpg</albedo_map>
                <emissive_map>package://brazilian_rps_sim/materials/textures/sun_photosphere_2k.jpg</emissive_map>
                <roughness>0.1</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>sun</body_type>
      </plugin>
    </model>

    <!-- Trilha Visual da Órbita da Terra ao redor do Sol -->
    <model name="earth_orbit_trail">
      <static>true</static>
      <pose>0 0 0 0 0 0</pose>
      <link name="trail_link">
        <visual name="v_earth_orbit_ring">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/earth_orbit_ring.gltf</uri></mesh>
          </geometry>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>earth_trail</body_type>
      </plugin>
    </model>

    <!-- ======================================================================= -->
    <!-- 🌍 A TERRA: CORPO SÓLIDO COM MALHA GLB PARAMÉTRICA (+Z NORTE, +X 0° LON) -->
    <!-- ======================================================================= -->
    <model name="earth">
      <pose>1200 0 0 0 0 0</pose>
      <link name="earth_link">
        <collision name="earth_col">
          <geometry><sphere><radius>6.378</radius></sphere></geometry>
        </collision>

        <!-- 1. Superfície Sólida da Terra (Malha GLB Paramétrica de Alta Precisão) -->
        <visual name="earth_surface">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/earth_globe.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>1.0 1.0 1.0 1.0</diffuse>
            <specular>0.8 0.8 0.8 1.0</specular>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/earth_day_albedo_2k.jpg</albedo_map>
                <emissive_map>package://brazilian_rps_sim/materials/textures/earth_night_lights_2k.jpg</emissive_map>
                <roughness_map>package://brazilian_rps_sim/materials/textures/earth_roughness_2k.jpg</roughness_map>
                <normal_map>package://brazilian_rps_sim/materials/textures/earth_normal_2k.jpg</normal_map>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>

        <!-- 2. Halo Azul Atmosférico (Espalhamento de Rayleigh) -->
        <visual name="earth_atmosphere_halo">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <sphere><radius>6.423</radius></sphere>
          </geometry>
          <material>
            <diffuse>0.2 0.65 1.0 0.85</diffuse>
            <specular>0.4 0.7 1.0 1.0</specular>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/earth_atmosphere_halo_2k.png</albedo_map>
                <emissive_map>package://brazilian_rps_sim/materials/textures/earth_atmosphere_emissive_2k.jpg</emissive_map>
                <roughness>0.85</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>
      </link>

      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>earth</body_type>
      </plugin>
    </model>

    <!-- 3. Camada Externa de Nuvens Dinâmicas (Malha GLB Paramétrica) -->
    <model name="earth_clouds">
      <pose>1200 0 0 0 0 0</pose>
      <link name="clouds_link">
        <visual name="clouds_surface">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/earth_clouds.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>1.0 1.0 1.0 0.95</diffuse>
            <specular>0.5 0.5 0.5 1.0</specular>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/earth_clouds_2k.png</albedo_map>
                <roughness>0.9</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>earth_clouds</body_type>
      </plugin>
    </model>

    <!-- ======================================================================= -->
    <!-- 🌕 A LUA: MODELO CIENTÍFICO LRO COM ALBEDO E RELEVO 3D                  -->
    <!-- ======================================================================= -->
    <model name="moon">
      <pose>1584.4 0 0 0 0 0</pose>
      <link name="moon_link">
        <collision name="moon_col">
          <geometry><sphere><radius>1.7374</radius></sphere></geometry>
        </collision>
        <visual name="moon_surface">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <sphere><radius>1.7374</radius></sphere>
          </geometry>
          <material>
            <diffuse>1.0 1.0 1.0 1.0</diffuse>
            <specular>0.1 0.1 0.1 1.0</specular>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/moon_day_albedo_2k.jpg</albedo_map>
                <normal_map>package://brazilian_rps_sim/materials/textures/moon_normal_2k.jpg</normal_map>
                <roughness>0.95</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>moon</body_type>
      </plugin>
    </model>

    <!-- Trilha Visual da Órbita da Lua ao redor da Terra -->
    <model name="moon_orbit_trail">
      <static>true</static>
      <pose>1200 0 0 0 0 0</pose>
      <link name="moon_trail_link">
        <visual name="v_moon_orbit_ring">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/moon_orbit_ring.gltf</uri></mesh>
          </geometry>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>moon_trail</body_type>
      </plugin>
    </model>
"""

    # 4. Inserção dos Anéis Orbitais Visuais (se habilitados)
    if show_rings:
        sdf_content += """
    <!-- ======================================================================= -->
    <!-- 🛰️ ANÉIS ORBITAIS VISUAIS DA CONSTELAÇÃO (GEO e IGSO)                   -->
    <!-- ======================================================================= -->
    <model name="constellation_orbit_rings">
      <static>true</static>
      <pose>1200 0 0 0 0 0</pose>
      <link name="rings_link">
        <!-- Anel Geoestacionário (GEO - Plano Equatorial 0°) -->
        <visual name="v_orbit_geo">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_geo.gltf</uri></mesh>
          </geometry>
        </visual>
        <!-- Anel Geossíncrono Inclinado (IGSO - Inclinação 29°) -->
        <visual name="v_orbit_igso">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_igso.gltf</uri></mesh>
          </geometry>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>earth_trail</body_type>
      </plugin>
    </model>
"""

    # 5. Inserção Dinâmica de cada Satélite com Malha PBR e Marcadores Refinados
    sdf_content += """
    <!-- ======================================================================= -->
    <!-- 🛰️ CONSTELAÇÃO DINÂMICA DO RPS-BR (MODELOS 3D PBR + MARCADORES REFINADOS) -->
    <!-- ======================================================================= -->
"""

    for s in satellites:
        sat_id = s.get('id', 1)
        name = s.get('name', f"SAT-{sat_id}")
        sat_type = s.get('type', 'GEO')
        type_lower = sat_type.lower()
        a_km = float(s.get('semi_major_axis_km', 42164.14))
        a_scale = a_km / 1000.0 # 42.164 unidades no mundo
        e = float(s.get('eccentricity', 0.0))
        inc_deg = float(s.get('inclination_deg', 0.0))
        raan_deg = float(s.get('raan_deg', 0.0))
        argp_deg = float(s.get('arg_perigee_deg', 0.0))
        m0_deg = float(s.get('mean_anomaly_deg', 0.0))

        model_name = f"rps_sat_{sat_id}"

        sdf_content += f"""
    <!-- Satélite {sat_id}: {name} [{sat_type}] -->
    <model name="{model_name}">
      <pose>1242.164 0 0 0 0 0</pose>
      <link name="{model_name}_link">
        <collision name="col">
          <geometry><sphere><radius>0.2</radius></sphere></geometry>
        </collision>

        <!-- 1. Malha 3D Fotorrealista PBR do Satélite Small GEO -->
        <visual name="v_satellite_pbr">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/satellite_navsat.glb</uri>
              <scale>{sat_scale} {sat_scale} {sat_scale}</scale>
            </mesh>
          </geometry>
        </visual>
"""

        # Marcador 1: Retículo/Anel Holográfico Radiante (se ativado)
        if show_beacon:
            sdf_content += f"""
        <!-- 2. Marcador Visual: Retículo Holográfico Radiante Neon -->
        <visual name="v_locator_ring">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/locator_ring_{type_lower}.glb</uri>
            </mesh>
          </geometry>
        </visual>
"""

        # Marcador 2: Cone de Feixe Nadir Ultratranslúcido (se ativado)
        if show_cone:
            sdf_content += f"""
        <!-- 3. Marcador Visual: Feixe de Cobertura Nadir Ultratranslúcido -->
        <visual name="v_nadir_beam">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/nadir_beam_{type_lower}.glb</uri>
            </mesh>
          </geometry>
        </visual>
"""

        sdf_content += f"""      </link>

      <!-- Plugin C++ de Propagação Orbital no Gazebo -->
      <plugin filename="libOrbitalMotionPlugin.so" name="brazilian_rps::OrbitalMotionPlugin">
        <semi_major_axis>{a_scale:.6f}</semi_major_axis>
        <eccentricity>{e:.6f}</eccentricity>
        <inclination_deg>{inc_deg:.6f}</inclination_deg>
        <raan_deg>{raan_deg:.6f}</raan_deg>
        <arg_perigee_deg>{argp_deg:.6f}</arg_perigee_deg>
        <mean_anomaly_deg>{m0_deg:.6f}</mean_anomaly_deg>
        <heliocentric>true</heliocentric>
      </plugin>
    </model>
"""

    sdf_content += """
  </world>
</sdf>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sdf_content)

    print(f"🌍 [WorldGenerator] Mundo SDF gerado com sucesso para {len(satellites)} satélites com malhas GLB da Terra: {output_path}")

if __name__ == '__main__':
    generate_world_sdf()
