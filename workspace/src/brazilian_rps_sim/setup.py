from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'brazilian_rps_sim'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools', 'numpy'],
    zip_safe=True,
    maintainer='rjgamito',
    maintainer_email='rjgamito@ita.br',
    description='Simulador Matemático e Astrodinâmico do Sistema de Posicionamento Regional Brasileiro (7 Satélites)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'orbit_publisher = brazilian_rps_sim.orbit_publisher_node:main',
            'run_math_simulation = brazilian_rps_sim.constellation_simulator:run_simulation',
        ],
    },
)
