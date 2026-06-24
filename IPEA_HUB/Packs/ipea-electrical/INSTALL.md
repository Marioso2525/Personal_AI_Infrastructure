# INSTALL — ipea-electrical

## Prerequisito

ipea-core debe estar instalado.

## Paso 1: Copiar Scripts Python

```bash
mkdir -p $PAI_DIR/scripts/python
cp src/python/voltage_drop.py $PAI_DIR/scripts/python/
cp src/python/nom_validator.py $PAI_DIR/scripts/python/
cp src/python/load_calculation.py $PAI_DIR/scripts/python/
cp src/python/report_generator.py $PAI_DIR/scripts/python/
```

## Paso 2: Copiar Tablas Normativas

```bash
mkdir -p $PAI_DIR/standards/nom-001-sede-2012
cp src/standards/nom-001-sede-2012/tables.json $PAI_DIR/standards/nom-001-sede-2012/
cp src/standards/nom-001-sede-2012/factors.json $PAI_DIR/standards/nom-001-sede-2012/
```

## Paso 3: Copiar Skill

```bash
mkdir -p $PAI_DIR/skills/electrical
cp src/skills/ELECTRICAL.md $PAI_DIR/skills/electrical/
```

## Paso 4: Instalar Dependencias Python

```bash
pip install python-docx reportlab openpyxl pandas numpy scipy
```

## Paso 5: Agregar Índice Normativo

```bash
cat > $PAI_DIR/standards/nom-001-sede-2012/index.json << 'EOF'
{
  "code": "NOM-001-SEDE-2012",
  "version": "2012",
  "title": "Instalaciones Eléctricas (Utilización)",
  "country": "México",
  "discipline": "electrical"
}
EOF
```

## Paso 6: Verificar

```bash
python $PAI_DIR/scripts/python/voltage_drop.py
python $PAI_DIR/scripts/python/nom_validator.py
python $PAI_DIR/scripts/python/load_calculation.py
```

Cada script debe ejecutarse sin errores y mostrar resultados de ejemplo.
