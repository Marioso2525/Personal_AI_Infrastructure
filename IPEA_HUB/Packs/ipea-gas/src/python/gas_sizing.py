"""
gas_sizing.py — IPEA_HUB / ipea-gas
Dimensionamiento de tuberías de gas LP y Gas Natural.
Conforme NOM-004-SEDG-2004 y NOM-002-SECRE-2010.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GasType(str, Enum):
    LP = "lp"
    NATURAL = "natural"


class PipeMaterial(str, Enum):
    BLACK_STEEL = "black_steel"
    COPPER = "copper"
    GALVANIZED = "galvanized"
    POLYETHYLENE = "polyethylene"


GAS_PROPERTIES = {
    GasType.LP: {
        "density_kg_m3": 2.00,
        "lower_heating_value_MJ_m3": 93.3,
        "specific_gravity": 1.55,
        "max_pressure_kPa_low": 3.5,
        "max_pressure_kPa_medium": 68.9,
        "design_pressure_drop_Pa": 125,
    },
    GasType.NATURAL: {
        "density_kg_m3": 0.75,
        "lower_heating_value_MJ_m3": 37.3,
        "specific_gravity": 0.60,
        "max_pressure_kPa_low": 3.5,
        "max_pressure_kPa_medium": 68.9,
        "design_pressure_drop_Pa": 125,
    },
}

APPLIANCE_CONSUMPTION: dict[str, dict[GasType, float]] = {
    "estufa_domestica":      {GasType.LP: 2.0,  GasType.NATURAL: 4.0},
    "calentador_10L":        {GasType.LP: 4.5,  GasType.NATURAL: 8.5},
    "calentador_15L":        {GasType.LP: 6.0,  GasType.NATURAL: 12.0},
    "calentador_paso_11L":   {GasType.LP: 5.0,  GasType.NATURAL: 10.0},
    "horno_industrial":      {GasType.LP: 10.0, GasType.NATURAL: 18.0},
    "caldera_pequena":       {GasType.LP: 15.0, GasType.NATURAL: 28.0},
    "quemador_industrial":   {GasType.LP: 25.0, GasType.NATURAL: 45.0},
    "generador_4kW":         {GasType.LP: 3.5,  GasType.NATURAL: 6.5},
    "restaurante_fogones_4": {GasType.LP: 8.0,  GasType.NATURAL: 15.0},
}

PIPE_ROUGHNESS_MM = {
    PipeMaterial.BLACK_STEEL:   0.046,
    PipeMaterial.COPPER:        0.0015,
    PipeMaterial.GALVANIZED:    0.15,
    PipeMaterial.POLYETHYLENE:  0.007,
}

STANDARD_PIPE_DIAMETERS_MM = [12.7, 19.05, 25.4, 31.75, 38.1, 50.8, 63.5, 76.2, 101.6, 127.0, 152.4]


@dataclass
class GasAppliance:
    name: str
    appliance_type: str
    quantity: int
    gas_type: GasType
    demand_factor: float = 1.0

    @property
    def flow_m3_h(self) -> float:
        unit_flow = APPLIANCE_CONSUMPTION.get(self.appliance_type, {}).get(self.gas_type, 0)
        return unit_flow * self.quantity * self.demand_factor


@dataclass
class GasSegment:
    name: str
    appliances: list[GasAppliance]
    length_m: float
    gas_type: GasType
    material: PipeMaterial = PipeMaterial.BLACK_STEEL
    inlet_pressure_kPa: float = 2.8
    simultaneity_factor: float = 0.75

    @property
    def total_flow_m3_h(self) -> float:
        return sum(a.flow_m3_h for a in self.appliances) * self.simultaneity_factor


@dataclass
class GasSizingResult:
    segment: GasSegment
    total_flow_m3_h: float
    velocity_m_s: float
    pressure_drop_Pa: float
    pipe_diameter_mm: float
    outlet_pressure_kPa: float
    complies_velocity: bool
    complies_pressure: bool
    recommended_size: str


def colebrook_friction(Re: float, roughness: float, diameter: float) -> float:
    if Re < 2300:
        return 64 / Re
    f = 0.02
    for _ in range(50):
        f_new = (-2 * math.log10(roughness / (3.7 * diameter) + 2.51 / (Re * math.sqrt(f)))) ** -2
        if abs(f_new - f) < 1e-8:
            break
        f = f_new
    return f


def size_gas_pipe(segment: GasSegment) -> GasSizingResult:
    props = GAS_PROPERTIES[segment.gas_type]
    total_flow = segment.total_flow_m3_h
    flow_m3_s = total_flow / 3600.0

    max_vel = 15.0 if segment.inlet_pressure_kPa > 3.5 else 10.0
    max_dp = props["design_pressure_drop_Pa"]
    rho = props["density_kg_m3"]
    eps = PIPE_ROUGHNESS_MM[segment.material] / 1000.0

    best_diameter = None
    for d_mm in STANDARD_PIPE_DIAMETERS_MM:
        d_m = d_mm / 1000.0
        area = math.pi / 4 * d_m**2
        vel = flow_m3_s / area if area > 0 else 999

        mu = 1.2e-5
        Re = rho * vel * d_m / mu if mu > 0 else 0
        f = colebrook_friction(Re, eps, d_m) if Re > 0 else 0.02

        dp = f * (segment.length_m / d_m) * (rho * vel**2 / 2)

        if vel <= max_vel and dp <= max_dp:
            best_diameter = d_mm
            final_vel = vel
            final_dp = dp
            break

    if best_diameter is None:
        best_diameter = STANDARD_PIPE_DIAMETERS_MM[-1]
        d_m = best_diameter / 1000.0
        area = math.pi / 4 * d_m**2
        final_vel = flow_m3_s / area
        Re = rho * final_vel * d_m / 1.2e-5
        f = colebrook_friction(Re, eps, d_m)
        final_dp = f * (segment.length_m / d_m) * (rho * final_vel**2 / 2)

    outlet_pressure = segment.inlet_pressure_kPa - final_dp / 1000

    return GasSizingResult(
        segment=segment,
        total_flow_m3_h=round(total_flow, 3),
        velocity_m_s=round(final_vel, 2),
        pressure_drop_Pa=round(final_dp, 1),
        pipe_diameter_mm=best_diameter,
        outlet_pressure_kPa=round(outlet_pressure, 3),
        complies_velocity=final_vel <= max_vel,
        complies_pressure=final_dp <= max_dp,
        recommended_size=f'Ø{best_diameter:.1f}mm ({best_diameter/25.4:.2f}")',
    )


def print_gas_report(results: list[GasSizingResult]) -> None:
    gas_name = results[0].segment.gas_type.value.upper() if results else ""
    print("=" * 70)
    print(f"  DIMENSIONAMIENTO DE TUBERÍAS DE GAS {gas_name}")
    print("=" * 70)
    print(f"  {'SEGMENTO':<20} {'m³/h':>6} {'m/s':>6} {'Pa':>8} {'Tuber.':>15} {'OK':>6}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*8} {'-'*15} {'-'*6}")

    for r in results:
        vel_ok = "✅" if r.complies_velocity and r.complies_pressure else "❌"
        print(
            f"  {r.segment.name:<20} {r.total_flow_m3_h:>6.2f} {r.velocity_m_s:>6.2f} "
            f"{r.pressure_drop_Pa:>8.1f} {r.recommended_size:>15} {vel_ok:>6}"
        )

    print("=" * 70)
    print("  Normas: NOM-004-SEDG-2004 | NOM-002-SECRE-2010")
    print("  Velocidad máxima: 10 m/s (baja presión) | 15 m/s (media presión)")
    print("  Caída de presión máxima: 125 Pa (baja presión)")
    print("=" * 70)


if __name__ == "__main__":
    segment = GasSegment(
        name="Alimentación principal",
        appliances=[
            GasAppliance("Estufa cocina", "estufa_domestica", 1, GasType.LP),
            GasAppliance("Calentador agua", "calentador_15L", 1, GasType.LP),
            GasAppliance("Calefacción", "caldera_pequena", 1, GasType.LP),
        ],
        length_m=15,
        gas_type=GasType.LP,
        material=PipeMaterial.BLACK_STEEL,
        inlet_pressure_kPa=2.8,
        simultaneity_factor=0.75,
    )

    result = size_gas_pipe(segment)
    print_gas_report([result])
