#!/usr/bin/env bash
set -e

if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source "/opt/ros/jazzy/setup.bash"
fi

if [ -f "/home/rjgamito/ros2_ws/install/setup.bash" ]; then
    source "/home/rjgamito/ros2_ws/install/setup.bash"
fi

export GZ_SIM_RESOURCE_PATH="/home/rjgamito/ros2_ws/install/brazilian_rps_sim/share:/home/rjgamito/ros2_ws/install/brazilian_rps_sim/share/brazilian_rps_sim:${GZ_SIM_RESOURCE_PATH}"
export GZ_SIM_SYSTEM_PLUGIN_PATH="/home/rjgamito/ros2_ws/install/brazilian_rps_sim/lib:${GZ_SIM_SYSTEM_PLUGIN_PATH}"
export GZ_GUI_PLUGIN_PATH="/home/rjgamito/ros2_ws/install/brazilian_rps_sim/lib:${GZ_GUI_PLUGIN_PATH}"
export LD_LIBRARY_PATH="/home/rjgamito/ros2_ws/install/brazilian_rps_sim/lib:${LD_LIBRARY_PATH}"

exec "$@"
