# IPEA_HUB — Infraestructura de Personal AI para Ingeniería

**Sistema Operativo de Ingeniería AI** construido sobre Personal AI Infrastructure (PAI) y Claude Code para automatizar la producción técnica en disciplinas MEP (Mechanical, Electrical, Plumbing).

---

## Visión

IPEA_HUB no es un chatbot. Es una infraestructura técnica acumulativa capaz de:

- **Recordar** decisiones de diseño, cálculos y preferencias del cliente
- **Automatizar** cálculos técnicos y generación documental
- **Validar** cumplimiento normativo (NOM-001-SEDE-2012, ASHRAE, NFPA)
- **Aprender** de proyectos anteriores
- **Reutilizar** conocimiento técnico acumulado
- **Estandarizar** entregables profesionales

---

## Disciplinas Cubiertas

| Disciplina          | Pack                  | Estado    |
|---------------------|-----------------------|-----------|
| Ingeniería Eléctrica | `ipea-electrical`    | ✅ Activo |
| HVAC                | `ipea-hvac`           | ✅ Activo |
| Hidrosanitario      | `ipea-hydrosanitary`  | ✅ Activo |
| Gas                 | `ipea-gas`            | ✅ Activo |
| QA/QC CAD           | `ipea-cad-qa`         | ✅ Activo |
| QA/QC BIM/Revit     | `ipea-revit-qa`       | ✅ Activo |
| Automatización Doc. | `ipea-documentation`  | ✅ Activo |
| Core / Hooks        | `ipea-core`           | ✅ Base   |

---

## Arquitectura del Sistema

```
Claude Code
    │
    ▼
PAI (Personal AI Infrastructure)
    │
    ├── ipea-core         ← Hooks, seguridad, historial, contexto
    ├── ipea-electrical   ← Cálculos eléctricos + NOM-001-SEDE-2012
    ├── ipea-hvac         ← HVAC sizing + ASHRAE
    ├── ipea-hydrosanitary← Hidráulico + sanitario
    ├── ipea-gas          ← Dimensionamiento de gas
    ├── ipea-cad-qa       ← QA/QC de planos AutoCAD
    ├── ipea-revit-qa     ← QA/QC BIM Revit + Dynamo
    └── ipea-documentation← Memorias + reportes Word/PDF/Excel
```

---

## Stack Tecnológico

| Componente        | Tecnología                          |
|-------------------|-------------------------------------|
| AI Runtime        | Claude Code (Anthropic)             |
| PAI Framework     | Personal AI Infrastructure          |
| Hooks             | TypeScript + Bun                    |
| Cálculos          | Python 3.11+                        |
| Documentación     | python-docx, ReportLab, openpyxl    |
| Normativa base    | NOM-001-SEDE-2012, ASHRAE, NFPA     |
| Control versiones | Git                                 |
| Contenedores      | Docker (opcional)                   |

---

## Instalación Rápida

### 1. Prerequisitos

```bash
bun --version    # >= 1.0
python --version # >= 3.11
git --version
```

### 2. Dependencias Python

```bash
pip install pandas numpy openpyxl python-docx reportlab matplotlib scipy pydantic
```

### 3. Variables de Entorno

```bash
export PAI_DIR="$HOME/.pai-engineering"
export DA="EngineeringAI"
export TIME_ZONE="America/Cancun"
```

### 4. Instalación de Packs

Instalar en orden de dependencia:

```bash
# 1. Core (fundación)
cp -r Packs/ipea-core/src/* $PAI_DIR/

# 2. Disciplinas
cp -r Packs/ipea-electrical/src/* $PAI_DIR/
cp -r Packs/ipea-hvac/src/* $PAI_DIR/
cp -r Packs/ipea-hydrosanitary/src/* $PAI_DIR/
cp -r Packs/ipea-gas/src/* $PAI_DIR/
cp -r Packs/ipea-cad-qa/src/* $PAI_DIR/
cp -r Packs/ipea-revit-qa/src/* $PAI_DIR/
cp -r Packs/ipea-documentation/src/* $PAI_DIR/
```

