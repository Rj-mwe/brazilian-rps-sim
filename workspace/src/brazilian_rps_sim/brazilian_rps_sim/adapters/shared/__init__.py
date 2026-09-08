"""
Kernel Compartilhado de Adaptadores (Shared Adapter Kernel)
===========================================================
Grandezas de infraestrutura, paletas de cores universais e utilitários
compartilhados por todas as plataformas externas (Gazebo, CesiumJS, Bevy).
"""

from .color_palette import resolve_color, COLOR_PALETTE

__all__ = ["resolve_color", "COLOR_PALETTE"]
