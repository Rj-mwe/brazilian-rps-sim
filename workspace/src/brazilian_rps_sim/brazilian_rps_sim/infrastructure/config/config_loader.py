"""
Módulo de Infraestrutura: Carregador de Configuração Declarativa YAML
====================================================================
Localiza e carrega o arquivo central 'simulation_parameters.yaml',
fornecendo a fonte única da verdade (SSOT) para parâmetros de simulação,
constelação orbital e renderização gráfica.
"""

import os
import yaml

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:
    get_package_share_directory = None


def find_config_file(filename: str = 'simulation_parameters.yaml') -> str:
    """Busca o arquivo de configuração YAML no pacote ROS 2 instalado ou em caminhos de desenvolvimento."""
    paths_to_check = []
    if get_package_share_directory:
        try:
            pkg_share = get_package_share_directory('brazilian_rps_sim')
            paths_to_check.append(os.path.join(pkg_share, 'config', filename))
        except Exception:
            pass

    # Caminhos relativos de desenvolvimento
    current_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_check.append(os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'config', filename)))
    paths_to_check.append(os.path.join('/home/rjgamito/Projetos/Engenharia/Aeroespacial/brazilian-rps-sim/workspace/src/brazilian_rps_sim/config', filename))

    for p in paths_to_check:
        if os.path.exists(p):
            return os.path.abspath(p)
    return ""


def load_simulation_config(config_path: str = None) -> dict:
    """Carrega o dicionário de configurações a partir do arquivo YAML."""
    if not config_path:
        config_path = find_config_file()

    if not config_path or not os.path.exists(config_path):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