O usar el bundle completo:

```bash
cd Bundles/IPEA_HUB
bun run install.ts
```

---

## Orden de Instalación de Packs

```
ipea-core
    ↓
ipea-electrical  ipea-hvac  ipea-hydrosanitary  ipea-gas
    ↓                  ↓              ↓              ↓
ipea-cad-qa    ipea-revit-qa    ipea-documentation
```

---

## Capacidades por Disciplina

### Eléctrica (NOM-001-SEDE-2012)
- Caída de tensión (monofásico / trifásico)
- Cálculo de corriente nominal y demanda
- Dimensionamiento de conductores y canalizaciones
- Factores de corrección por temperatura y agrupamiento
- Protecciones (breakers, fusibles)
- Balanceo de tableros
- Memoria de cálculo automática (Word + PDF)
- Validación automática NOM-001-SEDE-2012

### HVAC (ASHRAE)
- Cargas térmicas (sensible + latente)
- Dimensionamiento de ductos (velocidad y fricción)
- Selección de equipos
- Pérdida de carga en ductos y tuberías
- Reporte técnico ASHRAE

### Hidrosanitario
- Cálculo de gasto probable (Hunter)
- Dimensionamiento de tuberías
- Cálculo de presiones (dinámica / estática)
- Cálculo sanitario (aguas residuales)
- Isométricos automáticos

### Gas
- Dimensionamiento de tuberías de gas LP/Natural
- Caída de presión
- Caudales de diseño
- Materiales y especificaciones
- Seguridad y ventilación

### QA/QC CAD
- Revisión de layers y nomenclatura
- Validación de escalas
- Detección de bloques incorrectos
- Limpieza de drawings

### QA/QC BIM (Revit)
- Validación de parámetros compartidos
- Revisión clash detection
- Automatización de schedules
- Exportación de entregables

### Documentación Automática
- Memorias descriptivas (Word)
- Memorias de cálculo (Word + PDF)
- Reportes QA/QC
- Especificaciones técnicas
- Dashboard Excel con resultados

---

## Principios de Diseño

1. **Modular** — cada pack es independiente e instalable por separado
2. **Seguro** — hooks de seguridad previenen operaciones destructivas
3. **Persistente** — sistema de memoria acumula conocimiento
4. **Verificable** — cada pack incluye VERIFY.md con checklist
5. **Escalable** — preparado para vector databases y multi-agente
6. **Normativo** — validación automática vs. normas aplicables

---

## Estructura de Directorios del Sistema

```
$PAI_DIR/   (~/.pai-engineering/)
│
├── hooks/              ← TypeScript event handlers
├── skills/             ← Markdown skill definitions
│   ├── electrical/
│   ├── hvac/
│   ├── hydrosanitary/
│   ├── gas/
│   ├── cad/
│   └── revit/
├── standards/          ← Tablas normativas
│   ├── nom-001-sede-2012/
│   ├── ashrae/
│   └── nfpa/
├── scripts/            ← Python automation scripts
│   └── python/
├── templates/          ← Word, Excel, PDF templates
├── history/            ← Sistema de memoria
│   ├── projects/
│   ├── calculations/
│   └── decisions/
├── logs/               ← Audit trail
└── config/             ← Configuración del sistema
```

---

## Roadmap

| Fase | Contenido                          | Estado    |
|------|------------------------------------|-----------|
| 1    | Core + Hooks + History             | ✅ Listo  |
| 2    | Electrical + NOM validator         | ✅ Listo  |
| 3    | HVAC + Hydrosanitary + Gas         | ✅ Listo  |
| 4    | CAD QA + Revit QA                  | ✅ Listo  |
| 5    | Semantic memory + vector DB        | 🔜 Futuro |
| 6    | Multi-agent orchestration          | 🔜 Futuro |
| 7    | Enterprise BIM workflows           | 🔜 Futuro |

---

## Licencia

MIT — uso libre para proyectos profesionales y académicos.

---

*Parte del ecosistema Personal AI Infrastructure (PAI)*
