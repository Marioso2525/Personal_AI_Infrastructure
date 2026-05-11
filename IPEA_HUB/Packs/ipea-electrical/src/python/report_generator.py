"""
report_generator.py — IPEA_HUB / ipea-electrical
Genera memorias de cálculo eléctrico en Word y PDF conforme NOM-001-SEDE-2012.
Requiere: python-docx, reportlab
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
    )
    from reportlab.lib.units import cm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


COMPANY_NAME = "IPEA_HUB Engineering"
STANDARD_REF = "NOM-001-SEDE-2012"


def _add_heading(doc: "Document", text: str, level: int = 1) -> None:
    heading = doc.add_heading(text, level=level)
    heading.style.font.color.rgb = RGBColor(0x1A, 0x1A, 0x6C)


def _add_table_row(table, cells: list[str], bold_first: bool = False) -> None:
    row = table.add_row()
    for i, cell_text in enumerate(cells):
        cell = row.cells[i]
        cell.text = cell_text
        if bold_first and i == 0:
            cell.paragraphs[0].runs[0].bold = True


def generate_electrical_memory_docx(
    project_name: str,
    circuit_results: list[dict],
    output_path: str,
    engineer_name: str = "Ing. IPEA_HUB",
    project_number: str = "IPEA-001",
) -> str:
    if not DOCX_AVAILABLE:
        return "ERROR: python-docx no instalado. Ejecutar: pip install python-docx"

    doc = Document()
    styles = doc.styles

    section = doc.sections[0]
    section.page_width = Cm(21.59)
    section.page_height = Cm(27.94)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(f"MEMORIA DE CÁLCULO ELÉCTRICA")
    run.bold = True
    run.font.size = Pt(16)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run(f"Conforme {STANDARD_REF}").bold = True

    doc.add_paragraph()

    info_table = doc.add_table(rows=5, cols=2)
    info_table.style = "Table Grid"
    rows_data = [
        ("Proyecto:", project_name),
        ("Número:", project_number),
        ("Elaboró:", engineer_name),
        ("Fecha:", datetime.now().strftime("%d/%m/%Y")),
        ("Norma aplicable:", STANDARD_REF),
    ]
    for i, (label, value) in enumerate(rows_data):
        row = info_table.rows[i]
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[1].text = value

    doc.add_paragraph()
    _add_heading(doc, "1. ALCANCE", level=1)
    doc.add_paragraph(
        "La presente memoria documenta los cálculos eléctricos realizados conforme a la "
        f"Norma Oficial Mexicana {STANDARD_REF}, Instalaciones Eléctricas (Utilización). "
        "Se verifican: ampacidad de conductores, caída de tensión, protecciones y dimensionamiento de canalizaciones."
    )

    _add_heading(doc, "2. CRITERIOS DE DISEÑO", level=1)
    criteria_table = doc.add_table(rows=5, cols=2)
    criteria_table.style = "Table Grid"
    criteria_data = [
        ("Norma aplicable", STANDARD_REF),
        ("Límite caída de tensión (ramal)", "≤ 3%"),
        ("Límite caída de tensión (total)", "≤ 5%"),
        ("Factor cargas continuas", "125% (1.25×)"),
        ("Material conductor", "Cobre / Aluminio según proyecto"),
    ]
    for i, (label, value) in enumerate(criteria_data):
        row = criteria_table.rows[i]
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[1].text = value

    doc.add_paragraph()
    _add_heading(doc, "3. RESULTADOS DE CÁLCULO", level=1)

    for idx, result in enumerate(circuit_results, 1):
        _add_heading(doc, f"3.{idx} {result.get('description', f'Circuito {idx}')}", level=2)

        res_table = doc.add_table(rows=1, cols=4)
        res_table.style = "Table Grid"
        header_row = res_table.rows[0]
        headers = ["Parámetro", "Valor", "Límite NOM", "Estado"]
        for i, h in enumerate(headers):
            header_row.cells[i].text = h
            header_row.cells[i].paragraphs[0].runs[0].bold = True

        for item in result.get("validation_items", []):
            row = res_table.add_row()
            row.cells[0].text = item.get("name", "")
            row.cells[1].text = item.get("value", "")
            row.cells[2].text = item.get("limit", "")
            row.cells[3].text = "✅ PASA" if item.get("passed") else "❌ FALLA"

        doc.add_paragraph()

    _add_heading(doc, "4. CONCLUSIONES", level=1)
    doc.add_paragraph(
        f"Los cálculos presentados cumplen con los requerimientos establecidos en {STANDARD_REF}. "
        "Se recomienda su revisión periódica ante cambios en las cargas del proyecto."
    )

    _add_heading(doc, "5. REFERENCIAS NORMATIVAS", level=1)
    for ref in [
        "NOM-001-SEDE-2012 — Instalaciones Eléctricas (Utilización)",
        "NOM-008-ENER-1997 — Eficiencia Energética en Edificaciones",
        "NFPA 70 — National Electrical Code (referencia)",
    ]:
        doc.add_paragraph(ref, style="List Bullet")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    return f"Memoria de cálculo generada: {output}"


def generate_electrical_memory_pdf(
    project_name: str,
    circuit_results: list[dict],
    output_path: str,
    engineer_name: str = "Ing. IPEA_HUB",
    project_number: str = "IPEA-001",
) -> str:
    if not PDF_AVAILABLE:
        return "ERROR: reportlab no instalado. Ejecutar: pip install reportlab"

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output), pagesize=A4)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1A1A6C"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=colors.HexColor("#1A1A6C"),
        spaceAfter=8,
    )

    story = []

    story.append(Paragraph("MEMORIA DE CÁLCULO ELÉCTRICA", title_style))
    story.append(Paragraph(f"Conforme {STANDARD_REF}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A1A6C")))
    story.append(Spacer(1, 0.3 * cm))

    info_data = [
        ["Proyecto:", project_name],
        ["Número:", project_number],
        ["Elaboró:", engineer_name],
        ["Fecha:", datetime.now().strftime("%d/%m/%Y")],
        ["Norma:", STANDARD_REF],
    ]
    info_table = Table(info_data, colWidths=[4 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("RESULTADOS DE VALIDACIÓN NOM-001-SEDE-2012", heading_style))

    for result in circuit_results:
        story.append(Paragraph(result.get("description", "Circuito"), styles["Heading2"]))

        items = result.get("validation_items", [])
        if items:
            table_data = [["Verificación", "Valor", "Límite", "Estado"]]
            for item in items:
                table_data.append([
                    item.get("name", ""),
                    item.get("value", ""),
                    item.get("limit", ""),
                    "PASA" if item.get("passed") else "FALLA",
                ])

            t = Table(table_data, colWidths=[6 * cm, 4 * cm, 3 * cm, 2.5 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A6C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ]))

            for row_idx, item in enumerate(items, 1):
                cell_color = colors.HexColor("#D4EDDA") if item.get("passed") else colors.HexColor("#F8D7DA")
                t.setStyle(TableStyle([("BACKGROUND", (3, row_idx), (3, row_idx), cell_color)]))

            story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    return f"Reporte PDF generado: {output}"


if __name__ == "__main__":
    sample_results = [
        {
            "description": "Alimentador Tablero T-1",
            "validation_items": [
                {"name": "Ampacidad", "value": "85A corregida", "limit": "≥ 75A", "passed": True},
                {"name": "Caída de Tensión", "value": "2.1% (4.6V)", "limit": "≤ 3%", "passed": True},
                {"name": "Protección", "value": "80A", "limit": "≤ 85A", "passed": True},
                {"name": "Relleno Conduit", "value": "35.2%", "limit": "≤ 40%", "passed": True},
            ],
        }
    ]

    msg = generate_electrical_memory_docx(
        project_name="Edificio Corporativo Norte",
        circuit_results=sample_results,
        output_path="/tmp/memoria_electrica.docx",
        engineer_name="Ing. IPEA_HUB",
        project_number="IPEA-2025-001",
    )
    print(msg)

    msg = generate_electrical_memory_pdf(
        project_name="Edificio Corporativo Norte",
        circuit_results=sample_results,
        output_path="/tmp/memoria_electrica.pdf",
        engineer_name="Ing. IPEA_HUB",
        project_number="IPEA-2025-001",
    )
    print(msg)
