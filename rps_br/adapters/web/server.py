"""
Compatibilidade retroativa com o servidor legado rps_br.adapters.web.server.
O servidor oficial reside em rps_br.adapters.api.server.
"""

from rps_br.adapters.api.server import app, run_server

__all__ = ["app", "run_server"]

if __name__ == "__main__":
    run_server()
