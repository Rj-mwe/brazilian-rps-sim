#!/usr/bin/env python3
"""
Módulo de Visualização 2D do Ground-Track (Traço de Solo) da Constelação RPS-BR
Gera e plota as trajetórias sub-satélite sobre o mapa da América do Sul e do Brasil.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

try:
    from brazilian_rps_sim.astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        ecef_to_lat_lon_alt,
        SIDEREAL_DAY
    )
except ImportError:
    from astrodynamics import (
        get_brazilian_rps_constellation,
        propagate_orbit_eci,
        eci_to_ecef,
        ecef_to_lat_lon_alt,
        SIDEREAL_DAY
    )

def generate_ground_track_plot(output_file: str = None):
    if output_file is None:
        # Salva na pasta do workspace
        ws_dir = os.path.expanduser("~/ros2_ws") if os.path.exists(os.path.expanduser("~/ros2_ws")) else "."
        output_file = os.path.join(ws_dir, "rps_ground_track_2d.png")

    constellation = get_brazilian_rps_constellation()
    num_points = 500
    t_seconds = np.linspace(0, SIDEREAL_DAY, num_points)

    plt.figure(figsize=(12, 8), dpi=150)
    ax = plt.subplot(1, 1, 1)

    ax.set_facecolor('#0f172a') # Fundo escuro elegante (Dark Space)
    plt.grid(True, color='#334155', linestyle='--', linewidth=0.7, alpha=0.7)

    # Linhas de Latitude e Longitude Chave
    plt.axhline(0, color='#64748b', linestyle='-', linewidth=1.2, label='Linha do Equador (0°)')
    plt.axvline(-50, color='#475569', linestyle=':', linewidth=1.0, label='Meridiano Central (50°W - BSB)')
    plt.axhline(29, color='#e2e8f0', linestyle=':', linewidth=0.8, alpha=0.5)
    plt.axhline(-29, color='#e2e8f0', linestyle=':', linewidth=0.8, alpha=0.5)
    plt.text(-88, 29.5, '+29 deg (Norte)', color='#94a3b8', fontsize=8)
    plt.text(-88, -28.5, '-29 deg (Sul)', color='#94a3b8', fontsize=8)

    # Cidades Estratégicas Brasileiras
    cidades = {
        "Brasilia (DF)": (-15.79, -47.88),
        "Sao Jose dos Campos (ITA)": (-23.21, -45.88),
        "Manaus (AM)": (-3.12, -60.02),
        "Recife (PE)": (-8.05, -34.88),
        "Porto Alegre (RS)": (-30.03, -51.23),
        "Boa Vista (RR)": (2.82, -60.67),
    }
    for nome, (lat, lon) in cidades.items():
        plt.plot(lon, lat, 'o', color='#38bdf8', markersize=6)
        plt.text(lon + 1.2, lat - 0.5, nome, color='#bae6fd', fontsize=8, fontweight='semibold')

    # Propagação dos Satélites (GEO e IGSO)
    colors = ['#f59e0b', '#06b6d4', '#ec4899', '#10b981']
    markers = ['s', 'o', '^', 'D']

    for idx, sat in enumerate(constellation):
        lats = []
        lons = []
        for t in t_seconds:
            r_eci = propagate_orbit_eci(sat, t)
            r_ecef = eci_to_ecef(r_eci, t)
            lat, lon, alt = ecef_to_lat_lon_alt(r_ecef)
            lats.append(lat)
            lons.append(lon)

        c = colors[idx % len(colors)]
        m = markers[idx % len(markers)]

        if sat.sat_type == "GEO":
            plt.plot(lons[0], lats[0], marker=m, color=c, markersize=10, 
                     label=f'{sat.name} (GEO Fixo)', zorder=5)
        else:
            plt.plot(lons, lats, color=c, linewidth=2.5, 
                     label=f'{sat.name} (Traco em Figura-8)', zorder=4)
            plt.plot(lons[0], lats[0], marker=m, color=c, markersize=8, zorder=5)

    plt.title('Traco de Solo 2D (Ground-Track) - Sistema de Posicionamento Regional Brasileiro (RPS-BR)', 
              color='white', fontsize=12, pad=15, fontweight='bold')
    plt.xlabel('Longitude Geodesica (deg W / deg E)', color='white', fontsize=10)
    plt.ylabel('Latitude Geodesica (deg N / deg S)', color='white', fontsize=10)
    plt.xlim([-90, -20])
    plt.ylim([-45, +20])

    ax.tick_params(colors='white')
    leg = plt.legend(loc='lower left', facecolor='#1e293b', edgecolor='#475569', labelcolor='white')

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    plt.savefig(output_file, facecolor=ax.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"✅ Gráfico do Ground-Track 2D salvo com sucesso em: {output_file}")

if __name__ == '__main__':
    generate_ground_track_plot()
