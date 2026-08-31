import math
from brazilian_rps_sim.core.domain.services.KeplerSolverService import KeplerSolverService

def test_kepler_solver_convergence():
    # Testa para várias excentricidades e anomalias médias
    eccentricities = [0.0, 0.06, 0.25, 0.7]
    anomalies = [0.0, math.pi / 4, math.pi / 2, math.pi, 1.5 * math.pi]

    for e in eccentricities:
        for M in anomalies:
            E = KeplerSolverService.solve_kepler(M, e, tol=1e-12)
            residual = abs(E - e * math.sin(E) - (M % (2.0 * math.pi)))
            assert residual < 1e-10, f"Falha de convergência para e={e}, M={M}: residual={residual}"
