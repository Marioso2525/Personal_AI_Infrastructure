# INSTALL — ipea-gas

## Prerequisito
ipea-core instalado.

## Paso 1: Copiar Scripts
```bash
mkdir -p $PAI_DIR/scripts/python
cp src/python/*.py $PAI_DIR/scripts/python/
```

## Paso 2: Copiar Skill
```bash
mkdir -p $PAI_DIR/skills/gas
cp src/skills/*.md $PAI_DIR/skills/gas/
```

## Paso 3: Verificar
```bash
python $PAI_DIR/scripts/python/gas_sizing.py
```
