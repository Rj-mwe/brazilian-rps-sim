#!/usr/bin/env python3
"""
Gerador Dinâmico e Desacoplado do Mundo SDFormat (solar_system_brazilian_rps.sdf)
para o Sistema Solar e a Constelação de N Satélites do RPS-BR.
Implementa o Design Pattern de INJEÇÃO DE DEPENDÊNCIAS VIA SDF:
Lê a configuração central (simulation_parameters.yaml) e injeta todos os parâmetros
orbitais, temporais e mecânicos diretamente nas tags <plugin> do XML, eliminando
qualquer acoplamento ou leitura direta de arquivos dentro do C++.
"""

import os
import yaml

try:
    from brazilian_rps_sim.color_palette import resolve_color
except ImportError:
    from color_palette import resolve_color

def generate_world_sdf(config_path: str = None, output_path: str = None):
    if not config_path or not os.path.exists(config_path):
        try:
            from ament_index_python.packages import get_package_share_directory
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            candidate = os.path.join(pkg_share, 'config', 'simulation_parameters.yaml')
            if os.path.exists(candidate):
                config_path = candidate
        except Exception:
            pass

    if not config_path or not os.path.exists(config_path):
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(pkg_dir, 'config', 'simulation_parameters.yaml')
        if os.path.exists(candidate):
            config_path = candidate
        else:
            config_path = '/home/rjgamito/ros2_ws/src/brazilian_rps_sim/config/simulation_parameters.yaml'

    if not output_path:
        try:
            from ament_index_python.packages import get_package_share_directory
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            candidate = os.path.join(pkg_share, 'worlds', 'solar_system_brazilian_rps.sdf')
            output_path = candidate
        except Exception:
            pass

    if not output_path:
        if config_path and os.path.exists(config_path):
            output_path = os.path.join(os.path.dirname(os.path.dirname(config_path)), 'worlds', 'solar_system_brazilian_rps.sdf')
        else:
            output_path = '/home/rjgamito/ros2_ws/src/brazilian_rps_sim/worlds/solar_system_brazilian_rps.sdf'

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    # 1. Configurações Globais e Temporais
    sim_cfg = cfg.get('simulation', {})
    time_multiplier = float(sim_cfg.get('time_multiplier', 3600.0))
    render_scale = float(sim_cfg.get('render_scale', 0.001))

    # 2. Mecânica Celeste e Parâmetros Físicos
    celestial_cfg = cfg.get('celestial_mechanics', {})
    earth_cfg = celestial_cfg.get('earth', {})
    moon_cfg = celestial_cfg.get('moon', {})

    dist_sun_earth = float(earth_cfg.get('dist_sun_render', 1200.0))
    dist_earth_moon = float(moon_cfg.get('dist_earth_render', 384.4))
    obliquity_deg = float(earth_cfg.get('obliquity_deg', 23.43928))
    clouds_drift = float(earth_cfg.get('clouds_drift_factor', 1.035))
    sidereal_day_sec = float(earth_cfg.get('sidereal_day_sec', 86164.0905))
    sidereal_year_sec = float(earth_cfg.get('sidereal_year_sec', 31558149.76))
    sidereal_month_sec = float(moon_cfg.get('sidereal_month_sec', 2360591.51))
    moon_inc_deg = float(moon_cfg.get('inclination_deg', 5.145))

    # 3. Visualização e Marcadores
    vis_cfg = cfg.get('visualization', {})
    trails_cfg = vis_cfg.get('orbit_trails', {})
    show_earth_orbit = trails_cfg.get('show_earth_orbit', True)
    show_moon_orbit = trails_cfg.get('show_moon_orbit', True)
    show_geo_orbit = trails_cfg.get('show_geo_orbit', True)
    show_igso_orbit = trails_cfg.get('show_igso_orbit', True)

    color_orbit_geo = resolve_color(trails_cfg.get('color_geo_orbit', 'cyan'), default=(0.0, 0.90, 1.0))
    color_orbit_igso = resolve_color(trails_cfg.get('color_igso_orbit', 'amber'), default=(1.0, 0.80, 0.10))

    markers_cfg = vis_cfg.get('satellite_markers', vis_cfg.get('markers', {}))
    geo_cfg = markers_cfg.get('geo_markers', {})
    igso_cfg = markers_cfg.get('igso_markers', {})

    sat_scale = float(markers_cfg.get('satellite_visual_scale', 0.08))

    # 4. Satélites
    satellites = cfg.get('constellation', {}).get('satellites', [])

    # Helper para injeção de tags comuns no CelestialMechanicsPlugin
    def make_celestial_plugin_tag(body_type: str) -> str:
        return f"""<plugin filename="libCelestialMechanicsPlugin.so" name="celestial_sim::CelestialMechanicsPlugin">
        <body_type>{body_type}</body_type>
        <time_scale>{time_multiplier}</time_scale>
        <dist_sun_earth>{dist_sun_earth}</dist_sun_earth>
        <dist_earth_moon>{dist_earth_moon}</dist_earth_moon>
        <obliquity_deg>{obliquity_deg}</obliquity_deg>
        <clouds_drift_factor>{clouds_drift}</clouds_drift_factor>
        <sidereal_day_sec>{sidereal_day_sec}</sidereal_day_sec>
        <sidereal_year_sec>{sidereal_year_sec}</sidereal_year_sec>
        <sidereal_month_sec>{sidereal_month_sec}</sidereal_month_sec>
        <moon_inclination_deg>{moon_inc_deg}</moon_inclination_deg>
      </plugin>"""

    # 5. Construção do SDFormat
    sdf_content = f"""<?xml version="1.0" ?>
<!--
  ==============================================================================
  Projeto: Brazilian RPS Sim (Sistema de Posicionamento e Aumento Brasileiro)
  Arquivo: solar_system_brazilian_rps.sdf
  Descrição: Mundo SDFormat gerado dinamicamente a partir de config/simulation_parameters.yaml
             Implementa Injeção de Dependências via SDFormat para todos os Plugins C++.
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

    <!-- 🌟 Cúpula Celeste: Starfield Hipparcos 360° -->
    <model name="celestial_skydome">
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
      {make_celestial_plugin_tag("sun")}
    </model>
"""

    # 1. Trilha da Órbita da Terra ao redor do Sol
    if show_earth_orbit:
        sdf_content += f"""
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
          <material>
            <diffuse>1.0 0.75 0.1 1.0</diffuse>
            <ambient>1.0 0.75 0.1 1.0</ambient>
            <emissive>1.0 0.75 0.1 1.0</emissive>
            <double_sided>true</double_sided>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("earth_trail")}
    </model>
"""

    # 2. A Terra
    sdf_content += f"""
    <!-- ======================================================================= -->
    <!-- 🌍 A TERRA: CORPO SÓLIDO COM MALHA GLB PARAMÉTRICA (+Z POLAR)           -->
    <!-- ======================================================================= -->
    <model name="earth">
      <pose>{dist_sun_earth} 0 0 0 0 0</pose>
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
                <roughness>0.6</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>

        <!-- Camada Atmosférica de Nuvens Dinâmicas -->
        <visual name="earth_clouds">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/earth_clouds.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>1.0 1.0 1.0 1.0</diffuse>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/earth_clouds_2k.png</albedo_map>
                <roughness>0.9</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
            <render_order>1</render_order>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("earth")}
    </model>

    <!-- ======================================================================= -->
    <!-- 🌕 A LUA: ESFERA COM TEXTURA LRO PBR 2K (+Z POLAR)                      -->
    <!-- ======================================================================= -->
    <model name="moon">
      <pose>{dist_sun_earth + dist_earth_moon} 0 0 0 0 0</pose>
      <link name="moon_link">
        <collision name="moon_col">
          <geometry><sphere><radius>1.737</radius></sphere></geometry>
        </collision>

        <visual name="moon_surface">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <sphere><radius>1.737</radius></sphere>
          </geometry>
          <material>
            <diffuse>1.0 1.0 1.0 1.0</diffuse>
            <specular>0.1 0.1 0.1 1.0</specular>
            <pbr>
              <metal>
                <albedo_map>package://brazilian_rps_sim/materials/textures/moon_day_albedo_2k.jpg</albedo_map>
                <normal_map>package://brazilian_rps_sim/materials/textures/moon_normal_2k.jpg</normal_map>
                <roughness>0.9</roughness>
                <metalness>0.0</metalness>
              </metal>
            </pbr>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("moon")}
    </model>

    <!-- Trilha Visual da Órbita da Lua ao redor da Terra -->
    <model name="moon_orbit_trail">
      <static>true</static>
      <pose>{dist_sun_earth} 0 0 0 0 0</pose>
      <link name="moon_trail_link">
        <visual name="v_moon_orbit_ring">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/moon_orbit_ring.gltf</uri></mesh>
          </geometry>
          <material>
            <diffuse>0.0 0.85 1.0 1.0</diffuse>
            <ambient>0.0 0.85 1.0 1.0</ambient>
            <emissive>0.0 0.85 1.0 1.0</emissive>
            <double_sided>true</double_sided>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("moon_trail")}
    </model>
"""

    # 4. Inserção dos Anéis Orbitais dos Satélites (GEO e IGSO)
    if show_geo_orbit:
        sdf_content += f"""
    <!-- Anel Orbital Equatorial GEO -->
    <model name="constellation_orbit_geo">
      <static>true</static>
      <pose>{dist_sun_earth} 0 0 0 0 0</pose>
      <link name="geo_ring_link">
        <visual name="v_orbit_geo">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_geo.gltf</uri></mesh>
          </geometry>
          <material>
            <diffuse>{color_orbit_geo[0]} {color_orbit_geo[1]} {color_orbit_geo[2]} 1.0</diffuse>
            <ambient>{color_orbit_geo[0]} {color_orbit_geo[1]} {color_orbit_geo[2]} 1.0</ambient>
            <emissive>{color_orbit_geo[0]} {color_orbit_geo[1]} {color_orbit_geo[2]} 1.0</emissive>
            <double_sided>true</double_sided>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("constellation_geo_ring")}
    </model>
"""

    if show_igso_orbit:
        sdf_content += f"""
    <!-- Trajetória 3D da Figura-8 dos IGSOs (Fixa sobre o Brasil) -->
    <model name="constellation_orbit_igso">
      <static>true</static>
      <pose>{dist_sun_earth} 0 0 0 0 0</pose>
      <link name="igso_ring_link">
        <visual name="v_orbit_igso">
          <cast_shadows>false</cast_shadows>
          <geometry>
            <mesh><uri>package://brazilian_rps_sim/meshes/orbit_igso.gltf</uri></mesh>
          </geometry>
          <material>
            <diffuse>{color_orbit_igso[0]} {color_orbit_igso[1]} {color_orbit_igso[2]} 1.0</diffuse>
            <ambient>{color_orbit_igso[0]} {color_orbit_igso[1]} {color_orbit_igso[2]} 1.0</ambient>
            <emissive>{color_orbit_igso[0]} {color_orbit_igso[1]} {color_orbit_igso[2]} 1.0</emissive>
            <double_sided>true</double_sided>
          </material>
        </visual>
      </link>
      {make_celestial_plugin_tag("constellation_igso_trail")}
    </model>
"""

    # 5. Inserção dos Modelos 3D dos Satélites com Injeção de Parâmetros
    sdf_content += """
    <!-- ======================================================================= -->
    <!-- 🛰️ CONSTELAÇÃO DINÂMICA DO RPS-BR (INJEÇÃO DE DEPENDÊNCIAS VIA SDF)     -->
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

        if is_geo:
            show_beacon = geo_cfg.get('show_beacon_halo', markers_cfg.get('show_beacon_halo_geo', True))
            color_beacon = resolve_color(geo_cfg.get('color', 'cyan'), default=(0.0, 0.90, 1.0))
            e_beacon = float(geo_cfg.get('beacon_emissive', markers_cfg.get('beacon_emissive_geo', 0.80)))

            show_cone = geo_cfg.get('show_nadir_beam', markers_cfg.get('show_nadir_cone_geo', True))
            show_cage = geo_cfg.get('show_generatrix_rays', True)
            show_bore = geo_cfg.get('show_boresight_ray', True)
            color_cage = resolve_color(geo_cfg.get('color', 'cyan'), default=(0.0, 0.90, 1.0))
            color_bore = resolve_color(geo_cfg.get('color_boresight', 'white'), default=(0.95, 0.95, 1.0))
            e_cone = float(geo_cfg.get('emissive_intensity', markers_cfg.get('nadir_cone_emissive_geo', 0.85)))
            cone_render_order = 10
        else:
            show_beacon = igso_cfg.get('show_beacon_halo', markers_cfg.get('show_beacon_halo_igso', True))
            color_beacon = resolve_color(igso_cfg.get('color', 'amber'), default=(1.0, 0.80, 0.10))
            e_beacon = float(igso_cfg.get('beacon_emissive', markers_cfg.get('beacon_emissive_igso', 0.85)))

            show_cone = igso_cfg.get('show_nadir_beam', markers_cfg.get('show_nadir_cone_igso', True))
            show_cage = igso_cfg.get('show_generatrix_rays', True)
            show_bore = igso_cfg.get('show_boresight_ray', True)
            color_cage = resolve_color(igso_cfg.get('color', 'amber'), default=(1.0, 0.80, 0.10))
            color_bore = resolve_color(igso_cfg.get('color_boresight', 'orange'), default=(1.0, 0.45, 0.05))
            e_cone = float(igso_cfg.get('emissive_intensity', markers_cfg.get('nadir_cone_emissive_igso', 0.95)))
            cone_render_order = 12

        sdf_content += f"""
    <!-- Satélite {sat_id}: {name} [{sat_type}] -->
    <model name="{model_name}">
      <pose>{dist_sun_earth + 42.164} 0 0 0 0 0</pose>
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
            <diffuse>{color_beacon[0]} {color_beacon[1]} {color_beacon[2]} 1.0</diffuse>
            <ambient>{color_beacon[0]} {color_beacon[1]} {color_beacon[2]} 1.0</ambient>
            <emissive>{color_beacon[0]*e_beacon} {color_beacon[1]*e_beacon} {color_beacon[2]*e_beacon} 1.0</emissive>
            <double_sided>true</double_sided>
            <render_order>15</render_order>
          </material>
        </visual>
