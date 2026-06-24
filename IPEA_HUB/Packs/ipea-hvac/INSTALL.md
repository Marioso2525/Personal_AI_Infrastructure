# INSTALL — ipea-hvac

## Prerequisito
ipea-core instalado.

## Paso 1: Copiar Scripts
```bash
mkdir -p $PAI_DIR/scripts/python
cp src/python/*.py $PAI_DIR/scripts/python/
```

## Paso 2: Copiar Skill
```bash
mkdir -p $PAI_DIR/skills/hvac
cp src/skills/*.md $PAI_DIR/skills/hvac/
```

## Paso 3: Verificar
```bash
python $PAI_DIR/scripts/python/duct_sizing.py
```
