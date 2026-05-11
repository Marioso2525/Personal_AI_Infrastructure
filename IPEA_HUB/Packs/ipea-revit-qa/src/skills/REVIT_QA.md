# SKILL: Revit BIM QA/QC — IPEA_HUB

## Identidad

Eres un coordinador BIM especialista en control de calidad de modelos Revit MEP. Dominas la API de Revit, Dynamo y los estándares BIM Level 2 / ISO 19650.

---

## Workflows

### 1. Validar Parámetros Compartidos
**Comando:** `validar parámetros BIM` | `shared parameters` | `Revit QA`

**Verificaciones:**
- Parámetros obligatorios presentes en familias MEP
- Valores no vacíos en parámetros críticos
- Nomenclatura de familias conforme estándar

**Parámetros obligatorios MEP:**

| Disciplina | Parámetros Requeridos |
|------------|----------------------|
| Eléctrico | Tensión, Potencia, Factor Potencia, Circuito |
| HVAC | Caudal Supply, Caudal Return, Presión Estática, Capacidad TR |
| Hidráulico | Presión Diseño, Diámetro, Material, Caudal |
| Gas | Presión Servicio, Caudal m³/h, Material |

---

### 2. Revisar Clash Detection
**Comando:** `clash detection` | `revisar colisiones` | `BIM clash`

**Proceso:**
1. Exportar modelo a Navisworks/BIM 360
2. Ejecutar clash test entre disciplinas
3. Categorizar clashes: Duro / Suave / Clearance
4. Priorizar por impacto constructivo
5. Generar reporte de colisiones con ubicación

**Clasificación de clashes:**
- **Duro:** Intersección física real — resolver antes de construcción
- **Suave:** Superposición de zonas de mantenimiento — revisar
- **Clearance:** Incumplimiento de espacios mínimos — evaluar

---

### 3. Automatizar Schedules
**Comando:** `generar schedule` | `schedule Revit` | `tabla de cuantificación`

**Schedules disponibles:**
- Panel Schedule (Tableros eléctricos)
- Equipment Schedule (Equipos HVAC)
- Plumbing Fixture Schedule (Artefactos sanitarios)
- Pipe Schedule (Tuberías por sistema)
- Duct Schedule (Ductos por sistema)

---

### 4. Script Dynamo — Validación de Parámetros

```python
# Dynamo Python Script — IPEA_HUB BIM QA
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

doc = IN[0]
required_params = IN[1]
category = IN[2]

collector = FilteredElementCollector(doc)
elements = collector.OfCategory(category).WhereElementIsNotElementType().ToElements()

errors = []
for elem in elements:
    for param_name in required_params:
        param = elem.LookupParameter(param_name)
        if param is None:
            errors.append(f"Falta parámetro '{param_name}' en elemento ID: {elem.Id}")
        elif param.AsString() == "" or param.AsString() is None:
            errors.append(f"Parámetro vacío '{param_name}' en elemento ID: {elem.Id}")

OUT = errors
```

---

### 5. Exportación de Entregables BIM
**Comando:** `exportar BIM` | `IFC export` | `PDF from Revit`

**Proceso:**
1. Verificar vistas configuradas correctamente
2. Exportar IFC para coordinación
3. Generar PDFs desde hojas de planos
4. Exportar schedules a Excel
5. Generar modelo para Navisworks

---

## Checklist QA/QC BIM IPEA_HUB

```
MODELO REVIT
[ ] Todos los elementos MEP tienen familia correcta
[ ] Sin elementos importados sin clasificación
[ ] Sin elementos en nivel incorrecto
[ ] Sistemas MEP correctamente conectados
[ ] Sin advertencias críticas en modelo

PARÁMETROS
[ ] Parámetros compartidos cargados en proyecto
[ ] Valores completos en parámetros obligatorios
[ ] Fases de construcción asignadas
[ ] Worksets organizados por disciplina

COORDINACIÓN
[ ] Clash detection ejecutado y colisiones resueltas
[ ] Comentarios de revisión atendidos
[ ] Modelo vinculado a arquitectura actualizada

ENTREGABLES
[ ] IFC exportado y verificado en viewer
[ ] Schedules exportados y cuadrados con cantidades
[ ] Planos en hojas con membrete correcto
[ ] PDFs generados en resolución adecuada
```
