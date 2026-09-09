"""
Adaptador de Saída Gazebo Sim: GazeboWorldControlAdapter
========================================================
Implementa a porta ISimulationControlOutboundPort da camada de domínio.
Atua como um Gateway que traduz ordens de controle da sessão (pause, resume, step)
para chamadas de serviço concretas do Gazebo Sim (/world/<world_name>/control).

Suporta execução tanto de dentro do contêiner quanto a partir do host (via podman exec).
"""

import os
import shutil
import subprocess
from typing import Optional

from rps_br.core.domain.interfaces.ISimulationControlOutboundPort import (
    ISimulationControlOutboundPort,
)


class GazeboWorldControlAdapter(ISimulationControlOutboundPort):
    """Adaptador de saída para despacho de comandos WorldControl para o Gazebo Sim Harmonic."""

    def __init__(
        self,
        world_name: str = "solar_system_rps_world",
        container_name: Optional[str] = None
    ):
        self.world_name = world_name
        self.container_name = container_name or os.environ.get("RPS_CONTAINER_NAME", "rps_sim")
        self.service_name = f"/world/{self.world_name}/control"

    def _call_gz_service(self, req_text: str, timeout_sec: float = 1.0) -> bool:
        """Invoca o comando 'gz service' no ambiente disponível (nativo ou via Podman)."""
        # 1. Se gz estiver disponível nativamente (ex: dentro do contêiner)
        if shutil.which("gz"):
            cmd = [
                "gz", "service",
                "-s", self.service_name,
                "--reqtype", "gz.msgs.WorldControl",
                "--reptype", "gz.msgs.Boolean",
                "--timeout", str(int(timeout_sec * 1000)),
                "--req", req_text
            ]
        # 2. Se estiver no host, despacha via podman exec no contêiner rps_sim
        elif shutil.which("podman"):
            cmd = [
                "podman", "exec", self.container_name,
                "gz", "service",
                "-s", self.service_name,
                "--reqtype", "gz.msgs.WorldControl",
                "--reptype", "gz.msgs.Boolean",
                "--timeout", str(int(timeout_sec * 1000)),
                "--req", req_text
            ]
        else:
            return False

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec + 1.0
            )
            return res.returncode == 0
        except Exception:
            return False

    def pause_simulation(self) -> bool:
        """Pausa o avanço do tempo físico no Gazebo Sim."""
        return self._call_gz_service("pause: true")

    def resume_simulation(self) -> bool:
        """Retoma o avanço do tempo físico no Gazebo Sim."""
        return self._call_gz_service("pause: false")

    def step_simulation(self, steps: int = 1) -> bool:
        """Avança a simulação em passos discretos."""
        if steps <= 1:
            return self._call_gz_service("step: true")
        else:
            return self._call_gz_service(f"multi_step: {steps}")

    def set_simulation_rate(self, multiplier: float) -> bool:
        """O Gazebo Harmonic define RTF principalmente pelo physics block, mas aceita step/rate."""
        return True
