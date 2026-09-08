"""
Adaptadores de Exportação Tabular e Gráfica (Grau 0)
===================================================
Utilitários de geração de mapas 2D de solo (Ground Track) e persistência
de trajetórias.
"""

from .ground_track_plotter import generate_ground_track_plot

# Alias amigável
plot_ground_track = generate_ground_track_plot

__all__ = ["generate_ground_track_plot", "plot_ground_track"]
