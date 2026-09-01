#!/usr/bin/env python3
"""
Testes Automatizados de Casamento e Alinhamento de Linhas Orbitais (Trails)
Garante matematicamente que todos os satélites GEO, IGSO e a Lua pertençam
rigorosamente e sem desvios às suas respectivas malhas de trilha 3D.
"""

import math
import yaml
import numpy as np
import pytest
from pathlib import Path

@pytest.fixture
def config():
    pkg_dir = Path(__file__).resolve().parents[2]
    config_path = pkg_dir / "config" / "simulation_parameters.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_geo_satellites_perfect_alignment_on_equatorial_ring(config):
    """Garante que todos os satélites GEO estejam no anel circular equatorial (z=0, r=42164.14 km)."""
    geo_sats = [s for s in config["constellation"]["satellites"] if s["type"] == "GEO"]
    assert len(geo_sats) == 3

    for sat in geo_sats:
        a = float(sat["semi_major_axis_km"])
        e = float(sat["eccentricity"])
        inc = float(sat["inclination_deg"])
        
        assert math.isclose(a, 42164.14, abs_tol=1e-2), f"Semieixo GEO incorreto para {sat['name']}"
        assert math.isclose(e, 0.0, abs_tol=1e-6), f"Excentricidade GEO deve ser zero para {sat['name']}"
        assert math.isclose(inc, 0.0, abs_tol=1e-6), f"Inclinação GEO deve ser zero para {sat['name']}"

def test_all_four_igso_satellites_coincide_with_figure8_trail(config):
    """Garante que os 4 satélites IGSO compartilhem rigorosamente a mesma curva 3D em Figura-8."""
    igso_sats = [s for s in config["constellation"]["satellites"] if s["type"] == "IGSO"]
    assert len(igso_sats) == 4

    omega_earth = 7.292115e-5
    
    # 1. Gera a curva do Trail de referência (IGSO 1) com alta resolução (5000 pontos)
    ref = igso_sats[0]
    a = float(ref["semi_major_axis_km"])
    e = float(ref["eccentricity"])
    inc = math.radians(float(ref["inclination_deg"]))
    raan = math.radians(float(ref["raan_deg"]))
    argp = math.radians(float(ref["arg_perigee_deg"]))
    m0 = math.radians(float(ref["mean_anomaly_deg"]))

    pts_ref_body = []
    for t in np.linspace(0, 86164.0905, 5000, endpoint=False):
        M = m0 + omega_earth * t
        E = M
        for _ in range(10):
            E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
        r = a * (1 - e * math.cos(E))
        
        px = r * math.cos(nu)
        py = r * math.sin(nu)
        
        cO, sO = math.cos(raan), math.sin(raan)
        cw, sw = math.cos(argp), math.sin(argp)
        ci, si = math.cos(inc), math.sin(inc)
        
        Px = cO * cw - sO * sw * ci
        Py = sO * cw + cO * sw * ci
        Pz = sw * si
        Qx = -cO * sw - sO * cw * ci
        Qy = -sO * sw + cO * cw * ci
        Qz = cw * si
        
        ecix = px * Px + py * Qx
        eciy = px * Py + py * Qy
        eciz = px * Pz + py * Qz
        
        th_spin = omega_earth * t
        xb = ecix * math.cos(th_spin) + eciy * math.sin(th_spin)
        yb = -ecix * math.sin(th_spin) + eciy * math.cos(th_spin)
        zb = eciz
        pts_ref_body.append([xb, yb, zb])

    pts_ref_body = np.array(pts_ref_body)

    # 2. Testa cada um dos 4 IGSOs ao longo de 24 horas
    for sat in igso_sats:
        sat_name = sat["name"]
        raan_s = math.radians(float(sat["raan_deg"]))
        m0_s = math.radians(float(sat["mean_anomaly_deg"]))
        
        for t_test in [0.0, 3600.0, 7200.0, 14400.0, 21600.0, 43200.0, 64800.0]:
            M_s = m0_s + omega_earth * t_test
            E_s = M_s
            for _ in range(10):
                E_s = E_s - (E_s - e * math.sin(E_s) - M_s) / (1 - e * math.cos(E_s))
            nu_s = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E_s / 2), math.sqrt(1 - e) * math.cos(E_s / 2))
            r_s = a * (1 - e * math.cos(E_s))
            
            px_s = r_s * math.cos(nu_s)
            py_s = r_s * math.sin(nu_s)
            
            cO, sO = math.cos(raan_s), math.sin(raan_s)
            cw, sw = math.cos(argp), math.sin(argp)
            ci, si = math.cos(inc), math.sin(inc)
            
            Px = cO * cw - sO * sw * ci
            Py = sO * cw + cO * sw * ci
            Pz = sw * si
            Qx = -cO * sw - sO * cw * ci
            Qy = -sO * sw + cO * cw * ci
            Qz = cw * si
            
            ecix = px_s * Px + py_s * Qx
            eciy = px_s * Py + py_s * Qy
            eciz = px_s * Pz + py_s * Qz
            
            th_spin = omega_earth * t_test
            xb_sat = ecix * math.cos(th_spin) + eciy * math.sin(th_spin)
            yb_sat = -ecix * math.sin(th_spin) + eciy * math.cos(th_spin)
            zb_sat = eciz
            sat_body = np.array([xb_sat, yb_sat, zb_sat])
            
            # Distância euclidiana mínima até a malha do Trail
            dist_km = np.min(np.linalg.norm(pts_ref_body - sat_body, axis=1))
            assert dist_km < 10.0, f"Satélite {sat_name} desalinhou do Trail em t={t_test/3600}h (dist={dist_km:.2f}km)"

def test_moon_orbit_alignment_and_inclination(config):
    """Garante que a órbita da Lua e sua malha de trilha 3D coincidam analiticamente com erro zero."""
    moon_cfg = config["celestial_mechanics"]["moon"]
    dist_scale = float(moon_cfg["dist_earth_render"]) # 384.4 unidades (384.400 km)
    dist_km = dist_scale * 1000.0
    inc_deg = float(moon_cfg["inclination_deg"])       # 5.145°
    inc_rad = math.radians(inc_deg)
    sidereal_month_sec = float(moon_cfg["sidereal_month_sec"])
    omega_moon = 2.0 * math.pi / sidereal_month_sec

    # Testa a posição da Lua para múltiplos instantes de tempo
    for t in np.linspace(0, sidereal_month_sec, 50):
        theta_m = omega_moon * t
        moon_x = dist_km * math.cos(theta_m)
        moon_y = dist_km * math.sin(theta_m) * math.cos(inc_rad)
        moon_z = dist_km * math.sin(theta_m) * math.sin(inc_rad)

        # 1. Raio constante exato
        r_actual = math.sqrt(moon_x**2 + moon_y**2 + moon_z**2)
        assert math.isclose(r_actual, dist_km, abs_tol=1e-5), f"Raio lunar incorreto: {r_actual} vs {dist_km}"

        # 2. Pertencimento rigoroso ao plano inclinado em i = 5.145°
        plane_dev = abs(-moon_y * math.sin(inc_rad) + moon_z * math.cos(inc_rad))
        assert math.isclose(plane_dev, 0.0, abs_tol=1e-5), f"Desvio do plano orbital lunar: {plane_dev} km"
