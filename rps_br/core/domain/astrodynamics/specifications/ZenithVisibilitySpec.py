"""
Specification booleana pura para validar se um satélite está em alta elevação (zênite) sobre uma estação.
"""

class ZenithVisibilitySpec:
    def __init__(self, min_elevation_deg: float = 60.0):
        self.min_elevation_deg = min_elevation_deg

    def is_satisfied_by(self, current_elevation_deg: float) -> bool:
        """Verifica se o satélite atinge o limiar de alta elevação no céu."""
        return current_elevation_deg >= self.min_elevation_deg
