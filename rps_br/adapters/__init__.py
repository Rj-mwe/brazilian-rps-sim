"""
Camada de Adaptadores do Hexágono Dourado (Agrupamento por Ecossistema / Plataforma)
===================================================================================
Estrutura de Borda:
- shared/: Kernel compartilhado de adaptadores (cores, temas, conversores universais).
- ros2/: Plataforma ROS 2 (nós, publicadores de telemetria, bridges).
- gazebo/: Plataforma Gazebo Sim (geração procedural glTF, mundos SDF, tubos RMF).
- export/: Adaptadores de exportação estática (gráficos 2D, ephemeris, CSV).
"""

from . import shared
from . import ros2
from . import gazebo
from . import export

# Retrocompatibilidade
outbound = gazebo
inbound = ros2

__all__ = ["shared", "ros2", "gazebo", "export", "outbound", "inbound"]