"""

        # Marcador: Gaiola Externa & Pegada 2D
        if show_cone and show_cage:
            sdf_content += f"""
        <!-- 3a. Marcador Visual: Gaiola Holográfica Externa / Pegada 2D -->
        <visual name="v_nadir_cage">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/nadir_cage_{type_lower}.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>{color_cage[0]} {color_cage[1]} {color_cage[2]} 1.0</diffuse>
            <ambient>{color_cage[0]} {color_cage[1]} {color_cage[2]} 1.0</ambient>
            <emissive>{color_cage[0]*e_cone} {color_cage[1]*e_cone} {color_cage[2]*e_cone} 1.0</emissive>
            <double_sided>true</double_sided>
            <render_order>{cone_render_order}</render_order>
          </material>
        </visual>
"""

        # Marcador: Feixe Central Laser Boresight & Mira
        if show_cone and show_bore:
            sdf_content += f"""
        <!-- 3b. Marcador Visual: Feixe Central Laser Boresight & Mira -->
        <visual name="v_nadir_boresight">
          <cast_shadows>false</cast_shadows>
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <mesh>
              <uri>package://brazilian_rps_sim/meshes/nadir_boresight_{type_lower}.glb</uri>
            </mesh>
          </geometry>
          <material>
            <diffuse>{color_bore[0]} {color_bore[1]} {color_bore[2]} 1.0</diffuse>
            <ambient>{color_bore[0]} {color_bore[1]} {color_bore[2]} 1.0</ambient>
            <emissive>{color_bore[0]} {color_bore[1]} {color_bore[2]} 1.0</emissive>
            <double_sided>true</double_sided>
            <render_order>{cone_render_order + 2}</render_order>
          </material>
        </visual>
