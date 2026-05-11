"""
hvac_loads.py — IPEA_HUB / ipea-hvac
Cálculo de cargas térmicas conforme ASHRAE para sistemas HVAC.
Método simplificado ASHRAE Fundamentals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClimateZone(str, Enum):
    HOT_HUMID = "hot_humid"       # Cancún, Mérida, Veracruz
    HOT_DRY = "hot_dry"           # Monterrey, Hermosillo, Chihuahua
    TEMPERATE = "temperate"        # CDMX, Guadalajara, Puebla
    COLD = "cold"                  # Toluca, San Cristóbal


DESIGN_CONDITIONS: dict[ClimateZone, dict] = {
    ClimateZone.HOT_HUMID:  {"db_C": 35, "wb_C": 28, "rh_pct": 80, "latitude": 21},
    ClimateZone.HOT_DRY:    {"db_C": 42, "wb_C": 24, "rh_pct": 20, "latitude": 26},
    ClimateZone.TEMPERATE:  {"db_C": 30, "wb_C": 18, "rh_pct": 50, "latitude": 19},
    ClimateZone.COLD:       {"db_C": 22, "wb_C": 14, "rh_pct": 45, "latitude": 19},
}

INTERIOR_CONDITIONS = {"db_C": 23, "rh_pct": 50}


@dataclass
class ThermalZone:
    name: str
    area_m2: float
    height_m: float
    people: int
    lighting_W_per_m2: float
    equipment_W_per_m2: float
    window_area_m2: float
    wall_area_m2: float
    roof_area_m2: float
    climate_zone: ClimateZone
    activity_level: str = "seated_office"
    ventilation_L_s_per_person: float = 10.0
    window_shading_coeff: float = 0.65
    wall_U_W_m2K: float = 0.45
    roof_U_W_m2K: float = 0.35
    window_U_W_m2K: float = 3.50
    orientation: str = "south"


@dataclass
class ThermalLoads:
    zone: ThermalZone
    sensible_W: float
    latent_W: float
    total_W: float
    total_kW: float
    tons_refrigeration: float
    breakdown: dict[str, float] = field(default_factory=dict)
    ventilation_cfm: float = 0.0


ACTIVITY_HEAT_GAIN = {
    "seated_office":   {"sensible_W": 73, "latent_W": 45},
    "standing_light":  {"sensible_W": 75, "latent_W": 55},
    "walking":         {"sensible_W": 75, "latent_W": 75},
    "seated_heavy":    {"sensible_W": 80, "latent_W": 80},
    "dancing":         {"sensible_W": 90, "latent_W": 175},
}

SOLAR_HEAT_GAIN: dict[str, dict[str, float]] = {
    "south":     {"hot_humid": 450, "hot_dry": 520, "temperate": 420, "cold": 380},
    "north":     {"hot_humid": 150, "hot_dry": 130, "temperate": 130, "cold": 100},
    "east":      {"hot_humid": 380, "hot_dry": 420, "temperate": 360, "cold": 300},
    "west":      {"hot_humid": 420, "hot_dry": 480, "temperate": 400, "cold": 340},
    "horizontal":{"hot_humid": 700, "hot_dry": 800, "temperate": 650, "cold": 550},
}


def calculate_thermal_loads(zone: ThermalZone) -> ThermalLoads:
    conditions = DESIGN_CONDITIONS[zone.climate_zone]
    delta_T = conditions["db_C"] - INTERIOR_CONDITIONS["db_C"]

    wall_gain = zone.wall_area_m2 * zone.wall_U_W_m2K * delta_T
    roof_gain = zone.roof_area_m2 * zone.roof_U_W_m2K * (delta_T + 5)
    window_cond_gain = zone.window_area_m2 * zone.window_U_W_m2K * delta_T

    shgc_table = SOLAR_HEAT_GAIN.get(zone.orientation.lower(), SOLAR_HEAT_GAIN["south"])
    shgc_W_m2 = shgc_table.get(zone.climate_zone.value, 450)
    solar_gain = zone.window_area_m2 * shgc_W_m2 * zone.window_shading_coeff

    lighting_gain = zone.area_m2 * zone.lighting_W_per_m2 * 1.25
    equipment_gain = zone.area_m2 * zone.equipment_W_per_m2

    activity = ACTIVITY_HEAT_GAIN.get(zone.activity_level, ACTIVITY_HEAT_GAIN["seated_office"])
    people_sensible = zone.people * activity["sensible_W"]
    people_latent = zone.people * activity["latent_W"]

    vent_L_s = zone.people * zone.ventilation_L_s_per_person
    vent_cfm = vent_L_s * 2.119
    vent_sensible = vent_L_s * 1.23 * delta_T
    vent_latent = vent_L_s * 3010 * (0.016 - 0.010)

    total_sensible = (
        wall_gain + roof_gain + window_cond_gain + solar_gain
        + lighting_gain + equipment_gain + people_sensible + vent_sensible
    )
    total_latent = people_latent + vent_latent
    total = total_sensible + total_latent
    tons = total / 3517.0

    return ThermalLoads(
        zone=zone,
        sensible_W=round(total_sensible, 1),
        latent_W=round(total_latent, 1),
        total_W=round(total, 1),
        total_kW=round(total / 1000, 2),
        tons_refrigeration=round(tons, 2),
        ventilation_cfm=round(vent_cfm, 1),
        breakdown={
            "muros_W": round(wall_gain, 1),
            "techo_W": round(roof_gain, 1),
            "ventanas_conduccion_W": round(window_cond_gain, 1),
            "solar_W": round(solar_gain, 1),
            "iluminacion_W": round(lighting_gain, 1),
            "equipo_W": round(equipment_gain, 1),
            "personas_sensible_W": round(people_sensible, 1),
            "personas_latente_W": round(people_latent, 1),
            "ventilacion_sensible_W": round(vent_sensible, 1),
            "ventilacion_latente_W": round(vent_latent, 1),
        },
    )


def print_hvac_report(loads: ThermalLoads) -> None:
    z = loads.zone
    cond = DESIGN_CONDITIONS[z.climate_zone]
    print("=" * 60)
    print("  CÁLCULO DE CARGAS TÉRMICAS — ASHRAE")
    print("=" * 60)
    print(f"  Zona:          {z.name}")
    print(f"  Área:          {z.area_m2} m²")
    print(f"  Zona climática:{z.climate_zone.value}")
    print(f"  T. exterior:   {cond['db_C']}°C BS | {cond['wb_C']}°C BH")
    print(f"  T. interior:   {INTERIOR_CONDITIONS['db_C']}°C | {INTERIOR_CONDITIONS['rh_pct']}% HR")
    print("-" * 60)
    print("  DESGLOSE DE GANANCIAS:")
    for k, v in loads.breakdown.items():
        print(f"    {k:<35} {v:>8.1f} W")
    print("-" * 60)
    print(f"  Carga sensible total:   {loads.sensible_W:>10.1f} W")
    print(f"  Carga latente total:    {loads.latent_W:>10.1f} W")
    print(f"  CARGA TOTAL:            {loads.total_W:>10.1f} W")
    print(f"  CARGA TOTAL:            {loads.total_kW:>10.2f} kW")
    print(f"  CARGA TOTAL:            {loads.tons_refrigeration:>10.2f} TR")
    print(f"  Ventilación requerida:  {loads.ventilation_cfm:>10.1f} CFM")
    print("=" * 60)


if __name__ == "__main__":
    zone = ThermalZone(
        name="Oficinas Planta Baja",
        area_m2=120,
        height_m=3.0,
        people=15,
        lighting_W_per_m2=12,
        equipment_W_per_m2=20,
        window_area_m2=18,
        wall_area_m2=60,
        roof_area_m2=120,
        climate_zone=ClimateZone.HOT_HUMID,
        orientation="west",
    )
    loads = calculate_thermal_loads(zone)
    print_hvac_report(loads)
