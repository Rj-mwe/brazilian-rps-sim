#!/usr/bin/env python3
"""
Gerador Dinâmico e Desacoplado do Mundo SDFormat (solar_system_brazilian_rps.sdf)
para o Sistema Solar e a Constelação de N Satélites do RPS-BR.
Aplica ordem de renderização (render_order) explícita no Gazebo/OGRE 2 para garantir
que os cones e marcadores dos IGSOs se sobreponham aos feixes de fundo dos GEOs sem oclusão.
"""

import os
import yaml

try:
    from brazilian_rps_sim.color_palette import resolve_color
except ImportError:
    from color_palette import resolve_color

def generate_world_sdf(config_path: str = None, output_path: str = None):
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not config_path:
        config_path = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
    if not output_path:
        output_path = os.path.join(pkg_dir, 'worlds', 'solar_system_brazilian_rps.sdf')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    vis_cfg = cfg.get('visualization', {})
    
    # 1. Linhas e Trilhas Orbitais (Orbit Trails)
    trails_cfg = vis_cfg.get('orbit_trails', {})
    show_earth_orbit = trails_cfg.get('show_earth_orbit', True)
    show_moon_orbit = trails_cfg.get('show_moon_orbit', True)
    show_geo_orbit = trails_cfg.get('show_geo_orbit', True)
    show_igso_orbit = trails_cfg.get('show_igso_orbit', True)

    # 2. Marcadores dos Satélites (Satellite Markers)
    markers_cfg = vis_cfg.get('satellite_markers', vis_cfg.get('markers', {}))
    show_beacon_geo = markers_cfg.get('show_beacon_halo_geo', True)
    show_beacon_halo_igso = markers_cfg.get('show_beacon_halo_igso', True)
    show_cone_geo = markers_cfg.get('show_nadir_cone_geo', True)
    show_cone_igso = markers_cfg.get('show_nadir_cone_igso', True)
    sat_scale = float(markers_cfg.get('satellite_visual_scale', 0.08))

    # Cores
    color_cone_geo = resolve_color(markers_cfg.get('color_nadir_cone_geo', 'cyan'), default=(0.0, 0.90, 1.0))
    color_cone_igso = resolve_color(markers_cfg.get('color_nadir_cone_igso', 'amber'), default=(1.0, 0.80, 0.10))
    op_geo = float(markers_cfg.get('nadir_cone_opacity_geo', 0.06))
    op_igso = float(markers_cfg.get('nadir_cone_opacity_igso', 0.35))
    e_geo = float(markers_cfg.get('nadir_cone_emissive_geo', 0.10))
    e_igso = float(markers_cfg.get('nadir_cone_emissive_igso', 0.85))

    # 3. Satélites
    satellites = cfg.get('constellation', {}).get('satellites', [])

    # 4. Construção do SDFormat
    sdf_content = f"""<?xml version="1.0" ?>
<!--
  ==============================================================================
  Projeto: Brazilian RPS Sim (Sistema de Posicionamento e Aumento Brasileiro)
  Arquivo: solar_system_brazilian_rps.sdf
  Descrição: Mundo SDFormat gerado dinamicamente a partir de config/simulation_parameters.yaml
             Contém Sol, Terra NASA PBR 5 camadas, Lua LRO, Cúpula Gaia GLB,
             Linhas de Trajetória sob demanda e {len(satellites)} Satélites com render_order diferenciado.
  ==============================================================================
-->
<sdf version="1.8">
  <world name="solar_system_rps_world">
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

    <!-- 🌌 Cúpula Celeste 360° Gaia GLB -->
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

    <!-- ☀️ Luz Solar Heliocêntrica -->
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
"""

    # 1. Trilha da Órbita da Terra ao redor do Sol
    if show_earth_orbit:
        sdf_content += """
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
"""

    # 2. A Terra
    sdf_content += """
    <!-- ======================================================================= -->
    <!-- 🌍 A TERRA: CORPO SÓLIDO COM MALHA GLB PARAMÉTRICA (+Z POLAR)           -->
    <!-- ======================================================================= -->
    <model name="earth">
      <pose>1200 0 0 0 0 0</pose>
      <link name="earth_link">
        <collision name="earth_col">
          <geometry><sphere><radius>6.378</radius></sphere></geometry>
        </collision>

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

    <!-- Nuvens da Terra -->
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
    <!-- 🌕 A LUA: MODELO CIENTÍFICO LRO                                         -->
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
"""

    # 3. Trilha da Órbita da Lua ao redor da Terra
    if show_moon_orbit:
        sdf_content += """
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

    # 4. Inserção dos Anéis Orbitais dos Satélites (GEO e IGSO)
    if show_geo_orbit:
        sdf_content += """
    <!-- Anel Orbital Equatorial GEO -->
    <model name="constellation_orbit_geo">
      <static>true</static>
      <pose>1200 0 0 0 0 0</pose>
      <link name="geo_ring_link">
        <visual name="v_orbit_geo">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_geo.gltf</uri></mesh>
          </geometry>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>constellation_geo_ring</body_type>
      </plugin>
    </model>
