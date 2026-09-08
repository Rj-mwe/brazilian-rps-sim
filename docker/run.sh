#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/rps_br" ]; then
    REPO_ROOT="${SCRIPT_DIR}"
else
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

IMAGE_NAME="ros2-jazzy-gazebo:latest"
USER_ID="$(id -u)"
USER_NAME="$(id -un)"

CONTAINER_WS="${HOME}/Contêineres e VM's/brazilian-rps-sim"
mkdir -p "${CONTAINER_WS}/build"
mkdir -p "${CONTAINER_WS}/install"
mkdir -p "${CONTAINER_WS}/log"

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
    -e GZ_SIM_RESOURCE_PATH="/home/${USER_NAME}/ros2_ws/install/rps_br/share:/home/${USER_NAME}/ros2_ws/install/rps_br/share/rps_br"
    -e GZ_SIM_SYSTEM_PLUGIN_PATH="/home/${USER_NAME}/ros2_ws/install/rps_br/lib"
    -e LD_LIBRARY_PATH="/home/${USER_NAME}/ros2_ws/install/rps_br/lib"
    -e XDG_RUNTIME_DIR="/run/user/${USER_ID}"
    -v "/run/user/${USER_ID}:/run/user/${USER_ID}:rw"
    -v "${REPO_ROOT}:/home/${USER_NAME}/ros2_ws/src/rps_br:Z"
    -v "${CONTAINER_WS}/build:/home/${USER_NAME}/ros2_ws/build:Z"
    -v "${CONTAINER_WS}/install:/home/${USER_NAME}/ros2_ws/install:Z"
    -v "${CONTAINER_WS}/log:/home/${USER_NAME}/ros2_ws/log:Z"
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
    echo "   🛰️ [SIMULAÇÃO UNIFICADA RPS-BR (Sol, Terra, Lua, 7 Satélites)]:"
    echo "       ros2 launch rps_br unified_sim.launch.py"
    echo "   Para compilar alterações no contêiner:"
    echo "       colcon build --symlink-install"
    echo "   Para sair do contêiner: exit"
    echo "===================================================================="
    exec podman run "${PODMAN_ARGS[@]}" "${IMAGE_NAME}" bash
fi
