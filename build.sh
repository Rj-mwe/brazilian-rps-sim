#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="ros2-jazzy-gazebo:latest"

echo "============================================================"
echo "🔨 Construindo imagem Podman: ${IMAGE_NAME}"
echo "📁 Diretório base: ${SCRIPT_DIR}"
echo "👤 Usuário: $(id -un) (UID: $(id -u), GID: $(id -g))"
echo "============================================================"

podman build \
    --build-arg USERNAME="$(id -un)" \
    --build-arg USER_UID="$(id -u)" \
    --build-arg USER_GID="$(id -g)" \
    -t "${IMAGE_NAME}" \
    -f "${SCRIPT_DIR}/Containerfile" \
    "${SCRIPT_DIR}"

echo ""
echo "✅ Imagem ${IMAGE_NAME} construída com sucesso no Podman!"
echo "🚀 Para executar o contêiner, use: ./run.sh"