"""

    if show_igso_orbit:
        sdf_content += """
    <!-- Trajetória 3D da Figura-8 dos IGSOs (Fixa sobre o Brasil) -->
    <model name="constellation_orbit_igso">
      <static>true</static>
      <pose>1200 0 0 0 0 0</pose>
      <link name="igso_ring_link">
        <visual name="v_orbit_igso">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_igso.gltf</uri></mesh>
          </geometry>
        </visual>
      </link>
      <plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>constellation_igso_trail</body_type>
      </plugin>
    </model>
"""

    # 5. Inserção dos Modelos 3D dos Satélites com Render Order
    sdf_content += """
    <!-- ======================================================================= -->
    <!-- 🛰️ CONSTELAÇÃO DINÂMICA DO RPS-BR (MODELOS 3D PBR + MARCADORES SOBREPOSTOS)-->
    <!-- ======================================================================= -->
"""

    for s in satellites:
        sat_id = s.get('id', 1)
        name = s.get('name', f"SAT-{sat_id}")
        sat_type = s.get('type', 'GEO')
        type_lower = sat_type.lower()
        is_geo = (sat_type == 'GEO')

        a_km = float(s.get('semi_major_axis_km', 42164.14))
        a_scale = a_km / 1000.0
        e = float(s.get('eccentricity', 0.0))
        inc_deg = float(s.get('inclination_deg', 0.0))
        raan_deg = float(s.get('raan_deg', 0.0))
        argp_deg = float(s.get('arg_perigee_deg', 0.0))
        m0_deg = float(s.get('mean_anomaly_deg', 0.0))

        model_name = f"rps_sat_{sat_id}"

        show_beacon = show_beacon_geo if is_geo else show_beacon_halo_igso
        show_cone = show_cone_geo if is_geo else show_cone_igso

        # Render Order no OGRE 2: GEO = 0 (fundo), IGSO = 10 (frente / sobreposto)
        cone_render_order = 0 if is_geo else 10
        cone_color = color_cone_geo if is_geo else color_cone_igso
        cone_op = op_geo if is_geo else op_igso
        cone_em = e_geo if is_geo else e_igso

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

        # Marcador: Halo
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
          <material>
            <render_order>15</render_order>
          </material>
        </visual>
"""

        # Marcador: Cone Nadir (Com Render Order Explícito para Sobreposição)
        if show_cone:
            sdf_content += f"""
        <!-- 3. Marcador Visual: Feixe de Cobertura Nadir (Render Order: {cone_render_order}) -->
        <visual name="v_nadir_beam">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/nadir_beam_{type_lower}.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>{cone_color[0]} {cone_color[1]} {cone_color[2]} {cone_op}</diffuse>
            <ambient>{cone_color[0]} {cone_color[1]} {cone_color[2]} {cone_op}</ambient>
            <emissive>{cone_color[0]*cone_em} {cone_color[1]*cone_em} {cone_color[2]*cone_em} 1.0</emissive>
            <double_sided>true</double_sided>
            <render_order>{cone_render_order}</render_order>
          </material>
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

    print(f"🌍 [WorldGenerator] Mundo SDF gerado com sucesso com render_order diferenciado e {len(satellites)} satélites: {output_path}")

if __name__ == '__main__':
    generate_world_sdf()
