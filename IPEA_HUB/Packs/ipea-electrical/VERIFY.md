# VERIFY — ipea-electrical

## Checklist de Verificación

### Scripts Python

```bash
[ ] python $PAI_DIR/scripts/python/voltage_drop.py
    → Debe mostrar tabla de caída de tensión y calibre mínimo

[ ] python $PAI_DIR/scripts/python/nom_validator.py
    → Debe mostrar reporte de validación NOM-001-SEDE-2012 con ✅/❌

[ ] python $PAI_DIR/scripts/python/load_calculation.py
    → Debe mostrar cédula de cargas completa
```

### Tablas Normativas

```bash
[ ] cat $PAI_DIR/standards/nom-001-sede-2012/tables.json | python -m json.tool
    → JSON válido sin errores

[ ] cat $PAI_DIR/standards/nom-001-sede-2012/factors.json | python -m json.tool
    → JSON válido sin errores
```

### Skill

```bash
[ ] ls $PAI_DIR/skills/electrical/ELECTRICAL.md
    → Debe existir
```

### Test de Cálculo Manual

Verificar manualmente:
- Circuito 3Φ, 220V, 45A, 80m, 6AWG cobre, FP=0.85
- Resistencia 6AWG Cu: 1.64 mΩ/m
- VD = √3 × (1.64/1000) × 80 × 45 × 0.85 = **8.66V = 3.94%**
- Límite NOM: 3% → ❌ FALLA (necesita 4AWG o superior)

```bash
[ ] El script confirma VD > 3% para ese circuito
[ ] El script sugiere 4AWG como mínimo para cumplir NOM
```

### Test de Reporte

```bash
[ ] python $PAI_DIR/scripts/python/report_generator.py
    → Genera /tmp/memoria_electrica.docx y /tmp/memoria_electrica.pdf
```

---

## Resultado Esperado

Todos los checks en ✅ = **ipea-electrical correctamente instalado**.
