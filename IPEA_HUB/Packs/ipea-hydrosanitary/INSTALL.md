# INSTALL — ipea-hydrosanitary

## Prerequisito
ipea-core instalado.

## Paso 1: Copiar Scripts
```bash
mkdir -p $PAI_DIR/scripts/python
cp src/python/*.py $PAI_DIR/scripts/python/
```

## Paso 2: Copiar Skill
```bash
mkdir -p $PAI_DIR/skills/hydrosanitary
cp src/skills/*.md $PAI_DIR/skills/hydrosanitary/
```

## Paso 3: Verificar
```bash
python $PAI_DIR/scripts/python/pipe_sizing.py
```
