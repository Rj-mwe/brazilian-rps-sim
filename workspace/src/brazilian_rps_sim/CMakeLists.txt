cmake_minimum_required(VERSION 3.20)
project(brazilian_rps_sim)

# Dependências do ROS 2 e Gazebo Sim Harmonic
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)
find_package(gz-math7 REQUIRED)

# ------------------------------------------------------------------------------
# 1. Plugins C++ do Gazebo Sim
# ------------------------------------------------------------------------------

# Plugin 1: Mecânica Orbital Kepleriana para Satélites Artificiais (GEO e IGSO)
add_library(OrbitalMotionPlugin SHARED
    src/OrbitalMotionPlugin.cpp
)
target_include_directories(OrbitalMotionPlugin PUBLIC
    include
    ${GZ-SIM_INCLUDE_DIRS}
)
target_link_libraries(OrbitalMotionPlugin
    gz-sim8::gz-sim8
    gz-plugin2::gz-plugin2
    gz-math7::gz-math7
)

# Plugin 2: Mecânica Celeste Gravitacional Sol-Terra-Lua
add_library(CelestialMechanicsPlugin SHARED
    src/CelestialMechanicsPlugin.cpp
)
target_include_directories(CelestialMechanicsPlugin PUBLIC
    include
    ${GZ-SIM_INCLUDE_DIRS}
)
target_link_libraries(CelestialMechanicsPlugin
    gz-sim8::gz-sim8
    gz-plugin2::gz-plugin2
    gz-math7::gz-math7
)

# Instalação das Bibliotecas de Plugins
install(TARGETS OrbitalMotionPlugin CelestialMechanicsPlugin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

# ------------------------------------------------------------------------------
# 2. Instalação de Recursos Estáticos (Mundos SDF, Launch, Malhas e Texturas)
# ------------------------------------------------------------------------------
install(DIRECTORY worlds launch meshes materials config
    DESTINATION share/${PROJECT_NAME}
)

# ------------------------------------------------------------------------------
# 3. Módulos e Scripts Python do ROS 2
# ------------------------------------------------------------------------------
ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
    scripts/rps_constellation_node
    ${PROJECT_NAME}/ground_track_plotter.py
    ${PROJECT_NAME}/satellite_mesh_generator.py
    ${PROJECT_NAME}/world_generator.py
    ${PROJECT_NAME}/marker_mesh_generator.py
    ${PROJECT_NAME}/camera_auto_focus.py
    DESTINATION lib/${PROJECT_NAME}
)

ament_package()
