import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_arena_game = get_package_share_directory('arena_game')

    world_path = os.path.join(pkg_arena_game, 'worlds', 'arena_game.sdf')

    # 1. Inicializa o Gazebo Harmonic com a Arena 3D
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # 2. Ponte de Comunicação ROS 2 <-> Gazebo
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='game_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        bridge
    ])
