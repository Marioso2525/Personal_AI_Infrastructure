"""
voltage_drop.py — IPEA_HUB / ipea-electrical
Calcula caída de tensión conforme NOM-001-SEDE-2012.
Límite: 3% en circuitos ramales, 5% total alimentador + ramal.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


TABLES_PATH = Path(__file__).parent.parent / "standards" / "nom-001-sede-2012" / "tables.json"
FACTORS_PATH = Path(__file__).parent.parent / "standards" / "nom-001-sede-2012" / "factors.json"


class CircuitType(str, Enum):
    SINGLE_PHASE_2W = "single_phase_2w"
    SINGLE_PHASE_3W = "single_phase_3w"
    THREE_PHASE_3W = "three_phase_3w"
    THREE_PHASE_4W = "three_phase_4w"


class ConductorMaterial(str, Enum):
    COPPER = "copper"
    ALUMINUM = "aluminum"


@dataclass
class VoltageDropInput:
    voltage_V: float
    current_A: float
    length_m: float
    conductor_awg: str
    circuit_type: CircuitType = CircuitType.THREE_PHASE_4W
    material: ConductorMaterial = ConductorMaterial.COPPER
    power_factor: float = 0.85
    conductor_temp_C: int = 75


@dataclass
class VoltageDropResult:
    input: VoltageDropInput
    resistance_mohm_per_m: float
    voltage_drop_V: float
    voltage_drop_percent: float
    nom_limit_percent: float
    complies_nom: bool
    receiving_voltage_V: float
    notes: list[str] = field(default_factory=list)


def _load_tables() -> tuple[dict, dict]:
    with open(TABLES_PATH) as f:
        tables = json.load(f)
    with open(FACTORS_PATH) as f:
        factors = json.load(f)
    return tables, factors


def _get_resistance(awg: str, material: ConductorMaterial, tables: dict) -> float:
    key = (
        "resistance_copper_mohm_per_m"
        if material == ConductorMaterial.COPPER
        else "resistance_aluminum_mohm_per_m"
    )
    resistance_table = tables[key]
    if awg not in resistance_table:
        raise ValueError(f"Calibre '{awg}' no encontrado en tablas NOM-001-SEDE-2012.")
    return resistance_table[awg]


def calculate_voltage_drop(inp: VoltageDropInput) -> VoltageDropResult:
    tables, _ = _load_tables()

    r_mohm_per_m = _get_resistance(inp.conductor_awg, inp.material, tables)
    r_ohm_per_m = r_mohm_per_m / 1000.0

    if inp.circuit_type in (CircuitType.SINGLE_PHASE_2W, CircuitType.SINGLE_PHASE_3W):
        multiplier = 2.0
    else:
        multiplier = math.sqrt(3)

    vd_V = multiplier * r_ohm_per_m * inp.length_m * inp.current_A * inp.power_factor
    vd_percent = (vd_V / inp.voltage_V) * 100.0

    nom_limit = tables["voltage_drop_limits_nom"]["branch_circuits_max_percent"]
    complies = vd_percent <= nom_limit

    notes = []
    if vd_percent > 5.0:
        notes.append("CRÍTICO: Caída de tensión > 5%. Aumentar calibre urgentemente.")
    elif vd_percent > 3.0:
        notes.append("ADVERTENCIA: Excede límite NOM-001-SEDE-2012 de 3% para circuito ramal.")
    else:
        notes.append("OK: Cumple NOM-001-SEDE-2012 (≤ 3%).")

    if inp.power_factor < 0.80:
        notes.append("Nota: Factor de potencia bajo. Considerar banco de capacitores.")

    return VoltageDropResult(
        input=inp,
        resistance_mohm_per_m=r_mohm_per_m,
        voltage_drop_V=round(vd_V, 3),
        voltage_drop_percent=round(vd_percent, 2),
        nom_limit_percent=nom_limit,
        complies_nom=complies,
        receiving_voltage_V=round(inp.voltage_V - vd_V, 2),
        notes=notes,
    )


def find_minimum_conductor(
    voltage_V: float,
    current_A: float,
    length_m: float,
    circuit_type: CircuitType = CircuitType.THREE_PHASE_4W,
    material: ConductorMaterial = ConductorMaterial.COPPER,
    power_factor: float = 0.85,
    max_vd_percent: float = 3.0,
) -> Optional[str]:
    tables, _ = _load_tables()
    conductor_order = tables["standard_conductor_sizes_awg_order"]

    for awg in conductor_order:
        r_key = (
            "resistance_copper_mohm_per_m"
            if material == ConductorMaterial.COPPER
            else "resistance_aluminum_mohm_per_m"
        )
        if awg not in tables[r_key]:
            continue

        r_ohm_per_m = tables[r_key][awg] / 1000.0
        multiplier = 2.0 if circuit_type in (CircuitType.SINGLE_PHASE_2W, CircuitType.SINGLE_PHASE_3W) else math.sqrt(3)
        vd = multiplier * r_ohm_per_m * length_m * current_A * power_factor
        vd_pct = (vd / voltage_V) * 100.0

        if vd_pct <= max_vd_percent:
            return awg

    return None


def print_report(result: VoltageDropResult) -> None:
    inp = result.input
    print("=" * 60)
    print("  CÁLCULO DE CAÍDA DE TENSIÓN — NOM-001-SEDE-2012")
    print("=" * 60)
    print(f"  Voltaje nominal:       {inp.voltage_V} V")
    print(f"  Corriente de diseño:   {inp.current_A} A")
    print(f"  Longitud del circuito: {inp.length_m} m")
    print(f"  Conductor:             {inp.conductor_awg} {inp.material.value.upper()}")
    print(f"  Tipo de circuito:      {inp.circuit_type.value}")
    print(f"  Factor de potencia:    {inp.power_factor}")
    print("-" * 60)
    print(f"  Resistencia:           {result.resistance_mohm_per_m} mΩ/m")
    print(f"  Caída de tensión:      {result.voltage_drop_V} V")
    print(f"  Caída de tensión:      {result.voltage_drop_percent}%")
    print(f"  Límite NOM:            {result.nom_limit_percent}%")
    print(f"  Voltaje en receptor:   {result.receiving_voltage_V} V")
    print(f"  Cumple NOM:            {'✅ SÍ' if result.complies_nom else '❌ NO'}")
    print("-" * 60)
    for note in result.notes:
        print(f"  {note}")
    print("=" * 60)


if __name__ == "__main__":
    example = VoltageDropInput(
        voltage_V=220,
        current_A=45,
        length_m=80,
        conductor_awg="6AWG",
        circuit_type=CircuitType.THREE_PHASE_4W,
        material=ConductorMaterial.COPPER,
        power_factor=0.85,
    )
    result = calculate_voltage_drop(example)
    print_report(result)

    print("\n--- Búsqueda de calibre mínimo ---")
    min_awg = find_minimum_conductor(
        voltage_V=220,
        current_A=45,
        length_m=80,
        circuit_type=CircuitType.THREE_PHASE_4W,
        material=ConductorMaterial.COPPER,
        power_factor=0.85,
        max_vd_percent=3.0,
    )
    print(f"Calibre mínimo para ≤3% VD: {min_awg}")
