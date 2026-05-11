"""
nom_validator.py — IPEA_HUB / ipea-electrical
Validación integral de circuitos eléctricos contra NOM-001-SEDE-2012.
Verifica: ampacidad, caída de tensión, protecciones y canalización.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from voltage_drop import (
    VoltageDropInput,
    CircuitType,
    ConductorMaterial,
    calculate_voltage_drop,
)

TABLES_PATH = Path(__file__).parent.parent / "standards" / "nom-001-sede-2012" / "tables.json"
FACTORS_PATH = Path(__file__).parent.parent / "standards" / "nom-001-sede-2012" / "factors.json"


@dataclass
class CircuitDesign:
    description: str
    voltage_V: float
    current_A: float
    length_m: float
    conductor_awg: str
    conduit_size: str
    num_conductors_in_conduit: int
    circuit_type: CircuitType
    material: ConductorMaterial
    ambient_temp_C: int
    conductor_insulation_temp: int
    protection_A: float
    is_continuous_load: bool = False
    power_factor: float = 0.85
    motor_load: bool = False


@dataclass
class ValidationItem:
    name: str
    passed: bool
    value: str
    limit: str
    reference: str
    recommendation: Optional[str] = None


@dataclass
class NOMValidationReport:
    circuit: CircuitDesign
    items: list[ValidationItem] = field(default_factory=list)

    @property
    def all_pass(self) -> bool:
        return all(item.passed for item in self.items)

    @property
    def pass_count(self) -> int:
        return sum(1 for item in self.items if item.passed)

    @property
    def fail_count(self) -> int:
        return sum(1 for item in self.items if not item.passed)


def _load_tables() -> tuple[dict, dict]:
    with open(TABLES_PATH) as f:
        tables = json.load(f)
    with open(FACTORS_PATH) as f:
        factors = json.load(f)
    return tables, factors


def _get_corrected_ampacity(
    awg: str,
    material: ConductorMaterial,
    insulation_temp: int,
    ambient_temp_C: int,
    num_conductors: int,
    tables: dict,
    factors: dict,
) -> float:
    ampacity_key = (
        "conductor_ampacity_copper" if material == ConductorMaterial.COPPER else "conductor_ampacity_aluminum"
    )
    base_table = tables[ampacity_key]

    if awg not in base_table:
        raise ValueError(f"Calibre {awg} no en tablas.")

    temp_key = f"{insulation_temp}C"
    base_ampacity = base_table[awg].get(temp_key)
    if base_ampacity is None:
        raise ValueError(f"Temperatura de aislamiento {insulation_temp}°C no disponible para {awg}.")

    temp_factors = factors["temperature_correction_factors"]["ambient_temp_C"]
    temp_str = str(min(int(ambient_temp_C), 80))
    temp_corr = temp_factors.get(temp_str, {}).get(temp_key, 1.0)
    if temp_corr is None:
        raise ValueError(
            f"Conductor {insulation_temp}°C no puede operar a temperatura ambiente de {ambient_temp_C}°C."
        )

    bundling_factors = factors["bundling_adjustment_factors"]
    if num_conductors <= 3:
        bundle_corr = 1.0
    elif num_conductors <= 6:
        bundle_corr = bundling_factors["4_to_6"]
    elif num_conductors <= 9:
        bundle_corr = bundling_factors["7_to_9"]
    elif num_conductors <= 20:
        bundle_corr = bundling_factors["10_to_20"]
    elif num_conductors <= 30:
        bundle_corr = bundling_factors["21_to_30"]
    elif num_conductors <= 40:
        bundle_corr = bundling_factors["31_to_40"]
    else:
        bundle_corr = bundling_factors["41_plus"]

    return round(base_ampacity * temp_corr * bundle_corr, 1)


def validate_ampacity(circuit: CircuitDesign, tables: dict, factors: dict) -> ValidationItem:
    corrected = _get_corrected_ampacity(
        circuit.conductor_awg,
        circuit.material,
        circuit.conductor_insulation_temp,
        circuit.ambient_temp_C,
        circuit.num_conductors_in_conduit,
        tables,
        factors,
    )

    required_current = circuit.current_A * (1.25 if circuit.is_continuous_load else 1.0)

    passed = corrected >= required_current
    mult_note = " × 1.25 (carga continua)" if circuit.is_continuous_load else ""
    recommendation = None if passed else (
        f"Aumentar calibre. Ampacidad corregida {corrected}A < requerida {required_current:.1f}A."
    )

    return ValidationItem(
        name="Ampacidad NOM-001-SEDE-2012",
        passed=passed,
        value=f"{corrected}A corregida (base × temp × agrupamiento)",
        limit=f"≥ {required_current:.1f}A ({circuit.current_A}A{mult_note})",
        reference="NOM-001-SEDE-2012 §310.15",
        recommendation=recommendation,
    )


def validate_voltage_drop(circuit: CircuitDesign, tables: dict) -> ValidationItem:
    inp = VoltageDropInput(
        voltage_V=circuit.voltage_V,
        current_A=circuit.current_A,
        length_m=circuit.length_m,
        conductor_awg=circuit.conductor_awg,
        circuit_type=circuit.circuit_type,
        material=circuit.material,
        power_factor=circuit.power_factor,
    )
    result = calculate_voltage_drop(inp)
    limit = tables["voltage_drop_limits_nom"]["branch_circuits_max_percent"]

    return ValidationItem(
        name="Caída de Tensión NOM-001-SEDE-2012",
        passed=result.complies_nom,
        value=f"{result.voltage_drop_percent}% ({result.voltage_drop_V}V)",
        limit=f"≤ {limit}%",
        reference="NOM-001-SEDE-2012 §210.19(A)(1) Nota 4",
        recommendation=None if result.complies_nom else (
            f"Aumentar calibre de conductor. VD actual: {result.voltage_drop_percent}%"
        ),
    )


def validate_protection(circuit: CircuitDesign, tables: dict, factors: dict) -> ValidationItem:
    ampacity_key = (
        "conductor_ampacity_copper" if circuit.material == ConductorMaterial.COPPER else "conductor_ampacity_aluminum"
    )
    base_table = tables[ampacity_key]

    if circuit.conductor_awg not in base_table:
        return ValidationItem(
            name="Protección NOM-001-SEDE-2012",
            passed=False,
            value=f"{circuit.protection_A}A",
            limit="Calibre no encontrado",
            reference="NOM-001-SEDE-2012 §240",
        )

    temp_key = f"{circuit.conductor_insulation_temp}C"
    base_ampacity = base_table[circuit.conductor_awg].get(temp_key, 0)

    if circuit.motor_load:
        max_protection = base_ampacity * factors["protection_sizing_factors"]["motor_breaker_max_factor"]
    else:
        max_protection = base_ampacity * 1.0

    passed = circuit.protection_A <= max_protection

    return ValidationItem(
        name="Protección NOM-001-SEDE-2012",
        passed=passed,
        value=f"{circuit.protection_A}A (protección instalada)",
        limit=f"≤ {max_protection:.0f}A para {circuit.conductor_awg}",
        reference="NOM-001-SEDE-2012 §240.4",
        recommendation=None if passed else (
            f"Reducir protección a máx. {max_protection:.0f}A o aumentar calibre de conductor."
        ),
    )


def validate_conduit(circuit: CircuitDesign, tables: dict) -> ValidationItem:
    conduit_table = tables.get("conduit_emt_fill", {})
    if circuit.conduit_size not in conduit_table:
        return ValidationItem(
            name="Canalización NOM-001-SEDE-2012",
            passed=False,
            value=circuit.conduit_size,
            limit="Tamaño no en tablas",
            reference="NOM-001-SEDE-2012 §358 / NEC Chapter 9",
        )

    conduit_data = conduit_table[circuit.conduit_size]
    conduit_area = conduit_data["area_mm2"]

    conductor_areas = tables.get("conductor_area_thhn_mm2", {})
    if circuit.conductor_awg not in conductor_areas:
        return ValidationItem(
            name="Canalización NOM-001-SEDE-2012",
            passed=False,
            value="Área de conductor no en tablas",
            limit="N/A",
            reference="NOM-001-SEDE-2012 §358",
        )

    cond_area = conductor_areas[circuit.conductor_awg]
    total_conductor_area = cond_area * circuit.num_conductors_in_conduit

    max_fill_pct = (
        tables["conduit_emt_fill"]["_max_fill_1_conductor"] if circuit.num_conductors_in_conduit == 1
        else tables["conduit_emt_fill"]["_max_fill_2_conductors"] if circuit.num_conductors_in_conduit == 2
        else tables["conduit_emt_fill"]["_max_fill_3plus_conductors"]
    )

    max_fill_area = conduit_area * max_fill_pct / 100.0
    actual_fill_pct = (total_conductor_area / conduit_area) * 100.0
    passed = total_conductor_area <= max_fill_area

    return ValidationItem(
        name="Relleno de Canalización NOM-001-SEDE-2012",
        passed=passed,
        value=f"{actual_fill_pct:.1f}% ({total_conductor_area:.0f}mm² / {conduit_area:.0f}mm²)",
        limit=f"≤ {max_fill_pct}%",
        reference="NOM-001-SEDE-2012 §358 / NEC Ch.9 Table 1",
        recommendation=None if passed else "Aumentar diámetro de conduit.",
    )


def validate_circuit(circuit: CircuitDesign) -> NOMValidationReport:
    tables, factors = _load_tables()
    report = NOMValidationReport(circuit=circuit)

    report.items.append(validate_ampacity(circuit, tables, factors))
    report.items.append(validate_voltage_drop(circuit, tables))
    report.items.append(validate_protection(circuit, tables, factors))
    report.items.append(validate_conduit(circuit, tables))

    return report


def print_validation_report(report: NOMValidationReport) -> None:
    c = report.circuit
    print("=" * 70)
    print("  VALIDACIÓN NOM-001-SEDE-2012 — IPEA_HUB")
    print("=" * 70)
    print(f"  Circuito: {c.description}")
    print(f"  {c.voltage_V}V | {c.current_A}A | {c.length_m}m | {c.conductor_awg} {c.material.value.upper()}")
    print(f"  Conduit: {c.conduit_size} EMT | {c.num_conductors_in_conduit} conductores")
    print(f"  Protección: {c.protection_A}A | Temp. ambiente: {c.ambient_temp_C}°C")
    print("-" * 70)

    for item in report.items:
        status = "✅ PASA" if item.passed else "❌ FALLA"
        print(f"\n  {status} — {item.name}")
        print(f"    Valor:      {item.value}")
        print(f"    Límite:     {item.limit}")
        print(f"    Referencia: {item.reference}")
        if item.recommendation:
            print(f"    ACCIÓN:     {item.recommendation}")

    print("\n" + "=" * 70)
    print(f"  RESULTADO FINAL: {report.pass_count}/{len(report.items)} verificaciones pasadas")
    print(f"  Estado: {'✅ CUMPLE NOM-001-SEDE-2012' if report.all_pass else '❌ NO CUMPLE — REQUIERE CORRECCIÓN'}")
    print("=" * 70)


if __name__ == "__main__":
    circuit = CircuitDesign(
        description="Alimentador tablero T-1, Planta Baja",
        voltage_V=220,
        current_A=60,
        length_m=45,
        conductor_awg="4AWG",
        conduit_size='1"',
        num_conductors_in_conduit=4,
        circuit_type=CircuitType.THREE_PHASE_4W,
        material=ConductorMaterial.COPPER,
        ambient_temp_C=35,
        conductor_insulation_temp=75,
        protection_A=70,
        is_continuous_load=True,
        power_factor=0.85,
    )

    report = validate_circuit(circuit)
    print_validation_report(report)
