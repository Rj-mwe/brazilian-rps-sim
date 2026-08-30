# ==============================================================================
# Containerfile: ROS 2 Jazzy Jalisco + Gazebo Harmonic (Gz Sim)
# Otimizado para Arch Linux (Host) com Podman Rootless e GPU AMD Radeon
# ==============================================================================

# 1. IMAGEM BASE: ROS 2 Jazzy Desktop oficial (Ubuntu 24.04 Noble LTS)
FROM docker.io/osrf/ros:jazzy-desktop

# Define variáveis para instalação não-interativa do apt
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 2. INSTALAÇÃO DE DEPENDÊNCIAS DE SISTEMA, DRIVERS MESA (GPU AMD) E GAZEBO
RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-vulkan-drivers \
    libgl1-mesa-dri \
    libglx-mesa0 \
    mesa-utils \
    vulkan-tools \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    git \
    nano \
    vim \
    curl \
    wget \
    sudo \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# 3. CRIAÇÃO DE USUÁRIO NÃO-ROOT IGUAL AO HOST (UID: 1000, GID: 1000)
ARG USERNAME=rjgamito
ARG USER_UID=1000
ARG USER_GID=1000

RUN if id -u $USER_UID >/dev/null 2>&1; then \
        EXISTING_USER=$(id -un $USER_UID); \
        userdel -r "$EXISTING_USER" 2>/dev/null || true; \
    fi && \
    if getent group $USER_GID >/dev/null 2>&1; then \
        EXISTING_GRP=$(getent group $USER_GID | cut -d: -f1); \
        groupdel "$EXISTING_GRP" 2>/dev/null || true; \
    fi && \
    groupadd --gid $USER_GID $USERNAME && \
    groupadd -f render && \
    groupadd -f video && \
    useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME && \
    usermod -aG sudo,video,render $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# 4. CONFIGURAÇÃO DO ENTRYPOINT E WORKSPACE
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER $USERNAME
WORKDIR /home/$USERNAME/ros2_ws

RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "if [ -f /home/$USERNAME/ros2_ws/install/setup.bash ]; then source /home/$USERNAME/ros2_ws/install/setup.bash; fi" >> /home/$USERNAME/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
