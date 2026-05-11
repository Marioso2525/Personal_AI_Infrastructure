"""
pipe_sizing.py — IPEA_HUB / ipea-hydrosanitary
Dimensionamiento de tuberías hidráulicas y sanitarias.
Método de Hunter para agua potable; método de unidades mueble para sanitario.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PipeType(str, Enum):
    COLD_WATER = "cold_water"
    HOT_WATER = "hot_water"
    DRAIN = "drain"
    VENT = "vent"


class PipeMaterial(str, Enum):
    COPPER = "copper"
    CPVC = "cpvc"
    PVC = "pvc"
    GALVANIZED = "galvanized"
    HDPE = "hdpe"


HAZEN_WILLIAMS_C = {
    PipeMaterial.COPPER: 130,
    PipeMaterial.CPVC: 140,
    PipeMaterial.PVC: 140,
    PipeMaterial.GALVANIZED: 100,
    PipeMaterial.HDPE: 150,
}

FIXTURE_UNITS: dict[str, dict[str, int]] = {
    "lavabo":               {"cold": 1, "hot": 1, "drain": 2},
    "WC_tanque":            {"cold": 3, "hot": 0, "drain": 4},
    "WC_fluxometro":        {"cold": 6, "hot": 0, "drain": 4},
    "regadera":             {"cold": 2, "hot": 2, "drain": 2},
    "tina":                 {"cold": 2, "hot": 2, "drain": 4},
    "fregadero_domestico":  {"cold": 2, "hot": 2, "drain": 2},
    "fregadero_comercial":  {"cold": 4, "hot": 4, "drain": 4},
    "lavarropa":            {"cold": 3, "hot": 3, "drain": 3},
    "lavadero":             {"cold": 3, "hot": 3, "drain": 4},
    "urinario_fluxometro":  {"cold": 5, "hot": 0, "drain": 4},
    "urinario_tanque":      {"cold": 3, "hot": 0, "drain": 2},
    "bebedero":             {"cold": 1, "hot": 0, "drain": 1},
    "tornaviaje":           {"cold": 2, "hot": 0, "drain": 0},
    "manguera_jardín":      {"cold": 4, "hot": 0, "drain": 0},
}

STANDARD_PIPE_DIAMETERS_MM = [13, 19, 25, 32, 38, 50, 63, 75, 100, 125, 150, 200, 250, 300]


def hunter_flow_rate_L_s(fixture_units: int, is_flush_valve: bool = False) -> float:
    if fixture_units <= 0:
        return 0.0
    if is_flush_valve:
        if fixture_units <= 10:
            return 0.945
        elif fixture_units <= 25:
            return 1.26
        elif fixture_units <= 50:
            return 1.77
        elif fixture_units <= 100:
            return 2.52
        elif fixture_units <= 200:
            return 3.78
        else:
            return 4.73
    else:
        if fixture_units <= 2:
            return 0.06
        elif fixture_units <= 3:
            return 0.13
        elif fixture_units <= 6:
            return 0.25
        elif fixture_units <= 10:
            return 0.38
        elif fixture_units <= 15:
            return 0.44
        elif fixture_units <= 25:
            return 0.57
        elif fixture_units <= 50:
            return 0.76
        elif fixture_units <= 100:
            return 1.13
        elif fixture_units <= 200:
            return 1.51
        elif fixture_units <= 400:
            return 2.15
        elif fixture_units <= 600:
            return 2.65
        elif fixture_units <= 1000:
            return 3.40
        else:
            return 3.40 + (fixture_units - 1000) * 0.003


def hazen_williams_diameter_mm(
    flow_L_s: float,
    length_m: float,
    pressure_drop_kPa: float,
    material: PipeMaterial = PipeMaterial.CPVC,
) -> float:
    C = HAZEN_WILLIAMS_C[material]
    Q_m3_s = flow_L_s / 1000.0
    hf_m = pressure_drop_kPa / 9.81

    if hf_m <= 0 or length_m <= 0:
        return 0.0

    S = hf_m / length_m
    diam_m = (Q_m3_s / (0.2785 * C * S**0.54)) ** (1 / 2.63)
    return diam_m * 1000


def select_standard_diameter(required_mm: float) -> float:
    for d in STANDARD_PIPE_DIAMETERS_MM:
        if d >= required_mm:
            return float(d)
    return float(STANDARD_PIPE_DIAMETERS_MM[-1])


def velocity_m_s(flow_L_s: float, diam_mm: float) -> float:
    if diam_mm <= 0:
        return 0.0
    area = math.pi / 4 * (diam_mm / 1000) ** 2
    return (flow_L_s / 1000) / area


@dataclass
class FixtureCount:
    fixture_type: str
    quantity: int

    @property
    def cold_units(self) -> int:
        return FIXTURE_UNITS.get(self.fixture_type, {}).get("cold", 0) * self.quantity

    @property
    def hot_units(self) -> int:
        return FIXTURE_UNITS.get(self.fixture_type, {}).get("hot", 0) * self.quantity

    @property
    def drain_units(self) -> int:
        return FIXTURE_UNITS.get(self.fixture_type, {}).get("drain", 0) * self.quantity


@dataclass
class PlumbingSystem:
    name: str
    fixtures: list[FixtureCount]
    available_pressure_kPa: float
    pipe_length_m: float
    material: PipeMaterial = PipeMaterial.CPVC
    has_flush_valves: bool = False


@dataclass
class PlumbingSizingResult:
    system: PlumbingSystem
    total_cold_FU: int
    total_hot_FU: int
    total_drain_FU: int
    cold_flow_L_s: float
    hot_flow_L_s: float
    cold_pipe_mm: float
    hot_pipe_mm: float
    drain_pipe_mm: float
    cold_velocity_m_s: float
    hot_velocity_m_s: float
    velocity_ok_cold: bool
    velocity_ok_hot: bool


def size_plumbing_system(system: PlumbingSystem) -> PlumbingSizingResult:
    total_cold_FU = sum(f.cold_units for f in system.fixtures)
    total_hot_FU = sum(f.hot_units for f in system.fixtures)
    total_drain_FU = sum(f.drain_units for f in system.fixtures)

    cold_flow = hunter_flow_rate_L_s(total_cold_FU, system.has_flush_valves)
    hot_flow = hunter_flow_rate_L_s(total_hot_FU, False)

    pressure_for_pipe = system.available_pressure_kPa * 0.5

    cold_diam_req = hazen_williams_diameter_mm(cold_flow, system.pipe_length_m, pressure_for_pipe, system.material)
    hot_diam_req = hazen_williams_diameter_mm(hot_flow, system.pipe_length_m, pressure_for_pipe, system.material)

    drain_diam_req = 50.0 if total_drain_FU <= 8 else (75.0 if total_drain_FU <= 20 else 100.0)

    cold_std = select_standard_diameter(cold_diam_req)
    hot_std = select_standard_diameter(hot_diam_req)
    drain_std = select_standard_diameter(drain_diam_req)

    vel_cold = velocity_m_s(cold_flow, cold_std)
    vel_hot = velocity_m_s(hot_flow, hot_std)

    return PlumbingSizingResult(
        system=system,
        total_cold_FU=total_cold_FU,
        total_hot_FU=total_hot_FU,
        total_drain_FU=total_drain_FU,
        cold_flow_L_s=round(cold_flow, 3),
        hot_flow_L_s=round(hot_flow, 3),
        cold_pipe_mm=cold_std,
        hot_pipe_mm=hot_std,
        drain_pipe_mm=drain_std,
        cold_velocity_m_s=round(vel_cold, 2),
        hot_velocity_m_s=round(vel_hot, 2),
        velocity_ok_cold=0.6 <= vel_cold <= 2.5,
        velocity_ok_hot=0.6 <= vel_hot <= 2.5,
    )


def print_plumbing_report(result: PlumbingSizingResult) -> None:
    s = result.system
    print("=" * 60)
    print("  DIMENSIONAMIENTO HIDROSANITARIO — MÉTODO HUNTER")
    print("=" * 60)
    print(f"  Sistema:    {s.name}")
    print(f"  Material:   {s.material.value.upper()}")
    print(f"  Presión:    {s.available_pressure_kPa} kPa")
    print()
    print("  ARTEFACTOS:")
    for f in s.fixtures:
        print(f"    {f.fixture_type:<25} × {f.quantity}")
    print()
    print(f"  Unidades mueble agua fría:  {result.total_cold_FU} UM")
    print(f"  Unidades mueble agua cal.:  {result.total_hot_FU} UM")
    print(f"  Unidades mueble drenaje:    {result.total_drain_FU} UM")
    print()
    print(f"  Gasto probable agua fría:   {result.cold_flow_L_s} L/s")
    print(f"  Gasto probable agua cal.:   {result.hot_flow_L_s} L/s")
    print()
    cold_ok = "✅" if result.velocity_ok_cold else "❌"
    hot_ok = "✅" if result.velocity_ok_hot else "❌"
    print(f"  Tubería agua fría:  Ø{result.cold_pipe_mm:.0f}mm — {result.cold_velocity_m_s} m/s {cold_ok}")
    print(f"  Tubería agua cal.:  Ø{result.hot_pipe_mm:.0f}mm — {result.hot_velocity_m_s} m/s {hot_ok}")
    print(f"  Tubería drenaje:    Ø{result.drain_pipe_mm:.0f}mm")
    print()
    print("  Velocidades permitidas: 0.6 – 2.5 m/s")
    print("=" * 60)


if __name__ == "__main__":
    system = PlumbingSystem(
        name="Planta Baja — Baños Públicos",
        fixtures=[
            FixtureCount("WC_fluxometro", 6),
            FixtureCount("urinario_fluxometro", 4),
            FixtureCount("lavabo", 8),
        ],
        available_pressure_kPa=350,
        pipe_length_m=30,
        material=PipeMaterial.CPVC,
        has_flush_valves=True,
    )
    result = size_plumbing_system(system)
    print_plumbing_report(result)
