#!/usr/bin/env python3
"""
Testes Unitários para o Adaptador de Exportação (ground_track_plotter.py).
Valida a geração de gráficos 2D de traço de solo a partir de Agregados do Domínio.
"""

import os
import pytest
from rps_br.adapters.export.ground_track_plotter import generate_ground_track_plot, plot_ground_track

def test_ground_track_plotter_generation(tmp_path):
    """Garante que a função de plotagem gere a imagem PNG corretamente."""
    output_png = str(tmp_path / "ground_track_test.png")
    
    generate_ground_track_plot(output_file=output_png)

    assert os.path.exists(output_png)
    assert os.path.getsize(output_png) > 1000, "O arquivo PNG de ground track deve possuir conteúdo válido"

def test_ground_track_plotter_alias():
    """Garante que o alias amigável plot_ground_track aponte para a mesma função."""
    assert plot_ground_track is generate_ground_track_plot
