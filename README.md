# Ambiente Podman: ROS 2 Jazzy Jalisco + Gazebo Harmonic

Ambiente isolado, declarativo e reproduzível para robótica e simulação física 3D no Arch Linux.

## 🏗️ Estrutura do Repositório

```text
/srv/memory/src/ros2-gazebo/
├── Containerfile       # Receita da imagem (ROS 2 Jazzy, Gazebo Harmonic, Mesa GPU AMD)
├── entrypoint.sh       # Script de inicialização que carrega as variáveis do ROS 2
├── build.sh            # Script para construir/atualizar a imagem no Podman
├── run.sh              # Script para iniciar o contêiner com aceleração gráfica e rede DDS
├── README.md           # Este guia didático
└── workspace/          # Seu workspace de código persistente montado em ~/ros2_ws
    └── src/            # Seus pacotes ROS 2, nós Python/C++, modelos SDF e robôs
```

## 🚀 Como Usar

### 1. Construir a imagem (executar apenas na primeira vez ou ao alterar o Containerfile)
```bash
cd /srv/memory/src/ros2-gazebo
./build.sh
```

### 2. Entrar no contêiner interativo
```bash
./run.sh
```

### 3. Rodar uma simulação de teste no Gazebo Harmonic
Dentro do contêiner:
```bash
gz sim shapes.sdf
```
Ou com a ponte ROS 2:
```bash
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="-r shapes.sdf"
```

### 4. Executar comandos diretamente sem abrir o terminal interativo
```bash
./run.sh gz sim -v 4
./run.sh ros2 topic list
```

## 🧠 Detalhes Técnicos de Integração

1. **Aceleração 3D por Hardware (GPU AMD):** Repassa `/dev/dri` com bibliotecas Mesa/Vulkan instaladas no contêiner.
2. **Exibição Gráfica (Wayland & XWayland):** Repassa sockets de display sem comprometer a segurança.
3. **Comunicação DDS (Multi-processo):** `--net=host` e `--ipc=host` permitem que nós ROS 2 dentro do contêiner descubram nós rodando no host ou em outros contêineres.
4. **Permissões Limpas:** Mapeado para o seu UID/GID host (`1000:1000`). Os arquivos criados em `workspace/` pertencem diretamente a você.
