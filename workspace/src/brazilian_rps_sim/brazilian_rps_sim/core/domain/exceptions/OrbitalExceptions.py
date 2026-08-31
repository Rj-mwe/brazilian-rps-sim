"""
Exceções de violação de regras e física de domínio astrodinâmico.
"""

class DomainException(Exception):
    """Exceção base do domínio."""
    pass

class OrbitalSingularityException(DomainException):
    """Lançada quando uma singularidade matemática ocorre (ex: colisão ou r -> 0)."""
    pass

class InvalidSatelliteParametersException(DomainException):
    """Lançada quando parâmetros orbitais de satélite violam limites físicos."""
    pass
