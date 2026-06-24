"""
panel_schedule.py — IPEA_HUB / ipea-electrical
Genera cédula de tablero eléctrico en Excel (.xlsx) conforme NOM-001-SEDE-2012.
Requiere: openpyxl
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side, GradientFill
    )
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


# ── Colores corporativos IPEA_HUB ──────────────────────────────────────────
COLOR_HEADER_DARK  = "1A1A6C"   # Azul marino
COLOR_HEADER_MID   = "2E4099"   # Azul medio
COLOR_SUBHEADER    = "C5CAE9"   # Azul claro
COLOR_ALT_ROW      = "F5F5FB"   # Gris muy claro
COLOR_WHITE        = "FFFFFF"
COLOR_GREEN        = "D4EDDA"
COLOR_RED          = "F8D7DA"
COLOR_YELLOW       = "FFF3CD"
COLOR_BORDER       = "9FA8DA"


@dataclass
class Circuit:
    polo: int                    # Número de polo (1, 3, 5...)
    description: str             # Descripción del circuito
    breaker_A: float             # Amperaje del interruptor
    load_W: float                # Potencia en Watts
    power_factor: float = 0.90   # Factor de potencia
    voltage_V: float = 127.0     # Voltaje del circuito
    phases: int = 1              # Fases (1 o 3)
    conductor_awg: str = "12AWG" # Calibre del conductor
    conduit: str = '1/2"'        # Canalización
    is_spare: bool = False        # ¿Polo de reserva?
    is_space: bool = False        # ¿Espacio vacío?

    @property
    def current_A(self) -> float:
        if self.is_spare or self.is_space:
            return 0.0
        if self.phases == 1:
            return self.load_W / (self.voltage_V * self.power_factor)
        else:
            return self.load_W / (math.sqrt(3) * self.voltage_V * self.power_factor)

    @property
    def load_phase_A(self, phase: int = 1) -> float:
        return self.current_A


@dataclass
class PanelSchedule:
    panel_name: str
    project_name: str
    project_number: str
    location: str
    engineer: str
    voltage_V: float
    phases: int
    wires: int
    main_breaker_A: float
    fed_from: str = "Acometida"
    circuits: list[Circuit] = field(default_factory=list)

    @property
    def total_load_W(self) -> float:
        return sum(c.load_W for c in self.circuits if not c.is_spare and not c.is_space)

    @property
    def total_current_A(self) -> float:
        if self.phases == 1:
            return self.total_load_W / (self.voltage_V * 0.85)
        return self.total_load_W / (math.sqrt(3) * self.voltage_V * 0.85)

    @property
    def load_phase_A(self) -> tuple[float, float, float]:
        """Distribución por fase A, B, C"""
        phase_a = phase_b = phase_c = 0.0
        for i, c in enumerate(self.circuits):
            if c.is_spare or c.is_space:
                continue
            phase_idx = i % 3
            if phase_idx == 0:
                phase_a += c.current_A
            elif phase_idx == 1:
                phase_b += c.current_A
            else:
                phase_c += c.current_A
        return round(phase_a, 2), round(phase_b, 2), round(phase_c, 2)

    @property
    def balance_percent(self) -> float:
        pa, pb, pc = self.load_phase_A
        avg = (pa + pb + pc) / 3 if (pa + pb + pc) > 0 else 1
        max_dev = max(abs(pa - avg), abs(pb - avg), abs(pc - avg))
        return round((max_dev / avg) * 100, 1)

    @property
    def utilization_percent(self) -> float:
        return round((self.total_current_A / self.main_breaker_A) * 100, 1)


def _border(style: str = "thin") -> Border:
    s = Side(style=style, color=COLOR_BORDER)
    return Border(left=s, right=s, top=s, bottom=s)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _font(bold: bool = False, size: int = 10, color: str = "000000", italic: bool = False) -> Font:
    return Font(bold=bold, size=size, color=color, italic=italic)


def _align(h: str = "center", v: str = "center", wrap: bool = True) -> Alignment:
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def _merge_set(ws, cell_range: str, value: str, fill_color: str,
               bold: bool = True, font_size: int = 10,
               font_color: str = COLOR_WHITE, h_align: str = "center") -> None:
    ws.merge_cells(cell_range)
    cell = ws[cell_range.split(":")[0]]
    cell.value = value
    cell.fill = _fill(fill_color)
    cell.font = _font(bold=bold, size=font_size, color=font_color)
    cell.alignment = _align(h=h_align)
    cell.border = _border()


def generate_panel_schedule_xlsx(panel: PanelSchedule, output_path: str) -> str:
    if not OPENPYXL_AVAILABLE:
        return "ERROR: openpyxl no instalado. Ejecutar: pip install openpyxl"

    wb = Workbook()
    ws = wb.active
    ws.title = panel.panel_name[:31]

    # ── Column widths ──────────────────────────────────────────────────────
    col_widths = {
        "A": 6,   # Polo
        "B": 32,  # Descripción
        "C": 10,  # Interruptor A
        "D": 10,  # W
        "E": 8,   # FP
        "F": 10,  # Corriente A
        "G": 10,  # Conductor
        "H": 10,  # Conduit
        "I": 10,  # Fase A
        "J": 10,  # Fase B
        "K": 10,  # Fase C
    }
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width

    row = 1

    # ── TÍTULO PRINCIPAL ───────────────────────────────────────────────────
    ws.row_dimensions[row].height = 28
    _merge_set(ws, f"A{row}:K{row}",
               f"CÉDULA DE CARGAS — {panel.panel_name}",
               COLOR_HEADER_DARK, font_size=14)
    row += 1

    # ── INFO DEL PROYECTO ──────────────────────────────────────────────────
    ws.row_dimensions[row].height = 16
    info_pairs = [
        ("Proyecto:", panel.project_name, "Número:", panel.project_number),
        ("Ubicación:", panel.location, "Elaboró:", panel.engineer),
        ("Sistema:", f"{panel.voltage_V}V / {panel.phases}Φ / {panel.wires}H",
         "Alimentado desde:", panel.fed_from),
        ("Interruptor principal:", f"{panel.main_breaker_A}A",
         "Norma:", "NOM-001-SEDE-2012"),
    ]

    for label1, val1, label2, val2 in info_pairs:
        ws.row_dimensions[row].height = 15
        # Left pair
        ws.merge_cells(f"A{row}:B{row}")
        c = ws[f"A{row}"]
        c.value = label1
        c.font = _font(bold=True, color=COLOR_HEADER_DARK)
        c.fill = _fill(COLOR_SUBHEADER)
        c.alignment = _align(h="left")
        c.border = _border()

        ws.merge_cells(f"C{row}:E{row}")
        c2 = ws[f"C{row}"]
        c2.value = val1
        c2.alignment = _align(h="left")
        c2.border = _border()

        # Right pair
        ws.merge_cells(f"F{row}:G{row}")
        c3 = ws[f"F{row}"]
        c3.value = label2
        c3.font = _font(bold=True, color=COLOR_HEADER_DARK)
        c3.fill = _fill(COLOR_SUBHEADER)
        c3.alignment = _align(h="left")
        c3.border = _border()

        ws.merge_cells(f"H{row}:K{row}")
        c4 = ws[f"H{row}"]
        c4.value = val2
        c4.alignment = _align(h="left")
        c4.border = _border()
        row += 1

    row += 1  # Espacio

    # ── ENCABEZADOS DE COLUMNAS ────────────────────────────────────────────
    ws.row_dimensions[row].height = 30
    headers = [
        ("A", "POLO"), ("B", "DESCRIPCIÓN DEL CIRCUITO"),
        ("C", "INTER.\n(A)"), ("D", "CARGA\n(W)"),
        ("E", "F.P."), ("F", "CORR.\n(A)"),
        ("G", "CONDUCTOR"), ("H", "CONDUIT"),
        ("I", "FASE A\n(A)"), ("J", "FASE B\n(A)"), ("K", "FASE C\n(A)"),
    ]
    for col, title in headers:
        c = ws[f"{col}{row}"]
        c.value = title
        c.fill = _fill(COLOR_HEADER_MID)
        c.font = _font(bold=True, color=COLOR_WHITE, size=9)
        c.alignment = _align()
        c.border = _border()
    row += 1

    # ── CIRCUITOS ──────────────────────────────────────────────────────────
    phase_totals = [0.0, 0.0, 0.0]

    for i, circuit in enumerate(panel.circuits):
        ws.row_dimensions[row].height = 14
        bg = COLOR_ALT_ROW if i % 2 == 0 else COLOR_WHITE

        if circuit.is_spare:
            values = [circuit.polo, "RESERVA", "", "", "", "", "", "", "", "", ""]
            bg = COLOR_YELLOW
        elif circuit.is_space:
            values = [circuit.polo, "ESPACIO", "", "", "", "", "", "", "", "", ""]
            bg = "EEEEEE"
        else:
            curr = round(circuit.current_A, 2)
            phase_idx = i % 3
            fa = curr if phase_idx == 0 else ""
            fb = curr if phase_idx == 1 else ""
            fc = curr if phase_idx == 2 else ""
            if fa:
                phase_totals[0] += curr
            if fb:
                phase_totals[1] += curr
            if fc:
                phase_totals[2] += curr

            values = [
                circuit.polo,
                circuit.description,
                circuit.breaker_A,
                round(circuit.load_W, 0),
                circuit.power_factor,
                curr,
                circuit.conductor_awg,
                circuit.conduit,
                fa, fb, fc,
            ]

        cols = list("ABCDEFGHIJK")
        for col_letter, val in zip(cols, values):
            c = ws[f"{col_letter}{row}"]
            c.value = val
            c.fill = _fill(bg)
            c.font = _font(size=9)
            c.border = _border("thin")
            if col_letter == "B":
                c.alignment = _align(h="left")
            else:
                c.alignment = _align()
        row += 1

    row += 1  # Espacio

    # ── TOTALES ────────────────────────────────────────────────────────────
    ws.row_dimensions[row].height = 18
    _merge_set(ws, f"A{row}:B{row}", "TOTALES", COLOR_HEADER_DARK)

    totals = [
        ("C", ""),
        ("D", round(panel.total_load_W, 0)),
        ("E", ""),
        ("F", round(panel.total_current_A, 2)),
        ("G", ""), ("H", ""),
        ("I", round(phase_totals[0], 2)),
        ("J", round(phase_totals[1], 2)),
        ("K", round(phase_totals[2], 2)),
    ]
    for col, val in totals:
        c = ws[f"{col}{row}"]
        c.value = val
        c.fill = _fill(COLOR_HEADER_MID)
        c.font = _font(bold=True, color=COLOR_WHITE, size=9)
        c.alignment = _align()
        c.border = _border()
    row += 1

    # ── RESUMEN NOM ────────────────────────────────────────────────────────
    ws.row_dimensions[row].height = 16
    _merge_set(ws, f"A{row}:K{row}", "RESUMEN NOM-001-SEDE-2012", COLOR_HEADER_DARK)
    row += 1

    utilization = panel.utilization_percent
    balance = panel.balance_percent
    util_color = COLOR_GREEN if utilization <= 80 else COLOR_RED
    bal_color = COLOR_GREEN if balance <= 10 else (COLOR_YELLOW if balance <= 15 else COLOR_RED)

    summary_rows = [
        ("Carga total", f"{panel.total_load_W:,.0f} W", ""),
        ("Corriente de demanda", f"{panel.total_current_A:.2f} A", ""),
        ("Interruptor principal", f"{panel.main_breaker_A} A", ""),
        ("Utilización del tablero", f"{utilization}%",
         "✅ CUMPLE (≤80%)" if utilization <= 80 else "❌ EXCEDE LÍMITE"),
        ("Desbalance de fases", f"{balance}%",
         "✅ ACEPTABLE (≤10%)" if balance <= 10 else
         ("⚠️ REVISAR (≤15%)" if balance <= 15 else "❌ DESBALANCEADO")),
        ("Fase A / B / C", f"{phase_totals[0]:.1f}A / {phase_totals[1]:.1f}A / {phase_totals[2]:.1f}A", ""),
    ]

    for label, value, status in summary_rows:
        ws.row_dimensions[row].height = 15
        ws.merge_cells(f"A{row}:D{row}")
        c = ws[f"A{row}"]
        c.value = label
        c.font = _font(bold=True, color=COLOR_HEADER_DARK)
        c.fill = _fill(COLOR_SUBHEADER)
        c.alignment = _align(h="left")
        c.border = _border()

        ws.merge_cells(f"E{row}:H{row}")
        c2 = ws[f"E{row}"]
        c2.value = value
        c2.alignment = _align()
        c2.border = _border()

        ws.merge_cells(f"I{row}:K{row}")
        c3 = ws[f"I{row}"]
        c3.value = status
        if label == "Utilización del tablero":
            c3.fill = _fill(util_color)
        elif label == "Desbalance de fases":
            c3.fill = _fill(bal_color)
        c3.alignment = _align()
        c3.border = _border()
        row += 1

    # ── FOOTER ─────────────────────────────────────────────────────────────
    row += 1
    ws.row_dimensions[row].height = 13
    _merge_set(ws, f"A{row}:K{row}",
               f"Elaborado por IPEA_HUB Engineering  |  {panel.engineer}  |  NOM-001-SEDE-2012",
               COLOR_HEADER_DARK, font_size=8)

    # ── GUARDAR ────────────────────────────────────────────────────────────
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return f"Cédula de tablero generada: {out}"


if __name__ == "__main__":
    panel = PanelSchedule(
        panel_name="T-PB-01",
        project_name="Edificio Corporativo Norte",
        project_number="IPEA-2025-001",
        location="Cuarto Eléctrico — Planta Baja, Eje C/3",
        engineer="Ing. IPEA_HUB",
        voltage_V=220,
        phases=3,
        wires=4,
        main_breaker_A=200,
        fed_from="Tablero General TG-01",
        circuits=[
            Circuit(1,  "Iluminación Recepción",        20, 1800,  0.95, 127),
            Circuit(3,  "Iluminación Oficinas A",        20, 2400,  0.95, 127),
            Circuit(5,  "Iluminación Oficinas B",        20, 2100,  0.95, 127),
            Circuit(7,  "Contactos Recepción",           20, 1800,  0.90, 127),
            Circuit(9,  "Contactos Oficinas A",          20, 3600,  0.90, 127),
            Circuit(11, "Contactos Oficinas B",          20, 3600,  0.90, 127),
            Circuit(13, "Aire Acondicionado Mini-Split", 30, 3500,  0.85, 220, phases=1),
            Circuit(15, "Aire Acondicionado Mini-Split", 30, 3500,  0.85, 220, phases=1),
            Circuit(17, "UPS Servidor",                  20, 2000,  0.90, 127),
            Circuit(19, "Calentador Eléctrico",          30, 3800,  1.00, 127),
            Circuit(21, "Motor Bomba Hidráulica",        30, 1865,  0.85, 220, phases=3, conductor_awg="10AWG"),
            Circuit(23, "RESERVA", 20, 0, is_spare=True),
            Circuit(25, "RESERVA", 20, 0, is_spare=True),
            Circuit(27, "ESPACIO", 0,  0, is_space=True),
        ],
    )

    result = generate_panel_schedule_xlsx(panel, "/tmp/cedula_T-PB-01.xlsx")
    print(result)
