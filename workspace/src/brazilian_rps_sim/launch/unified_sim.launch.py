#!/usr/bin/env python3
"""
Arquivo de inicialização unificado do Sistema Solar e da Constelação RPS-BR.
Executa a simulação multiescala completa: Sol, Terra realista da NASA, Lua e Satélites.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('brazilian_rps_sim')
    world_path = os.path.join(pkg_share, 'worlds', 'solar_system_brazilian_rps.sdf')
    gui_config_path = os.path.join(pkg_share, 'launch', 'space_gui.config')
    focus_script = os.path.join(pkg_share, 'lib', 'brazilian_rps_sim', 'camera_auto_focus.py')
    if not os.path.exists(focus_script):
        focus_script = '/home/rjgamito/ros2_ws/install/brazilian_rps_sim/lib/brazilian_rps_sim/camera_auto_focus.py'

    return LaunchDescription([
        # 1. Motor de Simulação do Gazebo Harmonic com layout espacial e alcance de 10^6 km
        ExecuteProcess(
            cmd=[
                'gz', 'sim', '-r', world_path,
                '--gui-config', gui_config_path
            ],
            output='screen'
        ),

        # 2. Nó de Efemérides Astronômicas e Relógio Cósmico
        Node(
            package='brazilian_rps_sim',
            executable='celestial_ephemeris_node.py',
            name='celestial_ephemeris_node',
            output='screen'
        ),

        # 3. Nó de Telemetria Orbital da Constelação Brasileira RPS-BR
        Node(
            package='brazilian_rps_sim',
            executable='orbit_publisher_node.py',
            name='rps_orbit_publisher',
            output='screen'
        ),

        # 4. Ajuste automático da câmera do Gazebo com visão panorâmica sobre a Terra e satélites
        ExecuteProcess(
            cmd=['python3', focus_script, 'earth'],
            output='screen'
        )
    ])
