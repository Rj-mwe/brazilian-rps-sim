"""
Agregado representando a mecânica celeste do Sistema Sol-Terra-Lua.
"""

import math
from dataclasses import dataclass
from brazilian_rps_sim.core.domain.value_objects.Vector3DVO import Vector3DVO
from brazilian_rps_sim.core.domain.value_objects.QuaternionVO import QuaternionVO

@dataclass
class CelestialSystemAggregate:
    dist_sun_earth_render: float = 1200.0
    dist_earth_moon_render: float = 384.4
    obliquity_earth_deg: float = 23.43928
    inclination_moon_deg: float = 5.145
    seconds_per_day: float = 86164.0905
    seconds_per_month: float = 27.321661 * 86400.0
    seconds_per_year: float = 365.256363 * 86400.0

    def compute_state(self, t_sec: float) -> dict:
        """Calcula as posições e orientações dos corpos celestes para o instante t_sec."""
        omega_orbit_earth = 2.0 * math.pi / self.seconds_per_year
        omega_spin_earth = 2.0 * math.pi / self.seconds_per_day
        omega_orbit_moon = 2.0 * math.pi / self.seconds_per_month

        # 1. Terra ao redor do Sol
        theta_earth = omega_orbit_earth * t_sec
        earth_x = self.dist_sun_earth_render * math.cos(theta_earth)
        earth_y = self.dist_sun_earth_render * math.sin(theta_earth)
        earth_pos = Vector3DVO(earth_x, earth_y, 0.0)

        # Rotação da Terra
        earth_spin_rad = (omega_spin_earth * t_sec) % (2.0 * math.pi)
        eps_rad = math.radians(self.obliquity_earth_deg)
        q_earth = QuaternionVO.from_euler(eps_rad, 0.0, earth_spin_rad)

        # 2. Lua ao redor da Terra
        theta_moon = omega_orbit_moon * t_sec
        inc_moon_rad = math.radians(self.inclination_moon_deg)
        moon_rel_x = self.dist_earth_moon_render * math.cos(theta_moon)
        moon_rel_y = self.dist_earth_moon_render * math.sin(theta_moon) * math.cos(inc_moon_rad)
        moon_rel_z = self.dist_earth_moon_render * math.sin(theta_moon) * math.sin(inc_moon_rad)
        moon_rel_pos = Vector3DVO(moon_rel_x, moon_rel_y, moon_rel_z)

        # 3. Fase da Lua
        moon_elongation = (theta_moon - theta_earth) % (2.0 * math.pi)
        illum_pct = (1.0 - math.cos(moon_elongation)) * 50.0

        return {
            'earth_pos': earth_pos,
            'earth_rot': q_earth,
            'moon_rel_pos': moon_rel_pos,
            'moon_illumination_pct': illum_pct,
            'sim_time_sec': t_sec
        }
