#!/usr/bin/env python3
"""
Arquivo de inicialização unificado do Sistema Solar e da Constelação RPS-BR.
Arquitetura Hexagonal:
- Gera proceduralmente os marcadores e o mundo SDFormat com base no YAML antes da inicialização
- Executa o Gazebo Sim Harmonic com o mundo atualizado
- Conecta a ponte de relógio (/clock)
- Inicializa o nó mestre da constelação (rps_constellation_node)
- Aplica o foco automático de câmera
"""

import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node

def build_world_and_markers(context, *args, **kwargs):
    """Executa os geradores de malhas e mundo para aplicar qualquer alteração feita no YAML."""
    pkg_share = get_package_share_directory('brazilian_rps_sim')
    config_file_path = os.path.join(pkg_share, 'config', 'simulation_parameters.yaml')
    mesh_dir = os.path.join(pkg_share, 'meshes')
    world_path = os.path.join(pkg_share, 'worlds', 'solar_system_brazilian_rps.sdf')

    try:
        from brazilian_rps_sim.marker_mesh_generator import generate_all_marker_assets
        from brazilian_rps_sim.world_generator import generate_world_sdf
        from brazilian_rps_sim.earth_globe_generator import generate_all_earth_assets

        # Garante que as malhas da Terra e marcadores estão sincronizadas com o YAML
        generate_all_earth_assets(mesh_dir)
        generate_all_marker_assets(config_file_path, mesh_dir)
        generate_world_sdf(config_file_path, world_path)
    except Exception as e:
        print(f"⚠️ [Launch] Aviso na geração procedural: {e}")

    return []

def generate_launch_description():
    pkg_share = get_package_share_directory('brazilian_rps_sim')
    world_path = os.path.join(pkg_share, 'worlds', 'solar_system_brazilian_rps.sdf')
    gui_config_path = os.path.join(pkg_share, 'launch', 'space_gui.config')
    config_file_path = os.path.join(pkg_share, 'config', 'simulation_parameters.yaml')
    mesh_dir = os.path.join(pkg_share, 'meshes')

    # Executa a geração procedural no momento do carregamento
    try:
        from brazilian_rps_sim.marker_mesh_generator import generate_all_marker_assets
        from brazilian_rps_sim.world_generator import generate_world_sdf
        from brazilian_rps_sim.earth_globe_generator import generate_all_earth_assets

        generate_all_earth_assets(mesh_dir)
        generate_all_marker_assets(config_file_path, mesh_dir)
        generate_world_sdf(config_file_path, world_path)
    except Exception as e:
        pass

    focus_script = os.path.join(pkg_share, 'lib', 'brazilian_rps_sim', 'camera_auto_focus.py')
    if not os.path.exists(focus_script):
        focus_script = '/home/rjgamito/ros2_ws/install/brazilian_rps_sim/lib/brazilian_rps_sim/camera_auto_focus.py'

    return LaunchDescription([
        # 1. Atualização procedural a quente dos parâmetros visuais e do mundo
        OpaqueFunction(function=build_world_and_markers),

        # 2. Motor de Simulação do Gazebo Harmonic
        ExecuteProcess(
            cmd=[
                'gz', 'sim', '-r', world_path,
                '--gui-config', gui_config_path
            ],
            output='screen'
        ),

        # 3. Ponte de Relógio entre Gazebo Sim e ROS 2 (Sincronização 1:1 estrita)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='clock_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            output='screen'
        ),

        # 4. Nó de Domínio Hexagonal: Constelação RPS-BR (7 Satélites) e Sistema Celeste
        Node(
            package='brazilian_rps_sim',
            executable='rps_constellation_node',
            name='rps_constellation_node',
            parameters=[{
                'use_sim_time': True,
                'config_path': config_file_path
            }],
            output='screen'
        ),

        # 5. Ajuste automático da câmera do Gazebo com visão panorâmica sobre a Terra e satélites
        ExecuteProcess(
            cmd=['python3', focus_script, 'earth'],
            output='screen'
        )
    ])
