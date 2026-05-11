"""
doc_generator.py — IPEA_HUB / ipea-documentation
Generador automatizado de memorias descriptivas, reportes técnicos y especificaciones.
Requiere: python-docx, reportlab
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
    from reportlab.lib.units import cm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


COMPANY_DEFAULTS = {
    "name": "IPEA_HUB Engineering",
    "address": "Cancún, Quintana Roo, México",
    "phone": "+52 (998) 000-0000",
    "email": "info@ipea-hub.mx",
}


def generate_descriptive_memory(
    project_name: str,
    project_number: str,
    discipline: str,
    engineer: str,
    scope_text: str,
    system_description: str,
    design_criteria: list[tuple[str, str]],
    equipment_list: list[dict],
    output_path: str,
    output_format: str = "docx",
) -> str:
    if output_format == "docx":
        return _generate_descriptive_memory_docx(
            project_name, project_number, discipline, engineer,
            scope_text, system_description, design_criteria, equipment_list, output_path
        )
    elif output_format == "pdf":
        return _generate_descriptive_memory_pdf(
            project_name, project_number, discipline, engineer,
            scope_text, system_description, design_criteria, equipment_list, output_path
        )
    else:
        return "ERROR: Formato no soportado. Usar 'docx' o 'pdf'."


def _generate_descriptive_memory_docx(
    project_name: str,
    project_number: str,
    discipline: str,
    engineer: str,
    scope_text: str,
    system_description: str,
    design_criteria: list[tuple[str, str]],
    equipment_list: list[dict],
    output_path: str,
) -> str:
    if not DOCX_AVAILABLE:
        return "ERROR: python-docx no instalado."

    doc = Document()

    section = doc.sections[0]
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(f"MEMORIA DESCRIPTIVA")
    run.bold = True
    run.font.size = Pt(16)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run(f"{discipline.upper()} — {project_name}").bold = True

    doc.add_paragraph()

    info = doc.add_table(rows=5, cols=2)
    info.style = "Table Grid"
    for i, (k, v) in enumerate([
        ("Proyecto:", project_name),
        ("Número:", project_number),
        ("Disciplina:", discipline),
        ("Elaboró:", engineer),
        ("Fecha:", datetime.now().strftime("%d/%m/%Y")),
    ]):
        info.rows[i].cells[0].text = k
        info.rows[i].cells[0].paragraphs[0].runs[0].bold = True
        info.rows[i].cells[1].text = v

    doc.add_paragraph()

    h1 = doc.add_heading("1. ALCANCE Y OBJETIVOS", level=1)
    doc.add_paragraph(scope_text)

    h2 = doc.add_heading("2. DESCRIPCIÓN DEL SISTEMA", level=1)
    doc.add_paragraph(system_description)

    h3 = doc.add_heading("3. CRITERIOS DE DISEÑO", level=1)
    if design_criteria:
        crit_table = doc.add_table(rows=1, cols=2)
        crit_table.style = "Table Grid"
        crit_table.rows[0].cells[0].text = "Parámetro"
        crit_table.rows[0].cells[0].paragraphs[0].runs[0].bold = True
        crit_table.rows[0].cells[1].text = "Valor"
        crit_table.rows[0].cells[1].paragraphs[0].runs[0].bold = True
        for param, value in design_criteria:
            row = crit_table.add_row()
            row.cells[0].text = param
            row.cells[1].text = value

    doc.add_paragraph()

    if equipment_list:
        h4 = doc.add_heading("4. LISTA DE EQUIPOS Y MATERIALES", level=1)
        equip_table = doc.add_table(rows=1, cols=4)
        equip_table.style = "Table Grid"
        headers = ["Descripción", "Marca/Modelo", "Cantidad", "Unidad"]
        for i, h in enumerate(headers):
            equip_table.rows[0].cells[i].text = h
            equip_table.rows[0].cells[i].paragraphs[0].runs[0].bold = True

        for item in equipment_list:
            row = equip_table.add_row()
            row.cells[0].text = item.get("description", "")
            row.cells[1].text = item.get("model", "")
            row.cells[2].text = str(item.get("quantity", ""))
            row.cells[3].text = item.get("unit", "")

    doc.add_paragraph()
    doc.add_heading("5. NORMAS Y REFERENCIAS", level=1)
    norms = {
        "eléctrico": ["NOM-001-SEDE-2012", "NOM-008-ENER-1997"],
        "hvac": ["ASHRAE 62.1-2022", "ASHRAE 90.1-2022", "SMACNA"],
        "hidráulico": ["NOM-004-CNA", "NOM-006-CNA", "IPC"],
        "gas": ["NOM-004-SEDG-2004", "NOM-002-SECRE-2010"],
    }.get(discipline.lower(), ["Normas aplicables al proyecto"])

    for norm in norms:
        doc.add_paragraph(norm, style="List Bullet")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return f"Memoria descriptiva generada: {out}"


def _generate_descriptive_memory_pdf(
    project_name: str,
    project_number: str,
    discipline: str,
    engineer: str,
    scope_text: str,
    system_description: str,
    design_criteria: list[tuple[str, str]],
    equipment_list: list[dict],
    output_path: str,
) -> str:
    if not PDF_AVAILABLE:
        return "ERROR: reportlab no instalado."

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(out), pagesize=A4)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Title"], textColor=colors.HexColor("#1A1A6C"))
    h1_style = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1A1A6C"))

    story = [
        Paragraph("MEMORIA DESCRIPTIVA", title_style),
        Paragraph(f"{discipline.upper()} — {project_name}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1A1A6C")),
        Spacer(1, 0.5 * cm),
        Paragraph("1. ALCANCE", h1_style),
        Paragraph(scope_text, styles["Normal"]),
        Spacer(1, 0.3 * cm),
        Paragraph("2. DESCRIPCIÓN DEL SISTEMA", h1_style),
        Paragraph(system_description, styles["Normal"]),
        Spacer(1, 0.3 * cm),
    ]

    if design_criteria:
        story.append(Paragraph("3. CRITERIOS DE DISEÑO", h1_style))
        data = [["Parámetro", "Valor"]] + [[p, v] for p, v in design_criteria]
        t = Table(data, colWidths=[9 * cm, 7 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A6C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0F8")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    return f"Memoria descriptiva PDF generada: {out}"


if __name__ == "__main__":
    msg = generate_descriptive_memory(
        project_name="Edificio Corporativo Norte",
        project_number="IPEA-2025-001",
        discipline="Eléctrico",
        engineer="Ing. IPEA_HUB",
        scope_text=(
            "La presente memoria describe el sistema eléctrico del edificio corporativo. "
            "Incluye acometida, tableros de distribución, circuitos de iluminación, contactos "
            "y sistema de emergencia conforme NOM-001-SEDE-2012."
        ),
        system_description=(
            "Sistema trifásico 220/127V, 60Hz. Acometida subterránea desde red CFE. "
            "Tablero general TG-1 de 400A con interruptor principal. Distribución mediante "
            "alimentadores a tableros secundarios por nivel."
        ),
        design_criteria=[
            ("Voltaje de utilización", "220/127V 3Φ 4H 60Hz"),
            ("Caída de tensión máxima", "3% circuitos ramales / 5% total"),
            ("Factor de demanda", "75%"),
            ("Factor de potencia", "0.85 mínimo"),
            ("Temperatura ambiente diseño", "35°C"),
            ("Norma aplicable", "NOM-001-SEDE-2012"),
        ],
        equipment_list=[
            {"description": "Tablero general 400A 3Φ", "model": "Square D I-Line", "quantity": 1, "unit": "pza"},
            {"description": "Tablero secundario 200A", "model": "Square D QO", "quantity": 4, "unit": "pza"},
            {"description": "Conductor 4AWG Cu THWN-2", "model": "Condumex", "quantity": 850, "unit": "m"},
            {"description": "Conduit EMT 1\"", "model": "Viakon", "quantity": 200, "unit": "m"},
        ],
        output_path="/tmp/memoria_descriptiva_electrica.docx",
        output_format="docx",
    )
    print(msg)
