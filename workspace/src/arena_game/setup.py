import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'arena_game'

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
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rjgamito',
    maintainer_email='rjgamito@ita.br',
    description='Jogo de Arena e Simulação de Robô Autônomo no Gazebo Harmonic com ROS 2',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'game_agent = arena_game.game_agent:main',
        ],
    },
)
