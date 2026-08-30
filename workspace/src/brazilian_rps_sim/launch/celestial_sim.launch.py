import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_rps = get_package_share_directory('brazilian_rps_sim')
    pkg_parent_share = os.path.dirname(pkg_rps)

    world_path = os.path.join(pkg_rps, 'worlds', 'solar_system_earth_moon.sdf')
    gui_config_path = os.path.join(pkg_rps, 'launch', 'space_gui.config')

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{pkg_parent_share}:{pkg_rps}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}"
    )

    gz_sim_system_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=f"{os.path.join(pkg_rps, '..', '..', 'lib')}:{os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')}"
    )

    # 1. Gazebo Harmonic com configuração de espaço (Far Clip de 1.000.000 unidades)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'--gui-config {gui_config_path} -r {world_path}'}.items()
    )

    # 2. Nó de Efemérides Astronômicas e Fases da Lua
    ephemeris_node = Node(
        package='brazilian_rps_sim',
        executable='celestial_ephemeris_node.py',
        name='celestial_ephemeris_node',
        output='screen',
        parameters=[{
            'time_multiplier': 86400.0,
        }]
    )

    # 3. Posicionamento suave da Câmera
    camera_focus = ExecuteProcess(
        cmd=['python3', os.path.join(pkg_rps, '..', '..', 'lib', 'brazilian_rps_sim', 'camera_auto_focus.py'), 'earth'],
        output='screen'
    )

    return LaunchDescription([
        gz_resource_path,
        gz_sim_system_plugin_path,
        gz_sim,
        ephemeris_node,
        camera_focus
    ])
