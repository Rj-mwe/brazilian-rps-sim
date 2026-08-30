import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_rps = get_package_share_directory('brazilian_rps_sim')
    pkg_parent_share = os.path.dirname(pkg_rps)

    world_path = os.path.join(pkg_rps, 'worlds', 'earth_constellation.sdf')

    # Configura os caminhos de recursos para o Gazebo resolver package:// e model://
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{pkg_parent_share}:{pkg_rps}:{os.environ.get('GZ_SIM_RESOURCE_PATH', '')}"
    )

    gz_sim_system_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=f"{os.path.join(pkg_rps, '..', '..', 'lib')}:{os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')}"
    )

    # 1. Gazebo Harmonic com o Mundo 3D da Terra e Satélites
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # 2. Nó de Telemetria Orbital ROS 2
    orbit_node = Node(
        package='brazilian_rps_sim',
        executable='orbit_publisher_node.py',
        name='rps_orbit_publisher',
        output='screen',
        parameters=[{
            'time_multiplier': 300.0,
            'elevation_mask_deg': 10.0,
        }]
    )

    return LaunchDescription([
        gz_resource_path,
        gz_sim_system_plugin_path,
        gz_sim,
        orbit_node
    ])