"""

        # Plugin C++ com Injeção Explícita de Parâmetros
        sdf_content += f"""      </link>

      <!-- Plugin C++ de Propagação Orbital no Gazebo (Dependency Injection via SDF) -->
      <plugin filename="libOrbitalMotionPlugin.so" name="brazilian_rps::OrbitalMotionPlugin">
        <semi_major_axis>{a_scale:.6f}</semi_major_axis>
        <eccentricity>{e:.6f}</eccentricity>
        <inclination_deg>{inc_deg:.6f}</inclination_deg>
        <raan_deg>{raan_deg:.6f}</raan_deg>
        <arg_perigee_deg>{argp_deg:.6f}</arg_perigee_deg>
        <mean_anomaly_deg>{m0_deg:.6f}</mean_anomaly_deg>
        <time_scale>{time_multiplier}</time_scale>
        <heliocentric>true</heliocentric>
        <dist_sun_earth>{dist_sun_earth}</dist_sun_earth>
        <obliquity_deg>{obliquity_deg}</obliquity_deg>
        <sidereal_year_sec>{sidereal_year_sec}</sidereal_year_sec>
        <sidereal_day_sec>{sidereal_day_sec}</sidereal_day_sec>
      </plugin>
    </model>
"""

    sdf_content += """
  </world>
</sdf>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sdf_content)

    print(f"🌍 [WorldGenerator] Mundo SDF gerado com sucesso com Injeção de Dependências e {len(satellites)} satélites: {output_path}")

if __name__ == '__main__':
    generate_world_sdf()
