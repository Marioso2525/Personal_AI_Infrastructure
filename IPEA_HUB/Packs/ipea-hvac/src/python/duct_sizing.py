"""
duct_sizing.py — IPEA_HUB / ipea-hvac
Dimensionamiento de ductos por método de fricción igual conforme ASHRAE/SMACNA.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class DuctShape(str, Enum):
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"


class DuctMaterial(str, Enum):
    GALVANIZED = "galvanized"
    FLEXIBLE = "flexible"
    FIBERGLASS = "fiberglass"


ROUGHNESS_FACTORS = {
    DuctMaterial.GALVANIZED: 0.09,
    DuctMaterial.FLEXIBLE:   0.90,
    DuctMaterial.FIBERGLASS: 0.03,
}

MAX_VELOCITY_M_S = {
    "supply_main":  8.0,
    "supply_branch":6.0,
    "return_main":  6.0,
    "return_branch":4.0,
    "exhaust":      5.0,
}


@dataclass
class DuctSegment:
    name: str
    flow_cfm: float
    duct_type: str = "supply_main"
    material: DuctMaterial = DuctMaterial.GALVANIZED
    friction_rate_Pa_m: float = 1.0


@dataclass
class DuctSizingResult:
    segment: DuctSegment
    flow_m3_s: float
    velocity_m_s: float
    diameter_mm: float
    width_mm: float
    height_mm: float
    pressure_drop_Pa_m: float
    complies_velocity: bool
    recommended_size: str


def cfm_to_m3s(cfm: float) -> float:
    return cfm * 0.000471947


def calculate_circular_duct(flow_m3_s: float, friction_rate_Pa_m: float = 1.0) -> tuple[float, float, float]:
    diameter_m = (
        (flow_m3_s / (math.pi / 4 * math.sqrt(friction_rate_Pa_m / (0.9 * 1.2 * 0.5))))
        ** 0.4
    )
    velocity = flow_m3_s / (math.pi / 4 * diameter_m**2)
    return diameter_m * 1000, velocity, friction_rate_Pa_m


def size_duct_circular(segment: DuctSegment) -> DuctSizingResult:
    flow_m3_s = cfm_to_m3s(segment.flow_cfm)

    max_vel = MAX_VELOCITY_M_S.get(segment.duct_type, 6.0)
    min_area = flow_m3_s / max_vel
    min_diameter_m = math.sqrt(4 * min_area / math.pi)

    fr = segment.friction_rate_Pa_m
    diam_fr_m = (
        (0.66 * (ROUGHNESS_FACTORS[segment.material] ** 0.25)
         * (flow_m3_s ** 0.9))
        / (fr ** 0.5)
    ) ** (1 / 5.02)

    final_diameter_m = max(min_diameter_m, diam_fr_m)
    standard_diameters = [0.10, 0.125, 0.15, 0.175, 0.20, 0.225, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80]
    rounded_diam = next((d for d in standard_diameters if d >= final_diameter_m), standard_diameters[-1])

    area = math.pi / 4 * rounded_diam**2
    velocity = flow_m3_s / area

    actual_fr = (
        0.9 * 1.2 * (flow_m3_s**1.85) / (rounded_diam**5.02)
    ) if rounded_diam > 0 else 0

    return DuctSizingResult(
        segment=segment,
        flow_m3_s=round(flow_m3_s, 4),
        velocity_m_s=round(velocity, 2),
        diameter_mm=round(rounded_diam * 1000),
        width_mm=0,
        height_mm=0,
        pressure_drop_Pa_m=round(actual_fr, 3),
        complies_velocity=velocity <= max_vel,
        recommended_size=f"Ø{round(rounded_diam * 1000):.0f}mm",
    )


def size_duct_rectangular(segment: DuctSegment, aspect_ratio: float = 1.5) -> DuctSizingResult:
    flow_m3_s = cfm_to_m3s(segment.flow_cfm)
    max_vel = MAX_VELOCITY_M_S.get(segment.duct_type, 6.0)

    min_area = flow_m3_s / max_vel
    height_m = math.sqrt(min_area / aspect_ratio)
    width_m = aspect_ratio * height_m

    std_dims = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    h = next((d for d in std_dims if d >= height_m), std_dims[-1])
    w = next((d for d in std_dims if d >= width_m), std_dims[-1])

    area = h * w
    velocity = flow_m3_s / area

    dh = 2 * h * w / (h + w)
    actual_fr = 0.9 * 1.2 * (flow_m3_s**1.85) / (dh**5.02) if dh > 0 else 0

    return DuctSizingResult(
        segment=segment,
        flow_m3_s=round(flow_m3_s, 4),
        velocity_m_s=round(velocity, 2),
        diameter_mm=0,
        width_mm=round(w * 1000),
        height_mm=round(h * 1000),
        pressure_drop_Pa_m=round(actual_fr, 3),
        complies_velocity=velocity <= max_vel,
        recommended_size=f"{round(w*1000):.0f}×{round(h*1000):.0f}mm",
    )


def print_duct_report(results: list[DuctSizingResult]) -> None:
    print("=" * 70)
    print("  DIMENSIONAMIENTO DE DUCTOS — ASHRAE/SMACNA")
    print("=" * 70)
    print(f"  {'SEGMENTO':<20} {'CFM':>6} {'m³/s':>6} {'Vel.m/s':>8} {'Tamaño':>16} {'Pa/m':>6} {'OK':>4}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*8} {'-'*16} {'-'*6} {'-'*4}")
    for r in results:
        ok = "✅" if r.complies_velocity else "❌"
        print(
            f"  {r.segment.name:<20} {r.segment.flow_cfm:>6.0f} {r.flow_m3_s:>6.4f} "
            f"{r.velocity_m_s:>8.2f} {r.recommended_size:>16} {r.pressure_drop_Pa_m:>6.3f} {ok:>4}"
        )
    print("=" * 70)


if __name__ == "__main__":
    segments = [
        DuctSegment("Principal supply", 2000, "supply_main"),
        DuctSegment("Ramal ofic. 101", 400, "supply_branch"),
        DuctSegment("Ramal ofic. 102", 350, "supply_branch"),
        DuctSegment("Retorno principal", 1800, "return_main"),
    ]

    results = [size_duct_circular(s) for s in segments]
    print_duct_report(results)
