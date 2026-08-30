#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="ros2-jazzy-gazebo:latest"
USER_ID="$(id -u)"
USER_NAME="$(id -un)"

mkdir -p "${SCRIPT_DIR}/workspace/src"

INTERACTIVE_OPTS=()
if [ -t 0 ]; then
    INTERACTIVE_OPTS+=("-it")
else
    INTERACTIVE_OPTS+=("-i")
fi

PODMAN_ARGS=(
    --rm
    "${INTERACTIVE_OPTS[@]}"
    --hostname "ros2-gazebo"
    --net=host
    --ipc=host
    -e GZ_IP="127.0.0.1"
    --userns=keep-id
    --device /dev/dri
    --device /dev/input
    -e DISPLAY="${DISPLAY:-:1}"
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro
    -e LIBGL_DRI3_DISABLE=1
    -e QSG_RENDER_LOOP=basic
    -e QT_QPA_PLATFORM=xcb
    -e QT_X11_NO_MITSHM=1
    -e GZ_SIM_RESOURCE_PATH="/home/${USER_NAME}/ros2_ws/install/brazilian_rps_sim/share:/home/${USER_NAME}/ros2_ws/install/brazilian_rps_sim/share/brazilian_rps_sim"
    -e GZ_SIM_SYSTEM_PLUGIN_PATH="/home/${USER_NAME}/ros2_ws/install/brazilian_rps_sim/lib"
    -e LD_LIBRARY_PATH="/home/${USER_NAME}/ros2_ws/install/brazilian_rps_sim/lib"
    -e XDG_RUNTIME_DIR="/run/user/${USER_ID}"
    -v "/run/user/${USER_ID}:/run/user/${USER_ID}:rw"
    -v "${SCRIPT_DIR}/workspace:/home/${USER_NAME}/ros2_ws:Z"
)

if [ -n "${XAUTHORITY}" ] && [ -e "${XAUTHORITY}" ]; then
    PODMAN_ARGS+=(
        -e XAUTHORITY="${XAUTHORITY}"
        -v "${XAUTHORITY}:${XAUTHORITY}:ro"
    )
elif [ -e "${HOME}/.Xauthority" ]; then
    PODMAN_ARGS+=(
        -e XAUTHORITY="/home/${USER_NAME}/.Xauthority"
        -v "${HOME}/.Xauthority:/home/${USER_NAME}/.Xauthority:ro"
    )
fi

if [ "$#" -gt 0 ]; then
    exec podman run "${PODMAN_ARGS[@]}" "${IMAGE_NAME}" "$@"
else
    echo "===================================================================="
    echo "🤖 Container ROS 2 Jazzy + Gazebo Harmonic Ativo"
    echo "💡 PROJETOS DISPONÍVEIS:"
    echo "   🌌 [MECÂNICA CELESTE: SOL - TERRA - LUA (Escala Real)]:"
    echo "       ros2 launch brazilian_rps_sim celestial_sim.launch.py"
    echo "   🛰️ [RPS BRASIL: SATÉLITES GEO & IGSO]:"
    echo "       ros2 launch brazilian_rps_sim constellation_sim.launch.py"
    echo "   🚗 [ARENA GAMEBOT]:"
    echo "       ros2 launch arena_game play_game.launch.py"
    echo "   Para sair do contêiner: exit"
    echo "===================================================================="
    exec podman run "${PODMAN_ARGS[@]}" "${IMAGE_NAME}" bash
fi
