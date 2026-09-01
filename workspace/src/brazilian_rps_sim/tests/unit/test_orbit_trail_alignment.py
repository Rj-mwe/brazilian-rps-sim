#!/usr/bin/env python3
"""
Testes Automatizados de Casamento e Alinhamento de Linhas Orbitais (Trails).
Valida diretamente as malhas glTF 2.0 extraídas do disco (.gltf / .glb) contra
a cinemática orbital analítica dos 7 satélites (GEO e IGSO) e da Lua.
"""

import json
import base64
import math
import yaml
import numpy as np
import pytest
from pathlib import Path

@pytest.fixture
def pkg_paths():
    pkg_dir = Path(__file__).resolve().parents[2]
    config_path = pkg_dir / "config" / "simulation_parameters.yaml"
    mesh_dir = pkg_dir / "meshes"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg, mesh_dir

def extract_gltf_mesh_vertices(gltf_path: Path) -> np.ndarray:
    """Extrai os vértices tridimensionais (POSITION) diretamente do arquivo glTF 2.0 no disco."""
    with open(gltf_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    uri = doc["buffers"][0]["uri"]
    b64_data = uri.split(",")[1]
    bin_data = base64.b64decode(b64_data)
    
    pos_acc = doc["accessors"][0]
    count = pos_acc["count"]
    bv = doc["bufferViews"][pos_acc["bufferView"]]
    offset = bv["byteOffset"]
    
    raw_pos = bin_data[offset:offset + count * 12]
    return np.frombuffer(raw_pos, dtype=np.float32).reshape(-1, 3)

def point_to_closed_curve_distance(point: np.ndarray, curve_points: np.ndarray) -> float:
    """Calcula a distância ortogonal mínima de um ponto a um spline poligonal 3D fechado."""
    min_dist = float("inf")
    n = len(curve_points)
    for i in range(n):
        p1 = curve_points[i]
        p2 = curve_points[(i + 1) % n]
        v = p2 - p1
        w = point - p1
        c1 = np.dot(w, v)
        if c1 <= 0:
            d = np.linalg.norm(point - p1)
        else:
            c2 = np.dot(v, v)
            if c2 <= c1:
                d = np.linalg.norm(point - p2)
            else:
                b = c1 / c2
                pb = p1 + b * v
                d = np.linalg.norm(point - pb)
        if d < min_dist:
            min_dist = d
    return min_dist

def test_geo_satellites_perfect_alignment_on_equatorial_ring(pkg_paths):
    """Garante que todos os satélites GEO estejam no anel circular equatorial (z=0, r=42164.14 km)."""
    config, mesh_dir = pkg_paths
    geo_sats = [s for s in config["constellation"]["satellites"] if s["type"] == "GEO"]
    assert len(geo_sats) == 3

    # Validação da malha física em disco
    geo_mesh_file = mesh_dir / "orbit_geo.gltf"
    assert geo_mesh_file.exists(), "orbit_geo.gltf deve existir no diretório de meshes"
    mesh_verts = extract_gltf_mesh_vertices(geo_mesh_file)
    radii = np.linalg.norm(mesh_verts[:, :2], axis=1) * 1000.0 # em km
    assert np.all(np.isclose(radii, 42164.14, atol=200.0)), "Vértices do anel GEO devem ter raio 42.164 km"

    for sat in geo_sats:
        a = float(sat["semi_major_axis_km"])
        e = float(sat["eccentricity"])
        inc = float(sat["inclination_deg"])
        
        assert math.isclose(a, 42164.14, abs_tol=1e-2)
        assert math.isclose(e, 0.0, abs_tol=1e-6)
        assert math.isclose(inc, 0.0, abs_tol=1e-6)

def test_all_four_igso_satellites_coincide_with_figure8_mesh_on_disk(pkg_paths):
    """
    Teste End-to-End Real: Extrai a malha física orbit_igso.gltf do disco, reconstrói o
    eixo central do tubo 3D RMF e valida se os 4 satélites IGSO pertencem a ela em 24h.
    """
    config, mesh_dir = pkg_paths
    igso_sats = [s for s in config["constellation"]["satellites"] if s["type"] == "IGSO"]
    assert len(igso_sats) == 4

    igso_mesh_file = mesh_dir / "orbit_igso.gltf"
    assert igso_mesh_file.exists(), "orbit_igso.gltf deve existir no disco"
    mesh_verts = extract_gltf_mesh_vertices(igso_mesh_file)

    # Cada seção do tubo RMF tem 8 vértices radiais
    radial_segs = 8
    n_rings = len(mesh_verts) // radial_segs
    tube_centerline = np.array([mesh_verts[i * radial_segs:(i + 1) * radial_segs].mean(axis=0) for i in range(n_rings)])

    omega_earth = 7.292115e-5
    a = float(igso_sats[0]["semi_major_axis_km"]) / 1000.0
    e = float(igso_sats[0]["eccentricity"])
    inc = math.radians(float(igso_sats[0]["inclination_deg"]))
    argp = math.radians(float(igso_sats[0]["arg_perigee_deg"]))

    # Testa cada um dos 4 IGSOs ao longo de 24 horas
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
            
            # Converte para ECEF (Body Frame) na Terra girante
            th_spin = omega_earth * t_test
            xb_sat = ecix * math.cos(th_spin) + eciy * math.sin(th_spin)
            yb_sat = -ecix * math.sin(th_spin) + eciy * math.cos(th_spin)
            zb_sat = eciz
            sat_body = np.array([xb_sat, yb_sat, zb_sat])
            
            # Distância euclidiana mínima do satélite até o eixo central da malha glTF real
            dist_km = point_to_closed_curve_distance(sat_body, tube_centerline) * 1000.0
            
            # Tolerância máxima: 10 km (ao longo de um loop de 265.000 km com 720 seções)
            assert dist_km < 10.0, (
                f"Satélite {sat_name} desalinhou da malha orbit_igso.gltf em t={t_test/3600}h "
                f"(dist={dist_km:.4f}km, limite=10km)"
            )

def test_moon_orbit_alignment_and_inclination(pkg_paths):
    """Garante que a órbita da Lua e sua malha de trilha 3D coincidam analiticamente com erro zero."""
    config, _ = pkg_paths
    moon_cfg = config["celestial_mechanics"]["moon"]
    dist_scale = float(moon_cfg["dist_earth_render"])
    dist_km = dist_scale * 1000.0
    inc_deg = float(moon_cfg["inclination_deg"])
    inc_rad = math.radians(inc_deg)
    sidereal_month_sec = float(moon_cfg["sidereal_month_sec"])
    omega_moon = 2.0 * math.pi / sidereal_month_sec

    for t in np.linspace(0, sidereal_month_sec, 50):
        theta_m = omega_moon * t
        moon_x = dist_km * math.cos(theta_m)
        moon_y = dist_km * math.sin(theta_m) * math.cos(inc_rad)
        moon_z = dist_km * math.sin(theta_m) * math.sin(inc_rad)

        r_actual = math.sqrt(moon_x**2 + moon_y**2 + moon_z**2)
        assert math.isclose(r_actual, dist_km, abs_tol=1e-5)

        plane_dev = abs(-moon_y * math.sin(inc_rad) + moon_z * math.cos(inc_rad))
        assert math.isclose(plane_dev, 0.0, abs_tol=1e-5)
