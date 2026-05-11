# Bundle: IPEA_HUB — Infraestructura AI para Ingeniería

Bundle oficial que instala el sistema completo IPEA_HUB en un solo paso.

## Qué instala este Bundle

| Pack | Contenido |
|------|-----------|
| `ipea-core` | Hooks de seguridad, historial, contexto de proyecto |
| `ipea-electrical` | Cálculos NOM-001-SEDE-2012 + memorias de cálculo |
| `ipea-hvac` | Cargas térmicas ASHRAE + dimensionamiento de ductos |
| `ipea-hydrosanitary` | Método Hunter + Hazen-Williams + sanitario |
| `ipea-gas` | Gas LP/Natural + NOM-004-SEDG + NOM-002-SECRE |
| `ipea-cad-qa` | QA/QC AutoCAD: layers, escalas, bloques, limpieza |
| `ipea-revit-qa` | QA/QC BIM: parámetros, clash, schedules, Dynamo |
| `ipea-documentation` | Memorias descriptivas + cálculo + especificaciones |

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/marioso2525/personal_ai_infrastructure.git
cd personal_ai_infrastructure/IPEA_HUB/Bundles/IPEA_HUB

# Instalar bundle completo
bun run install.ts
```

## Prerequisitos

```bash
bun --version    # >= 1.0
python3 --version # >= 3.11
git --version
pip install python-docx reportlab openpyxl pandas numpy scipy pydantic
```

## Variables de Entorno

Configurar antes de instalar:
```bash
export PAI_DIR="$HOME/.pai-engineering"
export DA="EngineeringAI"
export TIME_ZONE="America/Cancun"
```

## Verificación Post-Instalación

```bash
# Core
ls $PAI_DIR/hooks/                  # 4 hooks TypeScript
ls $PAI_DIR/skills/electrical/      # ELECTRICAL.md
ls $PAI_DIR/scripts/python/         # 7+ scripts Python
ls $PAI_DIR/standards/nom-001-sede-2012/ # tables.json + factors.json

# Test eléctrico
python $PAI_DIR/scripts/python/voltage_drop.py     # debe ejecutarse
python $PAI_DIR/scripts/python/nom_validator.py    # debe ejecutarse
python $PAI_DIR/scripts/python/load_calculation.py # debe ejecutarse

# Test HVAC
python $PAI_DIR/scripts/python/hvac_loads.py       # debe ejecutarse

# Test Hidráulico
python $PAI_DIR/scripts/python/pipe_sizing.py      # debe ejecutarse

# Test Gas
python $PAI_DIR/scripts/python/gas_sizing.py       # debe ejecutarse
```
