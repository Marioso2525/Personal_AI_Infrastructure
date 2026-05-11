# ipea-electrical — Electrical Engineering Pack

Pack de ingeniería eléctrica para IPEA_HUB. Implementa cálculos, validaciones y generación de memorias conforme NOM-001-SEDE-2012.

## Capacidades

- Caída de tensión (monofásico / trifásico)
- Dimensionamiento de conductores con factores de corrección
- Validación integral NOM-001-SEDE-2012
- Cédula de cargas y dimensionamiento de tableros
- Generación de memorias de cálculo (Word + PDF)
- Tablas completas NOM-001-SEDE-2012 en JSON

## Dependencias

- ipea-core (instalado previamente)
- Python 3.11+ con: pandas, numpy, python-docx, reportlab, openpyxl

## Archivos Clave

| Archivo | Función |
|---------|---------|
| `src/python/voltage_drop.py` | Caída de tensión + búsqueda de calibre |
| `src/python/nom_validator.py` | Validación integral NOM-001-SEDE-2012 |
| `src/python/load_calculation.py` | Cédulas de carga y tableros |
| `src/python/report_generator.py` | Memorias Word + PDF |
| `src/standards/nom-001-sede-2012/tables.json` | Tablas de ampacidad y conduit |
| `src/standards/nom-001-sede-2012/factors.json` | Factores de corrección y ajuste |
| `src/skills/ELECTRICAL.md` | Skill definition para Claude Code |
