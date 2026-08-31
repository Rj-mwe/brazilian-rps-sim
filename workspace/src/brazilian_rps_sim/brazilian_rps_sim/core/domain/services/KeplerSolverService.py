"""
Serviço de Domínio para resolução numérica de equações transcendentais de Kepler e anomalias orbitais.
"""

import math

class KeplerSolverService:
    @staticmethod
    def solve_kepler(M: float, e: float, tol: float = 1e-10, max_iter: int = 30) -> float:
        """Resolve a Equação Transcendental de Kepler E - e*sin(E) = M pelo método de Newton-Raphson."""
        M_norm = M % (2.0 * math.pi)
        E = M_norm if e < 0.8 else math.pi

        for _ in range(max_iter):
            f = E - e * math.sin(E) - M_norm
            f_prime = 1.0 - e * math.cos(E)
            dE = -f / f_prime
            E += dE
            if abs(dE) < tol:
                break
        return E

    @staticmethod
    def true_anomaly_from_eccentric(E: float, e: float) -> float:
        """Calcula a anomalia verdadeira ν a partir da anomalia excêntrica E."""
        sin_nu = (math.sqrt(1.0 - e**2) * math.sin(E)) / (1.0 - e * math.cos(E))
        cos_nu = (math.cos(E) - e) / (1.0 - e * math.cos(E))
        return math.atan2(sin_nu, cos_nu)
