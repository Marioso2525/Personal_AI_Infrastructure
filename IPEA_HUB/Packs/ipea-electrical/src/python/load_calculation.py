"""
load_calculation.py — IPEA_HUB / ipea-electrical
Cálculo de cargas eléctricas y dimensionamiento de tableros conforme NOM-001-SEDE-2012.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

FACTORS_PATH = Path(__file__).parent.parent / "standards" / "nom-001-sede-2012" / "factors.json"


class LoadType(str, Enum):
    LIGHTING = "lighting"
    RECEPTACLE = "receptacle"
    MOTOR = "motor"
    HVAC = "hvac"
    HEATING = "heating"
    SPECIAL = "special"
    CONTINUOUS = "continuous"


@dataclass
class ElectricalLoad:
    name: str
    load_type: LoadType
    quantity: int
    unit_watts: float
    power_factor: float = 0.85
    is_continuous: bool = False
    demand_factor: float = 1.0
    voltage: float = 127.0
    phases: int = 1

    @property
    def total_watts(self) -> float:
        return self.quantity * self.unit_watts * self.demand_factor

    @property
    def total_va(self) -> float:
        return self.total_watts / self.power_factor

    @property
    def current_A(self) -> float:
        if self.phases == 1:
            return self.total_va / self.voltage
        else:
            return self.total_va / (math.sqrt(3) * self.voltage)

    @property
    def design_current_A(self) -> float:
        return self.current_A * (1.25 if self.is_continuous else 1.0)


@dataclass
class PanelBoard:
    name: str
    location: str
    voltage_V: float
    phases: int
    wires: int
    main_breaker_A: float
    loads: list[ElectricalLoad] = field(default_factory=list)

    @property
    def total_watts(self) -> float:
        return sum(load.total_watts for load in self.loads)

    @property
    def total_va(self) -> float:
        return sum(load.total_va for load in self.loads)

    @property
    def total_current_A(self) -> float:
        if self.phases == 1:
            return self.total_va / self.voltage_V
        else:
            return self.total_va / (math.sqrt(3) * self.voltage_V)

    @property
    def demand_current_A(self) -> float:
        demand_factor = self._apply_dwelling_demand()
        return self.total_current_A * demand_factor

    def _apply_dwelling_demand(self) -> float:
        va = self.total_va
        if va <= 3000:
            return 1.0
        elif va <= 120000:
            dem = 3000 + (va - 3000) * 0.35
        else:
            dem = 3000 + 117000 * 0.35 + (va - 120000) * 0.25
        return dem / va

    @property
    def largest_motor_load(self) -> Optional[ElectricalLoad]:
        motor_loads = [l for l in self.loads if l.load_type == LoadType.MOTOR]
        if not motor_loads:
            return None
        return max(motor_loads, key=lambda l: l.total_watts)

    @property
    def feeder_current_A(self) -> float:
        base = self.demand_current_A
        motor = self.largest_motor_load
        if motor:
            extra = motor.current_A * 0.25
            return base + extra
        return base

    @property
    def continuous_load_factor_current(self) -> float:
        cont_va = sum(l.total_va for l in self.loads if l.is_continuous)
        if self.phases == 1:
            cont_I = cont_va / self.voltage_V
        else:
            cont_I = cont_va / (math.sqrt(3) * self.voltage_V)
        other_I = self.demand_current_A - cont_I
        return cont_I * 1.25 + other_I


@dataclass
class LoadScheduleResult:
    panel: PanelBoard
    feeder_current_A: float
    design_current_A: float
    loads_by_type: dict[str, float]
    utilization_percent: float
    complies_main_breaker: bool


def calculate_panel_load(panel: PanelBoard) -> LoadScheduleResult:
    feeder_I = panel.feeder_current_A
    design_I = panel.continuous_load_factor_current

    loads_by_type: dict[str, float] = {}
    for load in panel.loads:
        key = load.load_type.value
        loads_by_type[key] = loads_by_type.get(key, 0.0) + load.total_watts

    utilization = (feeder_I / panel.main_breaker_A) * 100.0
    complies = feeder_I <= panel.main_breaker_A * 0.80

    return LoadScheduleResult(
        panel=panel,
        feeder_current_A=round(feeder_I, 2),
        design_current_A=round(design_I, 2),
        loads_by_type={k: round(v, 1) for k, v in loads_by_type.items()},
        utilization_percent=round(utilization, 1),
        complies_main_breaker=complies,
    )


def print_load_schedule(result: LoadScheduleResult) -> None:
    p = result.panel
    print("=" * 65)
    print(f"  CÉDULA DE CARGAS — {p.name}")
    print("=" * 65)
    print(f"  Ubicación:   {p.location}")
    print(f"  Sistema:     {p.voltage_V}V / {p.phases}Φ / {p.wires}H")
    print(f"  Interruptor: {p.main_breaker_A}A")
    print()
    print(f"  {'CIRCUITO':<30} {'CANT':>4} {'W/u':>8} {'W TOTAL':>10} {'A':>8}")
    print(f"  {'-'*30} {'-'*4} {'-'*8} {'-'*10} {'-'*8}")

    for load in p.loads:
        print(
            f"  {load.name:<30} {load.quantity:>4} {load.unit_watts:>8.0f} "
            f"{load.total_watts:>10.1f} {load.current_A:>8.2f}"
        )

    print(f"  {'-'*30} {'-'*4} {'-'*8} {'-'*10} {'-'*8}")
    print(f"  {'TOTALES':<30} {'':>4} {'':>8} {p.total_watts:>10.1f} {p.total_current_A:>8.2f}")
    print()
    print(f"  Corriente demanda (c/factores): {result.feeder_current_A}A")
    print(f"  Corriente de diseño (c/cargas continuas): {result.design_current_A}A")
    print()
    print("  Cargas por tipo:")
    for k, v in result.loads_by_type.items():
        print(f"    {k:<20}: {v:.1f} W")
    print()
    print(f"  Utilización del interruptor: {result.utilization_percent}%")
    status = "✅ CUMPLE (≤80%)" if result.complies_main_breaker else "❌ EXCEDE LÍMITE"
    print(f"  Estado NOM-001-SEDE-2012:    {status}")
    print("=" * 65)


if __name__ == "__main__":
    panel = PanelBoard(
        name="T-PLANTA BAJA",
        location="Cuarto eléctrico, eje C/3",
        voltage_V=220,
        phases=3,
        wires=4,
        main_breaker_A=200,
        loads=[
            ElectricalLoad("Iluminación LED general", LoadType.LIGHTING, 40, 60, 0.95, True),
            ElectricalLoad("Contactos 127V", LoadType.RECEPTACLE, 30, 180, 0.90, False),
            ElectricalLoad("Aire acondicionado 5TR", LoadType.HVAC, 3, 6000, 0.85, True),
            ElectricalLoad("Motor bomba hidráulica", LoadType.MOTOR, 1, 3730, 0.85, False),
            ElectricalLoad("Calentadores eléctricos", LoadType.HEATING, 2, 4000, 1.00, True),
            ElectricalLoad("Equipo de cómputo", LoadType.SPECIAL, 10, 350, 0.90, False),
        ],
    )

    result = calculate_panel_load(panel)
    print_load_schedule(result)
