from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rps_br'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['tests', 'tests.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('rps_br/adapters/ros2/launch/*.*')),
        (os.path.join('share', package_name, 'worlds'), glob('rps_br/adapters/gazebo/worlds/*.*')),
        (os.path.join('share', package_name, 'meshes'), glob('rps_br/adapters/gazebo/meshes/*.*')),
        (os.path.join('share', package_name, 'materials'), glob('rps_br/adapters/gazebo/materials/*.*')),
        (os.path.join('share', package_name, 'config'), glob('config/*.*')),
    ],
    install_requires=['setuptools', 'numpy', 'scipy', 'pyyaml'],
    zip_safe=True,
    maintainer='rjgamito',
    maintainer_email='rjgamito@ita.br',
    description='Simulador Matemático e Astrodinâmico do Sistema de Posicionamento Regional Brasileiro (7 Satélites)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rps_constellation_node = rps_br.adapters.ros2.Ros2ConstellationNode:main',
            'rps_web_bridge_node = rps_br.adapters.ros2.Ros2WebBridgeNode:main',
        ],
    },
)
